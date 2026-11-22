
"""python manage.py seed  (BE1)  – tạo dữ liệu mẫu cho cả nhóm.

Chạy lại bao nhiêu lần cũng được: dữ liệu đã có thì được cập nhật chứ không nhân đôi.
Mật khẩu chỉ được đặt khi tạo tài khoản mới (không ghi đè mật khẩu đã đổi), trừ khi dùng --reset-passwords.
Chỉ dành cho máy phát triển: khi DEBUG=0 lệnh từ chối chạy trừ khi có --force.

Dữ liệu mẫu:
  1 admin (AD001), 3 giảng viên (GV001-GV003), 20 sinh viên (100001-100020)
  6 môn (có môn tiên quyết), 2 học kỳ: học kỳ ĐÃ KẾT THÚC có điểm (bảng điểm đã khóa) và học kỳ ĐANG MỞ ĐĂNG KÝ
  1 section đã đầy (CS101-02) để thử lỗi "section đầy"; sinh viên bị đình chỉ / thôi học / đã tốt nghiệp để thử trạng thái;
  100001 rớt CS101 và MA101 để thử lỗi "chưa đạt môn tiên quyết".
"""
from datetime import date, time, timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounts.models import Teacher, User
from common.contract import (DEFAULT_WEIGHTS, GRADE_SCALE, PASS_MIN_SCORE, AcademicStatus, EnrollmentStatus,
                             Gender, Role)
from courses.models import Course, CourseSection, SectionSchedule, Semester
from grades.models import Grade, Gradebook, SemesterGPA
from registration.models import Enrollment
from students.models import Student

DEFAULT_PASSWORD = "Pass1234"

TEACHERS = [("GV001", "Nguyễn Văn Hùng", "Computer Science"),
            ("GV002", "Trần Thị Mai", "Mathematics"),
            ("GV003", "Lê Quang Minh", "Languages")]

# (mã, họ tên, giới tính, lớp, ngành, khóa, trạng thái)
STUDENTS = [
    ("100001", "Nguyễn Thị An", Gender.FEMALE, "CS24A", "Computer Science", "2024", AcademicStatus.ENROLLED),
    ("100002", "Trần Văn Bình", Gender.MALE, "CS24A", "Computer Science", "2024", AcademicStatus.ENROLLED),
    ("100003", "Lê Thị Cẩm", Gender.FEMALE, "CS24A", "Computer Science", "2024", AcademicStatus.ENROLLED),
    ("100004", "Phạm Văn Dũng", Gender.MALE, "CS24A", "Computer Science", "2024", AcademicStatus.ENROLLED),
    ("100005", "Hoàng Thị Em", Gender.FEMALE, "CS24A", "Computer Science", "2024", AcademicStatus.ENROLLED),
    ("100006", "Vũ Văn Phúc", Gender.MALE, "CS24B", "Computer Science", "2024", AcademicStatus.ENROLLED),
    ("100007", "Đặng Thị Giang", Gender.FEMALE, "CS24B", "Computer Science", "2024", AcademicStatus.ENROLLED),
    ("100008", "Bùi Văn Hải", Gender.MALE, "CS24B", "Computer Science", "2024", AcademicStatus.ENROLLED),
    ("100009", "Đỗ Thị Hương", Gender.FEMALE, "CS24B", "Computer Science", "2024", AcademicStatus.ENROLLED),
    ("100010", "Ngô Văn Khoa", Gender.MALE, "CS24B", "Computer Science", "2024", AcademicStatus.ENROLLED),
    ("100011", "Dương Thị Lan", Gender.FEMALE, "MA24A", "Mathematics", "2024", AcademicStatus.ENROLLED),
    ("100012", "Lý Văn Minh", Gender.MALE, "MA24A", "Mathematics", "2024", AcademicStatus.ENROLLED),
    ("100013", "Phan Thị Ngọc", Gender.FEMALE, "MA24A", "Mathematics", "2024", AcademicStatus.ENROLLED),
    ("100014", "Trịnh Văn Oanh", Gender.MALE, "MA24A", "Mathematics", "2024", AcademicStatus.ENROLLED),
    ("100015", "Mai Thị Phương", Gender.FEMALE, "MA25A", "Mathematics", "2025", AcademicStatus.ENROLLED),
    ("100016", "Cao Văn Quân", Gender.MALE, "CS25A", "Computer Science", "2025", AcademicStatus.ENROLLED),
    ("100017", "Tạ Thị Rạng", Gender.FEMALE, "CS25A", "Computer Science", "2025", AcademicStatus.ENROLLED),
    ("100018", "Châu Văn Sơn", Gender.MALE, "CS21A", "Computer Science", "2021", AcademicStatus.GRADUATED),
    ("100019", "Đinh Thị Trang", Gender.FEMALE, "MA24A", "Mathematics", "2024", AcademicStatus.TEMPORARILY_SUSPENDED),
    ("100020", "Lương Văn Út", Gender.MALE, "CS24B", "Computer Science", "2024", AcademicStatus.WITHDRAWN),
]

# (mã môn, tên, số tín chỉ, số tiết, môn tiên quyết)
COURSES = [
    ("CS101", "Introduction to Programming", 3, 45, []),
    ("CS102", "Data Structures", 3, 45, ["CS101"]),
    ("CS201", "Database Systems", 3, 45, ["CS102"]),
    ("MA101", "Calculus I", 4, 60, []),
    ("MA102", "Linear Algebra", 3, 45, ["MA101"]),
    ("EN101", "Academic English", 2, 30, []),
]

# (mã section, mã môn, học kỳ, giảng viên, phòng, sức chứa, [(thứ 0-6, giờ bắt đầu, giờ kết thúc)])
SECTIONS = [
    ("CS101-01", "CS101", "past", "GV001", "A101", 40, [(0, time(7, 0), time(9, 30))]),
    ("MA101-01", "MA101", "past", "GV002", "B201", 40, [(1, time(7, 0), time(10, 0))]),
    ("EN101-01", "EN101", "past", "GV003", "C301", 40, [(2, time(13, 0), time(15, 0))]),
    ("CS102-01", "CS102", "open", "GV001", "A102", 40, [(0, time(7, 0), time(9, 30))]),
    ("CS201-01", "CS201", "open", "GV001", "A103", 40, [(3, time(9, 30), time(12, 0))]),
    ("MA102-01", "MA102", "open", "GV002", "B202", 40, [(1, time(13, 0), time(15, 30))]),
    ("EN101-02", "EN101", "open", "GV003", "C302", 40, [(2, time(7, 0), time(9, 0))]),
    ("CS101-02", "CS101", "open", "GV001", "A104", 2, [(4, time(7, 0), time(9, 30))]),   # sức chứa 2, sẽ đầy
]

# Học kỳ đã kết thúc: section -> danh sách mã sinh viên
PAST_ENROLLMENTS = {
    "CS101-01": [f"1000{i:02d}" for i in range(1, 11)],
    "MA101-01": [f"1000{i:02d}" for i in range(1, 7)] + ["100011", "100012"],
    "EN101-01": [f"1000{i:02d}" for i in range(7, 13)],
}
# Học kỳ đang mở đăng ký
OPEN_ENROLLMENTS = {
    # Chỉ gồm sinh viên ĐÃ ĐẬU môn tiên quyết. 100001 rớt CS101 và MA101 -> thử đăng ký CS102/MA102 sẽ gặp PREREQ_NOT_MET
    "CS102-01": ["100002", "100003", "100004", "100005", "100006"],
    "MA102-01": ["100011", "100012"],
    "CS101-02": ["100016", "100017"],            # đủ 2/2 -> đầy
}


def _q2(value):
    return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _scores(student_code, section_code):
    """Điểm giả lập nhưng cố định (cùng một sinh viên/section luôn ra cùng điểm), có vài người rớt."""
    n = int(student_code[-2:]) + len(section_code)
    attendance = Decimal(8 + (n % 3) * Decimal("0.5"))
    midterm = Decimal(5 + (n * 7) % 5) + Decimal("0.5")
    final = Decimal(4 + (n * 11) % 6) + Decimal("0.5")
    if n % 9 == 0:                                      # một số người rớt
        midterm, final = Decimal("3.0"), Decimal("2.5")
    return _q2(attendance), _q2(midterm), _q2(final)


def _letter(score):
    for minimum, letter, point4 in GRADE_SCALE:
        if score >= minimum:
            return letter, point4
    return GRADE_SCALE[-1][1], GRADE_SCALE[-1][2]


class Command(BaseCommand):
    help = "Tạo dữ liệu mẫu (chạy lại được nhiều lần). Chỉ dùng cho máy phát triển."

    def add_arguments(self, parser):
        parser.add_argument("--password", default=DEFAULT_PASSWORD, help=f"Mật khẩu mẫu (mặc định {DEFAULT_PASSWORD})")
        parser.add_argument("--reset-passwords", action="store_true",
                            help="Đặt lại mật khẩu mẫu cho cả tài khoản đã tồn tại")
        parser.add_argument("--force", action="store_true", help="Cho phép chạy khi DEBUG=0")

    def handle(self, *args, **options):
        if not settings.DEBUG and not options["force"]:
            raise CommandError("Từ chối chạy seed khi DEBUG=0 (nhầm môi trường?). Dùng --force nếu thật sự muốn.")
        self.password = options["password"]
        self.reset_passwords = options["reset_passwords"]
        with transaction.atomic():
            self._accounts()
            self._courses()
            self._semesters_and_sections()
            self._enrollments_and_grades()
        self.stdout.write(self.style.SUCCESS("Seed xong."))
        self.stdout.write(
            f"Login (password: {self.password}): "
            "AD001 (admin) | GV001 (teacher) | 100001 (student)"
        )

    # ------------------------------------------------------------ tài khoản
    def _user(self, username, role, full_name):
        user, created = User.objects.get_or_create(username=username, defaults={
            "role": role, "full_name": full_name, "email": f"{username.lower()}@example.com"})
        if not created:
            user.role, user.full_name = role, full_name
        if created or self.reset_passwords:
            user.set_password(self.password)
            user.is_locked, user.failed_login_count = False, 0
        user.save()
        return user

    def _accounts(self):
        self._user("AD001", Role.ADMINISTRATOR, "Quản trị viên")
        for code, name, department in TEACHERS:
            user = self._user(code, Role.TEACHER, name)
            Teacher.objects.update_or_create(user=user, defaults={"teacher_code": code, "department": department})
        for index, (code, name, gender, klass, major, cohort, status) in enumerate(STUDENTS):
            user = self._user(code, Role.STUDENT, name)
            user.phone_number = f"09000000{index:02d}"
            user.address = f"{index + 1} Lê Lợi, Huế"
            user.save()
            Student.objects.update_or_create(student_code=code, defaults={
                "user": user, "date_of_birth": date(2004 + int(cohort) - 2024, 1 + index % 12, 1 + index % 28),
                "gender": gender, "place_of_birth": "Huế", "academic_cohort": cohort, "major": major,
                "student_class": klass, "academic_status": status})

    # ------------------------------------------------------------ môn học, học kỳ, section
    def _courses(self):
        for code, name, credits, periods, _ in COURSES:
            Course.objects.update_or_create(course_code=code, defaults={
                "course_name": name, "credit_hours": credits, "class_periods": periods,
                "description": f"{name} (dữ liệu mẫu)."})
        for code, _, _, _, prerequisites in COURSES:
            Course.objects.get(course_code=code).prerequisites.set(Course.objects.filter(course_code__in=prerequisites))

    def _semesters_and_sections(self):
        today = date.today()
        # Học kỳ đã kết thúc (có điểm) và học kỳ đang mở đăng ký (tính theo ngày hôm nay)
        self.semesters = {
            "past": Semester.objects.update_or_create(semester_name="Seed Past Semester", defaults={
                "start_date": today - timedelta(days=200), "end_date": today - timedelta(days=60),
                "registration_start": today - timedelta(days=230), "registration_end": today - timedelta(days=210),
                "cancellation_deadline": today - timedelta(days=190)})[0],
            "open": Semester.objects.update_or_create(semester_name="Seed Open Semester", defaults={
                "start_date": today + timedelta(days=21), "end_date": today + timedelta(days=140),
                "registration_start": today - timedelta(days=7), "registration_end": today + timedelta(days=14),
                "cancellation_deadline": today + timedelta(days=28)})[0],
        }
        for code, course_code, which, teacher_code, room, capacity, schedules in SECTIONS:
            section, _ = CourseSection.objects.update_or_create(section_code=code, defaults={
                "course": Course.objects.get(course_code=course_code), "semester": self.semesters[which],
                "teacher": Teacher.objects.get(teacher_code=teacher_code), "classroom": room,
                "max_capacity": capacity})
            section.schedules.all().delete()
            SectionSchedule.objects.bulk_create(
                [SectionSchedule(section=section, day_of_week=d, start_time=s, end_time=e) for d, s, e in schedules])

    # ------------------------------------------------------------ đăng ký và điểm
    def _enrollments_and_grades(self):
        weights = DEFAULT_WEIGHTS
        for section_code, codes in {**PAST_ENROLLMENTS, **OPEN_ENROLLMENTS}.items():
            section = CourseSection.objects.get(section_code=section_code)
            for code in codes:
                Enrollment.objects.get_or_create(
                    student=Student.objects.get(student_code=code), section=section,
                    defaults={"status": EnrollmentStatus.REGISTERED})

        for section_code, codes in PAST_ENROLLMENTS.items():                 # chỉ học kỳ đã kết thúc có điểm
            section = CourseSection.objects.get(section_code=section_code)
            gradebook, _ = Gradebook.objects.update_or_create(section=section, defaults={
                "attendance_weight": weights["attendance"], "midterm_weight": weights["midterm"],
                "final_weight": weights["final"], "is_locked": True})
            for code in codes:
                attendance, midterm, final = _scores(code, section_code)
                total = _q2((attendance * weights["attendance"] + midterm * weights["midterm"]
                             + final * weights["final"]) / Decimal(100))
                letter, point4 = _letter(total)
                Grade.objects.update_or_create(
                    enrollment=Enrollment.objects.get(student__student_code=code, section=section),
                    defaults={"gradebook": gradebook, "attendance_score": attendance, "midterm_score": midterm,
                              "final_exam_score": final, "final_score": total, "letter_grade": letter,
                              "grade_point4": point4, "passed": total >= PASS_MIN_SCORE})

        # Số đang đăng ký của mỗi section luôn khớp với số dòng REGISTERED
        for section in CourseSection.objects.all():
            section.current_enrollment = section.enrollments.filter(status=EnrollmentStatus.REGISTERED).count()
            section.save(update_fields=["current_enrollment"])

        # GPA từng học kỳ (thang 4, theo số tín chỉ) của học kỳ đã kết thúc
        past = self.semesters["past"]
        for student in Student.objects.filter(enrollments__section__semester=past).distinct():
            grades = Grade.objects.filter(enrollment__student=student, enrollment__section__semester=past
                                          ).select_related("enrollment__section__course")
            credits = sum(g.enrollment.section.course.credit_hours for g in grades)
            points = sum(g.grade_point4 * g.enrollment.section.course.credit_hours for g in grades)
            SemesterGPA.objects.update_or_create(student=student, semester=past, defaults={
                "gpa": _q2(points / credits), "total_credits": credits})