from django.urls import path
from . import views

app_name = "students"
urlpatterns = [
    path("", views.student_list_view, name="student_list_view"),
    path("new/", views.student_create_view, name="student_create_view"),
    path("<int:student_id>/edit/", views.student_edit_view, name="student_edit_view"),
    path("<int:student_id>/status/", views.student_status_view, name="student_status_view"),
]
