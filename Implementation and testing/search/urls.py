from django.urls import path
from . import views

app_name = "search"
urlpatterns = [
    path("", views.student_search_view, name="student_search_view"),
    path("student/<int:student_id>/", views.student_detail_view, name="student_detail_view"),
    path("assigned/", views.assigned_sections_view, name="assigned_sections_view"),
]
