"""
common/contract.py - HỢP ĐỒNG CHUNG CỦA NHÓM  (Phụ trách: BE1)

QUY TẮC (giống Order.h của project mẫu):
 - Đây là "hợp đồng" chung. Mỗi người chỉ cài đặt phần của mình,
   KHÔNG tự ý đổi tên enum, hằng số, mã lỗi, chữ ký hàm trong file này
   và trong các file services.py.
 - Muốn đổi: báo cả nhóm trước, vì đổi một chỗ có thể làm hỏng code người khác.
 - Hàm còn là khung sẽ gọi not_implemented("tên_hàm") -> báo lỗi rõ ràng,
   project vẫn import và chạy được.
"""
from decimal import Decimal


# ============================================================================
#  1. ENUM DÙNG CHUNG (khớp Class Diagram trong SRS)
# ============================================================================
class Role:
    STUDENT = "STUDENT"
    TEACHER = "TEACHER"
    ADMINISTRATOR = "ADMINISTRATOR"
    CHOICES = [(STUDENT, "Student"), (TEACHER, "Teacher"), (ADMINISTRATOR, "Administrator")]


class AcademicStatus:
    ENROLLED = "ENROLLED"
    WITHDRAWN = "WITHDRAWN"
    TEMPORARILY_SUSPENDED = "TEMPORARILY_SUSPENDED"
    GRADUATED = "GRADUATED"
    CHOICES = [
        (ENROLLED, "Enrolled"),
        (WITHDRAWN, "Withdrawn"),
        (TEMPORARILY_SUSPENDED, "Temporarily Suspended"),
        (GRADUATED, "Graduated"),
    ]
    # Quy tắc đổi trạng thái hợp lệ (xem DECISIONS.md mục 6). BE2 dùng trong UC Edit academic status.
    VALID_TRANSITIONS = {
        ENROLLED: {WITHDRAWN, TEMPORARILY_SUSPENDED, GRADUATED},
        TEMPORARILY_SUSPENDED: {ENROLLED, WITHDRAWN},
        WITHDRAWN: set(),
        GRADUATED: set(),
    }


class Gender:
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"
    CHOICES = [(MALE, "Male"), (FEMALE, "Female"), (OTHER, "Other")]


class EnrollmentStatus:
    REGISTERED = "REGISTERED"
    CANCELLED = "CANCELLED"
    CHOICES = [(REGISTERED, "Registered"), (CANCELLED, "Cancelled")]


class LetterGrade:
    A, B, C, D, F = "A", "B", "C", "D", "F"
    CHOICES = [(x, x) for x in (A, B, C, D, F)]


class ResetStatus:
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    EXPIRED = "EXPIRED"
    CHOICES = [(PENDING, "Pending"), (COMPLETED, "Completed"), (EXPIRED, "Expired")]


# ============================================================================
#  2. HẰNG SỐ NGHIỆP VỤ (chốt trong DECISIONS.md - sửa ở DECISIONS trước, rồi mới sửa ở đây)
# ============================================================================
STUDENT_CODE_REGEX = r"^\d{6}$"          # mã sinh viên: đúng 6 chữ số
TEACHER_CODE_REGEX = r"^GV\d{3,4}$"      # mã giảng viên: GV001...
ADMIN_CODE_REGEX = r"^AD\d{3,4}$"        # mã admin: AD001...

MIN_SCORE = Decimal("0")
MAX_SCORE = Decimal("10")

# Trọng số mặc định (tổng 100%): chuyên cần / giữa kỳ / cuối kỳ
DEFAULT_WEIGHTS = {"attendance": Decimal("10"), "midterm": Decimal("30"), "final": Decimal("60")}

# Bảng quy đổi: (điểm tối thiểu, chữ, thang 4). Duyệt từ trên xuống, gặp dòng đầu thỏa thì dừng.
GRADE_SCALE = [
    (Decimal("8.5"), LetterGrade.A, Decimal("4.0")),
    (Decimal("7.0"), LetterGrade.B, Decimal("3.0")),
    (Decimal("5.5"), LetterGrade.C, Decimal("2.0")),
    (Decimal("4.0"), LetterGrade.D, Decimal("1.0")),
    (Decimal("0"), LetterGrade.F, Decimal("0.0")),
]
PASS_MIN_SCORE = Decimal("4.0")           # từ 4.0 trở lên là đậu (passed)

MAX_FAILED_LOGINS = 5                      # đăng nhập sai quá số này thì khóa tài khoản
PASSWORD_RESET_TOKEN_MINUTES = 30
PAGE_SIZE = 10                             # số dòng mỗi trang cho mọi danh sách


# ============================================================================
#  3. MÃ LỖI - mọi service lỗi nghiệp vụ đều ném ServiceError(code, message)
#     FE dựa vào `code` để hiển thị đúng thông báo trong GUI.
# ============================================================================
class ErrorCode:
    # chung
    PERMISSION_DENIED = "PERMISSION_DENIED"
    NOT_FOUND = "NOT_FOUND"
    VALIDATION = "VALIDATION"
    MISSING_FIELDS = "MISSING_FIELDS"
    DUPLICATE = "DUPLICATE"
    # auth
    BAD_CREDENTIALS = "BAD_CREDENTIALS"
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"
    CANNOT_LOCK_SELF = "CANNOT_LOCK_SELF"
    # course / section
    COURSE_IN_USE = "COURSE_IN_USE"
    PREREQ_CYCLE = "PREREQ_CYCLE"
    TEACHER_CONFLICT = "TEACHER_CONFLICT"
    ROOM_CONFLICT = "ROOM_CONFLICT"
    INVALID_STATUS_CHANGE = "INVALID_STATUS_CHANGE"
    # registration
    REGISTRATION_CLOSED = "REGISTRATION_CLOSED"
    SECTION_FULL = "SECTION_FULL"
    ALREADY_REGISTERED = "ALREADY_REGISTERED"
    SCHEDULE_CONFLICT = "SCHEDULE_CONFLICT"
    PREREQ_NOT_MET = "PREREQ_NOT_MET"
    CANCEL_DEADLINE_PASSED = "CANCEL_DEADLINE_PASSED"
    # grades
    GRADEBOOK_LOCKED = "GRADEBOOK_LOCKED"
    GRADE_OUT_OF_RANGE = "GRADE_OUT_OF_RANGE"
    GRADES_INCOMPLETE = "GRADES_INCOMPLETE"
    UNLOCK_REASON_REQUIRED = "UNLOCK_REASON_REQUIRED"


class ServiceError(Exception):
    """Lỗi nghiệp vụ. `details` dùng cho lỗi nhiều mục (ví dụ danh sách ô điểm sai)."""

    def __init__(self, code, message="", details=None):
        super().__init__(message or code)
        self.code = code
        self.message = message or code
        self.details = details or []


# ============================================================================
#  4. KIỂU TRẢ VỀ CHUNG CHO DANH SÁCH PHÂN TRANG
# ============================================================================
class Page:
    """items: list; page: số trang (từ 1); num_pages; total: tổng số dòng."""

    def __init__(self, items, page, num_pages, total):
        self.items, self.page, self.num_pages, self.total = items, page, num_pages, total


# ============================================================================
#  5. HÀM TIỆN ÍCH CHO FILE KHUNG
# ============================================================================
def not_implemented(func_name):
    """Gọi trong thân hàm khung. Dòng này tương đương notImplemented() của project mẫu."""
    raise NotImplementedError(f"[CHƯA CÀI ĐẶT] {func_name}()")
