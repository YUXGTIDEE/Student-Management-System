from django.urls import path
from . import views

app_name = "courses"
urlpatterns = [
    path("", views.course_list_view, name="course_list_view"),
    path("<int:course_id>/edit/", views.course_edit_view, name="course_edit_view"),
    path("<int:course_id>/delete/", views.course_delete_view, name="course_delete_view"),
    path("sections/", views.section_list_view, name="section_list_view"),
    path("sections/new/", views.section_create_view, name="section_create_view"),
    path("sections/<int:section_id>/students/", views.section_students_view, name="section_students_view"),
]
