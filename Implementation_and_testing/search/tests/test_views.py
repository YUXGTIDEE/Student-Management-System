"""Test cho search/views.py bằng Django test client. Cần database."""
import pytest
from django.urls import reverse

from accounts.tests.test_services import make_admin, make_student, make_teacher
from search.tests.test_services import enroll, make_section, make_semester, student_of


@pytest.fixture(autouse=True)
def fast_password_hasher(settings):
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


SEARCH = "search:student_search_view"
DETAIL = "search:student_detail_view"
ASSIGNED = "search:assigned_sections_view"


# ------------------------------------------------------------ tìm kiếm
def test_search_access_control(client, db):
    assert client.get(reverse(SEARCH)).status_code == 302                    # chưa đăng nhập
    client.force_login(make_student("123456"))
    assert client.get(reverse(SEARCH)).status_code == 403


def test_admin_search_with_filters_and_pagination(client, db):
    for i in range(12):
        make_student(f"1000{i:02d}", full_name=f"Student {i}")
    client.force_login(make_admin())
    response = client.get(reverse(SEARCH))
    assert response.status_code == 200
    assert response.context["page"].total == 12 and list(response.context["page_numbers"]) == [1, 2]
    assert len(response.context["students"]) == 10
    response = client.get(reverse(SEARCH), {"q": "Student 3", "major": "CS", "page": "abc"})
    assert [s["student_code"] for s in response.context["students"]] == ["100003"]
    assert response.context["filters"]["q"] == "Student 3"
    assert response.context["query_string"] == "q=Student+3&major=CS"


def test_search_bad_status_shows_error_not_crash(client, db):
    client.force_login(make_admin())
    response = client.get(reverse(SEARCH), {"status": "BOSS"})
    assert response.status_code == 200 and response.context["error_code"] == "VALIDATION"
    assert response.context["field_errors"] == {"status": "Choose a valid academic status."}
    assert response.context["students"] == []


def test_teacher_search_limited_to_own_students(client, db):
    t1, t2 = make_teacher("GV001"), make_teacher("GV002")
    sem = make_semester()
    enroll(make_student("111111"), make_section(t1, "S1", semester=sem))
    enroll(make_student("222222"), make_section(t2, "S2", "CS102", sem))
    client.force_login(t1)
    response = client.get(reverse(SEARCH))
    assert [s["student_code"] for s in response.context["students"]] == ["111111"]


def test_search_is_get_only(client, db):
    client.force_login(make_admin())
    assert client.post(reverse(SEARCH)).status_code == 405


# ------------------------------------------------------------ hồ sơ chi tiết
def test_detail_for_admin_and_own_teacher(client, db):
    t1 = make_teacher("GV001")
    enroll(make_student("123456", full_name="An"), make_section(t1))
    pk = student_of("123456").pk
    client.force_login(make_admin())
    assert client.get(reverse(DETAIL, args=[pk])).context["student"]["full_name"] == "An"
    client.force_login(t1)
    response = client.get(reverse(DETAIL, args=[pk]))
    assert response.status_code == 200 and response.context["student"]["student_code"] == "123456"


def test_detail_errors_are_403_and_404(client, db):
    t1, t2 = make_teacher("GV001"), make_teacher("GV002")
    enroll(make_student("123456"), make_section(t2))
    pk = student_of("123456").pk
    client.force_login(t1)
    response = client.get(reverse(DETAIL, args=[pk]))
    assert response.status_code == 403 and response.context["student"] is None
    assert response.context["error_code"] == "PERMISSION_DENIED"
    client.force_login(make_admin())
    response = client.get(reverse(DETAIL, args=[99999]))
    assert response.status_code == 404 and response.context["error_code"] == "NOT_FOUND"


def test_detail_denied_for_student_role(client, db):
    student = make_student("123456")
    client.force_login(student)
    assert client.get(reverse(DETAIL, args=[student_of("123456").pk])).status_code == 403


# ------------------------------------------------------------ section được phân công
def test_assigned_only_for_teachers(client, db):
    client.force_login(make_admin())
    assert client.get(reverse(ASSIGNED)).status_code == 403


def test_assigned_lists_sections_and_semesters(client, db):
    t1 = make_teacher("GV001")
    sem1, sem2 = make_semester("Sem A"), make_semester("Sem B")
    make_section(t1, "S1", "CS101", sem1)
    make_section(t1, "S2", "CS102", sem2)
    client.force_login(t1)
    response = client.get(reverse(ASSIGNED))
    assert response.status_code == 200 and len(response.context["sections"]) == 2
    assert {s["name"] for s in response.context["semesters"]} == {"Sem A", "Sem B"}
    assert response.context["students"] == [] and response.context["selected_section"] is None
    filtered = client.get(reverse(ASSIGNED), {"semester": sem1.pk})
    assert [s["section_code"] for s in filtered.context["sections"]] == ["S1"]
    assert len(filtered.context["semesters"]) == 2                           # ô chọn học kỳ luôn đủ
    assert filtered.context["query_string"] == f"semester={sem1.pk}"


def test_assigned_shows_students_of_selected_section(client, db):
    t1 = make_teacher("GV001")
    sec = make_section(t1)
    for code in ("111111", "222222"):
        enroll(make_student(code), sec)
    client.force_login(t1)
    response = client.get(reverse(ASSIGNED), {"section": sec.pk})
    assert response.context["selected_section"]["section_code"] == "SEC1"
    assert [s["student_code"] for s in response.context["students"]] == ["111111", "222222"]
    assert response.context["page"].total == 2
    assert response.context["query_string"] == f"section={sec.pk}"


def test_assigned_foreign_or_invalid_section(client, db):
    t1, t2 = make_teacher("GV001"), make_teacher("GV002")
    foreign = make_section(t2, "S9", "CS109")
    make_section(t1, "S1")
    client.force_login(t1)
    response = client.get(reverse(ASSIGNED), {"section": foreign.pk})
    assert response.status_code == 403 and response.context["students"] == []
    assert len(response.context["sections"]) == 1                            # danh sách section vẫn hiện
    response = client.get(reverse(ASSIGNED), {"section": "abc"})
    assert response.status_code == 200 and response.context["error_code"] == "VALIDATION"