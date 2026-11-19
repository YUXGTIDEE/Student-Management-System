"""
registration/views.py  (Backend: Duy   Frontend: Đạt)

View khung: chưa cài thì hiện trang "[CHƯA CÀI ĐẶT] tên_view". Khi làm:
 1. BE gọi hàm trong services.py, bắt ServiceError, truyền dữ liệu vào template (context theo docs/api/registration.md).
 2. FE viết template tương ứng trong templates/registration/.
"""

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render

from common.contract import Role, ServiceError
from common.permissions import role_required
from courses.models import CourseSection
from . import services


def _get_student(request):
    """Lấy hồ sơ Student của tài khoản đang đăng nhập."""
    try:
        return request.user.student
    except ObjectDoesNotExist:
        return None


def _get_semester_id(request):
    """Đọc semester_id từ query string."""
    value = request.GET.get("semester_id")

    if not value:
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _error_context(error):
    """Chuẩn hóa thông tin lỗi để truyền vào template."""
    return {
        "error": error.message,
        "error_code": error.code,
        "error_details": error.details,
    }


@role_required(Role.STUDENT)
def open_sections_view(request, **kwargs):
    """Hiển thị danh sách lớp học phần có thể đăng ký."""
    student = _get_student(request)

    if student is None:
        return render(
            request,
            "registration/open_sections.html",
            {"error": "Không tìm thấy hồ sơ sinh viên."},
            status=404,
        )

    semester_id = _get_semester_id(request)
    keyword = request.GET.get("q", "").strip()

    if semester_id is None:
        return render(
            request,
            "registration/open_sections.html",
            {"error": "Vui lòng chọn học kỳ."},
            status=400,
        )

    try:
        result = services.list_open_sections(
            student,
            semester_id,
            keyword,
            request.GET.get("page", 1),
        )

        return render(
            request,
            "registration/open_sections.html",
            {
                "result": result,
                "sections": result.items,
                "page": result,
                "semester_id": semester_id,
                "q": keyword,
            },
        )

    except ServiceError as error:
        return render(
            request,
            "registration/open_sections.html",
            _error_context(error),
            status=400,
        )


@role_required(Role.STUDENT)
def register_confirm_view(request, section_id, **kwargs):
    """Kiểm tra điều kiện và hiển thị trang xác nhận đăng ký."""
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    student = _get_student(request)

    if student is None:
        return render(
            request,
            "registration/confirm.html",
            {"error": "Không tìm thấy hồ sơ sinh viên."},
            status=404,
        )

    section = get_object_or_404(
        CourseSection.objects.select_related(
            "course",
            "semester",
            "teacher__user",
        ).prefetch_related("schedules"),
        pk=section_id,
    )

    try:
        services.validate_registration(student, section)

        return render(
            request,
            "registration/confirm.html",
            {
                "section": section,
                "can_register": True,
            },
        )

    except ServiceError as error:
        return render(
            request,
            "registration/confirm.html",
            {
                "section": section,
                "can_register": False,
                **_error_context(error),
            },
            status=400,
        )


@role_required(Role.STUDENT)
def register_view(request, section_id, **kwargs):
    """Nhận POST và thực hiện đăng ký học phần."""
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    student = _get_student(request)

    if student is None:
        messages.error(request, "Không tìm thấy hồ sơ sinh viên.")
        return redirect("registration:open_sections_view")

    try:
        services.register_section(student, section_id)
        messages.success(request, "Đăng ký học phần thành công.")

    except ServiceError as error:
        messages.error(request, error.message)

    return redirect("registration:registered_sections_view")


@role_required(Role.STUDENT)
def registered_sections_view(request, **kwargs):
    """Hiển thị danh sách học phần sinh viên đã đăng ký."""
    student = _get_student(request)

    if student is None:
        return render(
            request,
            "registration/registered.html",
            {"error": "Không tìm thấy hồ sơ sinh viên."},
            status=404,
        )

    semester_id = _get_semester_id(request)

    try:
        sections = services.list_registered_sections(
            student,
            semester_id,
        )

        return render(
            request,
            "registration/registered.html",
            {
                "sections": sections,
                "semester_id": semester_id,
            },
        )

    except ServiceError as error:
        return render(
            request,
            "registration/registered.html",
            _error_context(error),
            status=400,
        )


@role_required(Role.STUDENT)
def cancel_view(request, section_id, **kwargs):
    """Nhận POST và thực hiện hủy đăng ký học phần."""
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    student = _get_student(request)

    if student is None:
        messages.error(request, "Không tìm thấy hồ sơ sinh viên.")
        return redirect("registration:registered_sections_view")

    try:
        services.cancel_registration(student, section_id)
        messages.success(request, "Đã hủy đăng ký học phần.")

    except ServiceError as error:
        messages.error(request, error.message)

    return redirect("registration:registered_sections_view")

