"""Unit test cho paginate() - dùng list nên không cần database."""
import pytest

from common.contract import PAGE_SIZE
from common.pagination import paginate

DATA = list(range(1, 26))          # 25 phần tử -> 3 trang với PAGE_SIZE = 10


def test_first_page():
    p = paginate(DATA, 1)
    assert p.items == list(range(1, PAGE_SIZE + 1))
    assert (p.page, p.num_pages, p.total) == (1, 3, 25)


def test_last_page_has_remainder():
    p = paginate(DATA, 3)
    assert p.items == [21, 22, 23, 24, 25]
    assert p.page == 3


def test_page_number_as_string():
    assert paginate(DATA, "2").page == 2


@pytest.mark.parametrize("bad", [None, "", "abc", 0, -5, 4, 999, "1.5"])
def test_invalid_page_falls_back_to_first(bad):
    p = paginate(DATA, bad)
    assert p.page == 1
    assert p.items == list(range(1, PAGE_SIZE + 1))


def test_custom_page_size():
    p = paginate(DATA, 2, page_size=5)
    assert p.items == [6, 7, 8, 9, 10]
    assert p.num_pages == 5


@pytest.mark.parametrize("bad_size", [0, -1, "x", None])
def test_invalid_page_size_uses_default(bad_size):
    assert paginate(DATA, 1, page_size=bad_size).num_pages == 3


def test_empty_list():
    p = paginate([], 1)
    assert p.items == [] and (p.page, p.num_pages, p.total) == (1, 1, 0)