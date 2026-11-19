"""grades/services.py  (Phụ trách: Duy)   UC: 10, 14, 15, 16, 17, 18 (theo SRS: xem điểm, nhập/sửa, khóa, mở khóa)"""

from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.db.models import Q

from common.contract import (
    EnrollmentStatus,
    ErrorCode,
    Role,
    ServiceError,
)
from common.pagination import paginate
from common.permissions import teacher_teaches_section

from accounts.models import Teacher
from courses.models import CourseSection
from registration.models import Enrollment
from students.models import Student

from .models import (
    Grade,
    Gradebook,
    GradeEditLog,
    GradebookUnlockLog,
    SemesterGPA,
)

from .calculator import (
    validate_scores,
    calculate_final_score,
    convert_to_letter,
    convert_to_grade_point4,
    is_passed,
    calculate_gpa,
)


def _check_teacher_permission(teacher_user, section_id):
    """Kiểm tra tài khoản giảng viên có được phân công lớp này không."""
    if getattr(teacher_user, "role", None) != Role.TEACHER:
        raise ServiceError(
            ErrorCode.PERMISSION_DENIED,
            "Tài khoản không phải giảng viên.",
        )

    if not teacher_teaches_section(teacher_user, section_id):
        raise ServiceError(
            ErrorCode.PERMISSION_DENIED,
            "Bạn không được phân công giảng dạy lớp học phần này.",
        )


def _check_admin_permission(admin_user):
    """Kiểm tra quyền quản trị viên."""
    if getattr(admin_user, "role", None) != Role.ADMINISTRATOR:
        raise ServiceError(
            ErrorCode.PERMISSION_DENIED,
            "Bạn không có quyền thực hiện chức năng này.",
        )


def _get_gradebook(section_id):
    """Lấy gradebook theo lớp học phần."""
    try:
        section = CourseSection.objects.select_related(
            "course",
            "semester",
            "teacher__user",
        ).get(pk=section_id)
    except CourseSection.DoesNotExist:
        raise ServiceError(
            ErrorCode.NOT_FOUND,
            "Không tìm thấy lớp học phần.",
        )

    # Gradebook được thiết kế tạo tự động khi tạo section.
    # get_or_create giúp tránh lỗi nếu dữ liệu cũ chưa có gradebook.
    gradebook, _ = Gradebook.objects.get_or_create(
        section=section,
    )

    return gradebook


def _get_registered_enrollments(section):
    """Lấy danh sách sinh viên đang đăng ký trong lớp học phần."""
    return Enrollment.objects.filter(
        section=section,
        status=EnrollmentStatus.REGISTERED,
    ).select_related(
        "student",
        "student__user",
    ).order_by("student__student_code")


def _get_or_create_grades(gradebook, enrollments):
    """Đảm bảo mỗi Enrollment có một Grade trong gradebook."""
    grades = []

    for enrollment in enrollments:
        grade, _ = Grade.objects.get_or_create(
            enrollment=enrollment,
            defaults={"gradebook": gradebook},
        )

        grades.append(grade)

    return grades


def get_gradebook(teacher_user, section_id: int) -> dict:
    """
    Trả về bảng điểm của lớp học phần.

    Chỉ giảng viên được phân công mới được xem bảng điểm.
    """
    _check_teacher_permission(teacher_user, section_id)

    gradebook = _get_gradebook(section_id)

    enrollments = list(
        _get_registered_enrollments(gradebook.section)
    )

    grades = _get_or_create_grades(
        gradebook,
        enrollments,
    )

    # Ghép điểm với thông tin sinh viên.
    grade_by_enrollment = {
        grade.enrollment_id: grade
        for grade in grades
    }

    rows = []

    for enrollment in enrollments:
        grade = grade_by_enrollment[enrollment.pk]

        rows.append({
            "enrollment_id": enrollment.pk,
            "student_code": enrollment.student.student_code,
            "full_name": enrollment.student.user.full_name,
            "attendance": grade.attendance_score,
            "midterm": grade.midterm_score,
            "final": grade.final_exam_score,
            "final_score": grade.final_score,
            "letter": grade.letter_grade,
            "gp4": grade.grade_point4,
            "passed": grade.passed,
        })

    return {
        "section": gradebook.section,
        "gradebook": gradebook,
        "is_locked": gradebook.is_locked,
        "weights": {
            "attendance": gradebook.attendance_weight,
            "midterm": gradebook.midterm_weight,
            "final": gradebook.final_weight,
        },
        "rows": rows,
    }


def save_grades(teacher_user, section_id: int, entries: list) -> None:
    """
    Lưu hoặc sửa điểm cho nhiều sinh viên.

    Quy trình:
    1. Kiểm tra quyền giảng viên.
    2. Kiểm tra gradebook đã khóa chưa.
    3. Kiểm tra toàn bộ dữ liệu điểm.
    4. Nếu có lỗi thì không lưu dòng nào.
    5. Lưu điểm và tính điểm tổng kết.
    6. Ghi GradeEditLog cho các giá trị thay đổi.
    """
    _check_teacher_permission(teacher_user, section_id)

    if not isinstance(entries, list) or not entries:
        raise ServiceError(
            ErrorCode.MISSING_FIELDS,
            "Danh sách điểm không được để trống.",
        )

    with transaction.atomic():
        gradebook = _get_gradebook(section_id)

        # Khóa gradebook để tránh hai request sửa điểm đồng thời.
        gradebook = Gradebook.objects.select_for_update().get(
            pk=gradebook.pk
        )

        if gradebook.is_locked:
            raise ServiceError(
                ErrorCode.GRADEBOOK_LOCKED,
                "Bảng điểm đã khóa, không thể chỉnh sửa.",
            )

        valid_enrollments = {
            enrollment.pk: enrollment
            for enrollment in _get_registered_enrollments(
                gradebook.section
            )
        }

        prepared_entries = []
        all_errors = []
        seen_ids = set()

        # Kiểm tra tất cả dòng trước khi ghi database.
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                all_errors.append({
                    "row": index,
                    "reason": "Dữ liệu dòng điểm không hợp lệ.",
                })
                continue

            enrollment_id = entry.get("enrollment_id")

            try:
                enrollment_id = int(enrollment_id)
            except (TypeError, ValueError):
                all_errors.append({
                    "row": index,
                    "reason": "Mã đăng ký học phần không hợp lệ.",
                })
                continue

            if enrollment_id in seen_ids:
                all_errors.append({
                    "row": index,
                    "enrollment_id": enrollment_id,
                    "reason": "Dòng đăng ký bị lặp.",
                })
                continue

            seen_ids.add(enrollment_id)

            if enrollment_id not in valid_enrollments:
                all_errors.append({
                    "row": index,
                    "enrollment_id": enrollment_id,
                    "reason": "Sinh viên không thuộc lớp học phần này.",
                })
                continue

            scores = {
                "attendance": entry.get("attendance"),
                "midterm": entry.get("midterm"),
                "final": entry.get("final"),
            }

            errors = validate_scores(scores)

            if errors:
                all_errors.extend([
                    {
                        "row": index,
                        "enrollment_id": enrollment_id,
                        **error,
                    }
                    for error in errors
                ])
                continue

            try:
                decimal_scores = {
                    key: Decimal(str(value))
                    for key, value in scores.items()
                }
            except (InvalidOperation, TypeError, ValueError):
                all_errors.append({
                    "row": index,
                    "enrollment_id": enrollment_id,
                    "reason": "Điểm không hợp lệ.",
                })
                continue

            prepared_entries.append({
                "enrollment": valid_enrollments[enrollment_id],
                "scores": decimal_scores,
            })

        if all_errors:
            raise ServiceError(
                ErrorCode.GRADE_OUT_OF_RANGE,
                "Có dữ liệu điểm không hợp lệ. Không có dòng nào được lưu.",
                details=all_errors,
            )

        # Trọng số lấy trực tiếp từ Gradebook.
        weights = {
            "attendance": gradebook.attendance_weight,
            "midterm": gradebook.midterm_weight,
            "final": gradebook.final_weight,
        }

        # Chỉ bắt đầu lưu khi toàn bộ dữ liệu hợp lệ.
        for item in prepared_entries:
            enrollment = item["enrollment"]
            scores = item["scores"]

            grade, _ = Grade.objects.get_or_create(
                enrollment=enrollment,
                defaults={"gradebook": gradebook},
            )

            if grade.gradebook_id != gradebook.pk:
                raise ServiceError(
                    ErrorCode.VALIDATION,
                    "Grade không thuộc gradebook của lớp học phần này.",
                )

            score_fields = {
                "attendance": (
                    "attendance_score",
                    scores["attendance"],
                ),
                "midterm": (
                    "midterm_score",
                    scores["midterm"],
                ),
                "final": (
                    "final_exam_score",
                    scores["final"],
                ),
            }

            # Chỉ ghi log khi giá trị thực sự thay đổi.
            for field_name, (model_field, new_value) in score_fields.items():
                old_value = getattr(grade, model_field)

                if old_value != new_value:
                    GradeEditLog.objects.create(
                        grade=grade,
                        editor=teacher_user,
                        field=field_name,
                        old_value=old_value,
                        new_value=new_value,
                    )

                    setattr(grade, model_field, new_value)

            # Tính điểm tổng kết và quy đổi điểm chữ.
            final_score = calculate_final_score(
                scores["attendance"],
                scores["midterm"],
                scores["final"],
                weights,
            )

            grade.final_score = final_score
            grade.letter_grade = convert_to_letter(final_score)
            grade.grade_point4 = convert_to_grade_point4(final_score)
            grade.passed = is_passed(final_score)

            grade.save()


def lock_gradebook(teacher_user, section_id: int) -> None:
    """
    Khóa bảng điểm.

    Không cho khóa nếu còn sinh viên chưa đủ 3 đầu điểm.
    Sau khi khóa, tính lại GPA cho từng sinh viên.
    """
    _check_teacher_permission(teacher_user, section_id)

    with transaction.atomic():
        gradebook = _get_gradebook(section_id)

        gradebook = Gradebook.objects.select_for_update().get(
            pk=gradebook.pk
        )

        if gradebook.is_locked:
            return

        enrollments = list(
            _get_registered_enrollments(gradebook.section)
        )

        grades = _get_or_create_grades(
            gradebook,
            enrollments,
        )

        incomplete = []

        grade_by_enrollment = {
            grade.enrollment_id: grade
            for grade in grades
        }

        # Kiểm tra từng sinh viên đã có đủ điểm chưa.
        for enrollment in enrollments:
            grade = grade_by_enrollment[enrollment.pk]

            if (
                grade.attendance_score is None
                or grade.midterm_score is None
                or grade.final_exam_score is None
            ):
                incomplete.append({
                    "student_code": enrollment.student.student_code,
                    "full_name": enrollment.student.user.full_name,
                })

        if incomplete:
            raise ServiceError(
                ErrorCode.GRADES_INCOMPLETE,
                "Không thể khóa bảng điểm vì còn sinh viên chưa đủ điểm.",
                details=incomplete,
            )

        # Khóa bảng điểm.
        gradebook.is_locked = True
        gradebook.save(update_fields=["is_locked"])

        # Tính lại GPA cho từng sinh viên trong học kỳ này.
        student_ids = {
            enrollment.student_id
            for enrollment in enrollments
        }

        for student in Student.objects.filter(pk__in=student_ids):
            recalculate_semester_gpa(
                student,
                gradebook.section.semester,
            )


def list_locked_gradebooks(admin_user, page: int = 1):
    """Danh sách gradebook đã khóa dành cho Admin."""
    _check_admin_permission(admin_user)

    gradebooks = Gradebook.objects.filter(
        is_locked=True
    ).select_related(
        "section",
        "section__course",
        "section__semester",
        "section__teacher__user",
    ).order_by(
        "-section__semester__start_date",
        "section__section_code",
    )

    return paginate(gradebooks, page)


def unlock_gradebook(admin_user, section_id: int, reason: str) -> None:
    """
    Admin mở khóa bảng điểm.

    Bắt buộc có lý do và lưu lại lịch sử mở khóa.
    Theo DECISIONS #8, GPA sẽ được tính lại khi gradebook
    được khóa lần tiếp theo.
    """
    _check_admin_permission(admin_user)

    reason = (reason or "").strip()

    if not reason:
        raise ServiceError(
            ErrorCode.UNLOCK_REASON_REQUIRED,
            "Vui lòng nhập lý do mở khóa bảng điểm.",
        )

    if len(reason) > 255:
        raise ServiceError(
            ErrorCode.VALIDATION,
            "Lý do mở khóa không được vượt quá 255 ký tự.",
        )

    with transaction.atomic():
        gradebook = _get_gradebook(section_id)

        gradebook = Gradebook.objects.select_for_update().get(
            pk=gradebook.pk
        )

        if not gradebook.is_locked:
            raise ServiceError(
                ErrorCode.VALIDATION,
                "Bảng điểm hiện không ở trạng thái đã khóa.",
            )

        gradebook.is_locked = False
        gradebook.save(update_fields=["is_locked"])

        GradebookUnlockLog.objects.create(
            gradebook=gradebook,
            admin=admin_user,
            reason=reason,
        )


def get_unlock_history(admin_user, section_id: int = None) -> list:
    """Lấy lịch sử mở khóa gradebook dành cho Admin."""
    _check_admin_permission(admin_user)

    history = GradebookUnlockLog.objects.select_related(
        "gradebook",
        "gradebook__section",
        "admin",
    ).order_by("-unlocked_at")

    if section_id is not None:
        history = history.filter(
            gradebook__section_id=section_id
        )

    return list(history)


def get_student_results(student, semester_id: int = None) -> dict:
    """
    Lấy kết quả học tập của sinh viên.

    Theo chữ ký hàm và mô tả services.py:
    - rows chỉ lấy từ gradebook đã khóa.
    - has_unlocked cho biết có bảng điểm đang mở khóa hay không.
    """
    enrollments = Enrollment.objects.filter(
        student=student,
        status=EnrollmentStatus.REGISTERED,
    ).select_related(
        "section",
        "section__course",
        "section__semester",
    ).prefetch_related(
        "section__gradebook",
        "section__gradebook__grades",
    )

    if semester_id is not None:
        enrollments = enrollments.filter(
            section__semester_id=semester_id
        )

    rows = []
    gpa_items = []

    has_unlocked = False

    for enrollment in enrollments:
        gradebook = getattr(
            enrollment.section,
            "gradebook",
            None,
        )

        if gradebook is None:
            continue

        # Ghi nhận có gradebook đang được mở khóa.
        if not gradebook.is_locked:
            has_unlocked = True
            continue

        try:
            grade = enrollment.grade
        except Grade.DoesNotExist:
            continue

        rows.append({
            "section_code": enrollment.section.section_code,
            "course_name": enrollment.section.course.course_name,
            "credits": enrollment.section.course.credit_hours,
            "attendance": grade.attendance_score,
            "midterm": grade.midterm_score,
            "final": grade.final_exam_score,
            "final_score": grade.final_score,
            "letter": grade.letter_grade,
            "passed": grade.passed,
        })

        if grade.grade_point4 is not None:
            credits = enrollment.section.course.credit_hours

            gpa_items.append((
                grade.grade_point4,
                credits,
            ))

    return {
        "rows": rows,
        "gpa": calculate_gpa(gpa_items),
        "academic_status": student.academic_status,
        "has_unlocked": has_unlocked,
    }


def recalculate_semester_gpa(student, semester) -> None:
    """
    Tính lại GPA của sinh viên trong một học kỳ.

    Chỉ tính các Grade thuộc gradebook đã khóa.
    GPA = tổng (điểm hệ 4 x tín chỉ) / tổng tín chỉ.
    """
    grades = Grade.objects.filter(
        enrollment__student=student,
        enrollment__status=EnrollmentStatus.REGISTERED,
        enrollment__section__semester=semester,
        gradebook__is_locked=True,
        grade_point4__isnull=False,
    ).select_related(
        "enrollment__section__course",
    )

    items = []
    total_credits = 0

    for grade in grades:
        credits = grade.enrollment.section.course.credit_hours

        items.append((
            grade.grade_point4,
            credits,
        ))

        total_credits += credits

    gpa = calculate_gpa(items)

    SemesterGPA.objects.update_or_create(
        student=student,
        semester=semester,
        defaults={
            "gpa": gpa,
            "total_credits": total_credits,
        },
    )

