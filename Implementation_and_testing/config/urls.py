from django.contrib import admin
from django.urls import include, path
from accounts.views import home_view

urlpatterns = [
    path("", home_view, name="home"),
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("students/", include("students.urls")),
    path("courses/", include("courses.urls")),
    path("registration/", include("registration.urls")),
    path("grades/", include("grades.urls")),
    path("search/", include("search.urls")),
]
