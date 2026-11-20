"""Test cho search/services.py. Cần database (MySQL trong Docker)."""
from datetime import date, time

import pytest

from accounts.models import Teacher
from accounts.tests.test_services import error_of, make_admin, make_student, make_teacher, make_user
from common.contract import EnrollmentStatus
from courses.models import Course, CourseSection, Semester, SectionSchedule
from grades.models import Gradebook, Grade
from registration.models import Enrollment
from search import services
from students.models import Student


@pytest.fixture(autouse=True)
def fast_password_hasher(settings):
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


def student_of(code):
    return Student.objects.get(student_code=code)


def make_semester(name="2026-2027 / S1", start=date(2026, 9, 1)):
    return Semester.objects.create(semester_name=name, start_date=start, end_date=date(2027, 1, 15),
                                   registration_start=date(2026, 8, 1), registration_end=date(2026, 8, 20),
                                   cancellation_deadline=date(2026, 9, 15))


def make_section(teacher_user, code="SEC1", course_code="CS101", semester=None):
    course, _ = Course.objects.get_or_create(course_code=course_code,
                                             defaults=dict(course_name="Intro", credit_hours=3, class_periods=45))
    return CourseSection.objects.create(section_code=code, course=course, semester=semester or make_semester(),
                                        teacher=Teacher.objects.get(user=teacher_user),
                                        classroom="A101", max_capacity=40)


def enroll(student_user, section, status=EnrollmentStatus.REGISTERED):
    return Enrollment.objects.create(student=student_of(student_user.username), section=section, status=status)


# ------------------------------------------------------------ search_students
def test_admin_sees_everyone_sorted_by_code(db):
    admin = make_admin()
    make_student("200000", full_name="B")
    make_student("100000", full_name="A")
    page = services.search_students(admin)
    assert [r["student_code"] for r in page.items] == ["100000", "200000"]
    assert set(page.items[0]) == {"student_id", "student_code", "full_name", "student_class",
                                  "major", "academic_status"}


def test_teacher_sees_only_own_registered_students(db):
    t1, t2 = make_teacher("GV001"), make_teacher("GV002")
    mine, other, cancelled, nobody = (make_student(c) for c in ("111111", "222222", "333333", "444444"))
    sem = make_semester()
    enroll(mine, make_section(t1, "S1", semester=sem))
    enroll(other, make_section(t2, "S2", semester=sem))
    enroll(cancelled, CourseSection.objects.get(section_code="S1"), EnrollmentStatus.CANCELLED)
    page = services.search_students(t1)
    assert [r["student_code"] for r in page.items] == ["111111"]


def test_teacher_student_in_two_sections_listed_once(db):
    t1 = make_teacher("GV001")
    s = make_student("111111")
    sem = make_semester()
    enroll(s, make_section(t1, "S1", semester=sem))
    enroll(s, make_section(t1, "S2", "CS102", semester=sem))
    page = services.search_students(t1)
    assert page.total == 1


def test_search_filters(db):
    admin = make_admin()
    make_student("111111", full_name="Nguyen Van An")
    make_student("222222", full_name="Tran Thi Binh")
    Student.objects.filter(student_code="222222").update(student_class="C2", major="Math",
                                                         academic_cohort="2023", academic_status="GRADUATED")
    codes = lambda **kw: [r["student_code"] for r in services.search_students(admin, **kw).items]
    assert codes(keyword="nguyen") == ["111111"]
    assert codes(keyword="2222") == ["222222"]
    assert codes(student_class="c2") == ["222222"]
    assert codes(major="math") == ["222222"]
    assert codes(cohort="2024") == ["111111"]
    assert codes(status="GRADUATED") == ["222222"]
    assert codes(keyword="  nguyen  ", major="CS") == ["111111"]
    assert codes(keyword="zzz") == []


def test_search_invalid_status_is_validation_error(db):
    err = error_of(services.search_students, make_admin(), status="BOSS")
    assert err.code == "VALIDATION" and err.details[0]["field"] == "status"


def test_search_pagination(db):
    admin = make_admin()
    for i in range(12):
        make_student(f"1000{i:02d}")
    page = services.search_students(admin, page=2)
    assert (page.total, page.num_pages, len(page.items)) == (12, 2, 2)


def test_search_denied_for_student_locked_and_teacher_without_profile(db):
    assert error_of(services.search_students, make_student("123456")).code == "PERMISSION_DENIED"
    assert error_of(services.search_students, make_teacher("GV001", is_locked=True)).code == "PERMISSION_DENIED"
    assert error_of(services.search_students, make_user("GV009", "TEACHER")).code == "PERMISSION_DENIED"


# ------------------------------------------------------------ get_student_detail
def test_admin_detail_shows_all_registered_sections_with_grades(db):
    admin, t1, t2 = make_admin(), make_teacher("GV001"), make_teacher("GV002")
    s = make_student("123456", full_name="An", email="an@example.com", phone_number="0900000000", address="Hue")
    sem = make_semester()
    e1 = enroll(s, make_section(t1, "S1", semester=sem))
    enroll(s, make_section(t2, "S2", "CS102", semester=sem))
    gb = Gradebook.objects.create(section=e1.section)
    Grade.objects.create(gradebook=gb, enrollment=e1, attendance_score=9, midterm_score=8, final_exam_score=7,
                         final_score=7.5, letter_grade="B")
    detail = services.get_student_detail(admin, student_of("123456").pk)
    assert detail["full_name"] == "An" and detail["email"] == "an@example.com"
    assert detail["address"] == "Hue" and detail["gender_display"] == "Female"
    assert detail["academic_status_display"] == "Enrolled"
    by_code = {r["section_code"]: r for r in detail["sections"]}
    assert set(by_code) == {"S1", "S2"}
    assert by_code["S1"]["final_score"] == 7.5 and by_code["S1"]["letter_grade"] == "B"
    assert by_code["S2"]["final_score"] is None and by_code["S2"]["letter_grade"] == ""


def test_teacher_detail_only_own_sections(db):
    t1, t2 = make_teacher("GV001"), make_teacher("GV002")
    s = make_student("123456")
    sem = make_semester()
    enroll(s, make_section(t1, "S1", semester=sem))
    enroll(s, make_section(t2, "S2", "CS102", semester=sem))
    detail = services.get_student_detail(t1, student_of("123456").pk)
    assert [r["section_code"] for r in detail["sections"]] == ["S1"]


def test_teacher_detail_denied_for_foreign_cancelled_and_missing_students(db):
    t1, t2 = make_teacher("GV001"), make_teacher("GV002")
    foreign, cancelled = make_student("111111"), make_student("222222")
    sem = make_semester()
    enroll(foreign, make_section(t2, "S2", semester=sem))
    enroll(cancelled, make_section(t1, "S1", "CS102", semester=sem), EnrollmentStatus.CANCELLED)
    for pk in (student_of("111111").pk, student_of("222222").pk, 99999):
        assert error_of(services.get_student_detail, t1, pk).code == "PERMISSION_DENIED"


def test_detail_not_found_for_admin_and_denied_for_student(db):
    assert error_of(services.get_student_detail, make_admin(), 99999).code == "NOT_FOUND"
    s = make_student("123456")
    assert error_of(services.get_student_detail, s, student_of("123456").pk).code == "PERMISSION_DENIED"


# ------------------------------------------------------------ UC 11
def test_list_assigned_sections(db):
    t1, t2 = make_teacher("GV001"), make_teacher("GV002")
    old, new = make_semester("Old", date(2025, 9, 1)), make_semester("New", date(2026, 9, 1))
    a = make_section(t1, "S1", "CS101", old)
    b = make_section(t1, "S2", "CS102", new)
    make_section(t2, "S3", "CS103", new)
    SectionSchedule.objects.create(section=b, day_of_week=3, start_time=time(9), end_time=time(11))
    SectionSchedule.objects.create(section=b, day_of_week=1, start_time=time(7), end_time=time(9))
    rows = services.list_assigned_sections(t1)
    assert [r["section_code"] for r in rows] == ["S2", "S1"]                 # học kỳ mới nhất trước
    assert [s["day_of_week"] for s in rows[0]["schedules"]] == [1, 3]
    assert rows[0]["max_capacity"] == 40 and rows[0]["semester_name"] == "New"
    assert [r["section_code"] for r in services.list_assigned_sections(t1, old.pk)] == ["S1"]
    assert [r["section_code"] for r in services.list_assigned_sections(t1, str(old.pk))] == ["S1"]
    assert services.list_assigned_sections(t1, "")[0]["section_code"] == "S2"
    assert error_of(services.list_assigned_sections, t1, "abc").code == "VALIDATION"


def test_list_assigned_sections_teachers_only(db):
    assert error_of(services.list_assigned_sections, make_admin()).code == "PERMISSION_DENIED"
    assert error_of(services.list_assigned_sections, make_student("123456")).code == "PERMISSION_DENIED"


def test_list_section_students(db):
    t1, t2 = make_teacher("GV001"), make_teacher("GV002")
    sem = make_semester()
    sec, foreign = make_section(t1, "S1", semester=sem), make_section(t2, "S2", "CS102", sem)
    for code, target, status in (("222222", sec, "REGISTERED"), ("111111", sec, "REGISTERED"),
                                 ("333333", sec, "CANCELLED"), ("444444", foreign, "REGISTERED")):
        enroll(make_student(code), target, status)
    page = services.list_section_students_for_teacher(t1, sec.pk)
    assert [r["student_code"] for r in page.items] == ["111111", "222222"]
    assert set(page.items[0]) == {"student_id", "student_code", "full_name", "student_class"}
    assert error_of(services.list_section_students_for_teacher, t1, foreign.pk).code == "PERMISSION_DENIED"
    assert error_of(services.list_section_students_for_teacher, t1, 99999).code == "PERMISSION_DENIED"
    assert error_of(services.list_section_students_for_teacher, make_admin("AD001"), sec.pk).code == "PERMISSION_DENIED"