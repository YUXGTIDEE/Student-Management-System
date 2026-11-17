"""students/services.py  (Phụ trách: Minh)   UC: 23, 24, 25"""
from common.contract import not_implemented


def create_student(admin_user, data: dict):
    """data: student_code, full_name, date_of_birth, gender, email, phone_number, address,
    place_of_birth, academic_cohort, major, student_class, academic_status.
    Tạo User(role=STUDENT, username=student_code) + Student trong 1 transaction.
    Lỗi: DUPLICATE (mã SV/email), VALIDATION (mã SV không đúng ^\\d{6}$), MISSING_FIELDS."""
    not_implemented("create_student")


def update_student(admin_user, student_id: int, data: dict) -> None:
    """Sửa mọi thông tin TRỪ student_code. Lỗi: VALIDATION, MISSING_FIELDS, NOT_FOUND."""
    not_implemented("update_student")


def change_academic_status(admin_user, student_id: int, new_status: str, note: str = "") -> None:
    """Kiểm tra AcademicStatus.VALID_TRANSITIONS, ghi AcademicStatusHistory.
    Lỗi: INVALID_STATUS_CHANGE."""
    not_implemented("change_academic_status")


def list_students(admin_user, page: int = 1):
    not_implemented("list_students")


def get_status_history(admin_user, student_id: int) -> list:
    not_implemented("get_status_history")
