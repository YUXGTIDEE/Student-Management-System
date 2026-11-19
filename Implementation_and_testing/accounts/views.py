"""
accounts/views.py  (Backend: Binh   Frontend: Huy (Login/Reset) + Đạt (Student) + Thành (Admin))

Cách làm việc của các view trong file này:
 1. BE gọi hàm trong services.py, bắt ServiceError, truyền dữ liệu vào template.
    Tên biến trong context (và tên các ô <input>) được ghi ở docs/api/accounts.md - FE đọc file đó.
 2. FE viết template tương ứng trong templates/accounts/.
 3. Mọi form POST bắt buộc có {% csrf_token %}.

Lỗi nghiệp vụ truyền xuống template bằng 3 biến chung:
    error         - thông báo chung (chuỗi) hoặc None
    error_code    - mã lỗi (ErrorCode.X) hoặc None
    field_errors  - dict {tên_trường: thông_báo} để hiện lỗi cạnh đúng ô nhập
"""
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme, urlencode
from django.views.decorators.http import require_http_methods, require_POST

from common.contract import ErrorCode, Page, Role, ServiceError
from common.permissions import role_required

from . import services

# Trang đầu tiên mỗi role nhìn thấy sau khi đăng nhập
HOME_BY_ROLE = {
    Role.STUDENT: "accounts:profile_view",             # 3.1 Thông tin cá nhân
    Role.TEACHER: "search:assigned_sections_view",     # 4.3 Danh sách được phân công
    Role.ADMINISTRATOR: "accounts:account_list_view",  # 5.1 Accounts
}


# =============================================================================
#  Hàm phụ
# =============================================================================
def _error_context(error):
    """ServiceError -> các biến chung cho template."""
    return {
        "error": error.message,
        "error_code": error.code,
        "field_errors": {d["field"]: d["message"] for d in error.details},
    }


def _safe_next(request, default):
    """Địa chỉ chuyển tới sau khi xong việc: tham số `next` nếu an toàn (cùng website), nếu không thì `default`.
    Chặn kiểu tấn công open redirect (?next=https://trang-la.com)."""
    target = request.POST.get("next") or request.GET.get("next") or ""
    if target and url_has_allowed_host_and_scheme(
            target, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return target
    return default


# =============================================================================
#  Trang chủ
# =============================================================================
@login_required
def home_view(request):
    """Trang chủ: chuyển người dùng tới trang đầu tiên của role mình."""
    user = request.user
    target = HOME_BY_ROLE.get(user.role)
    if user.is_locked or target is None:        # tài khoản bị khóa lúc đang đăng nhập, hoặc role lạ
        logout(request)
        messages.error(request, "This account cannot be used. Please contact an administrator.")
        return redirect("accounts:login_view")
    return redirect(target)


# =============================================================================
#  UC 1, 2, 3: đăng nhập, đăng xuất, quên mật khẩu
# =============================================================================
@require_http_methods(["GET", "POST"])
def login_view(request, **kwargs):
    """Màn hình đăng nhập (UC 1)
    Template: accounts/login.html
    Ô nhập: identifier, password, next (ẩn). Context: identifier, next, error, error_code, field_errors."""
    if request.user.is_authenticated:
        return redirect(_safe_next(request, settings.LOGIN_REDIRECT_URL))

    context = {"identifier": "", "next": request.GET.get("next", "")}
    if request.method == "POST":
        identifier = request.POST.get("identifier", "")
        context.update(identifier=identifier.strip(), next=request.POST.get("next", ""))
        try:
            services.authenticate_user(request, identifier, request.POST.get("password", ""))
        except ServiceError as error:
            context.update(_error_context(error))     # không bao giờ đưa mật khẩu trở lại template
        else:
            return redirect(_safe_next(request, settings.LOGIN_REDIRECT_URL))
    return render(request, "accounts/login.html", context)


@require_POST
def logout_view(request, **kwargs):
    """Đăng xuất (UC 2)
    Chỉ nhận POST (nút Log out phải là <form method="post"> có csrf_token, không dùng thẻ <a>).
    Template: (không có - POST rồi redirect về trang đăng nhập)"""
    logout(request)
    return redirect("accounts:login_view")


@require_http_methods(["GET", "POST"])
def reset_password_view(request, **kwargs):
    """Quên mật khẩu (UC 3)
    Template: accounts/reset_password.html
    Ô nhập: identifier (email hoặc mã). Thành công -> về trang đăng nhập kèm thông báo.
    Giai đoạn 1: yêu cầu được ghi nhận cho Admin xử lý (DECISIONS #11), không gửi email."""
    context = {"identifier": ""}
    if request.method == "POST":
        identifier = request.POST.get("identifier", "")
        context["identifier"] = identifier.strip()
        try:
            services.request_password_reset(identifier)
        except ServiceError as error:
            context.update(_error_context(error))
        else:
            messages.success(request, "Your request has been sent. "
                                      "An administrator will reset your password and contact you.")
            return redirect("accounts:login_view")
    return render(request, "accounts/reset_password.html", context)


# =============================================================================
#  UC 4, 5: hồ sơ cá nhân (Student, Teacher)
# =============================================================================
@role_required(Role.STUDENT, Role.TEACHER)
def profile_view(request, **kwargs):
    """Xem hồ sơ cá nhân (UC 4) - SV 3.1
    Template: accounts/profile.html
    Context: profile (dict từ services.get_profile), error..."""
    try:
        profile = services.get_profile(request.user)
    except ServiceError as error:
        status = 404 if error.code == ErrorCode.NOT_FOUND else 403
        return render(request, "accounts/profile.html", {"profile": None, **_error_context(error)}, status=status)
    return render(request, "accounts/profile.html", {"profile": profile})


@role_required(Role.STUDENT, Role.TEACHER)
@require_http_methods(["GET", "POST"])
def contact_edit_view(request, **kwargs):
    """Cập nhật liên hệ (UC 5) - SV 3.2
    Template: accounts/contact_edit.html
    Ô nhập: email, phone_number, address (address chỉ có với sinh viên: can_edit_address).
    Mã và họ tên chỉ hiển thị (disabled) lấy từ profile. Nút Cancel = liên kết về profile_view."""
    user = request.user
    can_edit_address = user.role == Role.STUDENT
    context = {"can_edit_address": can_edit_address}
    try:
        context["profile"] = services.get_profile(user)
    except ServiceError as error:
        return render(request, "accounts/contact_edit.html",
                      {**context, "profile": None, **_error_context(error)}, status=404)

    context["form_data"] = {"email": user.email, "phone_number": user.phone_number, "address": user.address}
    if request.method == "POST":
        form = {
            "email": request.POST.get("email", ""),
            "phone_number": request.POST.get("phone_number", ""),
            "address": request.POST.get("address", user.address),
        }
        context["form_data"] = form
        try:
            services.update_contact(user, form["email"], form["phone_number"],
                                    request.POST.get("address") if can_edit_address else None)
        except ServiceError as error:
            context.update(_error_context(error))
        else:
            messages.success(request, "Contact details updated.")
            return redirect("accounts:profile_view")
    return render(request, "accounts/contact_edit.html", context)


# =============================================================================
#  UC 19, 20, 21: quản lý tài khoản (Administrator)
# =============================================================================
@role_required(Role.ADMINISTRATOR)
def account_list_view(request, **kwargs):
    """Admin 5.1 danh sách tài khoản (UC 21)
    Template: accounts/account_list.html
    Tham số URL: q, role, status ("", "locked", "active"), page.
    Context: accounts, page (items/page/num_pages/total), page_numbers, filters, query_string (để nối
    vào liên kết phân trang: ?{{ query_string }}&page=N), roles, current_user_id (đánh dấu tài khoản của
    chính mình), password_notice ({username, password} hiện MỘT lần sau khi tạo/reset mật khẩu, hoặc None)."""
    filters = {key: request.GET.get(key, "").strip() for key in ("q", "role", "status")}
    context = {
        "filters": filters,
        "roles": Role.CHOICES,
        "current_user_id": request.user.pk,
        "password_notice": request.session.pop("password_notice", None),   # đọc xong là xóa
    }
    try:
        page = services.list_accounts(filters["q"], filters["role"], filters["status"], request.GET.get("page", 1))
    except ServiceError as error:
        context.update(_error_context(error))
        page = Page(items=[], page=1, num_pages=1, total=0)
    context.update(
        accounts=page.items,
        page=page,
        page_numbers=range(1, page.num_pages + 1),
        query_string=urlencode({key: value for key, value in filters.items() if value}),
    )
    return render(request, "accounts/account_list.html", context)


@role_required(Role.ADMINISTRATOR)
@require_http_methods(["GET", "POST"])
def account_create_view(request, **kwargs):
    """Admin 5.2 tạo tài khoản (UC 19)
    Template: accounts/account_form.html (dùng chung với sửa; mode = "create")
    Ô nhập: full_name, email, role, username. Thành công -> về danh sách, mật khẩu tạm hiện một lần."""
    context = {"mode": "create", "account": None, "roles": Role.CHOICES, "form_data": {}}
    if request.method == "POST":
        form = {key: request.POST.get(key, "").strip() for key in ("full_name", "email", "role", "username")}
        context["form_data"] = form
        try:
            user, password = services.create_account(request.user, **form)
        except ServiceError as error:
            context.update(_error_context(error))
        else:
            request.session["password_notice"] = {"username": user.username, "password": password}
            messages.success(request, f"Account {user.username} created.")
            return redirect("accounts:account_list_view")
    return render(request, "accounts/account_form.html", context)


@role_required(Role.ADMINISTRATOR)
@require_http_methods(["GET", "POST"])
def account_edit_view(request, user_id, **kwargs):
    """Admin 5.2 sửa tài khoản (UC 20)
    Template: accounts/account_form.html (mode = "edit"; account = tài khoản đang sửa, username chỉ đọc)
    Ô nhập: full_name, email, role. Nút Reset password nằm ở form riêng (account_reset_password_view)."""
    try:
        account = services.get_account(request.user, user_id)
    except ServiceError as error:
        raise Http404(error.message)

    context = {
        "mode": "edit", "account": account, "roles": Role.CHOICES,
        "form_data": {"full_name": account.full_name, "email": account.email, "role": account.role},
    }
    if request.method == "POST":
        form = {key: request.POST.get(key, "").strip() for key in ("full_name", "email", "role")}
        context["form_data"] = form
        try:
            services.edit_account(request.user, user_id, **form)
        except ServiceError as error:
            context.update(_error_context(error))
        else:
            messages.success(request, f"Account {account.username} updated.")
            return redirect("accounts:account_list_view")
    return render(request, "accounts/account_form.html", context)


@role_required(Role.ADMINISTRATOR)
@require_POST
def account_status_view(request, user_id, **kwargs):
    """POST khóa/mở khóa (UC 21)
    Ô gửi: action = "lock" hoặc "unlock", next (tùy chọn: địa chỉ danh sách đang xem, giữ nguyên bộ lọc/trang).
    Hộp thoại xác nhận do FE làm trước khi gửi. Template: (không có - POST rồi redirect)"""
    action = request.POST.get("action", "")
    if action not in ("lock", "unlock"):
        messages.error(request, "Invalid action.")
    else:
        try:
            services.set_account_status(request.user, user_id, locked=(action == "lock"))
        except ServiceError as error:
            messages.error(request, error.message)
        else:
            messages.success(request, "Account locked." if action == "lock" else "Account unlocked.")
    return redirect(_safe_next(request, "accounts:account_list_view"))


@role_required(Role.ADMINISTRATOR)
@require_POST
def account_reset_password_view(request, user_id, **kwargs):
    """POST admin reset mật khẩu
    Mật khẩu mới hiện MỘT lần ở danh sách (password_notice). Template: (không có - POST rồi redirect)"""
    try:
        account = services.get_account(request.user, user_id)
        password = services.admin_reset_password(request.user, user_id)
    except ServiceError as error:
        messages.error(request, error.message)
    else:
        # Lưu tạm trong session để hiện đúng một lần ở trang danh sách (account_list_view lấy ra rồi xóa)
        request.session["password_notice"] = {"username": account.username, "password": password}
        messages.success(request, f"Password of {account.username} has been reset.")
    return redirect(_safe_next(request, "accounts:account_list_view"))