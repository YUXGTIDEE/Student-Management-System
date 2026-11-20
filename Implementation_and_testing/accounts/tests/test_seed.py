"""Test lệnh seed: tạo đúng dữ liệu và chạy lại được."""
import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from accounts.models import User
from courses.models import CourseSection
from grades.models import Grade
from registration.models import Enrollment
from students.models import Student


@pytest.fixture(autouse=True)
def fast_password_hasher(settings):
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
    settings.DEBUG = True


def counts():
    return (User.objects.count(), Student.objects.count(), CourseSection.objects.count(),
            Enrollment.objects.count(), Grade.objects.count())


def test_seed_creates_expected_data(db):
    call_command("seed")
    assert User.objects.count() == 1 + 3 + 20 and Student.objects.count() == 20
    assert User.objects.get(username="100001").check_password("Pass1234")
    full = CourseSection.objects.get(section_code="CS101-02")
    assert full.current_enrollment == full.max_capacity == 2
    assert Grade.objects.filter(gradebook__is_locked=True).count() == Grade.objects.count() > 0
    assert all(s.current_enrollment == s.enrollments.count() for s in CourseSection.objects.all())


def test_seed_is_idempotent_and_keeps_changed_passwords(db):
    call_command("seed")
    first = counts()
    user = User.objects.get(username="100001")
    user.set_password("Changed123")
    user.save()
    call_command("seed")
    assert counts() == first
    assert User.objects.get(username="100001").check_password("Changed123")
    call_command("seed", "--reset-passwords")
    assert User.objects.get(username="100001").check_password("Pass1234")


def test_seed_refuses_when_debug_off(db, settings):
    settings.DEBUG = False
    with pytest.raises(CommandError):
        call_command("seed")
    call_command("seed", "--force")
    assert User.objects.filter(username="AD001").exists()