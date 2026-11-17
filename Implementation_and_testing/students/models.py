"""students/models.py (model do Bình chốt; nghiệp vụ do Minh viết)"""
from django.conf import settings
from django.db import models
from common.contract import AcademicStatus, Gender


class Student(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="student")
    student_code = models.CharField(max_length=6, unique=True)   # 6 chữ số, KHÔNG sửa sau khi tạo
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=Gender.CHOICES)
    place_of_birth = models.CharField(max_length=150, blank=True)
    academic_cohort = models.CharField(max_length=10)             # khóa, ví dụ "2024"
    major = models.CharField(max_length=100)
    student_class = models.CharField(max_length=50)
    academic_status = models.CharField(max_length=30, choices=AcademicStatus.CHOICES,
                                       default=AcademicStatus.ENROLLED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class AcademicStatusHistory(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="status_history")
    editor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    old_status = models.CharField(max_length=30)
    new_status = models.CharField(max_length=30)
    note = models.CharField(max_length=255, blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)
