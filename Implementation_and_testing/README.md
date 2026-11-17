# Nhóm … – Student Management System (Django + MySQL)

## Các phần trong project

| Thư mục / file | Backend | Frontend | Trạng thái |
|---|---|---|---|
| `common/contract.py` | **Cả nhóm** (hợp đồng chung, **không tự ý sửa**) | | Đã chốt |
| `common/permissions.py`, `common/pagination.py` | BE1 | | File khung (TODO) |
| `config/`, `*/models.py`, migration, seed | **BE1** (chỉ BE1 sửa) | | Models đã viết, migration chưa tạo |
| `accounts/` (đăng nhập, hồ sơ, tài khoản) | BE1 | FE2: Login/Reset · FE1: hồ sơ SV · FE3: 5.1, 5.2 | File khung (TODO) |
| `search/` (tìm kiếm, lọc, hồ sơ chi tiết, DS phân công) | BE1 | FE2: 4.1, 4.2, 4.3 | File khung (TODO) |
| `students/` (hồ sơ SV, trạng thái học tập) | BE2 | FE3: 5.3 | File khung (TODO) |
| `courses/` (course, section, trùng lịch) | BE2 | FE3: 5.4, 5.5, 5.6 | File khung (TODO) |
| `registration/` (đăng ký, hủy) | BE3 | FE1: 3.3 – 3.6 | File khung (TODO) |
| `grades/` (nhập điểm, tính điểm, khóa/mở khóa, xem điểm) | BE3 | FE2: 4.4, 4.5 · FE3: 5.7 · FE1: 3.7 | File khung (TODO) |
| `templates/common/` (layout, sidebar, component) | | **FE2**  | File khung (TODO) |
| `docs/api/*.md` | cặp BE–FE cùng viết 
| Test case, test tải, test đồng thời | Giai đoạn 2: test chéo (xem `docs/TEST_PLAN.md`) | | – |

Mỗi người **chỉ sửa file của mình**. Hàm nào còn là khung sẽ báo `[CHƯA CÀI ĐẶT] tên_hàm()`, project vẫn import và chạy bình thường.

## Tài liệu
- `docs/ARCHITECTURE.md`: kiến trúc Client–Server, trách nhiệm từng tầng, luồng request.
- `docs/WORK_BREAKDOWN.md`: danh sách task chi tiết từng người (mã task, UC, tiêu chí xong, ngày) và kế hoạch test giai đoạn 2.

## Cách bắt đầu viết phần của mình
1. Đọc `common/contract.py` và `DECISIONS.md`.
2. **Backend:** mở `<app>/services.py` của mình, đọc docstring từng hàm (có ghi UC, lỗi cần ném), viết code thay cho dòng `not_implemented(...)`, **giữ nguyên tên hàm, tham số**. Sau đó nối vào `<app>/views.py`.
3. **Frontend:** mở `templates/<app>/*.html`, đọc comment TODO và `docs/api/<app>.md` để biết dữ liệu nhận được. Trong lúc BE chưa xong, render với dữ liệu giả đúng cấu trúc.
4. Chạy thử, tự viết unit test trong `<app>/tests/` cho logic của mình, rồi mở pull request.

## Chạy dự án
```
cp .env.example .env
docker compose up -d                    # MySQL 8
python -m venv .venv && .venv\Scripts\activate    # Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```
Windows không cài được `mysqlclient`: đổi dòng đó trong `requirements.txt` thành `pymysql` (settings đã tự nhận).

## Quy ước chung
- **Chỉ Hoa Binh sửa model và migration.** Cần thêm cột thì nhắn Hoa Binh.
- Mọi view phải có `@role_required(...)`; **kiểm tra quyền ở server**, không chỉ ẩn nút ở giao diện.
- Số lượng chỗ (`current_enrollment`) chỉ cập nhật bằng câu lệnh nguyên tử trong transaction.


