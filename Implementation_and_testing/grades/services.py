"""grades/services.py  (Phụ trách: Duy)   UC: 10, 14, 15, 16, 17, 18 (theo SRS: xem điểm, nhập/sửa, khóa, mở khóa)"""
from common.contract import not_implemented


def get_gradebook(teacher_user, section_id: int) -> dict:
    """{section, is_locked, weights, rows:[{enrollment_id, student_code, full_name, attendance, midterm,
    final, final_score, letter, gp4}]}. Lỗi: PERMISSION_DENIED nếu không dạy section này."""
    not_implemented("get_gradebook")


def save_grades(teacher_user, section_id: int, entries: list) -> None:
    """UC Enter + Edit grades. entries: [{enrollment_id, attendance, midterm, final}].
    Quy trình: kiểm tra quyền -> kiểm tra khóa (GRADEBOOK_LOCKED) -> validate_scores cho TỪNG dòng
    (nếu có lỗi: ném GRADE_OUT_OF_RANGE kèm details, KHÔNG lưu dòng nào) -> lưu + tính lại final/letter/gp4
    -> ghi GradeEditLog cho mọi giá trị thay đổi. Toàn bộ trong transaction."""
    not_implemented("save_grades")


def lock_gradebook(teacher_user, section_id: int) -> None:
    """Lỗi: GRADES_INCOMPLETE (còn SV chưa đủ điểm), PERMISSION_DENIED. Sau khi khóa, tính SemesterGPA."""
    not_implemented("lock_gradebook")


def list_locked_gradebooks(admin_user, page: int = 1):
    not_implemented("list_locked_gradebooks")


def unlock_gradebook(admin_user, section_id: int, reason: str) -> None:
    """Lỗi: UNLOCK_REASON_REQUIRED nếu reason rỗng. Ghi GradebookUnlockLog. Quyết định về GPA: DECISIONS #8."""
    not_implemented("unlock_gradebook")


def get_unlock_history(admin_user, section_id: int = None) -> list:
    not_implemented("get_unlock_history")


def get_student_results(student, semester_id: int = None) -> dict:
    """UC 10. CHỈ gồm điểm của gradebook đã khóa.
    {rows:[{section_code, course_name, credits, attendance, midterm, final, final_score, letter, passed}],
     gpa, academic_status, has_unlocked: bool}"""
    not_implemented("get_student_results")


def recalculate_semester_gpa(student, semester) -> None:
    not_implemented("recalculate_semester_gpa")
