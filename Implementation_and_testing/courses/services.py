"""
courses/views.py  (Backend: Minh   Frontend: Thành (Admin) + Huy/Đạt (xem section))

View khung: chưa cài thì hiện trang "[CHƯA CÀI ĐẶT] tên_view". Khi làm:
 1. BE gọi hàm trong services.py, bắt ServiceError, truyền dữ liệu vào template (context theo docs/api/courses.md).
 2. FE viết template tương ứng trong templates/courses/.
"""
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render
from common.contract import Role, ServiceError
from common.permissions import role_required

from . import services
from .models import Course


def _stub(name):
    return HttpResponse(f"[CHƯA CÀI ĐẶT] {name}()", status=501)


@role_required(Role.ADMINISTRATOR)
def course_list_view(request, **kwargs):
    """Admin 5.4 danh sách + form thêm course (UC 26)
    Template: courses/course_list.html"""
    if request.method == "POST":
        p = request.POST
        try:
            services.create_course(request.user, p.get("course_code", ""), p.get("course_name", ""),
                                   p.get("credit_hours"), p.get("class_periods"), p.get("description", ""))
            return redirect("courses:course_list")
        except ServiceError as e:
            messages.error(request, e.message)
    q = request.GET.get("q", "")
    page = services.list_courses(q, request.GET.get("page", 1))
    return render(request, "courses/course_list.html", {"page": page, "q": q, "form_data": request.POST})


@role_required(Role.ADMINISTRATOR)
def course_edit_view(request, **kwargs):
    """Sửa course (UC 26)
    Template: courses/course_form.html"""
    course = Course.objects.filter(pk=kwargs.get("course_id")).first()
    if course is None:
        messages.error(request, "Không tìm thấy môn học")
        return redirect("courses:course_list")
    if request.method == "POST":
        p = request.POST
        try:
            if p.get("action") == "prerequisites":
                services.set_prerequisites(request.user, course.pk, p.getlist("prerequisite_ids"))
            else:
                services.update_course(request.user, course.pk, p.get("course_name", ""),
                                       p.get("credit_hours"), p.get("class_periods"), p.get("description", ""))
            return redirect("courses:course_list")
        except ServiceError as e:
            messages.error(request, e.message)
    return render(request, "courses/course_form.html", {"course": course, "form_data": request.POST})


@role_required(Role.ADMINISTRATOR)
def course_delete_view(request, **kwargs):
    """POST xóa course (UC 26)
    Template: (không có - POST rồi redirect)"""
    if request.method == "POST":
        try:
            services.delete_course(request.user, int(kwargs.get("course_id")))
        except ServiceError as e:
            messages.error(request, e.message)
    return redirect("courses:course_list")


@role_required(Role.ADMINISTRATOR, Role.TEACHER, Role.STUDENT)
def section_list_view(request, **kwargs):
    """Xem section của học kỳ (UC 6)
    Template: courses/section_list.html"""
    semesters = services.list_semesters()
    semester_id = kwargs.get("semester_id") or request.GET.get("semester_id")
    if not semester_id and semesters:
        semester_id = semesters[0].pk
    q = request.GET.get("q", "")
    page = services.list_offered_sections(int(semester_id), q, request.GET.get("page", 1)) if semester_id else None
    return render(request, "courses/section_list.html",
                  {"semesters": semesters, "semester_id": semester_id, "page": page, "q": q})


@role_required(Role.ADMINISTRATOR)
def section_create_view(request, **kwargs):
    """Admin 5.6 tạo section (UC 27)
    Template: courses/section_form.html"""
    if request.method == "POST":
        p = request.POST
        schedules = [{"day_of_week": d, "start_time": s, "end_time": e}
                     for d, s, e in zip(p.getlist("day_of_week"), p.getlist("start_time"), p.getlist("end_time"))
                     if d or s or e]
        try:
            services.create_section(request.user, p.get("section_code", ""), p.get("course_id"),
                                    p.get("semester_id"), p.get("teacher_id"), p.get("classroom", ""),
                                    p.get("max_capacity"), schedules)
            return redirect("courses:section_list")
        except ServiceError as e:
            messages.error(request, e.message)
    return render(request, "courses/section_form.html", {"form_data": request.POST})


@role_required(Role.ADMINISTRATOR)
def section_students_view(request, **kwargs):
    """Admin 5.5 DS sinh viên của section (UC 28)
    Template: courses/section_students.html"""
    try:
        data = services.list_section_students(
            request.user, int(kwargs.get("section_id")), request.GET.get("page", 1))
    except ServiceError as e:
        messages.error(request, e.message)
        return redirect("courses:section_list")
    return render(request, "courses/section_students.html", data)