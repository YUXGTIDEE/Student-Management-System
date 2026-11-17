from django.urls import path
from . import views

app_name = "accounts"
urlpatterns = [
    path("login/", views.login_view, name="login_view"),
    path("logout/", views.logout_view, name="logout_view"),
    path("reset-password/", views.reset_password_view, name="reset_password_view"),
    path("profile/", views.profile_view, name="profile_view"),
    path("profile/contact/", views.contact_edit_view, name="contact_edit_view"),
    path("manage/", views.account_list_view, name="account_list_view"),
    path("manage/new/", views.account_create_view, name="account_create_view"),
    path("manage/<int:user_id>/edit/", views.account_edit_view, name="account_edit_view"),
    path("manage/<int:user_id>/status/", views.account_status_view, name="account_status_view"),
    path("manage/<int:user_id>/reset-password/", views.account_reset_password_view, name="account_reset_password_view"),
]
