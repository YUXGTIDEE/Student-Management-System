"""courses/models.py (model do BE1 chốt; nghiệp vụ do BE2 viết)"""
from django.conf import settings
from django.db import models


class Course(models.Model):
    course_code = models.CharField(max_length=20, unique=True)
    course_name = models.CharField(max_length=150)
    credit_hours = models.PositiveSmallIntegerField()
    class_periods = models.PositiveSmallIntegerField()
    description = models.TextField(blank=True)
    prerequisites = models.ManyToManyField("self", symmetrical=False, blank=True, related_name="required_by")


class Semester(models.Model):
    semester_name = models.CharField(max_length=50)              # "2026-2027 / Semester 1"
    start_date = models.DateField()
    end_date = models.DateField()
    registration_start = models.DateField()
    registration_end = models.DateField()
    cancellation_deadline = models.DateField()


class CourseSection(models.Model):
    section_code = models.CharField(max_length=20, unique=True)
    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name="sections")
    semester = models.ForeignKey(Semester, on_delete=models.PROTECT, related_name="sections")
    teacher = models.ForeignKey("accounts.Teacher", on_delete=models.PROTECT, related_name="sections")
    classroom = models.CharField(max_length=30)
    max_capacity = models.PositiveIntegerField()
    # 0 <= current_enrollment <= max_capacity. CHỈ cập nhật bằng câu lệnh nguyên tử (xem DECISIONS #7)
    current_enrollment = models.PositiveIntegerField(default=0)


class SectionSchedule(models.Model):
    """Một buổi học trong tuần. Lưu giờ bắt đầu/kết thúc thẳng (xem DECISIONS #5)."""
    section = models.ForeignKey(CourseSection, on_delete=models.CASCADE, related_name="schedules")
    day_of_week = models.PositiveSmallIntegerField()             # 0=Thứ 2 ... 6=Chủ nhật
    start_time = models.TimeField()
    end_time = models.TimeField()
