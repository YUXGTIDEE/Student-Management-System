"""courses/services.py  (Phụ trách: Minh)   UC: 6 (xem section), 26, 27, 28 (xem DS sinh viên của section)"""
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Exists, OuterRef, Q
from django.utils.dateparse import parse_time

from common.contract import (
    DEFAULT_WEIGHTS, EnrollmentStatus, ErrorCode, Page, PAGE_SIZE, Role, ServiceError,
)
from .models import Course, CourseSection, SectionSchedule, Semester


# ---------------------------------------------------------------- hàm phụ
def _check_admin(user):
    if getattr(user, "role", None) != Role.ADMINISTRATOR:
        raise ServiceError(ErrorCode.PERMISSION_DENIED, "Chỉ Administrator mới được thực hiện")


def _is_empty(value):
    return value is None or (isinstance(value, str) and not value.strip())


def _paginate(qs, page):
    paginator = Paginator(qs, PAGE_SIZE)
    page_obj = paginator.get_page(page)
    return Page(list(page_obj.object_list), page_obj.number, paginator.num_pages, paginator.count)


def _to_positive_int(value, field):
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ServiceError(ErrorCode.VALIDATION, f"{field} phải là số nguyên")
    if number <= 0:
        raise ServiceError(ErrorCode.VALIDATION, f"{field} phải lớn hơn 0")
    return number


def _to_time(value, field):
    if hasattr(value, "hour"):          # đã là kiểu time
        return value
    parsed = parse_time(str(value)) if value else None
    if parsed is None:
        raise ServiceError(ErrorCode.VALIDATION, f"{field} không hợp lệ (dạng HH:MM)")
    return parsed


def _check_required(**fields):
    missing = [name for name, value in fields.items() if _is_empty(value)]
    if missing:
        raise ServiceError(ErrorCode.MISSING_FIELDS, "Thiếu thông tin: " + ", ".join(missing), missing)


# ---- UC 26: quản lý course ------------------------------------------------------
def list_courses(q: str = "", page: int = 1):
    """Mỗi dòng có thêm cờ in_use (đã có section) để FE hiện nhãn 'In use'."""
    qs = Course.objects.annotate(
        in_use=Exists(CourseSection.objects.filter(course=OuterRef("pk")))
    ).order_by("course_code")
    q = (q or "").strip()
    if q:
        qs = qs.filter(Q(course_code__icontains=q) | Q(course_name__icontains=q))
    return _paginate(qs, page)


def create_course(admin_user, course_code: str, course_name: str, credit_hours: int,
                  class_periods: int, description: str = ""):
    """Lỗi: DUPLICATE, VALIDATION."""
    _check_admin(admin_user)
    _check_required(course_code=course_code, course_name=course_name,
                    credit_hours=credit_hours, class_periods=class_periods)

    course_code = course_code.strip()
    course_name = course_name.strip()
    credit_hours = _to_positive_int(credit_hours, "Số tín chỉ")
    class_periods = _to_positive_int(class_periods, "Số tiết")

    if Course.objects.filter(course_code__iexact=course_code).exists():
        raise ServiceError(ErrorCode.DUPLICATE, "Mã môn học đã tồn tại")

    return Course.objects.create(
        course_code=course_code, course_name=course_name,
        credit_hours=credit_hours, class_periods=class_periods,
        description=(description or "").strip(),
    )


def update_course(admin_user, course_id: int, course_name: str, credit_hours: int,
                  class_periods: int, description: str = "") -> None:
    _check_admin(admin_user)
    course = Course.objects.filter(pk=course_id).first()
    if course is None:
        raise ServiceError(ErrorCode.NOT_FOUND, "Không tìm thấy môn học")

    _check_required(course_name=course_name, credit_hours=credit_hours, class_periods=class_periods)

    course.course_name = course_name.strip()
    course.credit_hours = _to_positive_int(credit_hours, "Số tín chỉ")
    course.class_periods = _to_positive_int(class_periods, "Số tiết")
    course.description = (description or "").strip()
    course.save()                       # không đụng tới course_code


def delete_course(admin_user, course_id: int) -> None:
    """Lỗi: COURSE_IN_USE nếu đã có section hoặc grade."""
    _check_admin(admin_user)
    course = Course.objects.filter(pk=course_id).first()
    if course is None:
        raise ServiceError(ErrorCode.NOT_FOUND, "Không tìm thấy môn học")

    # Điểm (grade) luôn gắn với section, nên chỉ cần kiểm tra section là đủ.
    if CourseSection.objects.filter(course=course).exists():
        raise ServiceError(ErrorCode.COURSE_IN_USE, "Môn học đã có lớp học phần, không thể xóa")
    course.delete()


def set_prerequisites(admin_user, course_id: int, prerequisite_ids: list) -> None:
    """Lỗi: PREREQ_CYCLE nếu tạo vòng lặp trực tiếp hoặc gián tiếp."""
    _check_admin(admin_user)
    course = Course.objects.filter(pk=course_id).first()
    if course is None:
        raise ServiceError(ErrorCode.NOT_FOUND, "Không tìm thấy môn học")

    try:
        ids = {int(x) for x in (prerequisite_ids or [])}
    except (TypeError, ValueError):
        raise ServiceError(ErrorCode.VALIDATION, "Danh sách môn tiên quyết không hợp lệ")

    if Course.objects.filter(pk__in=ids).count() != len(ids):
        raise ServiceError(ErrorCode.NOT_FOUND, "Có môn tiên quyết không tồn tại")

    # Dựng đồ thị "môn A cần môn B" từ DB, bỏ các cạnh của course này (vì sắp thay mới)
    Through = Course.prerequisites.through
    edges = {}
    for frm, to in Through.objects.exclude(from_course_id=course_id).values_list(
            "from_course_id", "to_course_id"):
        edges.setdefault(frm, set()).add(to)

    def reaches_course(start):
        """Đi theo các môn tiên quyết từ `start`, có gặp lại course_id không?"""
        stack, seen = [start], set()
        while stack:
            node = stack.pop()
            if node == course_id:
                return True
            if node in seen:
                continue
            seen.add(node)
            stack.extend(edges.get(node, ()))
        return False

    for pid in ids:                     # pid == course_id (tự tiên quyết chính mình) cũng bị bắt ở đây
        if reaches_course(pid):
            raise ServiceError(ErrorCode.PREREQ_CYCLE, "Môn tiên quyết tạo thành vòng lặp")

    course.prerequisites.set(ids)


# ---- UC 27: tạo section --------------------------------------------------------------
def _create_default_gradebook(section):
    """Tạo Gradebook mặc định 10/30/60.
    !!! Phụ thuộc app grades của bạn khác: nếu tên model/field khác thì sửa ở đây."""
    from grades.models import Gradebook
    Gradebook.objects.create(
        section=section,
        attendance_weight=DEFAULT_WEIGHTS["attendance"],
        midterm_weight=DEFAULT_WEIGHTS["midterm"],
        final_weight=DEFAULT_WEIGHTS["final"],
    )


def _overlap_exists(semester_id, day, start, end, **extra_filter):
    """Hai khoảng giờ trùng nhau khi: start1 < end2 và start2 < end1."""
    return SectionSchedule.objects.filter(
        section__semester_id=semester_id, day_of_week=day,
        start_time__lt=end, end_time__gt=start, **extra_filter,
    ).exists()


def create_section(admin_user, section_code: str, course_id: int, semester_id: int, teacher_id: int,
                   classroom: str, max_capacity: int, schedules: list):
    """schedules: [{day_of_week, start_time, end_time}].
    Tự tạo Gradebook mặc định (10/30/60) cho section.
    Lỗi: DUPLICATE (mã section), TEACHER_CONFLICT, ROOM_CONFLICT."""
    _check_admin(admin_user)
    _check_required(section_code=section_code, course_id=course_id, semester_id=semester_id,
                    teacher_id=teacher_id, classroom=classroom, max_capacity=max_capacity)
    if not schedules:
        raise ServiceError(ErrorCode.MISSING_FIELDS, "Thiếu thông tin: schedules", ["schedules"])

    section_code = section_code.strip()
    classroom = classroom.strip()
    course_id = _to_positive_int(course_id, "Course")
    semester_id = _to_positive_int(semester_id, "Semester")
    teacher_id = _to_positive_int(teacher_id, "Teacher")
    max_capacity = _to_positive_int(max_capacity, "Sĩ số tối đa")

    # Làm sạch lịch học
    cleaned = []
    for s in schedules:
        day = s.get("day_of_week")
        try:
            day = int(day)
        except (TypeError, ValueError):
            raise ServiceError(ErrorCode.VALIDATION, "Thứ trong tuần không hợp lệ")
        if not 0 <= day <= 6:
            raise ServiceError(ErrorCode.VALIDATION, "Thứ trong tuần phải từ 0 (Thứ 2) đến 6 (Chủ nhật)")
        start = _to_time(s.get("start_time"), "Giờ bắt đầu")
        end = _to_time(s.get("end_time"), "Giờ kết thúc")
        if start >= end:
            raise ServiceError(ErrorCode.VALIDATION, "Giờ bắt đầu phải trước giờ kết thúc")
        cleaned.append((day, start, end))

    # Các buổi trong cùng 1 section không được chồng nhau
    for i in range(len(cleaned)):
        for j in range(i + 1, len(cleaned)):
            d1, s1, e1 = cleaned[i]
            d2, s2, e2 = cleaned[j]
            if d1 == d2 and s1 < e2 and s2 < e1:
                raise ServiceError(ErrorCode.VALIDATION, "Các buổi học của section bị chồng giờ nhau")

    # Kiểm tra tồn tại
    if not Course.objects.filter(pk=course_id).exists():
        raise ServiceError(ErrorCode.NOT_FOUND, "Không tìm thấy môn học")
    if not Semester.objects.filter(pk=semester_id).exists():
        raise ServiceError(ErrorCode.NOT_FOUND, "Không tìm thấy học kỳ")
    Teacher = CourseSection._meta.get_field("teacher").related_model
    if not Teacher.objects.filter(pk=teacher_id).exists():
        raise ServiceError(ErrorCode.NOT_FOUND, "Không tìm thấy giảng viên")

    if CourseSection.objects.filter(section_code__iexact=section_code).exists():
        raise ServiceError(ErrorCode.DUPLICATE, "Mã section đã tồn tại")

    # Trùng lịch giảng viên / phòng học trong cùng học kỳ
    for day, start, end in cleaned:
        if _overlap_exists(semester_id, day, start, end, section__teacher_id=teacher_id):
            raise ServiceError(ErrorCode.TEACHER_CONFLICT, "Giảng viên bị trùng lịch dạy")
        if _overlap_exists(semester_id, day, start, end, section__classroom__iexact=classroom):
            raise ServiceError(ErrorCode.ROOM_CONFLICT, "Phòng học bị trùng lịch")

    # Tạo section + lịch + gradebook trong 1 transaction
    with transaction.atomic():
        section = CourseSection.objects.create(
            section_code=section_code, course_id=course_id, semester_id=semester_id,
            teacher_id=teacher_id, classroom=classroom, max_capacity=max_capacity,
        )
        SectionSchedule.objects.bulk_create([
            SectionSchedule(section=section, day_of_week=d, start_time=s, end_time=e)
            for d, s, e in cleaned
        ])
        _create_default_gradebook(section)
    return section


# ---- UC 6, 28: xem section --------------------------------------------------------
def list_offered_sections(semester_id: int, q: str = "", page: int = 1):
    """Các section của học kỳ. Dùng cho Student/Teacher/Admin xem."""
    qs = (CourseSection.objects.filter(semester_id=semester_id)
          .select_related("course", "teacher")
          .prefetch_related("schedules")
          .order_by("section_code"))
    q = (q or "").strip()
    if q:
        qs = qs.filter(
            Q(section_code__icontains=q)
            | Q(course__course_code__icontains=q)
            | Q(course__course_name__icontains=q)
        )
    return _paginate(qs, page)


def list_section_students(admin_user, section_id: int, page: int = 1) -> dict:
    """Trả về {section, current_enrollment, max_capacity, students: Page{student_code, full_name, class, registered_at}}."""
    _check_admin(admin_user)
    section = CourseSection.objects.filter(pk=section_id).first()
    if section is None:
        raise ServiceError(ErrorCode.NOT_FOUND, "Không tìm thấy section")

    # !!! Phụ thuộc app registration của bạn khác: nếu tên model/field khác thì sửa ở đây.
    from registration.models import Enrollment
    enrollments = (Enrollment.objects
                   .filter(section_id=section_id, status=EnrollmentStatus.REGISTERED)
                   .select_related("student__user")
                   .order_by("student__student_code"))

    paginator = Paginator(enrollments, PAGE_SIZE)
    page_obj = paginator.get_page(page)
    rows = [
        {
            "student_code": e.student.student_code,
            "full_name": e.student.user.full_name,
            "class": e.student.student_class,
            "registered_at": e.registered_at,
        }
        for e in page_obj.object_list
    ]
    return {
        "section": section,
        "current_enrollment": section.current_enrollment,
        "max_capacity": section.max_capacity,
        "students": Page(rows, page_obj.number, paginator.num_pages, paginator.count),
    }


def delete_section(admin_user, section_id: int) -> None:
    """Delete an unused section. Sections with enrollments or gradebooks are protected."""
    _check_admin(admin_user)
    section = CourseSection.objects.filter(pk=section_id).first()
    if section is None:
        raise ServiceError(ErrorCode.NOT_FOUND, "Section not found")

    from registration.models import Enrollment
    if Enrollment.objects.filter(section=section).exists():
        raise ServiceError(ErrorCode.VALIDATION, "Cannot delete a section that has enrollments")

    section.delete()


def list_semesters() -> list:
    return list(Semester.objects.order_by("-start_date"))