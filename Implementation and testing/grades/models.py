"""grades/models.py (model do BE1 chốt; nghiệp vụ do BE3 viết)"""
from django.conf import settings
from django.db import models
from common.contract import LetterGrade


class Gradebook(models.Model):
    section = models.OneToOneField("courses.CourseSection", on_delete=models.CASCADE, related_name="gradebook")
    attendance_weight = models.DecimalField(max_digits=5, decimal_places=2, default=10)
    midterm_weight = models.DecimalField(max_digits=5, decimal_places=2, default=30)
    final_weight = models.DecimalField(max_digits=5, decimal_places=2, default=60)
    is_locked = models.BooleanField(default=False)


class Grade(models.Model):
    gradebook = models.ForeignKey(Gradebook, on_delete=models.CASCADE, related_name="grades")
    enrollment = models.OneToOneField("registration.Enrollment", on_delete=models.CASCADE, related_name="grade")
    attendance_score = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    midterm_score = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    final_exam_score = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    final_score = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    letter_grade = models.CharField(max_length=1, choices=LetterGrade.CHOICES, blank=True)
    grade_point4 = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    passed = models.BooleanField(null=True)


class GradeEditLog(models.Model):
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name="edit_logs")
    editor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    field = models.CharField(max_length=20)          # attendance / midterm / final
    old_value = models.DecimalField(max_digits=4, decimal_places=2, null=True)
    new_value = models.DecimalField(max_digits=4, decimal_places=2, null=True)
    edited_at = models.DateTimeField(auto_now_add=True)


class GradebookUnlockLog(models.Model):
    gradebook = models.ForeignKey(Gradebook, on_delete=models.CASCADE, related_name="unlock_logs")
    admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    reason = models.CharField(max_length=255)
    unlocked_at = models.DateTimeField(auto_now_add=True)


class SemesterGPA(models.Model):
    student = models.ForeignKey("students.Student", on_delete=models.CASCADE, related_name="semester_gpas")
    semester = models.ForeignKey("courses.Semester", on_delete=models.CASCADE, related_name="gpas")
    gpa = models.DecimalField(max_digits=3, decimal_places=2)
    total_credits = models.PositiveSmallIntegerField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["student", "semester"], name="uniq_student_semester_gpa")]
