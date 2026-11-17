# DECISIONS – các điểm đã chốt (cả nhóm họp ngày 1 rồi sửa file này, sau đó mới sửa `common/contract.py`)

Các mục dưới đây là ĐỀ XUẤT MẶC ĐỊNH để nhóm xác nhận hoặc đổi. Các điểm này là chỗ SRS còn lệch hoặc thiếu.

| # | Vấn đề | Đề xuất | Chủ sở hữu | Xác nhận |
|---|---|---|---|---|
| 1 | Mã sinh viên | `student_code` VARCHAR(6), regex `^\d{6}$`, unique, không sửa. Khóa chính là `id` tự tăng | Bình | ☐ |
| 2 | Mã giảng viên / admin | `GV001…`, `AD001…` để không trùng với mã sinh viên khi đăng nhập | Bình | ☐ |
| 3 | Dữ liệu ACCOUNT | `User` có `full_name`, `email`, `phone_number`, `address`; Admin chỉ là `User(role=ADMINISTRATOR)` | Bình | ☐ |
| 4 | Bảng quy đổi điểm | A ≥ 8.5 (4.0), B ≥ 7.0 (3.0), C ≥ 5.5 (2.0), D ≥ 4.0 (1.0), F < 4.0 (0). Đậu từ 4.0. Xem `GRADE_SCALE` | Duy | ☐ |
| 5 | Lịch học | Lưu `day_of_week` + `start_time` + `end_time` (bỏ khái niệm "tiết") | Minh | ☐ |
| 6 | Đổi trạng thái học tập | ENROLLED → WITHDRAWN/SUSPENDED/GRADUATED; SUSPENDED → ENROLLED/WITHDRAWN; WITHDRAWN và GRADUATED là cuối | Minh | ☐ |
| 7 | Sĩ số | Cột `current_enrollment` trên section, cập nhật bằng `UPDATE … WHERE current_enrollment < max_capacity` trong transaction | Duy | ☐ |
| 8 | Mở khóa gradebook | Sau khi mở khóa: điểm vẫn hiển thị cho SV nhưng gắn nhãn "đang chỉnh sửa"; GPA tính lại khi khóa lần nữa. (Đổi nếu nhóm muốn ẩn điểm) | Duy | ☐ |
| 9 | Xóa course | Chặn nếu đã có section HOẶC có grade (theo quy tắc chặt hơn của SRS) | Minh | ☐ |
| 10 | Trọng số điểm | Cố định 10/30/60; gradebook tạo tự động khi tạo section | Minh/Duy | ☐ |
| 11 | Reset mật khẩu | Giai đoạn 1: chỉ Admin reset (sinh mật khẩu ngẫu nhiên, hiện cho admin). Không gửi email thật | Bình | ☐ |
| 12 | Hủy đăng ký | Đổi `status=CANCELLED`, không xóa dòng; đăng ký lại thì đổi về REGISTERED | Duy | ☐ |
| 13 | Điều kiện tiên quyết | "Đã qua" = có Grade `passed=True` ở gradebook đã khóa | Duy | ☐ |
| 14 | Phạm vi cắt (giai đoạn 1) | Không gửi email, không academic standing/cumulative GPA, tinh chỉnh UI để sau | cả nhóm | ☐ |
