"""common/pagination.py (Hoa Binh) - phân trang dùng chung."""
from django.core.paginator import Paginator
from .contract import PAGE_SIZE, Page

def paginate(queryset, page_number, page_size=None) -> Page:
    """Cắt queryset thành trang. page_size mặc định = PAGE_SIZE. Trang sai -> trang 1.

    - queryset: QuerySet hoặc list. Với QuerySet NÊN gọi .order_by(...) trước để thứ tự
      giữa các trang ổn định (nếu không Django sẽ cảnh báo UnorderedObjectListWarning).
    - page_number: số trang bắt đầu từ 1; nhận cả chuỗi từ request.GET.get("page").
      Giá trị None, rỗng, không phải số, < 1 hoặc vượt quá số trang đều quy về trang 1.
    - page_size: số dòng mỗi trang; None hoặc giá trị không hợp lệ (< 1) -> PAGE_SIZE.
    - Danh sách rỗng vẫn trả về Page(items=[], page=1, num_pages=1, total=0).
    """
    try:
        size = int(page_size) if page_size is not None else PAGE_SIZE
    except (TypeError, ValueError):
        size = PAGE_SIZE
    if size < 1:
        size = PAGE_SIZE

    paginator = Paginator(queryset, size)

    try:
        number = int(page_number)
    except (TypeError, ValueError):
        number = 1
    if number < 1 or number > paginator.num_pages:
        number = 1

    page = paginator.page(number)
    return Page(
        items=list(page.object_list),
        page=number,
        num_pages=paginator.num_pages,
        total=paginator.count,
    )
