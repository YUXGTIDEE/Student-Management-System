"""search/services.py  (Phụ trách: Bình)   UC: 11, 12, 13, 22

Quy tắc phân quyền (kiểm tra ở service, không chỉ ở view):
  - Admin: xem mọi sinh viên.
  - Teacher: chỉ xem sinh viên đang đăng ký (REGISTERED) trong section mình dạy, và chỉ thấy điểm của các section đó.
  - Role khác / tài khoản bị khóa: PERMISSION_DENIED.
Mọi hàm chỉ ĐỌC dữ liệu, không sửa gì.
"""
from django.db.models import Q

from accounts.models import Teacher
from common.contract import (AcademicStatus, EnrollmentStatus, ErrorCode, Gender, Page, Role,
                             ServiceError)
from common.pagination import paginate
from common.permissions import teacher_can_see_student, teacher_teaches_section
from courses.models import CourseSection
from registration.models import Enrollment
from students.models import Student

_ALLOWED_STATUSES = {value for value, _label in AcademicStatus.CHOICES}


# ---------------------------------------------------------------- helpers
def _deny(message="You do not have permission to perform this action."):
    return ServiceError(ErrorCode.PERMISSION_DENIED, message)


def _ensure_staff(user):
    """Chỉ Admin hoặc Teacher đang hoạt động."""
    if (getattr(user, "role", None) not in (Role.ADMINISTRATOR, Role.TEACHER)
            or getattr(user, "is_locked", False)):
        raise _deny()


def _ensure_teacher(user):
    if getattr(user, "role", None) != Role.TEACHER or getattr(user, "is_locked", False):
        raise _deny()
    teacher = Teacher.objects.filter(user=user).first()
    if teacher is None:
        raise _deny("No teacher profile is linked to this account.")
    return teacher


def _visible_students(user):
    """Queryset sinh viên mà user được phép thấy."""
    _ensure_staff(user)
    students = Student.objects.select_related("user")
    if user.role == Role.ADMINISTRATOR:
        return students
    teacher = _ensure_teacher(user)
    # Hai điều kiện trong CÙNG một filter() => áp dụng lên cùng một dòng enrollment
    return students.filter(enrollments__status=EnrollmentStatus.REGISTERED,
                           enrollments__section__teacher=teacher).distinct()


def _clean(value):
    return (value or "").strip() if isinstance(value, str) or value is None else str(value).strip()


def _map_page(page, func):
    return Page(items=[func(item) for item in page.items], page=page.page,
                num_pages=page.num_pages, total=page.total)


def _grade_value(value):
    return None if value is None else float(value)


# ---------------------------------------------------------------- UC 12, 22: tìm kiếm / lọc sinh viên
def search_students(user, keyword: str = "", student_class: str = "", major: str = "",
                    cohort: str = "", status: str = "", page: int = 1):
    """Trả về Page các dòng {student_id, student_code, full_name, student_class, major, academic_status}.
    keyword tìm theo mã hoặc họ tên (không phân biệt hoa thường); các bộ lọc còn lại là so khớp chính xác.
    Lỗi: PERMISSION_DENIED; VALIDATION nếu status không hợp lệ."""
    students = _visible_students(user)

    keyword, student_class = _clean(keyword), _clean(student_class)
    major, cohort, status = _clean(major), _clean(cohort), _clean(status)

    if status and status not in _ALLOWED_STATUSES:
        raise ServiceError(ErrorCode.VALIDATION, "Invalid academic status.",
                           [{"field": "status", "message": "Choose a valid academic status."}])

    if keyword:
        students = students.filter(Q(student_code__icontains=keyword) |
                                   Q(user__full_name__icontains=keyword))
    if student_class:
        students = students.filter(student_class__iexact=student_class)
    if major:
        students = students.filter(major__iexact=major)
    if cohort:
        students = students.filter(academic_cohort=cohort)
    if status:
        students = students.filter(academic_status=status)

    result = paginate(students.order_by("student_code"), page)
    return _map_page(result, lambda s: {
        "student_id": s.pk,
        "student_code": s.student_code,
        "full_name": s.user.full_name,
        "student_class": s.student_class,
        "major": s.major,
        "academic_status": s.academic_status,
    })


# ---------------------------------------------------------------- UC 13: hồ sơ chi tiết (chỉ đọc)
def get_student_detail(user, student_id: int) -> dict:
    """Hồ sơ chi tiết (chỉ đọc): thông tin cá nhân, liên hệ, section hiện tại, điểm của section GV dạy, trạng thái.
    Admin thấy các section đang đăng ký của sinh viên; Teacher chỉ thấy section do mình dạy.
    Lỗi: PERMISSION_DENIED (kể cả khi sinh viên không tồn tại, để giảng viên không dò được mã);
    NOT_FOUND chỉ dành cho Admin."""
    _ensure_staff(user)
    student = Student.objects.select_related("user").filter(pk=student_id).first()

    if user.role == Role.TEACHER:
        if student is None or not teacher_can_see_student(user, student):
            raise _deny("You can only view students enrolled in your own sections.")
    elif student is None:
        raise ServiceError(ErrorCode.NOT_FOUND, "Student not found.")

    enrollments = (Enrollment.objects
                   .filter(student=student, status=EnrollmentStatus.REGISTERED)
                   .select_related("section__course", "section__semester", "grade")
                   .order_by("-section__semester__start_date", "section__section_code"))
    if user.role == Role.TEACHER:
        enrollments = enrollments.filter(section__teacher__user=user)

    sections = []
    for enrollment in enrollments:
        section = enrollment.section
        grade = getattr(enrollment, "grade", None)      # chưa có điểm => None
        sections.append({
            "section_id": section.pk,
            "section_code": section.section_code,
            "course_code": section.course.course_code,
            "course_name": section.course.course_name,
            "semester_name": section.semester.semester_name,
            "classroom": section.classroom,
            "attendance_score": _grade_value(grade.attendance_score) if grade else None,
            "midterm_score": _grade_value(grade.midterm_score) if grade else None,
            "final_exam_score": _grade_value(grade.final_exam_score) if grade else None,
            "final_score": _grade_value(grade.final_score) if grade else None,
            "letter_grade": grade.letter_grade if grade else "",
        })

    account = student.user
    return {
        "student_id": student.pk,
        "student_code": student.student_code,
        "full_name": account.full_name,
        "date_of_birth": student.date_of_birth,
        "gender": student.gender,
        "gender_display": dict(Gender.CHOICES).get(student.gender, student.gender),
        "place_of_birth": student.place_of_birth,
        "email": account.email,
        "phone_number": account.phone_number,
        "address": account.address,
        "academic_cohort": student.academic_cohort,
        "major": student.major,
        "student_class": student.student_class,
        "academic_status": student.academic_status,
        "academic_status_display": dict(AcademicStatus.CHOICES).get(student.academic_status,
                                                                    student.academic_status),
        "sections": sections,
    }


# ---------------------------------------------------------------- UC 11: section được phân công
def list_assigned_sections(teacher_user, semester_id: int = None) -> list:
    """UC 11, bước 1: danh sách section giảng viên được phân công (mới nhất trước).
    Mỗi dòng: {section_id, section_code, course_code, course_name, semester_id, semester_name, classroom,
    max_capacity, current_enrollment, schedules: [{day_of_week, start_time, end_time}]}."""
    teacher = _ensure_teacher(teacher_user)
    sections = (CourseSection.objects.filter(teacher=teacher)
                .select_related("course", "semester").prefetch_related("schedules")
                .order_by("-semester__start_date", "section_code"))
    if semester_id not in (None, ""):
        try:
            sections = sections.filter(semester_id=int(semester_id))
        except (TypeError, ValueError):
            raise ServiceError(ErrorCode.VALIDATION, "Invalid semester.",
                               [{"field": "semester", "message": "Choose a valid semester."}])

    rows = []
    for section in sections:
        schedules = sorted(section.schedules.all(), key=lambda s: (s.day_of_week, s.start_time))
        rows.append({
            "section_id": section.pk,
            "section_code": section.section_code,
            "course_code": section.course.course_code,
            "course_name": section.course.course_name,
            "semester_id": section.semester_id,
            "semester_name": section.semester.semester_name,
            "classroom": section.classroom,
            "max_capacity": section.max_capacity,
            "current_enrollment": section.current_enrollment,
            "schedules": [{"day_of_week": s.day_of_week, "start_time": s.start_time,
                           "end_time": s.end_time} for s in schedules],
        })
    return rows


def list_section_students_for_teacher(teacher_user, section_id: int, page: int = 1):
    """UC 11, bước 3: Page các dòng {student_id, student_code, full_name, student_class}
    của sinh viên đang đăng ký section. Lỗi: PERMISSION_DENIED (kể cả section không tồn tại)."""
    _ensure_teacher(teacher_user)
    if not teacher_teaches_section(teacher_user, section_id):
        raise _deny("You are not assigned to this section.")

    students = (Student.objects.select_related("user")
                .filter(enrollments__section_id=section_id,
                        enrollments__status=EnrollmentStatus.REGISTERED)
                .order_by("student_code"))
    result = paginate(students, page)
    return _map_page(result, lambda s: {
        "student_id": s.pk,
        "student_code": s.student_code,
        "full_name": s.user.full_name,
        "student_class": s.student_class,
    })