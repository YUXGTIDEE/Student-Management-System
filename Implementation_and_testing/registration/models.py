"""registration/models.py (model do Bình chốt; nghiệp vụ do Duy viết)"""
from django.db import models
from common.contract import EnrollmentStatus


class Enrollment(models.Model):
    student = models.ForeignKey("students.Student", on_delete=models.PROTECT, related_name="enrollments")
    section = models.ForeignKey("courses.CourseSection", on_delete=models.PROTECT, related_name="enrollments")
    status = models.CharField(max_length=12, choices=EnrollmentStatus.CHOICES, default=EnrollmentStatus.REGISTERED)
    registered_at = models.DateTimeField(auto_now_add=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        # Một sinh viên chỉ có 1 dòng cho mỗi section (hủy rồi đăng ký lại thì đổi status, không tạo dòng mới)
        constraints = [models.UniqueConstraint(fields=["student", "section"], name="uniq_student_section")]
