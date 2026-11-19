"""
accounts/services.py  (Phụ trách: Binh)   UC: 1, 2, 3, 4, 5, 19, 20, 21
Chữ ký hàm là HỢP ĐỒNG với FE và BE khác. Lỗi nghiệp vụ -> raise ServiceError(ErrorCode.X, "...").

Quy ước về lỗi:
 - ServiceError.details là list các dict {"field": "<tên trường>", "message": "<lý do>"} để FE
   hiển thị lỗi cạnh đúng ô nhập.
 - Thông báo viết bằng tiếng Anh cho khớp với giao diện trong SRS (No students found, ...).
"""
import re
import secrets
from datetime import timedelta

from django.contrib.auth import login
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.db.models import F, Q
from django.utils import timezone

from common.contract import (
    ADMIN_CODE_REGEX,
    MAX_FAILED_LOGINS,
    PASSWORD_RESET_TOKEN_MINUTES,
    STUDENT_CODE_REGEX,
    TEACHER_CODE_REGEX,
    ErrorCode,
    ResetStatus,
    Role,
    ServiceError,
)
from common.pagination import paginate

from .models import PasswordReset, Teacher, User

_BACKEND = "django.contrib.auth.backends.ModelBackend"
_VALID_ROLES = {value for value, _label in Role.CHOICES}
_CODE_PATTERN = {
    Role.STUDENT: re.compile(STUDENT_CODE_REGEX),
    Role.TEACHER: re.compile(TEACHER_CODE_REGEX),
    Role.ADMINISTRATOR: re.compile(ADMIN_CODE_REGEX),
}
_PHONE_PATTERN = re.compile(r"^\+?\d{9,15}$")      # 9-15 chữ số, có thể bắt đầu bằng +
_BAD_CREDENTIALS_MSG = "Wrong username or password."

_LOWER, _UPPER, _DIGITS = "abcdefghjkmnpqrstuvwxyz", "ABCDEFGHJKMNPQRSTUVWXYZ", "23456789"


# =============================================================================
#  Hàm phụ dùng nội bộ
# =============================================================================
def _field(field, message):
    return {"field": field, "message": message}


def _ensure_admin(user):
    """Lớp bảo vệ thứ hai ở service (view đã có @role_required)."""
    if getattr(user, "role", None) != Role.ADMINISTRATOR:
        raise ServiceError(ErrorCode.PERMISSION_DENIED, "Only administrators can perform this action.")


def _get_user(user_id):
    try:
        return User.objects.get(pk=user_id)
    except (User.DoesNotExist, ValueError, TypeError):
        raise ServiceError(ErrorCode.NOT_FOUND, "Account not found.")


def _clean_name(value):
    return " ".join(str(value or "").split())      # bỏ khoảng trắng thừa


def _check_email(email, errors):
    if len(email) > 254:
        errors.append(_field("email", "Email is too long."))
        return
    try:
        validate_email(email)
    except ValidationError:
        errors.append(_field("email", "Email is not valid."))


def _email_taken(email, exclude_pk=None):
    qs = User.objects.filter(email__iexact=email)
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()


def _generate_password(length=12):
    """Mật khẩu ngẫu nhiên (module secrets), bỏ ký tự dễ nhầm (0/O, 1/l/I); đảm bảo có chữ hoa, thường, số."""
    alphabet = _LOWER + _UPPER + _DIGITS
    while True:
        password = "".join(secrets.choice(alphabet) for _ in range(length))
        if (any(c in _LOWER for c in password) and any(c in _UPPER for c in password)
                and any(c in _DIGITS for c in password)):
            return password


def _to_optional_bool(value):
    """None/'' -> None; bool -> bool; chuỗi từ query string ('1','true','locked'...) -> bool."""
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "locked"}:
        return True
    if text in {"0", "false", "no", "active"}:
        return False
    raise ServiceError(ErrorCode.VALIDATION, "Invalid status filter.", [_field("locked", "Invalid value.")])


def _find_login_user(identifier):
    """Tìm tài khoản theo mã (mọi role) hoặc email (chỉ Teacher và Administrator, theo SRS:
    sinh viên đăng nhập bằng mã sinh viên)."""
    user = User.objects.filter(username__iexact=identifier).first()
    if user is not None:
        return user
    if "@" in identifier:
        matches = list(User.objects.filter(email__iexact=identifier,
                                           role__in=[Role.TEACHER, Role.ADMINISTRATOR])[:2])
        if len(matches) == 1:                     # email trùng nhiều tài khoản -> coi như không tìm thấy
            return matches[0]
    return None


def _register_failed_login(user):
    """Tăng failed_login_count bằng câu lệnh nguyên tử; đủ MAX_FAILED_LOGINS thì khóa. True nếu vừa bị khóa."""
    User.objects.filter(pk=user.pk).update(failed_login_count=F("failed_login_count") + 1)
    count = User.objects.values_list("failed_login_count", flat=True).get(pk=user.pk)
    if count >= MAX_FAILED_LOGINS:
        User.objects.filter(pk=user.pk).update(is_locked=True)
        return True
    return False


# ---- UC 1, 2: đăng nhập / đăng xuất --------------------------------------
def authenticate_user(request, identifier: str, password: str):
    """identifier = mã SV, mã GV hoặc email. Trả về User.
    Lỗi: BAD_CREDENTIALS (tăng failed_login_count), ACCOUNT_LOCKED.

    - Email chỉ dùng được cho Teacher/Administrator; sinh viên phải dùng mã sinh viên.
    - Không tiết lộ "mã không tồn tại" hay "sai mật khẩu": cả hai đều BAD_CREDENTIALS.
    - Sai MAX_FAILED_LOGINS lần liên tiếp -> khóa tài khoản (lần sai cuối báo ACCOUNT_LOCKED).
    - Tài khoản đã khóa chỉ báo ACCOUNT_LOCKED khi nhập ĐÚNG mật khẩu (tránh lộ trạng thái cho người lạ);
      nhập sai thì vẫn BAD_CREDENTIALS và không tăng bộ đếm.
    - request=None dùng cho unit test (không tạo phiên đăng nhập).
    """
    identifier = (identifier or "").strip()
    if not identifier or not password:
        missing = [_field(name, "This field is required.")
                   for name, value in (("identifier", identifier), ("password", password)) if not value]
        raise ServiceError(ErrorCode.MISSING_FIELDS, "Please enter your ID/email and password.", missing)

    user = _find_login_user(identifier)
    if user is None:
        make_password(password)                   # tốn thời gian tương đương, tránh dò mã tồn tại qua độ trễ
        raise ServiceError(ErrorCode.BAD_CREDENTIALS, _BAD_CREDENTIALS_MSG)

    if not user.check_password(password):
        if not user.is_locked and user.is_active and _register_failed_login(user):
            raise ServiceError(ErrorCode.ACCOUNT_LOCKED,
                               "Too many failed attempts. The account has been locked; contact an administrator.")
        raise ServiceError(ErrorCode.BAD_CREDENTIALS, _BAD_CREDENTIALS_MSG)

    if user.is_locked or not user.is_active:
        raise ServiceError(ErrorCode.ACCOUNT_LOCKED,
                           "This account is locked or inactive and cannot be used.")

    if user.failed_login_count:
        User.objects.filter(pk=user.pk).update(failed_login_count=0)
        user.failed_login_count = 0
    if request is not None:
        login(request, user, backend=_BACKEND)
    return user


# ---- UC 3 (+21): quên mật khẩu ---------------------------------------------
def request_password_reset(identifier: str) -> None:
    """Tạo PasswordReset + sinh token ngẫu nhiên. Lỗi: NOT_FOUND nếu mã/email không tồn tại.

    Giai đoạn 1 (DECISIONS #11): chỉ GHI NHẬN yêu cầu, không gửi email. Admin xử lý bằng
    admin_reset_password(); khi đó các yêu cầu đang PENDING của người đó chuyển thành COMPLETED.
    Yêu cầu cũ còn PENDING của cùng người dùng bị đánh dấu EXPIRED (yêu cầu mới thay thế).
    """
    identifier = (identifier or "").strip()
    if not identifier:
        raise ServiceError(ErrorCode.MISSING_FIELDS, "Please enter your email or ID.",
                           [_field("identifier", "This field is required.")])

    user = (User.objects.filter(username__iexact=identifier).first()
            or User.objects.filter(email__iexact=identifier).order_by("pk").first())
    if user is None:
        raise ServiceError(ErrorCode.NOT_FOUND, "No account matches the information you entered.")
    if user.is_locked or not user.is_active:
        raise ServiceError(ErrorCode.ACCOUNT_LOCKED, "This account is locked; contact an administrator.")

    now = timezone.now()
    with transaction.atomic():
        PasswordReset.objects.filter(user=user, status=ResetStatus.PENDING).update(status=ResetStatus.EXPIRED)
        PasswordReset.objects.create(
            user=user,
            token=secrets.token_urlsafe(32),
            expires_at=now + timedelta(minutes=PASSWORD_RESET_TOKEN_MINUTES),
            status=ResetStatus.PENDING,
        )


def admin_reset_password(admin_user, target_user_id: int) -> str:
    """Admin reset: sinh mật khẩu ngẫu nhiên, lưu dạng băm, TRẢ VỀ mật khẩu rõ để hiển thị cho admin.
    Đồng thời xóa bộ đếm đăng nhập sai và hoàn tất các yêu cầu reset đang PENDING của người đó."""
    _ensure_admin(admin_user)
    target = _get_user(target_user_id)
    password = _generate_password()
    with transaction.atomic():
        target.set_password(password)              # lưu dạng băm
        target.failed_login_count = 0
        target.save(update_fields=["password", "failed_login_count"])
        PasswordReset.objects.filter(user=target, status=ResetStatus.PENDING).update(
            status=ResetStatus.COMPLETED)
    return password


# ---- UC 4, 5: hồ sơ cá nhân ----------------------------------------------------
def get_profile(user) -> dict:
    """Student: mã SV, họ tên, ngày sinh, giới tính, địa chỉ, SĐT, email.
    Teacher: mã GV, họ tên, khoa, SĐT, email.
    Admin không có chức năng xem hồ sơ cá nhân -> PERMISSION_DENIED."""
    base = {
        "role": user.role,
        "username": user.username,
        "full_name": user.full_name,
        "email": user.email,
        "phone_number": user.phone_number,
    }
    if user.role == Role.STUDENT:
        try:
            student = user.student
        except ObjectDoesNotExist:
            raise ServiceError(ErrorCode.NOT_FOUND, "Student record not found.")
        base.update(
            student_code=student.student_code,
            date_of_birth=student.date_of_birth,
            gender=student.gender,
            gender_display=student.get_gender_display(),
            address=user.address,
        )
        return base
    if user.role == Role.TEACHER:
        try:
            teacher = user.teacher
        except ObjectDoesNotExist:
            raise ServiceError(ErrorCode.NOT_FOUND, "Teacher record not found.")
        base.update(teacher_code=teacher.teacher_code, department=teacher.department)
        return base
    raise ServiceError(ErrorCode.PERMISSION_DENIED, "This account has no personal profile.")


def update_contact(user, email: str, phone_number: str, address: str = None) -> None:
    """Student sửa được email/SĐT/địa chỉ; Teacher chỉ email/SĐT (address phải là None).
    Lỗi: VALIDATION, MISSING_FIELDS, DUPLICATE (email đã dùng).

    - address=None nghĩa là KHÔNG đổi địa chỉ. Student gửi address rỗng "" -> MISSING_FIELDS.
    - Teacher gửi address (khác None) -> PERMISSION_DENIED.
    - Mọi kiểm tra xong mới ghi; lỗi thì dữ liệu giữ nguyên.
    """
    if user.role not in (Role.STUDENT, Role.TEACHER):
        raise ServiceError(ErrorCode.PERMISSION_DENIED, "You cannot update contact details.")
    if user.role == Role.TEACHER and address is not None:
        raise ServiceError(ErrorCode.PERMISSION_DENIED, "Teachers can only update email and phone number.",
                           [_field("address", "Not allowed.")])

    email = (email or "").strip()
    phone = re.sub(r"[\s.\-()]", "", (phone_number or ""))
    new_address = None if address is None else " ".join(str(address).split())

    missing = []
    if not email:
        missing.append(_field("email", "This field is required."))
    if not phone:
        missing.append(_field("phone_number", "This field is required."))
    if new_address is not None and not new_address:
        missing.append(_field("address", "This field is required."))
    if missing:
        raise ServiceError(ErrorCode.MISSING_FIELDS, "Please fill in all required fields.", missing)

    invalid = []
    if email:
        _check_email(email, invalid)
    if not _PHONE_PATTERN.fullmatch(phone):
        invalid.append(_field("phone_number", "Phone number must have 9-15 digits."))
    if new_address is not None and len(new_address) > 255:
        invalid.append(_field("address", "Address is too long (max 255 characters)."))
    if invalid:
        raise ServiceError(ErrorCode.VALIDATION, "Some information is not valid.", invalid)

    if _email_taken(email, exclude_pk=user.pk):
        raise ServiceError(ErrorCode.DUPLICATE, "This email is already used by another account.",
                           [_field("email", "Already in use.")])

    user.email = email
    user.phone_number = phone
    fields = ["email", "phone_number"]
    if new_address is not None:
        user.address = new_address
        fields.append("address")
    user.save(update_fields=fields)


# ---- UC 19, 20, 21: quản lý tài khoản (Admin) -----------------------------
def create_account(admin_user, full_name: str, email: str, role: str, username: str):
    """Tạo user + mật khẩu ngẫu nhiên (băm). Trả về (user, mật_khẩu_rõ). Lỗi: DUPLICATE, MISSING_FIELDS.

    - username phải đúng định dạng của role: SV 6 chữ số, GV "GV001", Admin "AD001" (DECISIONS #1, #2).
    - Role Teacher: tự tạo luôn hồ sơ Teacher (teacher_code = username).
    - Role Student: CHỈ tạo tài khoản; hồ sơ sinh viên do UC 23 (students.services.create_student).
    """
    _ensure_admin(admin_user)
    full_name = _clean_name(full_name)
    email = (email or "").strip()
    role = (role or "").strip()
    username = (username or "").strip().upper()

    missing = [_field(name, "This field is required.")
               for name, value in (("full_name", full_name), ("email", email),
                                   ("role", role), ("username", username)) if not value]
    if missing:
        raise ServiceError(ErrorCode.MISSING_FIELDS, "Please fill in all required fields.", missing)

    invalid = []
    if role not in _VALID_ROLES:
        invalid.append(_field("role", "Role must be Student, Teacher or Administrator."))
    elif not _CODE_PATTERN[role].fullmatch(username):
        invalid.append(_field("username", {
            Role.STUDENT: "Student ID must have exactly 6 digits.",
            Role.TEACHER: "Teacher ID must look like GV001.",
            Role.ADMINISTRATOR: "Administrator ID must look like AD001.",
        }[role]))
    if len(full_name) > 150:
        invalid.append(_field("full_name", "Full name is too long (max 150 characters)."))
    _check_email(email, invalid)
    if invalid:
        raise ServiceError(ErrorCode.VALIDATION, "Some information is not valid.", invalid)

    duplicates = []
    if User.objects.filter(username__iexact=username).exists():
        duplicates.append(_field("username", "Already in use."))
    if _email_taken(email):
        duplicates.append(_field("email", "Already in use."))
    if duplicates:
        raise ServiceError(ErrorCode.DUPLICATE, "The username or email already exists.", duplicates)

    password = _generate_password()
    try:
        with transaction.atomic():
            user = User(username=username, full_name=full_name, email=email, role=role)
            user.set_password(password)            # lưu dạng băm
            user.save()
            if role == Role.TEACHER:
                Teacher.objects.create(user=user, teacher_code=username)
    except IntegrityError:                         # hai admin tạo cùng mã gần như đồng thời
        raise ServiceError(ErrorCode.DUPLICATE, "The username or email already exists.")
    return user, password


def _ensure_role_change_allowed(target):
    """Chỉ cho đổi role khi tài khoản chưa gắn với dữ liệu học vụ."""
    from students.models import Student    # import muộn để tránh import vòng khi nạp app

    if Student.objects.filter(user=target).exists():
        raise ServiceError(ErrorCode.VALIDATION,
                           "Cannot change the role: this account already has a student record.",
                           [_field("role", "Not allowed.")])
    if Teacher.objects.filter(user=target, sections__isnull=False).exists():
        raise ServiceError(ErrorCode.VALIDATION,
                           "Cannot change the role: this teacher is assigned to course sections.",
                           [_field("role", "Not allowed.")])


def edit_account(admin_user, user_id: int, full_name: str, email: str, role: str) -> None:
    """Sửa họ tên, email, role. Lỗi: NOT_FOUND, MISSING_FIELDS, VALIDATION, DUPLICATE (email của tài khoản khác).

    - Không cho Admin tự đổi role của chính mình (tránh tự mất quyền).
    - Đổi role chỉ được khi tài khoản chưa có hồ sơ sinh viên / chưa được phân công section.
    - Đặt lại mật khẩu là chức năng riêng: admin_reset_password().
    """
    _ensure_admin(admin_user)
    target = _get_user(user_id)
    full_name = _clean_name(full_name)
    email = (email or "").strip()
    role = (role or "").strip()

    missing = [_field(name, "This field is required.")
               for name, value in (("full_name", full_name), ("email", email), ("role", role)) if not value]
    if missing:
        raise ServiceError(ErrorCode.MISSING_FIELDS, "Please fill in all required fields.", missing)

    invalid = []
    if role not in _VALID_ROLES:
        invalid.append(_field("role", "Role must be Student, Teacher or Administrator."))
    if len(full_name) > 150:
        invalid.append(_field("full_name", "Full name is too long (max 150 characters)."))
    _check_email(email, invalid)
    if invalid:
        raise ServiceError(ErrorCode.VALIDATION, "Some information is not valid.", invalid)

    if _email_taken(email, exclude_pk=target.pk):
        raise ServiceError(ErrorCode.DUPLICATE, "This email is already used by another account.",
                           [_field("email", "Already in use.")])

    if role != target.role:
        if target.pk == admin_user.pk:
            raise ServiceError(ErrorCode.VALIDATION, "You cannot change your own role.",
                               [_field("role", "Not allowed.")])
        _ensure_role_change_allowed(target)

    try:
        with transaction.atomic():
            target.full_name = full_name
            target.email = email
            target.role = role
            target.save(update_fields=["full_name", "email", "role"])
            if role == Role.TEACHER and not Teacher.objects.filter(user=target).exists():
                Teacher.objects.create(user=target, teacher_code=target.username)
    except IntegrityError:
        raise ServiceError(ErrorCode.DUPLICATE, "Could not update: the teacher ID is already in use.")


def set_account_status(admin_user, user_id: int, locked: bool) -> None:
    """Khóa/mở khóa. Lỗi: CANNOT_LOCK_SELF. Mở khóa thì xóa bộ đếm đăng nhập sai."""
    _ensure_admin(admin_user)
    target = _get_user(user_id)
    if locked and target.pk == admin_user.pk:
        raise ServiceError(ErrorCode.CANNOT_LOCK_SELF, "You cannot lock your own account.")
    updates = {"is_locked": bool(locked)}
    if not locked:
        updates["failed_login_count"] = 0
    User.objects.filter(pk=target.pk).update(**updates)


def list_accounts(q: str = "", role: str = "", locked=None, page: int = 1):
    """Trả về common.contract.Page, tìm theo tên/mã/email, lọc role/status.

    - locked: None = tất cả, True = đang khóa, False = đang hoạt động (nhận cả chuỗi '1'/'0'/'locked'/'active').
    - Hàm KHÔNG có tham số người dùng nên view bắt buộc phải có @role_required(Role.ADMINISTRATOR).
    """
    accounts = User.objects.all().order_by("username")
    q = (q or "").strip()
    if q:
        accounts = accounts.filter(Q(username__icontains=q) | Q(full_name__icontains=q) | Q(email__icontains=q))
    role = (role or "").strip()
    if role:
        if role not in _VALID_ROLES:
            raise ServiceError(ErrorCode.VALIDATION, "Invalid role filter.", [_field("role", "Invalid value.")])
        accounts = accounts.filter(role=role)
    flag = _to_optional_bool(locked)
    if flag is not None:
        accounts = accounts.filter(is_locked=flag)
    return paginate(accounts, page)