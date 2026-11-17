"""
courses/views.py  (Backend: BE2   Frontend: FE3 (Admin) + FE1/FE2 (xem section))

View khung: chưa cài thì hiện trang "[CHƯA CÀI ĐẶT] tên_view". Khi làm:
 1. BE gọi hàm trong services.py, bắt ServiceError, truyền dữ liệu vào template (context theo docs/api/courses.md).
 2. FE viết template tương ứng trong templates/courses/.
"""
from django.http import HttpResponse
from django.shortcuts import render
from common.contract import Role, ServiceError
from common.permissions import role_required


def _stub(name):
    return HttpResponse(f"[CHƯA CÀI ĐẶT] {name}()", status=501)


@role_required(Role.ADMINISTRATOR)
def course_list_view(request, **kwargs):
    """Admin 5.4 danh sách + form thêm course (UC 26)
    Template: courses/course_list.html"""
    # TODO (BE2): cài đặt
    return _stub("course_list_view")


@role_required(Role.ADMINISTRATOR)
def course_edit_view(request, **kwargs):
    """Sửa course (UC 26)
    Template: courses/course_form.html"""
    # TODO (BE2): cài đặt
    return _stub("course_edit_view")


@role_required(Role.ADMINISTRATOR)
def course_delete_view(request, **kwargs):
    """POST xóa course (UC 26)
    Template: (không có - POST rồi redirect)"""
    # TODO (BE2): cài đặt
    return _stub("course_delete_view")


@role_required(Role.ADMINISTRATOR, Role.TEACHER, Role.STUDENT)
def section_list_view(request, **kwargs):
    """Xem section của học kỳ (UC 6)
    Template: courses/section_list.html"""
    # TODO (BE2): cài đặt
    return _stub("section_list_view")


@role_required(Role.ADMINISTRATOR)
def section_create_view(request, **kwargs):
    """Admin 5.6 tạo section (UC 27)
    Template: courses/section_form.html"""
    # TODO (BE2): cài đặt
    return _stub("section_create_view")


@role_required(Role.ADMINISTRATOR)
def section_students_view(request, **kwargs):
    """Admin 5.5 DS sinh viên của section (UC 28)
    Template: courses/section_students.html"""
    # TODO (BE2): cài đặt
    return _stub("section_students_view")
