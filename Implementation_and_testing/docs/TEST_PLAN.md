# Giai đoạn 2 – test chéo (không ai test module của mình)
| Người | Test module của | Trọng tâm |
|---|---|---|
| BE1 | BE3 (đăng ký + điểm) | đăng ký đồng thời 50–100 request, điểm biên 0/10, ranh giới A–F, GPA, chỉ hiện điểm khi khóa |
| BE2 | BE1 (auth, tài khoản, tìm kiếm) | đăng nhập sai/khóa, ma trận phân quyền, GV chỉ thấy SV của mình |
| BE3 | BE2 (sinh viên, course, section) | trùng mã, validate, trùng lịch, xóa course đang dùng, vòng lặp tiên quyết |
| FE1 | màn hình Admin (FE3) | form, thông báo lỗi, phân trang, "không có kết quả" |
| FE2 | màn hình Student (FE1) | luồng đăng ký/hủy, dialog, nút Full/Registered/Deadline passed |
| FE3 | màn hình Teacher (FE2) | gradebook (ô lỗi tô đỏ), khóa, tìm kiếm, hồ sơ chỉ đọc |

Bảng test case: ID | Use-case | Mô tả | Tiền điều kiện | Bước | Kết quả mong đợi | Thực tế | Pass/Fail | Người test
