"""search/services.py  (Phụ trách: Bình)   UC: 11, 12, 13, 22"""
from common.contract import not_implemented


def search_students(user, keyword: str = "", student_class: str = "", major: str = "",
                    cohort: str = "", status: str = "", page: int = 1):
    """Trả về Page các dòng {student_code, full_name, student_class, major, academic_status}.
    Admin: toàn bộ sinh viên. Teacher: chỉ sinh viên trong section mình dạy."""
    not_implemented("search_students")


def get_student_detail(user, student_id: int) -> dict:
    """Hồ sơ chi tiết (chỉ đọc): thông tin cá nhân, liên hệ, section hiện tại, điểm của section GV dạy, trạng thái.
    Lỗi: PERMISSION_DENIED nếu giảng viên không dạy sinh viên này."""
    not_implemented("get_student_detail")


def list_assigned_sections(teacher_user, semester_id: int = None) -> list:
    """UC 11, bước 1: danh sách section giảng viên được phân công."""
    not_implemented("list_assigned_sections")


def list_section_students_for_teacher(teacher_user, section_id: int, page: int = 1):
    """UC 11, bước 3: {student_code, full_name, student_class}. Lỗi: PERMISSION_DENIED."""
    not_implemented("list_section_students_for_teacher")
