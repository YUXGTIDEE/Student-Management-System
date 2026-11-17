from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path

urlpatterns = [
    path("", lambda r: redirect("accounts:login_view")),   # TODO (Binh/Huy): trang chủ theo role
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("students/", include("students.urls")),
    path("courses/", include("courses.urls")),
    path("registration/", include("registration.urls")),
    path("grades/", include("grades.urls")),
    path("search/", include("search.urls")),
]
