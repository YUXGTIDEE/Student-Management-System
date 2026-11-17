"""
grades/calculator.py  (Phụ trách: BE3)   HÀM THUẦN, KHÔNG đụng database -> dễ unit test.
Công thức và bảng quy đổi lấy từ common/contract.py.
"""
from decimal import Decimal
from common.contract import not_implemented


def validate_scores(scores: dict) -> list:
    """UC 16. scores: {'attendance':..., 'midterm':..., 'final':...} (giá trị có thể là chuỗi/None).
    Trả về danh sách lỗi [{field, value, reason}]; rỗng nghĩa là hợp lệ. Khoảng hợp lệ MIN_SCORE..MAX_SCORE."""
    not_implemented("validate_scores")


def calculate_final_score(attendance, midterm, final_exam, weights: dict = None) -> Decimal:
    """Tổng có trọng số, làm tròn 2 chữ số."""
    not_implemented("calculate_final_score")


def convert_to_letter(final_score: Decimal) -> str:
    not_implemented("convert_to_letter")


def convert_to_grade_point4(final_score: Decimal) -> Decimal:
    not_implemented("convert_to_grade_point4")


def is_passed(final_score: Decimal) -> bool:
    not_implemented("is_passed")


def calculate_gpa(items: list) -> Decimal:
    """items: [(grade_point4, credit_hours), ...]. GPA = sum(gp4*credits)/sum(credits). Rỗng -> Decimal('0')."""
    not_implemented("calculate_gpa")
