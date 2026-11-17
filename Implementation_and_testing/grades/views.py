"""
grades/views.py  (Backend: Duy   Frontend: Đạt (Teacher) + Thành (Admin) + Huy (Student))

View khung: chưa cài thì hiện trang "[CHƯA CÀI ĐẶT] tên_view". Khi làm:
 1. BE gọi hàm trong services.py, bắt ServiceError, truyền dữ liệu vào template (context theo docs/api/grades.md).
 2. FE viết template tương ứng trong templates/grades/.
"""
from django.http import HttpResponse
from django.shortcuts import render
from common.contract import Role, ServiceError
from common.permissions import role_required


def _stub(name):
    return HttpResponse(f"[CHƯA CÀI ĐẶT] {name}()", status=501)


@role_required(Role.STUDENT)
def student_results_view(request, **kwargs):
    """SV 3.7 kết quả học tập (UC 10)
    Template: grades/student_results.html"""
    # TODO (Duy): cài đặt
    return _stub("student_results_view")


@role_required(Role.TEACHER)
def gradebook_view(request, **kwargs):
    """GV 4.4 gradebook (UC 14, 15)
    Template: grades/gradebook.html"""
    # TODO (Duy): cài đặt
    return _stub("gradebook_view")


@role_required(Role.TEACHER)
def gradebook_save_view(request, **kwargs):
    """POST lưu điểm (UC 14, 15, 16)
    Template: (không có - POST rồi redirect)"""
    # TODO (Duy): cài đặt
    return _stub("gradebook_save_view")


@role_required(Role.TEACHER)
def gradebook_lock_view(request, **kwargs):
    """POST khóa gradebook, dialog 4.5 (UC 17)
    Template: (không có - POST rồi redirect)"""
    # TODO (Duy): cài đặt
    return _stub("gradebook_lock_view")


@role_required(Role.ADMINISTRATOR)
def locked_gradebooks_view(request, **kwargs):
    """Admin 5.7 danh sách đã khóa (UC 18)
    Template: grades/locked_list.html"""
    # TODO (Duy): cài đặt
    return _stub("locked_gradebooks_view")


@role_required(Role.ADMINISTRATOR)
def gradebook_unlock_view(request, **kwargs):
    """POST mở khóa kèm lý do (UC 18)
    Template: (không có - POST rồi redirect)"""
    # TODO (Duy): cài đặt
    return _stub("gradebook_unlock_view")
