"""Unit test cho accounts/services.py. Cần database (MySQL trong Docker) vì dùng ORM thật."""
from datetime import date

import pytest
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory

from accounts import services
from accounts.models import PasswordReset, Teacher, User
from common.contract import MAX_FAILED_LOGINS, ErrorCode, Gender, ResetStatus, Role, ServiceError

PASSWORD = "Pass1234"


@pytest.fixture(autouse=True)
def fast_password_hasher(settings):
    """Băm nhanh trong test cho đỡ chậm (production vẫn dùng PBKDF2)."""
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


def make_user(username, role=Role.STUDENT, email=None, **extra):
    user = User(username=username, role=role, full_name=f"User {username}",
                email=email or f"{username.lower()}@example.com", **extra)
    user.set_password(PASSWORD)
    user.save()
    return user


def make_teacher(code="GV001", **extra):
    user = make_user(code, Role.TEACHER, **extra)
    Teacher.objects.create(user=user, teacher_code=code, department="IT")
    return user


def make_admin(code="AD001"):
    return make_user(code, Role.ADMINISTRATOR)


def make_student(code="123456", **extra):
    from students.models import Student
    user = make_user(code, Role.STUDENT, **extra)
    Student.objects.create(user=user, student_code=code, date_of_birth=date(2005, 3, 9),
                           gender=Gender.FEMALE, academic_cohort="2024", major="CS", student_class="C1")
    return user


def make_request():
    request = RequestFactory().post("/accounts/login/")
    SessionMiddleware(lambda r: None).process_request(request)
    request.session.save()
    return request


def error_of(func, *args, **kwargs):
    with pytest.raises(ServiceError) as info:
        func(*args, **kwargs)
    return info.value


def fields_of(error):
    return {d["field"] for d in error.details}


# ============================================================== UC 1: đăng nhập
def test_student_logs_in_with_student_code(db):
    user = make_user("123456")
    request = make_request()
    assert services.authenticate_user(request, "123456", PASSWORD) == user
    assert request.session["_auth_user_id"] == str(user.pk)


def test_teacher_logs_in_with_code_or_email(db):
    teacher = make_teacher("GV001", email="Thay.A@example.com")
    assert services.authenticate_user(None, "gv001", PASSWORD) == teacher          # không phân biệt hoa thường
    assert services.authenticate_user(None, "thay.a@example.com", PASSWORD) == teacher


def test_student_cannot_log_in_with_email(db):
    make_user("123456", email="sv@example.com")
    assert error_of(services.authenticate_user, None, "sv@example.com", PASSWORD).code == ErrorCode.BAD_CREDENTIALS


def test_wrong_password_and_unknown_id_give_same_error(db):
    make_user("123456")
    wrong = error_of(services.authenticate_user, None, "123456", "bad")
    unknown = error_of(services.authenticate_user, None, "999999", PASSWORD)
    assert wrong.code == unknown.code == ErrorCode.BAD_CREDENTIALS
    assert wrong.message == unknown.message


def test_missing_fields(db):
    error = error_of(services.authenticate_user, None, "", "")
    assert error.code == ErrorCode.MISSING_FIELDS
    assert fields_of(error) == {"identifier", "password"}


def test_failed_logins_are_counted_and_reset_on_success(db):
    user = make_user("123456")
    error_of(services.authenticate_user, None, "123456", "bad")
    user.refresh_from_db()
    assert user.failed_login_count == 1
    services.authenticate_user(None, "123456", PASSWORD)
    user.refresh_from_db()
    assert user.failed_login_count == 0


def test_account_locks_after_max_failed_logins(db):
    user = make_user("123456")
    for _ in range(MAX_FAILED_LOGINS - 1):
        assert error_of(services.authenticate_user, None, "123456", "bad").code == ErrorCode.BAD_CREDENTIALS
    assert error_of(services.authenticate_user, None, "123456", "bad").code == ErrorCode.ACCOUNT_LOCKED
    user.refresh_from_db()
    assert user.is_locked
    assert error_of(services.authenticate_user, None, "123456", PASSWORD).code == ErrorCode.ACCOUNT_LOCKED


def test_locked_account_with_wrong_password_does_not_reveal_lock_or_count(db):
    user = make_user("123456", is_locked=True)
    assert error_of(services.authenticate_user, None, "123456", "bad").code == ErrorCode.BAD_CREDENTIALS
    user.refresh_from_db()
    assert user.failed_login_count == 0


# ============================================================== UC 3: quên mật khẩu
def test_request_password_reset_creates_pending_request(db):
    user = make_user("123456")
    services.request_password_reset("123456")
    reset = PasswordReset.objects.get(user=user)
    assert reset.status == ResetStatus.PENDING and reset.token and reset.expires_at > reset.created_at


def test_request_password_reset_by_email_and_supersedes_old_request(db):
    user = make_teacher("GV001", email="t@example.com")
    services.request_password_reset("t@example.com")
    services.request_password_reset("GV001")
    statuses = sorted(PasswordReset.objects.filter(user=user).values_list("status", flat=True))
    assert statuses == [ResetStatus.EXPIRED, ResetStatus.PENDING]


def test_request_password_reset_unknown_creates_nothing(db):
    assert error_of(services.request_password_reset, "nobody").code == ErrorCode.NOT_FOUND
    assert PasswordReset.objects.count() == 0


def test_request_password_reset_locked_account(db):
    make_user("123456", is_locked=True)
    assert error_of(services.request_password_reset, "123456").code == ErrorCode.ACCOUNT_LOCKED


def test_admin_reset_password(db):
    admin, student = make_admin(), make_user("123456", failed_login_count=3)
    services.request_password_reset("123456")
    new_password = services.admin_reset_password(admin, student.pk)
    assert len(new_password) >= 12 and new_password != PASSWORD
    student.refresh_from_db()
    assert student.password != new_password and student.check_password(new_password)   # lưu dạng băm
    assert student.failed_login_count == 0
    assert PasswordReset.objects.get(user=student).status == ResetStatus.COMPLETED


def test_admin_reset_password_permissions_and_not_found(db):
    student = make_user("123456")
    assert error_of(services.admin_reset_password, student, student.pk).code == ErrorCode.PERMISSION_DENIED
    assert error_of(services.admin_reset_password, make_admin(), 99999).code == ErrorCode.NOT_FOUND


# ============================================================== UC 4: hồ sơ
def test_student_profile(db):
    profile = services.get_profile(make_student("123456"))
    assert profile["student_code"] == "123456"
    assert profile["date_of_birth"] == date(2005, 3, 9)
    assert profile["gender"] == Gender.FEMALE and profile["gender_display"]


def test_teacher_profile(db):
    profile = services.get_profile(make_teacher("GV001"))
    assert profile["teacher_code"] == "GV001" and profile["department"] == "IT"


def test_admin_has_no_profile_and_student_without_record(db):
    assert error_of(services.get_profile, make_admin()).code == ErrorCode.PERMISSION_DENIED
    assert error_of(services.get_profile, make_user("123456")).code == ErrorCode.NOT_FOUND


# ============================================================== UC 5: cập nhật liên hệ
def test_student_updates_contact(db):
    user = make_student("123456")
    services.update_contact(user, " New@Example.com ", "090 123-4567", "  1 Le Loi  ")
    user.refresh_from_db()
    assert (user.email, user.phone_number, user.address) == ("New@Example.com", "0901234567", "1 Le Loi")


def test_student_address_none_keeps_old_address(db):
    user = make_student("123456", address="Old")
    services.update_contact(user, "a@example.com", "0901234567")
    user.refresh_from_db()
    assert user.address == "Old"


def test_teacher_updates_phone_and_email_but_not_address(db):
    teacher = make_teacher("GV001")
    services.update_contact(teacher, "gv@example.com", "+84901234567")
    teacher.refresh_from_db()
    assert teacher.phone_number == "+84901234567"
    error = error_of(services.update_contact, teacher, "gv@example.com", "0901234567", "somewhere")
    assert error.code == ErrorCode.PERMISSION_DENIED


def test_update_contact_validation_and_nothing_changes_on_error(db):
    user = make_student("123456", phone_number="0900000000")
    error = error_of(services.update_contact, user, "not-an-email", "12", "x")
    assert error.code == ErrorCode.VALIDATION and fields_of(error) == {"email", "phone_number"}
    user.refresh_from_db()
    assert user.phone_number == "0900000000" and user.email == "123456@example.com"


def test_update_contact_missing_fields(db):
    error = error_of(services.update_contact, make_student("123456"), "", "", "")
    assert error.code == ErrorCode.MISSING_FIELDS and fields_of(error) == {"email", "phone_number", "address"}


def test_update_contact_duplicate_email(db):
    make_user("111111", email="taken@example.com")
    other = make_student("123456")
    error = error_of(services.update_contact, other, "TAKEN@example.com", "0901234567", "x")
    assert error.code == ErrorCode.DUPLICATE
    services.update_contact(other, other.email, "0901234567", "x")        # giữ email của chính mình thì được


def test_admin_cannot_update_contact(db):
    assert error_of(services.update_contact, make_admin(), "a@example.com", "0901234567").code == ErrorCode.PERMISSION_DENIED


# ============================================================== UC 19: tạo tài khoản
def test_create_student_teacher_admin_accounts(db):
    admin = make_admin("AD001")
    student, pw = services.create_account(admin, "  Nguyen   Van A ", "a@example.com", Role.STUDENT, "123456")
    assert student.full_name == "Nguyen Van A" and student.check_password(pw) and student.password != pw
    teacher, _ = services.create_account(admin, "Tran B", "b@example.com", Role.TEACHER, "gv002")
    assert teacher.username == "GV002" and Teacher.objects.get(user=teacher).teacher_code == "GV002"
    other_admin, _ = services.create_account(admin, "Le C", "c@example.com", Role.ADMINISTRATOR, "AD002")
    assert other_admin.role == Role.ADMINISTRATOR


def test_create_account_missing_invalid_and_duplicate(db):
    admin = make_admin("AD001")
    assert error_of(services.create_account, admin, "", "", "", "").code == ErrorCode.MISSING_FIELDS
    bad_code = error_of(services.create_account, admin, "A", "a@example.com", Role.STUDENT, "SV1")
    assert bad_code.code == ErrorCode.VALIDATION and fields_of(bad_code) == {"username"}
    assert error_of(services.create_account, admin, "A", "a@example.com", "BOSS", "123456").code == ErrorCode.VALIDATION
    make_user("123456", email="taken@example.com")
    dup = error_of(services.create_account, admin, "A", "TAKEN@example.com", Role.STUDENT, "123456")
    assert dup.code == ErrorCode.DUPLICATE and fields_of(dup) == {"username", "email"}


def test_create_account_requires_admin_and_creates_nothing_on_error(db):
    student = make_user("123456")
    assert error_of(services.create_account, student, "A", "a@example.com", Role.STUDENT, "654321").code == ErrorCode.PERMISSION_DENIED
    assert not User.objects.filter(username="654321").exists()


# ============================================================== UC 20: sửa tài khoản
def test_edit_account(db):
    admin, target = make_admin(), make_user("123456")
    services.edit_account(admin, target.pk, " New  Name ", "new@example.com", Role.STUDENT)
    target.refresh_from_db()
    assert (target.full_name, target.email) == ("New Name", "new@example.com")


def test_edit_account_errors(db):
    admin, target = make_admin(), make_user("123456")
    make_user("111111", email="taken@example.com")
    assert error_of(services.edit_account, admin, 99999, "N", "n@example.com", Role.STUDENT).code == ErrorCode.NOT_FOUND
    assert error_of(services.edit_account, admin, target.pk, "N", "taken@example.com", Role.STUDENT).code == ErrorCode.DUPLICATE
    assert error_of(services.edit_account, admin, target.pk, "", "n@example.com", Role.STUDENT).code == ErrorCode.MISSING_FIELDS
    assert error_of(services.edit_account, admin, target.pk, "N", "bad", Role.STUDENT).code == ErrorCode.VALIDATION
    target.refresh_from_db()
    assert target.full_name == "User 123456"          # lỗi thì không đổi


def test_edit_account_role_rules(db):
    admin = make_admin()
    assert error_of(services.edit_account, admin, admin.pk, "A", "a@example.com", Role.TEACHER).code == ErrorCode.VALIDATION
    student = make_student("123456")
    assert error_of(services.edit_account, admin, student.pk, "S", "s@example.com", Role.TEACHER).code == ErrorCode.VALIDATION
    plain = make_user("222222")
    services.edit_account(admin, plain.pk, "P", "p@example.com", Role.TEACHER)
    plain.refresh_from_db()
    assert plain.role == Role.TEACHER and Teacher.objects.filter(user=plain).exists()


# ============================================================== UC 21: trạng thái tài khoản
def test_lock_and_unlock_account(db):
    admin, target = make_admin(), make_user("123456", failed_login_count=4)
    services.set_account_status(admin, target.pk, True)
    target.refresh_from_db()
    assert target.is_locked
    services.set_account_status(admin, target.pk, False)
    target.refresh_from_db()
    assert not target.is_locked and target.failed_login_count == 0


def test_admin_cannot_lock_self_and_not_found(db):
    admin = make_admin()
    assert error_of(services.set_account_status, admin, admin.pk, True).code == ErrorCode.CANNOT_LOCK_SELF
    admin.refresh_from_db()
    assert not admin.is_locked
    assert error_of(services.set_account_status, admin, 99999, True).code == ErrorCode.NOT_FOUND
    assert error_of(services.set_account_status, make_user("123456"), admin.pk, True).code == ErrorCode.PERMISSION_DENIED


def test_list_accounts_search_filter_and_pagination(db):
    make_admin("AD001")
    make_teacher("GV001", email="thay@example.com")
    for i in range(12):
        make_user(f"1000{i:02d}", is_locked=(i == 0))
    everything = services.list_accounts()
    assert everything.total == 14 and everything.num_pages == 2 and len(everything.items) == 10
    assert services.list_accounts(page=2).items and services.list_accounts(page="abc").page == 1
    assert services.list_accounts(q="thay").total == 1
    assert services.list_accounts(q="100003").total == 1
    assert services.list_accounts(role=Role.STUDENT).total == 12
    assert services.list_accounts(locked=True).total == 1
    assert services.list_accounts(locked="active").total == 13
    assert services.list_accounts(q="zzz").total == 0
    assert error_of(services.list_accounts, role="BOSS").code == ErrorCode.VALIDATION
    assert error_of(services.list_accounts, locked="maybe").code == ErrorCode.VALIDATION


def test_get_account(db):
    admin, target = make_admin(), make_user("123456")
    assert services.get_account(admin, target.pk) == target
    assert error_of(services.get_account, admin, 99999).code == ErrorCode.NOT_FOUND
    assert error_of(services.get_account, target, target.pk).code == ErrorCode.PERMISSION_DENIED