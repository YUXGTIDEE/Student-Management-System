"""courses/services.py  (Phụ trách: BE2)   UC: 6 (xem section), 26, 27, 28 (xem DS sinh viên của section)"""
from common.contract import not_implemented


# ---- UC 26: quản lý course ------------------------------------------------------
def list_courses(q: str = "", page: int = 1):
    """Mỗi dòng có thêm cờ in_use (đã có section) để FE hiện nhãn 'In use'."""
    not_implemented("list_courses")


def create_course(admin_user, course_code: str, course_name: str, credit_hours: int,
                  class_periods: int, description: str = ""):
    """Lỗi: DUPLICATE, VALIDATION."""
    not_implemented("create_course")


def update_course(admin_user, course_id: int, course_name: str, credit_hours: int,
                  class_periods: int, description: str = "") -> None:
    not_implemented("update_course")


def delete_course(admin_user, course_id: int) -> None:
    """Lỗi: COURSE_IN_USE nếu đã có section hoặc grade."""
    not_implemented("delete_course")


def set_prerequisites(admin_user, course_id: int, prerequisite_ids: list) -> None:
    """Lỗi: PREREQ_CYCLE nếu tạo vòng lặp trực tiếp hoặc gián tiếp."""
    not_implemented("set_prerequisites")


# ---- UC 27: tạo section --------------------------------------------------------------
def create_section(admin_user, section_code: str, course_id: int, semester_id: int, teacher_id: int,
                   classroom: str, max_capacity: int, schedules: list):
    """schedules: [{day_of_week, start_time, end_time}].
    Tự tạo Gradebook mặc định (10/30/60) cho section.
    Lỗi: DUPLICATE (mã section), TEACHER_CONFLICT, ROOM_CONFLICT."""
    not_implemented("create_section")


# ---- UC 6, 28: xem section --------------------------------------------------------
def list_offered_sections(semester_id: int, q: str = "", page: int = 1):
    """Các section của học kỳ. Dùng cho Student/Teacher/Admin xem."""
    not_implemented("list_offered_sections")


def list_section_students(admin_user, section_id: int, page: int = 1) -> dict:
    """Trả về {section, current_enrollment, max_capacity, students: Page{student_code, full_name, class, registered_at}}."""
    not_implemented("list_section_students")


def list_semesters() -> list:
    not_implemented("list_semesters")
