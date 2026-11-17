"""
common/permissions.py  (Phụ trách: BE1)  - decorator phân quyền dùng cho MỌI view.
Ví dụ:
    @role_required(Role.ADMINISTRATOR)
    def accounts_list(request): ...
"""
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .contract import not_implemented


def role_required(*roles):
    """Chỉ cho các role trong `roles` vào. Chưa đăng nhập -> chuyển về trang login; sai role -> 403."""
    def decorator(view):
        @login_required
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            # TODO (BE1): kiểm tra request.user.role in roles, sai thì HttpResponseForbidden
            not_implemented("role_required")
        return wrapper
    return decorator


def teacher_teaches_section(teacher_user, section):
    """True nếu giáo viên được phân công section này. BE1 cài, BE3 và BE2 dùng."""
    not_implemented("teacher_teaches_section")


def teacher_can_see_student(teacher_user, student):
    """True nếu student có Enrollment REGISTERED trong section của giáo viên. BE1 cài."""
    not_implemented("teacher_can_see_student")
