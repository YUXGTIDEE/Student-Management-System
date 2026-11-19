"""
common/permissions.py  (Phụ trách: Hoa Binh)  - decorator phân quyền dùng cho MỌI view.
Ví dụ:
    @role_required(Role.ADMINISTRATOR)
    def accounts_list(request): ...
"""
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseForbidden

from .contract import EnrollmentStatus, Role


def role_required(*roles):
    """Chỉ cho các role trong `roles` vào. Chưa đăng nhập -> chuyển về trang login; sai role -> 403.

    - Tài khoản đang bị khóa (is_locked) cũng bị 403, kể cả khi phiên đăng nhập còn hạn
      (Admin khóa tài khoản trong lúc người đó đang dùng).
    - Có thể truyền nhiều role: @role_required(Role.ADMINISTRATOR, Role.TEACHER)
    """
    if not roles:
        raise ValueError("role_required() cần ít nhất một role")
    allowed = set(roles)

    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            user = request.user
            if getattr(user, "is_locked", False) or getattr(user, "role", None) not in allowed:
                return HttpResponseForbidden("403 - Bạn không có quyền truy cập chức năng này.")
            return view(request, *args, **kwargs)

        return login_required(wrapper)

    return decorator


def _teacher_profile(user):
    """Trả về Teacher của user, hoặc None nếu user không phải giáo viên / chưa có hồ sơ Teacher."""
    if getattr(user, "role", None) != Role.TEACHER:
        return None
    try:
        return user.teacher
    except ObjectDoesNotExist:
        return None


def teacher_teaches_section(teacher_user, section):
    """True nếu giáo viên được phân công section này. Hoa Binh cài, Duy và Minh dùng.

    `section` là CourseSection hoặc id (số nguyên) của section.
    """
    from courses.models import CourseSection   # import muộn để tránh import vòng khi nạp app

    teacher = _teacher_profile(teacher_user)
    if teacher is None:
        return False
    section_id = getattr(section, "pk", section)
    return CourseSection.objects.filter(pk=section_id, teacher=teacher).exists()


def teacher_can_see_student(teacher_user, student):
    """True nếu student có Enrollment REGISTERED trong section của giáo viên. Binh cài.

    `student` là Student hoặc id (số nguyên) của Student.
    """
    from registration.models import Enrollment   # import muộn để tránh import vòng khi nạp app

    teacher = _teacher_profile(teacher_user)
    if teacher is None:
        return False
    student_id = getattr(student, "pk", student)
    return Enrollment.objects.filter(
        student_id=student_id,
        status=EnrollmentStatus.REGISTERED,
        section__teacher=teacher,
    ).exists()
