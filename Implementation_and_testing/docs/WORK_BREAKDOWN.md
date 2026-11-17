# Phân chia công việc chi tiết (theo SRS v1.2)

Số UC theo bảng "List of Use-cases" (mục III.1.2 của SRS). Mỗi task có: mã, nội dung, **tiêu chí xong (DoD)**, ngày dự kiến.
Giai đoạn 1: ngày 1–8 (code). Giai đoạn 2: ngày 9–13 (test case + test). Ngày 14: dự phòng.

## 0. Tổng quan phân công

| Người | Vai trò | Use-case | Thư mục sở hữu |
|---|---|---|---|
| **BE1** (lead) | Nền tảng, tài khoản, tìm kiếm | 1, 2, 3, 4, 5, 11, 12, 13, 19, 20, 21, 22 | `config/`, `common/`, `*/models.py`, migration, seed, `accounts/`, `search/` |
| **BE2** | Dữ liệu nền (Admin) | 6, 23, 24, 25, 26, 27, 28 | `students/`, `courses/` |
| **BE3** | Đăng ký + điểm | 7, 8, 9, 10, 14, 15, 16, 17, 18 | `registration/`, `grades/` |
| **FE1** | Màn hình Student | UC 4, 5, 6, 7, 8, 9, 10 (giao diện) | `templates/{accounts/profile*, registration/, grades/student_results}` |
| **FE2** | Khung chung + Login + Teacher | UC 1, 2, 3, 11, 12, 13, 14–17, 22 (giao diện) | `templates/common/`, `templates/accounts/login|reset`, `templates/search/`, `templates/grades/gradebook` |
| **FE3** | Màn hình Administrator | UC 18–21, 23–28 (giao diện) | `templates/{accounts/account_*, students/, courses/, grades/locked_list}` |

Cặp làm việc: FE2↔BE1 · FE3↔BE2 · FE1↔BE3 · FE2↔BE3 (gradebook GV) · FE3↔BE1 (accounts) · FE3↔BE3 (mở khóa).

## 1. Backend

### BE1 – Nền tảng, tài khoản, tìm kiếm

| ID | Công việc | UC / SRS | Tiêu chí xong (DoD) | Ngày |
|---|---|---|---|---|
| BE1-1 | Dựng repo, Docker MySQL, `.env`, CI, `requirements.txt`, branch protection | II.5 | Cả nhóm `docker compose up` và `migrate` chạy được | 1 |
| BE1-2 | Hoàn thiện models, tạo migration đầu tiên, **seed data** (1 admin, 5 GV, 50 SV, 10 course, 2 học kỳ, 8 section, vài enrollment/điểm) | IV (class diagram) | `python manage.py seed` tạo đủ dữ liệu; `makemigrations --check` sạch | 1–2 |
| BE1-3 | `role_required`, `teacher_teaches_section`, `teacher_can_see_student`, `paginate` | II.4 Security | Sai role → 403; GV ngoài section bị từ chối; có unit test | 2 |
| BE1-4 | **UC 1 Log in:** đăng nhập bằng mã SV / mã GV / email; mật khẩu băm; đếm `failed_login_count`; khóa tài khoản sau 5 lần sai; từ chối tài khoản `is_locked` | 2.x | Đúng/sai mật khẩu, tài khoản khóa, đăng nhập bằng email chỉ GV – đều đúng thông báo | 2–3 |
| BE1-5 | **UC 2 Log out:** hủy session, về trang login | 3.x | Sau logout không vào được trang cần đăng nhập | 3 |
| BE1-6 | **UC 3 Request password reset:** nhận mã/email, tạo `PasswordReset` (token ngẫu nhiên, hết hạn 30 phút); mã không tồn tại → lỗi, không tạo bản ghi. Giai đoạn 1: **Admin reset** sinh mật khẩu ngẫu nhiên (băm) | 4.x, 21 | Token hết hạn/đã dùng không dùng lại được | 3–4 |
| BE1-7 | **UC 4 View personal info** (SV: mã, họ tên, ngày sinh, giới tính, địa chỉ, SĐT, email; GV tương tự) – chỉ xem của chính mình | 5.x | SV không xem được hồ sơ người khác (đổi id trên URL → 403) | 4 |
| BE1-8 | **UC 5 Update contact:** SV sửa email/SĐT/địa chỉ; GV chỉ email/SĐT; validate định dạng, email unique; lỗi thì không đổi dữ liệu | 6.x | GV gửi `address` → bị từ chối; email trùng → lỗi | 4 |
| BE1-9 | **UC 19 Create account:** nhập họ tên, email, role, username; mật khẩu ngẫu nhiên (băm), trả mật khẩu rõ một lần; trùng username/email, thiếu trường → lỗi | 20.x | Mật khẩu trong DB là hash; tạo xong đăng nhập được | 5 |
| BE1-10 | **UC 20 Edit account:** sửa họ tên, email, role, reset mật khẩu; email trùng tài khoản khác → lỗi | 21.x | Hủy/lỗi thì dữ liệu không đổi | 5 |
| BE1-11 | **UC 21 Manage account status:** khóa/mở khóa/ngưng; **không tự khóa mình**; danh sách có phân trang, tìm theo tên/mã/email, lọc role/status | 22.x | Tài khoản khóa không đăng nhập được | 5–6 |
| BE1-12 | **UC 22 Search students:** theo mã SV, họ tên (một phần/đầy đủ), lớp, ngành; phân trang; **GV chỉ thấy SV trong section mình dạy** | 23.x, III.3 | Admin thấy tất cả, GV chỉ thấy SV của mình; không có kết quả → thông báo | 5–6 |
| BE1-13 | **UC 12 Filter students:** lọc theo lớp, khóa, ngành, trạng thái học tập; kết hợp được với search | 13.x | Kết quả gồm mã, họ tên, lớp, ngành, trạng thái | 6 |
| BE1-14 | **UC 13 Open detailed record:** thông tin cá nhân, liên hệ, section hiện tại, điểm **của section GV dạy**, trạng thái; GV chỉ đọc | 14.x | GV mở SV ngoài section → "no permission" | 6 |
| BE1-15 | **UC 11 View assigned student lists:** danh sách section được phân công → chọn section → DS (mã, họ tên, lớp), phân trang; chưa có section → thông báo | 12.x | GV A không xem được DS section của GV B | 6 |
| BE1-16 | Trang chủ theo role, bảo mật cơ bản (CSRF, chống brute force, SQL injection qua ORM), index DB | II.3, II.4 | Không còn truy vấn thô nối chuỗi | 7 |
| BE1-17 | Hỗ trợ ghép nối, sửa lỗi sơ bộ, demo nội bộ | – | `main` chạy được toàn bộ MVP | 7–8 |

### BE2 – Dữ liệu nền

| ID | Công việc | UC / SRS | Tiêu chí xong (DoD) | Ngày |
|---|---|---|---|---|
| BE2-1 | **UC 23 Add student record:** mã SV (đúng `^\d{6}$`, unique), họ tên, ngày sinh, giới tính, email, SĐT, địa chỉ, nơi sinh, khóa, ngành, lớp, trạng thái; tạo `User(role=STUDENT)` + `Student` **trong một transaction** | 24.x | Trùng mã → lỗi; thiếu trường → báo trường thiếu; lỗi giữa chừng không tạo nửa bản ghi | 2–3 |
| BE2-2 | **UC 24 Edit student information:** sửa mọi thông tin **trừ mã SV** | 25.x | Gửi `student_code` khác → bị bỏ qua/từ chối | 3 |
| BE2-3 | Danh sách toàn bộ sinh viên cho Admin (phân trang) | II.2 | Có phân trang | 3 |
| BE2-4 | **UC 25 Edit academic status:** kiểm tra `VALID_TRANSITIONS`, ghi `AcademicStatusHistory` (người sửa, giờ, trạng thái cũ/mới, ghi chú) | 26.x | Đổi không hợp lệ → `INVALID_STATUS_CHANGE`; mỗi lần đổi có 1 dòng log | 3–4 |
| BE2-5 | **UC 26 Manage courses:** thêm/sửa/xóa, mã course unique, danh sách phân trang, cờ `in_use` | 27.x | Xóa course đã có section **hoặc** điểm → `COURSE_IN_USE` | 4 |
| BE2-6 | Course tiên quyết: `set_prerequisites`, **chặn vòng lặp trực tiếp và gián tiếp** | 10.5 | A→B→C→A bị từ chối | 4–5 |
| BE2-7 | Quản lý học kỳ (`Semester`): kiểm tra `start ≤ regStart ≤ regEnd ≤ cancelDeadline ≤ end` | 11.5 | Nhập sai thứ tự → lỗi | 5 |
| BE2-8 | **UC 27 Create course sections:** mã section unique, course, học kỳ, GV, phòng, sĩ số tối đa, lịch (`SectionSchedule`); **kiểm tra trùng lịch GV và phòng**; tự tạo `Gradebook` mặc định 10/30/60 | 28.x | Trùng GV → `TEACHER_CONFLICT`, trùng phòng → `ROOM_CONFLICT`; có test biên (kề giờ không tính trùng) | 5–6 |
| BE2-9 | **UC 6 View open course sections:** theo học kỳ, hiển thị mã section, tên course, GV, lịch, sĩ số, chỗ còn; phân trang; không có → thông báo. Dùng cho cả SV, GV, Admin xem | 7.x, III.4 | Chỗ còn = max − current | 6 |
| BE2-10 | **UC 28 View section student list (Admin):** mã SV, họ tên, lớp, ngày đăng ký + sĩ số hiện tại/tối đa; phân trang; chưa có SV → thông báo | 29.x | Chỉ tính enrollment `REGISTERED` | 6–7 |
| BE2-11 | Unit test cho trùng lịch, vòng tiên quyết, chuyển trạng thái; sửa lỗi, chuẩn bị demo | – | Test pass trong CI | 7–8 |

### BE3 – Đăng ký và điểm

| ID | Công việc | UC / SRS | Tiêu chí xong (DoD) | Ngày |
|---|---|---|---|---|
| BE3-1 | `grades/calculator.py` (hàm thuần): `validate_scores`, `calculate_final_score` (10/30/60), `convert_to_letter`, `convert_to_grade_point4`, `is_passed`, `calculate_gpa` | 17, 13.3, 14.5 | Unit test đủ biên: 0, 10, ranh giới A/B/C/D/F, GPA nhiều môn | 1–3 |
| BE3-2 | **UC 7 – `validate_registration`:** 5 điều kiện (kỳ đăng ký, còn chỗ, chưa đăng ký, không trùng lịch với section đã đăng ký, đã qua môn tiên quyết); trả đúng lý do | 8.x, 8.3 Enrollment.validate | Mỗi điều kiện có 1 test; lý do trả đúng `ErrorCode` | 3–4 |
| BE3-3 | **UC 7 – `register_section`:** `transaction.atomic()` + cập nhật sĩ số nguyên tử (`UPDATE … WHERE current < max`); tạo `Enrollment`; hủy rồi đăng ký lại thì đổi status | 8.3 | **Test đồng thời:** 20 thread vào section còn 2 chỗ → đúng 2 đăng ký thành công | 4–5 |
| BE3-4 | **UC 9 Cancel registration:** kiểm tra section thuộc SV và chưa quá hạn hủy; giảm sĩ số nguyên tử | 10.x | Quá hạn → `CANCEL_DEADLINE_PASSED`; hủy của người khác → 403 | 5 |
| BE3-5 | **UC 6 phía SV – `list_open_sections`** (state OPEN/FULL/REGISTERED/CLOSED) và **UC 8 `list_registered_sections`** (kèm `can_cancel`) | 7.x, 9.x | Chưa đăng ký gì → thông báo tương ứng | 5 |
| BE3-6 | **UC 14/15/16 – `get_gradebook`, `save_grades`:** kiểm tra quyền GV → kiểm tra khóa → validate từng dòng (có lỗi thì **không lưu dòng nào**, trả danh sách ô sai) → lưu, tính lại điểm tổng/chữ/thang 4 → ghi `GradeEditLog` (người sửa, giờ, cũ, mới) | 15.x, 16.x, 17.x | Điểm ngoài 0–10 hoặc không phải số bị từ chối; mỗi thay đổi có log | 5–6 |
| BE3-7 | **UC 17 Lock gradebook:** yêu cầu **đủ điểm mọi SV**; chuyển Locked; công bố điểm; tính `SemesterGPA` (Σ gp4×tín chỉ / Σ tín chỉ) | 18.x | Thiếu điểm → `GRADES_INCOMPLETE`; sau khóa GV không sửa được | 6 |
| BE3-8 | **UC 18 Unlock gradebook (Admin):** danh sách đã khóa, **bắt buộc lý do**, ghi `GradebookUnlockLog`; xử lý hiển thị điểm/GPA theo DECISIONS #8 | 19.x | Không lý do → `UNLOCK_REASON_REQUIRED`; mỗi lần mở có log | 6–7 |
| BE3-9 | **UC 10 View academic results:** chỉ điểm **đã khóa**; từng section (mã, course, tín chỉ, điểm thành phần, điểm tổng, đậu/rớt), GPA, trạng thái học tập; chưa có → thông báo | 11.x | SV không xem được điểm người khác; điểm chưa khóa không xuất hiện | 7 |
| BE3-10 | Unit test, sửa lỗi, hỗ trợ demo | – | CI xanh | 7–8 |

## 2. Frontend

### FE2 – Khung chung, Login, Teacher (làm sớm nhất vì FE1, FE3 dùng lại)

| ID | Công việc | UC / GUI | DoD | Ngày |
|---|---|---|---|---|
| FE2-1 | `common/base.html`: layout, **sidebar theo role**, khối người dùng + Log out, vùng hiển thị `messages` | II.1 Usability | Mỗi role thấy đúng menu của mình | 1–2 |
| FE2-2 | Component dùng chung: bảng, phân trang, badge trạng thái, dialog xác nhận, thông báo lỗi/thành công, ô tìm kiếm | – | FE1, FE3 dùng lại không phải viết lại | 2 |
| FE2-3 | **Login** (UC 1): ô "Student ID, teacher ID or email", lỗi sai mật khẩu, thông báo tài khoản bị khóa | 2.x | Thông báo đúng chữ spec | 2–3 |
| FE2-4 | **Reset password** (UC 3): nhập email/mã, thông báo mã không tồn tại | 4.x | Có đường quay lại/nhập lại | 3 |
| FE2-5 | **4.1 Tìm kiếm + lọc** (UC 12, 22): ô tìm, lọc lớp/khóa/ngành/trạng thái, nút Clear filters, "No students found", phân trang | 23.x, 13.x | Lọc giữ lại giá trị khi chuyển trang | 4–5 |
| FE2-6 | **4.2 Hồ sơ sinh viên chỉ đọc** (UC 13): cá nhân, liên hệ, section hiện tại, điểm của section mình dạy, trạng thái | 14.x | Không có nút sửa | 5 |
| FE2-7 | **4.3 Danh sách được phân công** (UC 11): chọn section → bảng SV; nút Open record / Open gradebook | 12.x | Chưa có section → thông báo | 5 |
| FE2-8 | **4.4 Gradebook + 4.5 Dialog khóa** (UC 14–17): bảng điểm nhập được, **ô sai tô đỏ + thông báo**, JS tính điểm tạm, dấu "–" khi thiếu điểm, dialog cảnh báo trước khi khóa | 15.x, 16.x, 17.x, 18.x | Gradebook đã khóa → ô nhập bị vô hiệu | 6–7 |
| FE2-9 | Sửa lỗi, kiểm tra trên Chrome/Firefox | – | – | 7–8 |

### FE1 – Student

| ID | Công việc | UC / GUI | DoD | Ngày |
|---|---|---|---|---|
| FE1-1 | **3.1 Thông tin cá nhân** (UC 4): thẻ thông tin, nút Edit | 5.x | – | 3–4 |
| FE1-2 | **3.2 Cập nhật liên hệ** (UC 5): form email/SĐT/địa chỉ, **mã và họ tên bị vô hiệu hóa**, thông báo lỗi, nút Cancel | 6.x | Lỗi hiển thị cạnh đúng trường | 4 |
| FE1-3 | **3.3 Section mở** (UC 6): tìm kiếm, chọn học kỳ, bảng, thanh tiến độ chỗ trống, nút Register / Full / Registered / Deadline passed, phân trang, "no section open" | 7.x | Trạng thái nút khớp `state` từ server | 4–5 |
| FE1-4 | **3.4 Dialog xác nhận đăng ký** (UC 7): hiển thị kết quả 5 điều kiện hoặc lý do bị từ chối (full, trùng lịch, thiếu tiên quyết) | 8.x | Không xác nhận → không ghi gì | 5 |
| FE1-5 | **3.5 Đã đăng ký + 3.6 Dialog hủy** (UC 8, 9): bảng (mã, course, GV, lịch, ngày đăng ký), nút Cancel hoặc nhãn "Deadline passed" | 9.x, 10.x | Chưa đăng ký gì → thông báo | 5–6 |
| FE1-6 | **3.7 Kết quả học tập** (UC 10): bảng điểm thành phần + điểm tổng + chữ + đậu/rớt, **GPA**, trạng thái học tập, nhãn "Gradebook not locked yet" | 11.x | Chưa có kết quả → thông báo | 6–7 |
| FE1-7 | Sửa lỗi, responsive cơ bản, demo | – | – | 7–8 |

### FE3 – Administrator

| ID | Công việc | UC / GUI | DoD | Ngày |
|---|---|---|---|---|
| FE3-1 | **5.1 Accounts** (UC 21): bảng, tìm kiếm, lọc role/status, Lock/Unlock/Activate có dialog xác nhận, **đánh dấu tài khoản của chính mình**, phân trang | 22.x | Nút khóa chính mình bị vô hiệu | 3–4 |
| FE3-2 | **5.2 Tạo/sửa account** (UC 19, 20): form dùng chung, nút Reset password, hiển thị mật khẩu tạm một lần | 20.x, 21.x | Lỗi trùng email/username hiện đúng chỗ | 4–5 |
| FE3-3 | **5.3 Hồ sơ sinh viên** (UC 23, 24, 25): form thêm/sửa, **ô note khi đổi trạng thái**, mã SV chỉ đọc khi sửa, lịch sử trạng thái | 24.x, 25.x, 26.x | Lỗi thiếu trường hiển thị rõ | 3–5 |
| FE3-4 | **5.4 Courses** (UC 26): bảng + form thêm bên phải, nhãn "In use", dialog xóa, chọn tiên quyết | 27.x | Xóa course đang dùng hiện thông báo từ chối | 5 |
| FE3-5 | **5.6 Tạo section** (UC 27): chọn course/học kỳ/GV, phòng, sĩ số, **nhập lịch nhiều buổi**, hiển thị lỗi trùng lịch GV/phòng | 28.x | Lỗi trùng chỉ rõ GV hay phòng | 5–6 |
| FE3-6 | **5.5 DS sinh viên của section** (UC 28): thông tin section, sĩ số x/y, bảng, phân trang, "no student registered" | 29.x | – | 6 |
| FE3-7 | **5.7 Gradebooks** (UC 18): danh sách đã khóa, **ô lý do bắt buộc**, dialog xác nhận, lịch sử mở khóa | 19.x | Không lý do → không gửi được | 6–7 |
| FE3-8 | Sửa lỗi, demo | – | – | 7–8 |

## 3. Mốc kiểm soát giai đoạn 1

| Ngày | Mốc | Điều kiện đạt |
|---|---|---|
| 2 | Nền tảng | Models + migration + seed; layout chung có sidebar |
| 3 | **Đăng nhập 3 role** | Login → trang chủ đúng role → Logout |
| 5 | Dữ liệu nền | Admin tạo được account, SV, course, section |
| 7 | **MVP trên `main`** | Đăng ký/hủy, nhập điểm, khóa/mở khóa, SV xem điểm chạy xuyên suốt; đóng băng tính năng |
| 8 | Demo nội bộ | Cả nhóm chạy kịch bản đầy đủ trên dữ liệu seed |


