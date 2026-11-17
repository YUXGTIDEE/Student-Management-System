"""
search/views.py  (Backend: BE1   Frontend: FE2)

View khung: chưa cài thì hiện trang "[CHƯA CÀI ĐẶT] tên_view". Khi làm:
 1. BE gọi hàm trong services.py, bắt ServiceError, truyền dữ liệu vào template (context theo docs/api/search.md).
 2. FE viết template tương ứng trong templates/search/.
"""
from django.http import HttpResponse
from django.shortcuts import render
from common.contract import Role, ServiceError
from common.permissions import role_required


def _stub(name):
    return HttpResponse(f"[CHƯA CÀI ĐẶT] {name}()", status=501)


@role_required(Role.ADMINISTRATOR, Role.TEACHER)
def student_search_view(request, **kwargs):
    """GV 4.1 / Admin tìm kiếm + lọc (UC 12, 22)
    Template: search/student_search.html"""
    # TODO (BE1): cài đặt
    return _stub("student_search_view")


@role_required(Role.ADMINISTRATOR, Role.TEACHER)
def student_detail_view(request, **kwargs):
    """GV 4.2 hồ sơ chi tiết chỉ đọc (UC 13)
    Template: search/student_detail.html"""
    # TODO (BE1): cài đặt
    return _stub("student_detail_view")


@role_required(Role.TEACHER)
def assigned_sections_view(request, **kwargs):
    """GV 4.3 danh sách được phân công (UC 11)
    Template: search/assigned.html"""
    # TODO (BE1): cài đặt
    return _stub("assigned_sections_view")
