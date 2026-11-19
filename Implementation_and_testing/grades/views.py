"""
grades/views.py  (Backend: Duy   Frontend: Đạt (Teacher) + Thành (Admin) + Huy (Student))

View khung: chưa cài thì hiện trang "[CHƯA CÀI ĐẶT] tên_view". Khi làm:
 1. BE gọi hàm trong services.py, bắt ServiceError, truyền dữ liệu vào template (context theo docs/api/grades.md).
 2. FE viết template tương ứng trong templates/grades/.
"""

import json

from django.contrib import messages
from django.http import HttpResponseNotAllowed
from django.shortcuts import redirect, render

from common.contract import Role, ServiceError
from common.permissions import role_required
from . import services
from django.core.exceptions import ObjectDoesNotExist

def _get_student(request):
    """Lấy hồ sơ Student của tài khoản hiện tại."""
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
    """Chuẩn hóa lỗi service để truyền vào template."""
    return {
        "error": error.message,
        "error_code": error.code,
        "error_details": error.details,
    }


def _parse_grade_entries(request):
    """
    Đọc dữ liệu điểm từ trường JSON 'entries'.

    Ví dụ dữ liệu gửi lên:
    [
        {
            "enrollment_id": 1,
            "attendance": 8,
            "midterm": 7,
            "final": 9
        }
    ]
    """
    raw_entries = request.POST.get("entries", "")

    if not raw_entries:
        raise ValueError("Không tìm thấy dữ liệu điểm.")

    entries = json.loads(raw_entries)

    if not isinstance(entries, list):
        raise ValueError("Dữ liệu điểm phải là một danh sách.")

    return entries


@role_required(Role.STUDENT)
def student_results_view(request, **kwargs):
    """Sinh viên xem kết quả học tập."""
    student = _get_student(request)

    if student is None:
        return render(
            request,
            "grades/student_results.html",
            {"error": "Không tìm thấy hồ sơ sinh viên."},
            status=404,
        )

    semester_id = _get_semester_id(request)

    try:
        result = services.get_student_results(
            student,
            semester_id,
        )

        return render(
            request,
            "grades/student_results.html",
            {
                "result": result,
                "rows": result["rows"],
                "gpa": result["gpa"],
                "academic_status": result["academic_status"],
                "has_unlocked": result["has_unlocked"],
                "semester_id": semester_id,
            },
        )

    except ServiceError as error:
        return render(
            request,
            "grades/student_results.html",
            _error_context(error),
            status=400,
        )


@role_required(Role.TEACHER)
def gradebook_view(request, section_id, **kwargs):
    """Giảng viên xem bảng điểm của lớp mình phụ trách."""
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])

    try:
        result = services.get_gradebook(
            request.user,
            section_id,
        )

        return render(
            request,
            "grades/gradebook.html",
            {
                "gradebook": result["gradebook"],
                "section": result["section"],
                "is_locked": result["is_locked"],
                "weights": result["weights"],
                "rows": result["rows"],
            },
        )

    except ServiceError as error:
        status_code = (
            403
            if error.code == "PERMISSION_DENIED"
            else 404
            if error.code == "NOT_FOUND"
            else 400
        )

        return render(
            request,
            "grades/gradebook.html",
            _error_context(error),
            status=status_code,
        )


@role_required(Role.TEACHER)
def gradebook_save_view(request, section_id, **kwargs):
    """Giảng viên lưu hoặc chỉnh sửa điểm."""
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    try:
        entries = _parse_grade_entries(request)

        services.save_grades(
            request.user,
            section_id,
            entries,
        )

        messages.success(request, "Lưu điểm thành công.")

    except json.JSONDecodeError:
        messages.error(
            request,
            "Dữ liệu điểm gửi lên không đúng định dạng JSON.",
        )

    except ValueError as error:
        messages.error(request, str(error))

    except ServiceError as error:
        messages.error(request, error.message)

    return redirect(
        "grades:gradebook_view",
        section_id=section_id,
    )


@role_required(Role.TEACHER)
def gradebook_lock_view(request, section_id, **kwargs):
    """Giảng viên khóa bảng điểm."""
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    try:
        services.lock_gradebook(
            request.user,
            section_id,
        )

        messages.success(request, "Đã khóa bảng điểm thành công.")

    except ServiceError as error:
        messages.error(request, error.message)

    return redirect(
        "grades:gradebook_view",
        section_id=section_id,
    )


@role_required(Role.ADMINISTRATOR)
def locked_gradebooks_view(request, **kwargs):
    """Admin xem danh sách gradebook đã khóa."""
    try:
        result = services.list_locked_gradebooks(
            request.user,
            request.GET.get("page", 1),
        )

        history = services.get_unlock_history(
            request.user,
        )

        return render(
            request,
            "grades/locked_list.html",
            {
                "result": result,
                "gradebooks": result.items,
                "page": result,
                "unlock_history": history,
            },
        )

    except ServiceError as error:
        return render(
            request,
            "grades/locked_list.html",
            _error_context(error),
            status=403 if error.code == "PERMISSION_DENIED" else 400,
        )


@role_required(Role.ADMINISTRATOR)
def gradebook_unlock_view(request, section_id, **kwargs):
    """Admin mở khóa bảng điểm và nhập lý do."""
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    reason = request.POST.get("reason", "").strip()

    try:
        services.unlock_gradebook(
            request.user,
            section_id,
            reason,
        )

        messages.success(request, "Đã mở khóa bảng điểm.")

    except ServiceError as error:
        messages.error(request, error.message)

    return redirect("grades:locked_gradebooks_view")

