"""
accounts/services.py  (Phụ trách: BE1)   UC: 1, 2, 3, 4, 5, 19, 20, 21
Chữ ký hàm là HỢP ĐỒNG với FE và BE khác. Lỗi nghiệp vụ -> raise ServiceError(ErrorCode.X, "...").
"""
from common.contract import not_implemented


# ---- UC 1, 2: đăng nhập / đăng xuất --------------------------------------
def authenticate_user(request, identifier: str, password: str):
    """identifier = mã SV, mã GV hoặc email. Trả về User.
    Lỗi: BAD_CREDENTIALS (tăng failed_login_count), ACCOUNT_LOCKED."""
    not_implemented("authenticate_user")


# ---- UC 3 (+21): quên mật khẩu ---------------------------------------------
def request_password_reset(identifier: str) -> None:
    """Tạo PasswordReset + sinh token ngẫu nhiên. Lỗi: NOT_FOUND nếu mã/email không tồn tại."""
    not_implemented("request_password_reset")


def admin_reset_password(admin_user, target_user_id: int) -> str:
    """Admin reset: sinh mật khẩu ngẫu nhiên, lưu dạng băm, TRẢ VỀ mật khẩu rõ để hiển thị cho admin."""
    not_implemented("admin_reset_password")


# ---- UC 4, 5: hồ sơ cá nhân ----------------------------------------------------
def get_profile(user) -> dict:
    """Student: mã SV, họ tên, ngày sinh, giới tính, địa chỉ, SĐT, email.
    Teacher: mã GV, họ tên, khoa, SĐT, email."""
    not_implemented("get_profile")


def update_contact(user, email: str, phone_number: str, address: str = None) -> None:
    """Student sửa được email/SĐT/địa chỉ; Teacher chỉ email/SĐT (address phải là None).
    Lỗi: VALIDATION, MISSING_FIELDS, DUPLICATE (email đã dùng)."""
    not_implemented("update_contact")


# ---- UC 19, 20, 21: quản lý tài khoản (Admin) -----------------------------
def create_account(admin_user, full_name: str, email: str, role: str, username: str):
    """Tạo user + mật khẩu ngẫu nhiên (băm). Trả về (user, mật_khẩu_rõ). Lỗi: DUPLICATE, MISSING_FIELDS."""
    not_implemented("create_account")


def edit_account(admin_user, user_id: int, full_name: str, email: str, role: str) -> None:
    not_implemented("edit_account")


def set_account_status(admin_user, user_id: int, locked: bool) -> None:
    """Khóa/mở khóa. Lỗi: CANNOT_LOCK_SELF."""
    not_implemented("set_account_status")


def list_accounts(q: str = "", role: str = "", locked=None, page: int = 1):
    """Trả về common.contract.Page, tìm theo tên/mã/email, lọc role/status."""
    not_implemented("list_accounts")
