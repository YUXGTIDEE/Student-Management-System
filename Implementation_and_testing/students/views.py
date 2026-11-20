"""
students/views.py  (Backend: Minh   Frontend: Thành)

View khung: chưa cài thì hiện trang "[CHƯA CÀI ĐẶT] tên_view". Khi làm:
 1. BE gọi hàm trong services.py, bắt ServiceError, truyền dữ liệu vào template (context theo docs/api/students.md).
 2. FE viết template tương ứng trong templates/students/.
"""
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render
from common.contract import Role, ServiceError
from common.permissions import role_required

from . import services
from .models import Student


def _stub(name):
    return HttpResponse(f"[CHƯA CÀI ĐẶT] {name}()", status=501)


@role_required(Role.ADMINISTRATOR)
def student_list_view(request, **kwargs):
    """Admin 5.3 danh sách hồ sơ (UC 23)
    Template: students/student_list.html"""
    page = services.list_students(request.user, request.GET.get("page", 1))
    return render(request, "students/student_list.html", {"page": page})


@role_required(Role.ADMINISTRATOR)
def student_create_view(request, **kwargs):
    """Admin 5.3 thêm hồ sơ (UC 23)
    Template: students/student_form.html"""
    if request.method == "POST":
        try:
            services.create_student(request.user, request.POST.dict())
            return redirect("students:student_list_view")
        except ServiceError as e:
            messages.error(request, e.message)
    return render(request, "students/student_form.html", {"form_data": request.POST})


@role_required(Role.ADMINISTRATOR)
def student_edit_view(request, **kwargs):
    """Admin 5.3 sửa hồ sơ (UC 24)
    Template: students/student_form.html"""
    student = Student.objects.select_related("user").filter(pk=kwargs.get("student_id")).first()
    if student is None:
        messages.error(request, "Không tìm thấy sinh viên")
        return redirect("students:student_list_view")
    if request.method == "POST":
        try:
            services.update_student(request.user, student.pk, request.POST.dict())
            return redirect("students:student_list_view")
        except ServiceError as e:
            messages.error(request, e.message)
    history = services.get_status_history(request.user, student.pk)
    return render(request, "students/student_form.html",
                  {"student": student, "history": history, "form_data": request.POST})


@role_required(Role.ADMINISTRATOR)
def student_status_view(request, **kwargs):
    """POST đổi trạng thái học tập (UC 25)
    Template: (không có - POST rồi redirect)"""
    if request.method == "POST":
        try:
            services.change_academic_status(
                request.user, int(kwargs.get("student_id")),
                request.POST.get("new_status", ""), request.POST.get("note", ""))
        except ServiceError as e:
            messages.error(request, e.message)
    return redirect("students:student_list_view")