"""
registration/views.py  (Backend: BE3   Frontend: FE1)

View khung: chưa cài thì hiện trang "[CHƯA CÀI ĐẶT] tên_view". Khi làm:
 1. BE gọi hàm trong services.py, bắt ServiceError, truyền dữ liệu vào template (context theo docs/api/registration.md).
 2. FE viết template tương ứng trong templates/registration/.
"""
from django.http import HttpResponse
from django.shortcuts import render
from common.contract import Role, ServiceError
from common.permissions import role_required


def _stub(name):
    return HttpResponse(f"[CHƯA CÀI ĐẶT] {name}()", status=501)


@role_required(Role.STUDENT)
def open_sections_view(request, **kwargs):
    """SV 3.3 section mở (UC 6)
    Template: registration/open_sections.html"""
    # TODO (BE3): cài đặt
    return _stub("open_sections_view")


@role_required(Role.STUDENT)
def register_confirm_view(request, **kwargs):
    """SV 3.4 dialog xác nhận, gọi validate_registration (UC 7)
    Template: registration/confirm.html"""
    # TODO (BE3): cài đặt
    return _stub("register_confirm_view")


@role_required(Role.STUDENT)
def register_view(request, **kwargs):
    """POST đăng ký (UC 7)
    Template: (không có - POST rồi redirect)"""
    # TODO (BE3): cài đặt
    return _stub("register_view")


@role_required(Role.STUDENT)
def registered_sections_view(request, **kwargs):
    """SV 3.5 đã đăng ký (UC 8)
    Template: registration/registered.html"""
    # TODO (BE3): cài đặt
    return _stub("registered_sections_view")


@role_required(Role.STUDENT)
def cancel_view(request, **kwargs):
    """POST hủy đăng ký (UC 9)
    Template: (không có - POST rồi redirect)"""
    # TODO (BE3): cài đặt
    return _stub("cancel_view")
