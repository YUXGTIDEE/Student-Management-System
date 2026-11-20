"""
search/views.py  (Backend: Bình   Frontend: Đạt)

 1. BE gọi hàm trong services.py, bắt ServiceError, truyền dữ liệu vào template (context theo docs/api/search.md).
 2. FE viết template tương ứng trong templates/search/.
"""
from django.shortcuts import render
from django.utils.http import urlencode
from django.views.decorators.http import require_GET

from common.contract import AcademicStatus, ErrorCode, Page, Role, ServiceError
from common.permissions import role_required

from . import services

_HTTP_STATUS = {ErrorCode.PERMISSION_DENIED: 403, ErrorCode.NOT_FOUND: 404}


def _error_context(error):
    """ServiceError -> các biến chung cho template."""
    return {
        "error": error.message,
        "error_code": error.code,
        "field_errors": {d["field"]: d["message"] for d in error.details},
    }


def _empty_page():
    return Page(items=[], page=1, num_pages=1, total=0)


@role_required(Role.ADMINISTRATOR, Role.TEACHER)
@require_GET
def student_search_view(request, **kwargs):
    """GV 4.1 / Admin tìm kiếm + lọc (UC 12, 22)
    Template: search/student_search.html
    Tham số URL: q, student_class, major, cohort, status, page.
    Context: students, page (items/page/num_pages/total), page_numbers, filters, query_string (nối vào liên kết
    phân trang: ?{{ query_string }}&page=N), statuses (danh sách (giá trị, nhãn) cho ô chọn trạng thái),
    error/error_code/field_errors khi bộ lọc sai."""
    keys = ("q", "student_class", "major", "cohort", "status")
    filters = {key: request.GET.get(key, "").strip() for key in keys}
    context = {"filters": filters, "statuses": AcademicStatus.CHOICES}
    try:
        page = services.search_students(
            request.user, keyword=filters["q"], student_class=filters["student_class"],
            major=filters["major"], cohort=filters["cohort"], status=filters["status"],
            page=request.GET.get("page", 1))
    except ServiceError as error:
        context.update(_error_context(error))
        page = _empty_page()
    context.update(
        students=page.items,
        page=page,
        page_numbers=range(1, page.num_pages + 1),
        query_string=urlencode({key: value for key, value in filters.items() if value}),
    )
    return render(request, "search/student_search.html", context,
                  status=_HTTP_STATUS.get(context.get("error_code"), 200))


@role_required(Role.ADMINISTRATOR, Role.TEACHER)
@require_GET
def student_detail_view(request, student_id, **kwargs):
    """GV 4.2 hồ sơ chi tiết chỉ đọc (UC 13)
    Template: search/student_detail.html
    Context: student (dict – xem services.get_student_detail; None khi lỗi), error, error_code.
    Lỗi: PERMISSION_DENIED -> HTTP 403, NOT_FOUND -> HTTP 404 (vẫn hiển thị template kèm thông báo)."""
    try:
        student = services.get_student_detail(request.user, student_id)
    except ServiceError as error:
        context = {"student": None, **_error_context(error)}
        return render(request, "search/student_detail.html", context, status=_HTTP_STATUS.get(error.code, 400))
    return render(request, "search/student_detail.html", {"student": student})


@role_required(Role.TEACHER)
@require_GET
def assigned_sections_view(request, **kwargs):
    """GV 4.3 danh sách được phân công (UC 11)
    Template: search/assigned.html
    Tham số URL: semester (id học kỳ, tùy chọn), section (id section để xem danh sách sinh viên), page.
    Context: sections (danh sách section – xem services.list_assigned_sections), semesters (list {id, name}
    để dựng ô chọn học kỳ), selected_semester (id hoặc ""), selected_section (dict của section đang xem hoặc None),
    students (sinh viên của section đang xem; [] nếu chưa chọn), page, page_numbers, query_string (nối vào liên
    kết phân trang: ?{{ query_string }}&page=N), error/error_code."""
    semester = request.GET.get("semester", "").strip()
    section_param = request.GET.get("section", "").strip()
    context = {"selected_semester": semester, "selected_section": None, "students": [],
               "sections": [], "semesters": [], "page": _empty_page()}
    status = 200

    try:
        all_sections = services.list_assigned_sections(request.user)
        seen = {}
        for row in all_sections:
            seen.setdefault(row["semester_id"], row["semester_name"])
        context["semesters"] = [{"id": key, "name": name} for key, name in seen.items()]
        context["sections"] = (services.list_assigned_sections(request.user, semester)
                               if semester else all_sections)

        if section_param:
            if not section_param.isdigit():
                raise ServiceError(ErrorCode.VALIDATION, "Invalid section.",
                                   [{"field": "section", "message": "Choose a valid section."}])
            section_id = int(section_param)
            context["selected_section"] = next((r for r in all_sections if r["section_id"] == section_id), None)
            page = services.list_section_students_for_teacher(request.user, section_id,
                                                              request.GET.get("page", 1))
            context.update(students=page.items, page=page)
    except ServiceError as error:
        context.update(_error_context(error))
        status = _HTTP_STATUS.get(error.code, 200)

    context["page_numbers"] = range(1, context["page"].num_pages + 1)
    context["query_string"] = urlencode({k: v for k, v in
                                         (("semester", semester), ("section", section_param)) if v})
    return render(request, "search/assigned.html", context, status=status)