from django.urls import path
from . import views

app_name = "registration"
urlpatterns = [
    path("sections/", views.open_sections_view, name="open_sections_view"),
    path("sections/<int:section_id>/confirm/", views.register_confirm_view, name="register_confirm_view"),
    path("sections/<int:section_id>/register/", views.register_view, name="register_view"),
    path("mine/", views.registered_sections_view, name="registered_sections_view"),
    path("sections/<int:section_id>/cancel/", views.cancel_view, name="cancel_view"),
]
