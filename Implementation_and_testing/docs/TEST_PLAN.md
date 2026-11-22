# Giai đoạn 2 – test chéo (không ai test module của mình)
| Người | Test module của | Trọng tâm |
|---|---|---|
| Bình | Duy (đăng ký + điểm) | đăng ký đồng thời 50–100 request, điểm biên 0/10, ranh giới A–F, GPA, chỉ hiện điểm khi khóa |
| Thành | Bình (auth, tài khoản, tìm kiếm) | đăng nhập sai/khóa, ma trận phân quyền, GV chỉ thấy SV của mình |
| Duy | Thành (sinh viên, course, section) | trùng mã, validate, trùng lịch, xóa course đang dùng, vòng lặp tiên quyết |
| Huy | màn hình Admin (Thành) | form, thông báo lỗi, phân trang, "không có kết quả" |
| Đạt | màn hình Student (Huy) | luồng đăng ký/hủy, dialog, nút Full/Registered/Deadline passed |
| Thành | màn hình Teacher (Đạt) | gradebook (ô lỗi tô đỏ), khóa, tìm kiếm, hồ sơ chỉ đọc |

Bảng test case: ID | Use-case | Mô tả | Tiền điều kiện | Bước | Kết quả mong đợi | Thực tế | Pass/Fail | Người test
