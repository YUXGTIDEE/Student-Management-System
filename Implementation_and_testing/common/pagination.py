"""common/pagination.py (BE1) - phân trang dùng chung."""
from .contract import Page, not_implemented


def paginate(queryset, page_number, page_size=None) -> Page:
    """Cắt queryset thành trang. page_size mặc định = PAGE_SIZE. Trang sai -> trang 1."""
    not_implemented("paginate")
