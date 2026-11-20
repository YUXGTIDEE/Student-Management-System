"""Test cho accounts/views.py bằng Django test client. Cần database (MySQL trong Docker)."""
import pytest
from django.contrib.messages import get_messages
from django.urls import reverse

from accounts.models import PasswordReset, User
from accounts.tests.test_services import PASSWORD, make_admin, make_student, make_teacher, make_user
from common.contract import Role

LOGIN = "accounts:login_view"


@pytest.fixture(autouse=True)
def fast_password_hasher(settings):
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


def url(name, *args):
    return reverse(name, args=args)


def flash(response):
    return [str(m) for m in get_messages(response.wsgi_request)]


# ============================================================== trang chủ
def test_home_redirects_by_role(client, db):
    expected = {
        Role.STUDENT: url("accounts:profile_view"),
        Role.TEACHER: url("search:assigned_sections_view"),
        Role.ADMINISTRATOR: url("accounts:account_list_view"),
    }
    for user in (make_student("123456"), make_teacher("GV001"), make_admin("AD001")):
        client.force_login(user)
        assert client.get(url("home")).url == expected[user.role]


def test_home_requires_login(client, db):
    response = client.get(url("home"))
    assert response.status_code == 302 and "/accounts/login/" in response.url


def test_home_logs_out_locked_account(client, db):
    client.force_login(make_user("123456", is_locked=True))
    assert client.get(url("home")).url == url(LOGIN)
    assert "_auth_user_id" not in client.session


# ============================================================== UC 1: đăng nhập
def test_login_page_renders(client, db):
    assert client.get(url(LOGIN)).status_code == 200


def test_login_success_redirects_home(client, db):
    user = make_user("123456")
    response = client.post(url(LOGIN), {"identifier": "123456", "password": PASSWORD})
    assert response.status_code == 302 and response.url == "/"
    assert client.session["_auth_user_id"] == str(user.pk)


def test_login_wrong_password_shows_error_and_never_echoes_password(client, db):
    make_user("123456")
    response = client.post(url(LOGIN), {"identifier": "123456", "password": "bad"})
    assert response.status_code == 200
    assert response.context["error_code"] == "BAD_CREDENTIALS"
    assert response.context["identifier"] == "123456"
    assert "password" not in response.context.flatten()
    assert "_auth_user_id" not in client.session


def test_login_missing_fields_gives_field_errors(client, db):
    response = client.post(url(LOGIN), {"identifier": "", "password": ""})
    assert set(response.context["field_errors"]) == {"identifier", "password"}


def test_login_next_parameter(client, db):
    make_user("123456")
    ok = client.post(url(LOGIN), {"identifier": "123456", "password": PASSWORD, "next": "/grades/results/"})
    assert ok.url == "/grades/results/"
    client.post(url("accounts:logout_view"))
    evil = client.post(url(LOGIN), {"identifier": "123456", "password": PASSWORD, "next": "https://evil.example/"})
    assert evil.url == "/"                                   # chặn open redirect


def test_login_page_redirects_if_already_logged_in(client, db):
    client.force_login(make_user("123456"))
    assert client.get(url(LOGIN)).status_code == 302


# ============================================================== UC 2: đăng xuất
def test_logout_is_post_only_and_ends_session(client, db):
    client.force_login(make_user("123456"))
    assert client.get(url("accounts:logout_view")).status_code == 405
    assert "_auth_user_id" in client.session
    response = client.post(url("accounts:logout_view"))
    assert response.url == url(LOGIN) and "_auth_user_id" not in client.session


# ============================================================== UC 3: quên mật khẩu
def test_reset_password_request(client, db):
    user = make_user("123456")
    response = client.post(url("accounts:reset_password_view"), {"identifier": "123456"})
    assert response.url == url(LOGIN)
    assert PasswordReset.objects.filter(user=user).count() == 1
    assert any("administrator" in m for m in flash(response))


def test_reset_password_unknown_id_shows_error(client, db):
    response = client.post(url("accounts:reset_password_view"), {"identifier": "nobody"})
    assert response.status_code == 200 and response.context["error_code"] == "NOT_FOUND"
    assert response.context["identifier"] == "nobody"
    assert PasswordReset.objects.count() == 0


# ============================================================== UC 4, 5: hồ sơ
def test_profile_for_student_and_teacher(client, db):
    client.force_login(make_student("123456"))
    assert client.get(url("accounts:profile_view")).context["profile"]["student_code"] == "123456"
    client.force_login(make_teacher("GV001"))
    assert client.get(url("accounts:profile_view")).context["profile"]["teacher_code"] == "GV001"


def test_profile_access_control(client, db):
    assert client.get(url("accounts:profile_view")).status_code == 302          # chưa đăng nhập
    client.force_login(make_admin("AD001"))
    assert client.get(url("accounts:profile_view")).status_code == 403          # admin không có hồ sơ cá nhân


def test_student_without_student_record_gets_404(client, db):
    client.force_login(make_user("123456"))
    response = client.get(url("accounts:profile_view"))
    assert response.status_code == 404 and response.context["error_code"] == "NOT_FOUND"


def test_contact_edit_get_is_prefilled(client, db):
    student = make_student("123456", phone_number="0900000000", address="Old street")
    client.force_login(student)
    response = client.get(url("accounts:contact_edit_view"))
    assert response.context["form_data"]["phone_number"] == "0900000000"
    assert response.context["can_edit_address"] is True


def test_student_updates_contact_via_form(client, db):
    student = make_student("123456")
    client.force_login(student)
    response = client.post(url("accounts:contact_edit_view"),
                           {"email": "new@example.com", "phone_number": "0901234567", "address": "1 Le Loi"})
    assert response.url == url("accounts:profile_view")
    student.refresh_from_db()
    assert (student.email, student.phone_number, student.address) == ("new@example.com", "0901234567", "1 Le Loi")


def test_contact_edit_invalid_input_rerenders_with_field_errors(client, db):
    student = make_student("123456", phone_number="0900000000")
    client.force_login(student)
    response = client.post(url("accounts:contact_edit_view"),
                           {"email": "bad", "phone_number": "1", "address": "x"})
    assert response.status_code == 200
    assert set(response.context["field_errors"]) == {"email", "phone_number"}
    assert response.context["form_data"]["email"] == "bad"                    # giữ lại những gì người dùng đã nhập
    student.refresh_from_db()
    assert student.phone_number == "0900000000"


def test_teacher_cannot_change_address_even_if_posted(client, db):
    teacher = make_teacher("GV001", address="Keep me")
    client.force_login(teacher)
    assert client.get(url("accounts:contact_edit_view")).context["can_edit_address"] is False
    client.post(url("accounts:contact_edit_view"),
                {"email": "t@example.com", "phone_number": "0901234567", "address": "Hacked"})
    teacher.refresh_from_db()
    assert teacher.address == "Keep me" and teacher.phone_number == "0901234567"


# ============================================================== UC 21: danh sách tài khoản
def test_account_list_requires_admin(client, db):
    client.force_login(make_teacher("GV001"))
    assert client.get(url("accounts:account_list_view")).status_code == 403


def test_account_list_search_filter_pagination(client, db):
    admin = make_admin("AD001")
    for i in range(12):
        make_user(f"1000{i:02d}", is_locked=(i == 0))
    client.force_login(admin)
    response = client.get(url("accounts:account_list_view"))
    assert response.context["page"].total == 13 and list(response.context["page_numbers"]) == [1, 2]
    assert response.context["current_user_id"] == admin.pk
    response = client.get(url("accounts:account_list_view"), {"q": "100003", "role": "STUDENT", "page": "x"})
    assert [u.username for u in response.context["accounts"]] == ["100003"]
    assert response.context["query_string"] == "q=100003&role=STUDENT"
    assert client.get(url("accounts:account_list_view"), {"status": "locked"}).context["page"].total == 1


def test_account_list_bad_filter_shows_error_not_crash(client, db):
    client.force_login(make_admin("AD001"))
    response = client.get(url("accounts:account_list_view"), {"role": "BOSS"})
    assert response.status_code == 200 and response.context["error_code"] == "VALIDATION"
    assert response.context["accounts"] == []


# ============================================================== UC 19: tạo tài khoản
def test_create_account_shows_password_once(client, db):
    client.force_login(make_admin("AD001"))
    response = client.post(url("accounts:account_create_view"), {
        "full_name": "Nguyen A", "email": "a@example.com", "role": "STUDENT", "username": "123456"})
    assert response.url == url("accounts:account_list_view")
    created = User.objects.get(username="123456")
    first = client.get(url("accounts:account_list_view"))
    notice = first.context["password_notice"]
    assert notice["username"] == "123456" and created.check_password(notice["password"])
    assert client.get(url("accounts:account_list_view")).context["password_notice"] is None   # chỉ hiện một lần


def test_create_account_errors_keep_form_data(client, db):
    client.force_login(make_admin("AD001"))
    response = client.post(url("accounts:account_create_view"), {
        "full_name": "A", "email": "bad", "role": "STUDENT", "username": "12"})
    assert response.status_code == 200
    assert set(response.context["field_errors"]) == {"email", "username"}
    assert response.context["form_data"]["username"] == "12"
    assert not User.objects.filter(username="12").exists()


# ============================================================== UC 20: sửa tài khoản
def test_edit_account(client, db):
    client.force_login(make_admin("AD001"))
    target = make_user("123456")
    page = client.get(url("accounts:account_edit_view", target.pk))
    assert page.context["account"] == target and page.context["form_data"]["email"] == target.email
    response = client.post(url("accounts:account_edit_view", target.pk),
                           {"full_name": "New Name", "email": "new@example.com", "role": "STUDENT"})
    assert response.url == url("accounts:account_list_view")
    target.refresh_from_db()
    assert target.full_name == "New Name"


def test_edit_account_unknown_is_404_and_errors_rerender(client, db):
    client.force_login(make_admin("AD001"))
    assert client.get(url("accounts:account_edit_view", 99999)).status_code == 404
    target = make_user("123456")
    response = client.post(url("accounts:account_edit_view", target.pk),
                           {"full_name": "", "email": "x@example.com", "role": "STUDENT"})
    assert response.status_code == 200 and "full_name" in response.context["field_errors"]


# ============================================================== UC 21: khóa / mở khóa / reset
def test_lock_and_unlock_via_post(client, db):
    client.force_login(make_admin("AD001"))
    target = make_user("123456")
    client.post(url("accounts:account_status_view", target.pk), {"action": "lock"})
    target.refresh_from_db()
    assert target.is_locked
    client.post(url("accounts:account_status_view", target.pk), {"action": "unlock"})
    target.refresh_from_db()
    assert not target.is_locked


def test_status_view_rules(client, db):
    admin = make_admin("AD001")
    client.force_login(admin)
    assert client.get(url("accounts:account_status_view", admin.pk)).status_code == 405
    response = client.post(url("accounts:account_status_view", admin.pk), {"action": "lock"})
    admin.refresh_from_db()
    assert not admin.is_locked and any("own account" in m for m in flash(response))
    assert any("Invalid action" in m for m in flash(
        client.post(url("accounts:account_status_view", admin.pk), {"action": "explode"})))


def test_status_view_next_is_safe(client, db):
    client.force_login(make_admin("AD001"))
    target = make_user("123456")
    keep = client.post(url("accounts:account_status_view", target.pk),
                       {"action": "lock", "next": "/accounts/manage/?q=123&page=2"})
    assert keep.url == "/accounts/manage/?q=123&page=2"
    evil = client.post(url("accounts:account_status_view", target.pk),
                       {"action": "unlock", "next": "https://evil.example/"})
    assert evil.url == url("accounts:account_list_view")


def test_non_admin_cannot_lock_accounts(client, db):
    client.force_login(make_teacher("GV001"))
    target = make_user("123456")
    assert client.post(url("accounts:account_status_view", target.pk), {"action": "lock"}).status_code == 403
    target.refresh_from_db()
    assert not target.is_locked


def test_admin_reset_password_view(client, db):
    client.force_login(make_admin("AD001"))
    target = make_user("123456")
    response = client.post(url("accounts:account_reset_password_view", target.pk))
    assert response.url == url("accounts:account_list_view")
    notice = client.get(url("accounts:account_list_view")).context["password_notice"]
    target.refresh_from_db()
    assert notice["username"] == "123456" and target.check_password(notice["password"])
    assert not target.check_password(PASSWORD)
    assert client.get(url("accounts:account_reset_password_view", target.pk)).status_code == 405


def test_reset_password_view_unknown_account(client, db):
    client.force_login(make_admin("AD001"))
    response = client.post(url("accounts:account_reset_password_view", 99999))
    assert any("not found" in m.lower() for m in flash(response))