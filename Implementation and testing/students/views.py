"""
students/views.py  (Backend: BE2   Frontend: FE3)

View khung: chưa cài thì hiện trang "[CHƯA CÀI ĐẶT] tên_view". Khi làm:
 1. BE gọi hàm trong services.py, bắt ServiceError, truyền dữ liệu vào template (context theo docs/api/students.md).
 2. FE viết template tương ứng trong templates/students/.
"""
from django.http import HttpResponse
from django.shortcuts import render
from common.contract import Role, ServiceError
from common.permissions import role_required


def _stub(name):
    return HttpResponse(f"[CHƯA CÀI ĐẶT] {name}()", status=501)


@role_required(Role.ADMINISTRATOR)
def student_list_view(request, **kwargs):
    """Admin 5.3 danh sách hồ sơ (UC 23)
    Template: students/student_list.html"""
    # TODO (BE2): cài đặt
    return _stub("student_list_view")


@role_required(Role.ADMINISTRATOR)
def student_create_view(request, **kwargs):
    """Admin 5.3 thêm hồ sơ (UC 23)
    Template: students/student_form.html"""
    # TODO (BE2): cài đặt
    return _stub("student_create_view")


@role_required(Role.ADMINISTRATOR)
def student_edit_view(request, **kwargs):
    """Admin 5.3 sửa hồ sơ (UC 24)
    Template: students/student_form.html"""
    # TODO (BE2): cài đặt
    return _stub("student_edit_view")


@role_required(Role.ADMINISTRATOR)
def student_status_view(request, **kwargs):
    """POST đổi trạng thái học tập (UC 25)
    Template: (không có - POST rồi redirect)"""
    # TODO (BE2): cài đặt
    return _stub("student_status_view")
