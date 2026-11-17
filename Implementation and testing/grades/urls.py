from django.urls import path
from . import views

app_name = "grades"
urlpatterns = [
    path("results/", views.student_results_view, name="student_results_view"),
    path("book/<int:section_id>/", views.gradebook_view, name="gradebook_view"),
    path("book/<int:section_id>/save/", views.gradebook_save_view, name="gradebook_save_view"),
    path("book/<int:section_id>/lock/", views.gradebook_lock_view, name="gradebook_lock_view"),
    path("locked/", views.locked_gradebooks_view, name="locked_gradebooks_view"),
    path("book/<int:section_id>/unlock/", views.gradebook_unlock_view, name="gradebook_unlock_view"),
]
