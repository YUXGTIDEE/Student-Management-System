"""Test mẫu cho BE3/QA: nhiều luồng cùng đăng ký section còn ít chỗ -> sĩ số không vượt max_capacity."""
import pytest


@pytest.mark.skip(reason="Bỏ skip khi register_section đã cài")
def test_capacity_never_exceeded_under_concurrency():
    # TODO: tạo section max_capacity=2, 20 sinh viên, chạy 20 thread register_section,
    # assert số Enrollment REGISTERED == 2 và current_enrollment == 2
    ...
