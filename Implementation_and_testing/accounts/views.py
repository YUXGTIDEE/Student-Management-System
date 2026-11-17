"""
accounts/views.py  (Backend: Binh   Frontend: Huy (Login/Reset) + Đạt (Student) + Thành (Admin))

View khung: chưa cài thì hiện trang "[CHƯA CÀI ĐẶT] tên_view". Khi làm:
 1. BE gọi hàm trong services.py, bắt ServiceError, truyền dữ liệu vào template (context theo docs/api/accounts.md).
 2. FE viết template tương ứng trong templates/accounts/.
"""
from django.http import HttpResponse
from django.shortcuts import render
from common.contract import Role, ServiceError
from common.permissions import role_required


def _stub(name):
    return HttpResponse(f"[CHƯA CÀI ĐẶT] {name}()", status=501)


def login_view(request, **kwargs):
    """Màn hình đăng nhập (UC 1)
    Template: accounts/login.html"""
    # TODO (BE1): cài đặt
    return _stub("login_view")


def logout_view(request, **kwargs):
    """Đăng xuất (UC 2)
    Template: (không có - POST rồi redirect)"""
    # TODO (BE1): cài đặt
    return _stub("logout_view")


def reset_password_view(request, **kwargs):
    """Quên mật khẩu (UC 3)
    Template: accounts/reset_password.html"""
    # TODO (BE1): cài đặt
    return _stub("reset_password_view")


@role_required(Role.STUDENT, Role.TEACHER)
def profile_view(request, **kwargs):
    """Xem hồ sơ cá nhân (UC 4) - SV 3.1
    Template: accounts/profile.html"""
    # TODO (BE1): cài đặt
    return _stub("profile_view")


@role_required(Role.STUDENT, Role.TEACHER)
def contact_edit_view(request, **kwargs):
    """Cập nhật liên hệ (UC 5) - SV 3.2
    Template: accounts/contact_edit.html"""
    # TODO (BE1): cài đặt
    return _stub("contact_edit_view")


@role_required(Role.ADMINISTRATOR)
def account_list_view(request, **kwargs):
    """Admin 5.1 danh sách tài khoản (UC 21)
    Template: accounts/account_list.html"""
    # TODO (BE1): cài đặt
    return _stub("account_list_view")


@role_required(Role.ADMINISTRATOR)
def account_create_view(request, **kwargs):
    """Admin 5.2 tạo tài khoản (UC 19)
    Template: accounts/account_form.html"""
    # TODO (BE1): cài đặt
    return _stub("account_create_view")


@role_required(Role.ADMINISTRATOR)
def account_edit_view(request, **kwargs):
    """Admin 5.2 sửa tài khoản (UC 20)
    Template: accounts/account_form.html"""
    # TODO (BE1): cài đặt
    return _stub("account_edit_view")


@role_required(Role.ADMINISTRATOR)
def account_status_view(request, **kwargs):
    """POST khóa/mở khóa (UC 21)
    Template: (không có - POST rồi redirect)"""
    # TODO (BE1): cài đặt
    return _stub("account_status_view")


@role_required(Role.ADMINISTRATOR)
def account_reset_password_view(request, **kwargs):
    """POST admin reset mật khẩu
    Template: (không có - POST rồi redirect)"""
    # TODO (BE1): cài đặt
    return _stub("account_reset_password_view")
