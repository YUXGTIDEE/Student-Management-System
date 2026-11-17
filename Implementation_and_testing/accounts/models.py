"""accounts/models.py  (Phụ trách: Binh - chỉ BE1 được sửa model/migration)"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from common.contract import Role, ResetStatus


class User(AbstractUser):
    """Tài khoản đăng nhập. username = mã sinh viên / mã giảng viên / mã admin."""
    role = models.CharField(max_length=20, choices=Role.CHOICES)
    full_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.CharField(max_length=255, blank=True)
    is_locked = models.BooleanField(default=False)   # khóa/ngưng hoạt động -> không đăng nhập được
    failed_login_count = models.PositiveIntegerField(default=0)
    # email: dùng trường email có sẵn của AbstractUser, phải unique (kiểm tra ở service)


class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="teacher")
    teacher_code = models.CharField(max_length=10, unique=True)
    department = models.CharField(max_length=100, blank=True)


class PasswordReset(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="password_resets")
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    status = models.CharField(max_length=10, choices=ResetStatus.CHOICES, default=ResetStatus.PENDING)
