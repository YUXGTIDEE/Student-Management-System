# Nhóm … – Student Management System (Django + MySQL)

## Các phần trong project

| Thư mục / file | Backend | Frontend | Trạng thái |
|---|---|---|---|
| `common/contract.py` | **Cả nhóm** (hợp đồng chung, **không tự ý sửa**) | | Đã chốt |
| `common/permissions.py`, `common/pagination.py` | Bình | | File khung (TODO) |
| `config/`, `*/models.py`, migration, seed | **Bình** (chỉ Bình sửa) | | Models đã viết, migration chưa tạo |
| `accounts/` (đăng nhập, hồ sơ, tài khoản) | Bình | Đạt: Login/Reset · Huy: hồ sơ SV · Thành: 5.1, 5.2 | File khung (TODO) |
| `search/` (tìm kiếm, lọc, hồ sơ chi tiết, DS phân công) | Bình | Đạt: 4.1, 4.2, 4.3 | File khung (TODO) |
| `students/` (hồ sơ SV, trạng thái học tập) | Minh | Thành: 5.3 | File khung (TODO) |
| `courses/` (course, section, trùng lịch) | Minh | Thành: 5.4, 5.5, 5.6 | File khung (TODO) |
| `registration/` (đăng ký, hủy) | Duy | Huy: 3.3 – 3.6 | File khung (TODO) |
| `grades/` (nhập điểm, tính điểm, khóa/mở khóa, xem điểm) | Duy | Đạt: 4.4, 4.5 · Thành: 5.7 · Huy: 3.7 | File khung (TODO) |
| `templates/common/` (layout, sidebar, component) | | **Đạt**  | File khung (TODO) |
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

### Windows (PowerShell)

```powershell
cd "C:\Users\Dat\Downloads\Student-Management-System-main\Implementation_and_testing"

Copy-Item .env.example .env
docker compose up -d

py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt

py manage.py migrate
py manage.py seed
py manage.py runserver 127.0.0.1:8000
```

Sau đó mở:

- http://127.0.0.1:8000/accounts/login/
- Tài khoản mẫu: `AD001 / Pass1234` (admin), `GV001 / Pass1234` (giảng viên), `100001 / Pass1234` (sinh viên).

Nếu PowerShell không chạy script activate vì policy, có thể dùng:

```powershell
.\.venv\Scripts\activate.bat
```

Hoặc chạy trực tiếp lệnh trong môi trường bằng `py` mà không cần activate.

### macOS/Linux

```bash
cp .env.example .env
docker compose up -d
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed
python manage.py runserver
```

Dừng server bằng `Ctrl+C`. Dừng MySQL bằng `docker compose stop`.

## Quy ước chung
- **Chỉ Hoa Binh sửa model và migration.** Cần thêm cột thì nhắn Hoa Binh.
- Mọi view phải có `@role_required(...)`; **kiểm tra quyền ở server**, không chỉ ẩn nút ở giao diện.
- Số lượng chỗ (`current_enrollment`) chỉ cập nhật bằng câu lệnh nguyên tử trong transaction.


