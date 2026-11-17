"""registration/services.py  (Phụ trách: BE3)   UC: 7, 8, 9 (đánh số theo SRS: 6-9 phía sinh viên)"""
from common.contract import not_implemented


def list_open_sections(student, semester_id: int, q: str = "", page: int = 1):
    """Mỗi dòng: {section_code, course_name, course_code, credits, teacher, schedule, classroom,
    max_capacity, remaining, state} với state in {OPEN, FULL, REGISTERED, CLOSED}."""
    not_implemented("list_open_sections")


def validate_registration(student, section) -> None:
    """Kiểm tra 5 điều kiện: kỳ đăng ký, còn chỗ, chưa đăng ký, không trùng lịch, đã qua môn tiên quyết.
    Không đủ -> raise ServiceError(REGISTRATION_CLOSED | SECTION_FULL | ALREADY_REGISTERED |
    SCHEDULE_CONFLICT | PREREQ_NOT_MET). Dùng cho dialog xác nhận (3.4)."""
    not_implemented("validate_registration")


def register_section(student, section_id: int):
    """Đăng ký thật. BẮT BUỘC chạy trong transaction.atomic() và tăng sĩ số bằng cập nhật nguyên tử:
        UPDATE ... SET current_enrollment = current_enrollment + 1 WHERE id=%s AND current_enrollment < max_capacity
    nếu 0 dòng bị ảnh hưởng -> SECTION_FULL. Trả về Enrollment."""
    not_implemented("register_section")


def cancel_registration(student, section_id: int) -> None:
    """Kiểm tra section thuộc sinh viên và chưa quá hạn hủy; giảm sĩ số nguyên tử.
    Lỗi: PERMISSION_DENIED, CANCEL_DEADLINE_PASSED."""
    not_implemented("cancel_registration")


def list_registered_sections(student, semester_id: int = None) -> list:
    """Mỗi dòng: {section_code, course_name, teacher, schedule, registered_at, can_cancel}."""
    not_implemented("list_registered_sections")
