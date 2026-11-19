"""
grades/calculator.py  (Phụ trách: Duy)   HÀM THUẦN, KHÔNG đụng database -> dễ unit test.
Công thức và bảng quy đổi lấy từ common/contract.py.
"""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from common.contract import (
    DEFAULT_WEIGHTS,
    GRADE_SCALE,
    MAX_SCORE,
    MIN_SCORE,
    PASS_MIN_SCORE,
)


def validate_scores(scores: dict) -> list:
    """
    Kiểm tra điểm chuyên cần, giữa kỳ và cuối kỳ.

    Trả về danh sách lỗi:
    [
        {
            "field": "attendance",
            "value": "12",
            "reason": "Điểm phải nằm trong khoảng 0 đến 10."
        }
    ]
    """
    errors = []

    required_fields = ["attendance", "midterm", "final"]

    for field in required_fields:
        value = scores.get(field)

        if value is None or value == "":
            errors.append({
                "field": field,
                "value": value,
                "reason": "Không được để trống điểm.",
            })
            continue

        try:
            score = Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            errors.append({
                "field": field,
                "value": value,
                "reason": "Điểm phải là một số hợp lệ.",
            })
            continue

        if not score.is_finite():
            errors.append({
                "field": field,
                "value": value,
                "reason": "Điểm phải là một số hữu hạn.",
            })
            continue

        if score < MIN_SCORE or score > MAX_SCORE:
            errors.append({
                "field": field,
                "value": value,
                "reason": "Điểm phải nằm trong khoảng 0 đến 10.",
            })

    return errors


def calculate_final_score(
    attendance,
    midterm,
    final_exam,
    weights: dict = None,
) -> Decimal:
    """Tính điểm tổng kết theo trọng số và làm tròn 2 chữ số."""
    weights = weights or DEFAULT_WEIGHTS

    attendance = Decimal(str(attendance))
    midterm = Decimal(str(midterm))
    final_exam = Decimal(str(final_exam))

    attendance_weight = Decimal(str(weights["attendance"]))
    midterm_weight = Decimal(str(weights["midterm"]))
    final_weight = Decimal(str(weights["final"]))

    total_weight = (
        attendance_weight + midterm_weight + final_weight
    )

    if total_weight != Decimal("100"):
        raise ValueError("Tổng trọng số phải bằng 100%.")

    result = (
        attendance * attendance_weight
        + midterm * midterm_weight
        + final_exam * final_weight
    ) / Decimal("100")

    return result.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def convert_to_letter(final_score: Decimal) -> str:
    """Quy đổi điểm tổng kết thành điểm chữ."""
    score = Decimal(str(final_score))

    for minimum, letter, _ in GRADE_SCALE:
        if score >= minimum:
            return letter

    return "F"


def convert_to_grade_point4(final_score: Decimal) -> Decimal:
    """Quy đổi điểm tổng kết thành thang điểm 4."""
    score = Decimal(str(final_score))

    for minimum, _, grade_point in GRADE_SCALE:
        if score >= minimum:
            return grade_point

    return Decimal("0.0")


def is_passed(final_score: Decimal) -> bool:
    """Kiểm tra sinh viên có đạt môn học hay không."""
    return Decimal(str(final_score)) >= PASS_MIN_SCORE


def calculate_gpa(items: list) -> Decimal:
    """
    Tính GPA có trọng số theo số tín chỉ.

    items:
    [
        (grade_point4, credit_hours),
        ...
    ]
    """
    total_points = Decimal("0")
    total_credits = 0

    for grade_point, credits in items:
        if grade_point is None or not credits:
            continue

        credits = int(credits)

        if credits <= 0:
            continue

        total_points += Decimal(str(grade_point)) * credits
        total_credits += credits

    if total_credits == 0:
        return Decimal("0.00")

    return (total_points / Decimal(total_credits)).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

