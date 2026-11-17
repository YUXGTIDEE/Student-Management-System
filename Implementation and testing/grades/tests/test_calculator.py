"""Unit test mẫu cho BE3 (hàm thuần). Điền giá trị đã tính tay, đặc biệt các giá trị biên."""
import pytest
from decimal import Decimal
from grades import calculator


@pytest.mark.skip(reason="BE3 bỏ skip khi cài calculate_final_score")
def test_final_score_weights_10_30_60():
    # 10*0.1 + 5*0.3 + 8*0.6 = 7.3
    assert calculator.calculate_final_score(Decimal("10"), Decimal("5"), Decimal("8")) == Decimal("7.30")
