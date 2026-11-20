"""Unit test cho common/permissions.py.
Phần role_required không cần database; phần teacher_* cần database (đánh dấu django_db)."""
from datetime import date, time
from types import SimpleNamespace

import pytest
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.test import RequestFactory

from common.contract import EnrollmentStatus, Gender, Role
from common.permissions import role_required, teacher_can_see_student, teacher_teaches_section


def make_request(user):
    request = RequestFactory().get("/x/")
    request.user = user
    return request


def fake_user(role, locked=False):
    return SimpleNamespace(is_authenticated=True, role=role, is_locked=locked)


@role_required(Role.ADMINISTRATOR)
def admin_view(request):
    return HttpResponse("ok")


@role_required(Role.TEACHER, Role.ADMINISTRATOR)
def multi_view(request):
    return HttpResponse("ok")


def test_allowed_role_passes():
    assert admin_view(make_request(fake_user(Role.ADMINISTRATOR))).status_code == 200


@pytest.mark.parametrize("role", [Role.STUDENT, Role.TEACHER])
def test_wrong_role_gets_403(role):
    assert admin_view(make_request(fake_user(role))).status_code == 403


def test_anonymous_redirects_to_login():
    response = admin_view(make_request(AnonymousUser()))
    assert response.status_code == 302
    assert "/accounts/login/" in response["Location"]


def test_locked_account_gets_403():
    assert admin_view(make_request(fake_user(Role.ADMINISTRATOR, locked=True))).status_code == 403


def test_multiple_roles():
    assert multi_view(make_request(fake_user(Role.TEACHER))).status_code == 200
    assert multi_view(make_request(fake_user(Role.ADMINISTRATOR))).status_code == 200
    assert multi_view(make_request(fake_user(Role.STUDENT))).status_code == 403


def test_no_roles_is_a_programming_error():
    with pytest.raises(ValueError):
        role_required()


# ---------------------------------------------------------------- cần database
@pytest.fixture
def world(db):
    from accounts.models import Teacher, User
    from courses.models import Course, CourseSection, Semester
    from registration.models import Enrollment
    from students.models import Student

    def teacher(code):
        u = User.objects.create_user(code, password="x", role=Role.TEACHER, full_name=code,
                                     email=f"{code}@example.com")
        return u, Teacher.objects.create(user=u, teacher_code=code)

    u1, t1 = teacher("GV001")
    u2, t2 = teacher("GV002")
    sem = Semester.objects.create(semester_name="S", start_date=date(2026, 1, 1), end_date=date(2026, 6, 1),
                                  registration_start=date(2026, 1, 1), registration_end=date(2026, 1, 10),
                                  cancellation_deadline=date(2026, 1, 20))
    course = Course.objects.create(course_code="C1", course_name="C", credit_hours=3, class_periods=45)
    sec1 = CourseSection.objects.create(section_code="S1", course=course, semester=sem, teacher=t1,
                                        classroom="A1", max_capacity=10)
    sec2 = CourseSection.objects.create(section_code="S2", course=course, semester=sem, teacher=t2,
                                        classroom="A2", max_capacity=10)

    def student(code):
        u = User.objects.create_user(code, password="x", role=Role.STUDENT, full_name=code,
                                     email=f"{code}@example.com")
        return Student.objects.create(user=u, student_code=code, date_of_birth=date(2005, 1, 1),
                                      gender=Gender.MALE, academic_cohort="2024", major="CS",
                                      student_class="C1")

    s1, s2 = student("100001"), student("100002")
    Enrollment.objects.create(student=s1, section=sec1)                        # GV001 dạy s1
    Enrollment.objects.create(student=s2, section=sec2,
                              status=EnrollmentStatus.CANCELLED)               # s2 đã hủy
    student_user = s1.user
    return SimpleNamespace(u1=u1, u2=u2, sec1=sec1, sec2=sec2, s1=s1, s2=s2, student_user=student_user)


def test_teacher_teaches_section(world):
    assert teacher_teaches_section(world.u1, world.sec1) is True
    assert teacher_teaches_section(world.u1, world.sec1.pk) is True      # nhận cả id
    assert teacher_teaches_section(world.u1, world.sec2) is False        # section của GV khác
    assert teacher_teaches_section(world.student_user, world.sec1) is False   # không phải giáo viên


def test_teacher_can_see_student(world):
    assert teacher_can_see_student(world.u1, world.s1) is True
    assert teacher_can_see_student(world.u1, world.s1.pk) is True
    assert teacher_can_see_student(world.u2, world.s1) is False          # s1 không học GV002
    assert teacher_can_see_student(world.u2, world.s2) is False          # s2 đã CANCELLED
    assert teacher_can_see_student(world.student_user, world.s1) is False