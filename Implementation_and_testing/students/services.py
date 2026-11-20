"""students/services.py  (Phụ trách: Minh)   UC: 23, 24, 25"""
import re

from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db import transaction
from django.utils.dateparse import parse_date

from common.contract import (
    AcademicStatus, ErrorCode, Gender, Page, PAGE_SIZE, Role,
    STUDENT_CODE_REGEX, ServiceError,
)
from .models import AcademicStatusHistory, Student

User = get_user_model()

# Các trường bắt buộc khi tạo sinh viên (place_of_birth và academic_status không bắt buộc)
REQUIRED_FIELDS = [
    "student_code", "full_name", "date_of_birth", "gender", "email", "phone_number",
    "address", "academic_cohort", "major", "student_class",
]
# Các trường nằm ở bảng Student
STUDENT_FIELDS = [
    "date_of_birth", "gender", "place_of_birth", "academic_cohort",
    "major", "student_class", "academic_status",
]
# Các trường nằm ở bảng User (tài khoản)
USER_FIELDS = ["full_name", "email", "phone_number", "address"]


# ---------------------------------------------------------------- hàm phụ
def _check_admin(user):
    if getattr(user, "role", None) != Role.ADMINISTRATOR:
        raise ServiceError(ErrorCode.PERMISSION_DENIED, "Chỉ Administrator mới được thực hiện")


def _is_empty(value):
    return value is None or (isinstance(value, str) and not value.strip())


def _clean_and_validate(data):
    """Làm sạch dữ liệu và kiểm tra giá trị. Trả về dict mới."""
    data = dict(data)
    for key, value in data.items():
        if isinstance(value, str):
            data[key] = value.strip()

    if "date_of_birth" in data:
        dob = data["date_of_birth"]
        if isinstance(dob, str):
            dob = parse_date(dob)          # chấp nhận "2005-03-20"
        if dob is None:
            raise ServiceError(ErrorCode.VALIDATION, "Ngày sinh không hợp lệ (dạng YYYY-MM-DD)")
        data["date_of_birth"] = dob

    if "gender" in data and data["gender"] not in dict(Gender.CHOICES):
        raise ServiceError(ErrorCode.VALIDATION, "Giới tính không hợp lệ")

    if "academic_status" in data and data["academic_status"] not in dict(AcademicStatus.CHOICES):
        raise ServiceError(ErrorCode.VALIDATION, "Trạng thái học tập không hợp lệ")

    if "email" in data and "@" not in data["email"]:
        raise ServiceError(ErrorCode.VALIDATION, "Email không hợp lệ")

    return data


def _email_taken(email, exclude_user_id=None):
    qs = User.objects.filter(email__iexact=email)
    if exclude_user_id:
        qs = qs.exclude(pk=exclude_user_id)
    return qs.exists()


# ---------------------------------------------------------------- UC 23
def create_student(admin_user, data: dict):
    """data: student_code, full_name, date_of_birth, gender, email, phone_number, address,
    place_of_birth, academic_cohort, major, student_class, academic_status.
    Tạo User(role=STUDENT, username=student_code) + Student trong 1 transaction.
    Lỗi: DUPLICATE (mã SV/email), VALIDATION (mã SV không đúng ^\\d{6}$), MISSING_FIELDS."""
    _check_admin(admin_user)

    # 1. Thiếu thông tin?
    missing = [f for f in REQUIRED_FIELDS if _is_empty(data.get(f))]
    if missing:
        raise ServiceError(ErrorCode.MISSING_FIELDS, "Thiếu thông tin: " + ", ".join(missing), missing)

    data = _clean_and_validate(data)

    # 2. Mã SV đúng 6 chữ số?
    if not re.match(STUDENT_CODE_REGEX, data["student_code"]):
        raise ServiceError(ErrorCode.VALIDATION, "Mã sinh viên phải gồm đúng 6 chữ số")

    # 3. Trùng mã SV hoặc email?
    if Student.objects.filter(student_code=data["student_code"]).exists() \
            or User.objects.filter(username=data["student_code"]).exists():
        raise ServiceError(ErrorCode.DUPLICATE, "Mã sinh viên đã tồn tại")
    if _email_taken(data["email"]):
        raise ServiceError(ErrorCode.DUPLICATE, "Email đã tồn tại")

    # 4. Tạo User + Student trong 1 transaction (lỗi giữa chừng thì hủy hết)
    with transaction.atomic():
        user = User.objects.create_user(
            username=data["student_code"],
            password=data["student_code"],      # mật khẩu ban đầu = mã SV (xem DECISIONS.md)
            email=data["email"],
            full_name=data["full_name"],
            phone_number=data["phone_number"],
            address=data["address"],
            role=Role.STUDENT,
        )
        student = Student.objects.create(
            user=user,
            student_code=data["student_code"],
            **{f: data[f] for f in STUDENT_FIELDS if f in data},
        )
    return student


# ---------------------------------------------------------------- UC 24
def update_student(admin_user, student_id: int, data: dict) -> None:
    """Sửa mọi thông tin TRỪ student_code. Lỗi: VALIDATION, MISSING_FIELDS, NOT_FOUND."""
    _check_admin(admin_user)

    student = Student.objects.select_related("user").filter(pk=student_id).first()
    if student is None:
        raise ServiceError(ErrorCode.NOT_FOUND, "Không tìm thấy sinh viên")

    data = dict(data)
    data.pop("student_code", None)      # không cho sửa mã SV

    # Trường bắt buộc mà bị gửi lên rỗng -> lỗi
    missing = [f for f in REQUIRED_FIELDS
               if f != "student_code" and f in data and _is_empty(data[f])]
    if missing:
        raise ServiceError(ErrorCode.MISSING_FIELDS, "Thiếu thông tin: " + ", ".join(missing), missing)

    data = _clean_and_validate(data)

    if "email" in data and _email_taken(data["email"], exclude_user_id=student.user_id):
        raise ServiceError(ErrorCode.DUPLICATE, "Email đã tồn tại")

    with transaction.atomic():
        user = student.user
        for f in USER_FIELDS:
            if f in data:
                setattr(user, f, data[f])
        user.save()

        for f in STUDENT_FIELDS:
            if f in data:
                setattr(student, f, data[f])
        student.save()


# ---------------------------------------------------------------- UC 25
def change_academic_status(admin_user, student_id: int, new_status: str, note: str = "") -> None:
    """Kiểm tra AcademicStatus.VALID_TRANSITIONS, ghi AcademicStatusHistory.
    Lỗi: INVALID_STATUS_CHANGE."""
    _check_admin(admin_user)

    with transaction.atomic():
        student = Student.objects.select_for_update().filter(pk=student_id).first()
        if student is None:
            raise ServiceError(ErrorCode.NOT_FOUND, "Không tìm thấy sinh viên")

        old_status = student.academic_status
        allowed = AcademicStatus.VALID_TRANSITIONS.get(old_status, set())
        if new_status not in allowed:
            raise ServiceError(
                ErrorCode.INVALID_STATUS_CHANGE,
                f"Không thể chuyển từ {old_status} sang {new_status}",
            )

        AcademicStatusHistory.objects.create(
            student=student, editor=admin_user,
            old_status=old_status, new_status=new_status, note=note or "",
        )
        student.academic_status = new_status
        student.save()


def list_students(admin_user, page: int = 1):
    """Danh sách sinh viên, mỗi trang PAGE_SIZE dòng."""
    _check_admin(admin_user)
    qs = Student.objects.select_related("user").order_by("student_code")
    paginator = Paginator(qs, PAGE_SIZE)
    page_obj = paginator.get_page(page)
    return Page(list(page_obj.object_list), page_obj.number, paginator.num_pages, paginator.count)


def get_status_history(admin_user, student_id: int) -> list:
    """Lịch sử đổi trạng thái của 1 sinh viên, mới nhất trước."""
    _check_admin(admin_user)
    if not Student.objects.filter(pk=student_id).exists():
        raise ServiceError(ErrorCode.NOT_FOUND, "Không tìm thấy sinh viên")
    return list(
        AcademicStatusHistory.objects.filter(student_id=student_id)
        .select_related("editor").order_by("-changed_at")
    )