"""registration/services.py  (Phụ trách: Duy)   UC: 7, 8, 9 (đánh số theo SRS: 6-9 phía sinh viên)"""

from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone

from common.contract import (
    EnrollmentStatus,
    ErrorCode,
    ServiceError,
)
from common.pagination import paginate
from courses.models import CourseSection
from grades.models import Grade
from .models import Enrollment


def _schedule_text(section):
    """Chuyển lịch học thành chuỗi để hiển thị trên giao diện."""
    day_names = [
        "Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5",
        "Thứ 6", "Thứ 7", "Chủ nhật",
    ]

    schedules = section.schedules.all().order_by(
        "day_of_week", "start_time"
    )

    result = []

    for item in schedules:
        day = (
            day_names[item.day_of_week]
            if 0 <= item.day_of_week <= 6
            else f"Ngày {item.day_of_week}"
        )

        result.append(
            f"{day} ({item.start_time.strftime('%H:%M')}"
            f" - {item.end_time.strftime('%H:%M')})"
        )

    return ", ".join(result)


def _get_registered_enrollments(student, semester_id=None):
    """Lấy các học phần sinh viên đang đăng ký."""
    queryset = Enrollment.objects.filter(
        student=student,
        status=EnrollmentStatus.REGISTERED,
    ).select_related(
        "section",
        "section__course",
        "section__semester",
    ).prefetch_related("section__schedules")

    if semester_id:
        queryset = queryset.filter(section__semester_id=semester_id)

    return queryset


def list_open_sections(student, semester_id: int, q: str = "", page: int = 1):
    """
    Danh sách lớp học phần trong một học kỳ.

    Mỗi dòng trả về:
    section_code, course_name, course_code, credits, teacher,
    schedule, classroom, max_capacity, remaining, state.
    """
    today = timezone.localdate()

    sections = CourseSection.objects.filter(
        semester_id=semester_id
    ).select_related(
        "course",
        "semester",
        "teacher__user",
    ).prefetch_related(
        "schedules",
        "enrollments",
    ).order_by("section_code")

    # Tìm kiếm theo mã lớp, mã môn hoặc tên môn.
    if q:
        sections = sections.filter(
            Q(section_code__icontains=q)
            | Q(course__course_code__icontains=q)
            | Q(course__course_name__icontains=q)
        )

    registered_ids = set(
        Enrollment.objects.filter(
            student=student,
            status=EnrollmentStatus.REGISTERED,
            section__semester_id=semester_id,
        ).values_list("section_id", flat=True)
    )

    rows = []

    for section in sections:
        remaining = max(
            section.max_capacity - section.current_enrollment,
            0,
        )

        # Xác định trạng thái của lớp học phần.
        if section.pk in registered_ids:
            state = "REGISTERED"
        elif not (
            section.semester.registration_start
            <= today
            <= section.semester.registration_end
        ):
            state = "CLOSED"
        elif remaining <= 0:
            state = "FULL"
        else:
            state = "OPEN"

        rows.append({
            "section_id": section.pk,
            "section_code": section.section_code,
            "course_name": section.course.course_name,
            "course_code": section.course.course_code,
            "credits": section.course.credit_hours,
            "teacher": section.teacher.user.full_name,
            "schedule": _schedule_text(section),
            "classroom": section.classroom,
            "max_capacity": section.max_capacity,
            "remaining": remaining,
            "state": state,
        })

    return paginate(rows, page)


def validate_registration(student, section) -> None:
    """
    Kiểm tra điều kiện trước khi đăng ký.

    Bao gồm:
    1. Đang trong thời gian đăng ký.
    2. Lớp còn chỗ.
    3. Sinh viên chưa đăng ký lớp này.
    4. Không trùng lịch.
    5. Đã qua các môn tiên quyết.
    """
    today = timezone.localdate()

    # Điều kiện 1: kiểm tra thời gian đăng ký.
    semester = section.semester

    if not (
        semester.registration_start
        <= today
        <= semester.registration_end
    ):
        raise ServiceError(
            ErrorCode.REGISTRATION_CLOSED,
            "Đã hết thời gian đăng ký học phần.",
        )

    # Điều kiện 2: kiểm tra sức chứa.
    if section.current_enrollment >= section.max_capacity:
        raise ServiceError(
            ErrorCode.SECTION_FULL,
            "Lớp học phần đã đủ sĩ số.",
        )

    # Điều kiện 3: không được đăng ký trùng.
    existing = Enrollment.objects.filter(
        student=student,
        section=section,
        status=EnrollmentStatus.REGISTERED,
    ).exists()

    if existing:
        raise ServiceError(
            ErrorCode.ALREADY_REGISTERED,
            "Bạn đã đăng ký lớp học phần này.",
        )

    # Điều kiện 4: kiểm tra trùng lịch học.
    current_schedules = list(section.schedules.all())

    registered_enrollments = _get_registered_enrollments(
        student,
        semester.pk,
    )

    for enrollment in registered_enrollments:
        other_schedules = enrollment.section.schedules.all()

        for current in current_schedules:
            for other in other_schedules:
                same_day = (
                    current.day_of_week == other.day_of_week
                )

                overlap = (
                    current.start_time < other.end_time
                    and other.start_time < current.end_time
                )

                if same_day and overlap:
                    raise ServiceError(
                        ErrorCode.SCHEDULE_CONFLICT,
                        "Lịch học bị trùng với một học phần đã đăng ký.",
                    )

    # Điều kiện 5: kiểm tra các môn tiên quyết.
    prerequisite_ids = list(
        section.course.prerequisites.values_list("id", flat=True)
    )

    if prerequisite_ids:
        passed_prerequisites = set(
            Grade.objects.filter(
                enrollment__student=student,
                enrollment__status=EnrollmentStatus.REGISTERED,
                enrollment__section__course_id__in=prerequisite_ids,
                gradebook__is_locked=True,
                passed=True,
            ).values_list(
                "enrollment__section__course_id",
                flat=True,
            )
        )

        missing_prerequisites = (
            set(prerequisite_ids) - passed_prerequisites
        )

        if missing_prerequisites:
            raise ServiceError(
                ErrorCode.PREREQ_NOT_MET,
                "Bạn chưa hoàn thành các môn học tiên quyết.",
                details=list(missing_prerequisites),
            )


def register_section(student, section_id: int):
    """
    Đăng ký lớp học phần.

    Toàn bộ quá trình chạy trong transaction:
    - Khóa bản ghi section.
    - Kiểm tra điều kiện.
    - Tăng sĩ số bằng UPDATE nguyên tử.
    - Tạo Enrollment hoặc cập nhật lại Enrollment đã hủy.
    """
    with transaction.atomic():
        try:
            section = CourseSection.objects.select_for_update().select_related(
                "course",
                "semester",
            ).get(pk=section_id)
        except CourseSection.DoesNotExist:
            raise ServiceError(
                ErrorCode.NOT_FOUND,
                "Không tìm thấy lớp học phần.",
            )

        # Kiểm tra lại toàn bộ điều kiện tại thời điểm đăng ký thật.
        validate_registration(student, section)

        # Cập nhật sĩ số nguyên tử, không cho vượt sức chứa.
        updated = CourseSection.objects.filter(
            pk=section_id,
            current_enrollment__lt=F("max_capacity"),
        ).update(
            current_enrollment=F("current_enrollment") + 1
        )

        if updated == 0:
            raise ServiceError(
                ErrorCode.SECTION_FULL,
                "Lớp học phần vừa đủ sĩ số. Vui lòng chọn lớp khác.",
            )

        # Nếu sinh viên đã hủy trước đó thì kích hoạt lại Enrollment.
        enrollment, created = Enrollment.objects.get_or_create(
            student=student,
            section=section,
            defaults={
                "status": EnrollmentStatus.REGISTERED,
            },
        )

        if not created:
            enrollment.status = EnrollmentStatus.REGISTERED
            enrollment.cancelled_at = None
            enrollment.registered_at = timezone.now()
            enrollment.save(
                update_fields=[
                    "status",
                    "cancelled_at",
                    "registered_at",
                ]
            )

        return enrollment


def cancel_registration(student, section_id: int) -> None:
    """
    Hủy đăng ký học phần.

    Không xóa Enrollment.
    Chỉ đổi trạng thái thành CANCELLED và giảm sĩ số.
    """
    with transaction.atomic():
        try:
            enrollment = Enrollment.objects.select_for_update().select_related(
                "section__semester"
            ).get(
                student=student,
                section_id=section_id,
                status=EnrollmentStatus.REGISTERED,
            )
        except Enrollment.DoesNotExist:
            raise ServiceError(
                ErrorCode.NOT_FOUND,
                "Không tìm thấy đăng ký học phần đang hoạt động.",
            )

        today = timezone.localdate()

        if today > enrollment.section.semester.cancellation_deadline:
            raise ServiceError(
                ErrorCode.CANCEL_DEADLINE_PASSED,
                "Đã quá hạn hủy đăng ký học phần.",
            )

        # Giảm sĩ số bằng cập nhật nguyên tử.
        updated = CourseSection.objects.filter(
            pk=section_id,
            current_enrollment__gt=0,
        ).update(
            current_enrollment=F("current_enrollment") - 1
        )

        if updated == 0:
            raise ServiceError(
                ErrorCode.VALIDATION,
                "Không thể cập nhật sĩ số lớp học phần.",
            )

        enrollment.status = EnrollmentStatus.CANCELLED
        enrollment.cancelled_at = timezone.now()
        enrollment.save(
            update_fields=["status", "cancelled_at"]
        )


def list_registered_sections(student, semester_id: int = None) -> list:
    """
    Danh sách học phần sinh viên đã đăng ký.

    Mỗi dòng gồm:
    section_code, course_name, teacher, schedule,
    registered_at, can_cancel.
    """
    today = timezone.localdate()

    enrollments = _get_registered_enrollments(
        student,
        semester_id,
    ).order_by(
        "section__semester__start_date",
        "section__section_code",
    )

    rows = []

    for enrollment in enrollments:
        section = enrollment.section

        rows.append({
            "enrollment_id": enrollment.pk,
            "section_id": section.pk,
            "section_code": section.section_code,
            "course_name": section.course.course_name,
            "teacher": section.teacher.user.full_name,
            "schedule": _schedule_text(section),
            "classroom": section.classroom,
            "registered_at": enrollment.registered_at,
            "can_cancel": (
                today <= section.semester.cancellation_deadline
            ),
        })

    return rows

