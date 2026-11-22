# Student Management System

Hệ thống quản lý sinh viên được xây dựng bằng Django, MySQL và giao diện
server-rendered. Ứng dụng hỗ trợ các vai trò **quản trị viên**, **giảng viên**
và **sinh viên**.

## Tính năng chính

- Đăng nhập, đăng xuất, khóa tài khoản và phân quyền theo vai trò.
- Quản lý hồ sơ sinh viên, giảng viên, môn học, học kỳ và lớp học phần.
- Tìm kiếm và lọc dữ liệu theo các tiêu chí của từng vai trò.
- Đăng ký, hủy đăng ký và kiểm tra sức chứa lớp học phần.
- Quản lý bảng điểm, tính điểm tổng kết, điểm chữ và GPA.
- Kiểm tra môn tiên quyết, trùng lịch và các quy tắc trạng thái học tập.
- Dữ liệu mẫu và bộ kiểm thử tự động cho các luồng chính.

## Công nghệ

- Python 3.12
- Django 5.x
- MySQL 8.0
- pytest và pytest-django
- Docker Compose (tùy chọn)

## Cấu trúc dự án

| Thư mục | Mục đích |
|---|---|
| `accounts/` | Người dùng, đăng nhập, tài khoản và phân quyền |
| `students/` | Hồ sơ và trạng thái học tập của sinh viên |
| `courses/` | Môn học, học kỳ, lớp học phần và lịch học |
| `registration/` | Đăng ký và hủy đăng ký học phần |
| `grades/` | Bảng điểm, tính điểm và GPA |
| `search/` | Tìm kiếm và lọc dữ liệu |
| `common/` | Hợp đồng dùng chung, phân trang và permission |
| `templates/` | Giao diện HTML |
| `static/` | CSS và JavaScript |
| `docs/` | Kế hoạch kiểm thử và phân rã công việc |

## Yêu cầu

- Python 3.12 trở lên.
- MySQL 8.0 trở lên đang chạy ở cổng `3307`, hoặc Docker Desktop nếu dùng
  Docker Compose.
- Git.

## Cài đặt và chạy local

Mở PowerShell trong thư mục `Implementation_and_testing`:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Chỉnh các biến kết nối MySQL trong `.env`, sau đó chạy migration và tạo dữ liệu
mẫu:

```powershell
python manage.py migrate
python manage.py seed
python manage.py runserver
```

Mở ứng dụng tại <http://127.0.0.1:8000/>.

Nếu PowerShell chặn việc kích hoạt virtual environment, có thể chạy trực tiếp
các lệnh bằng `py -3.12`, hoặc dùng:

```powershell
.\.venv\Scripts\activate.bat
```

### Cấu hình database mặc định

File `.env.example` dùng các giá trị sau:

| Biến | Giá trị mặc định |
|---|---|
| `DB_NAME` | `student_mgmt` |
| `DB_USER` | `sms_user` |
| `DB_HOST` | `127.0.0.1` |
| `DB_PORT` | `3307` |
| `DEBUG` | `1` |

Không commit file `.env` hoặc mật khẩu thật lên repository.

## Chạy bằng Docker Compose

Docker Compose khởi động MySQL và web app:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Sau khi các container sẵn sàng, mở <http://127.0.0.1:8000/>.

Các lệnh thường dùng:

```powershell
docker compose ps
docker compose logs -f web
docker compose stop
docker compose down
```

Muốn xóa cả dữ liệu MySQL trong volume, chỉ thực hiện khi chắc chắn không cần
dữ liệu hiện tại:

```powershell
docker compose down -v
```

## Tài khoản dữ liệu mẫu

Lệnh `python manage.py seed` có thể chạy lại nhiều lần và tạo dữ liệu mẫu cho
toàn bộ luồng chính. Mật khẩu mặc định của các tài khoản mẫu là `Pass1234`:

| Tài khoản | Vai trò |
|---|---|
| `AD001` | Quản trị viên |
| `GV001` | Giảng viên |
| `100001` | Sinh viên |


## Kiểm thử

Chạy toàn bộ test:

```powershell
pytest
```

Chạy một nhóm test cụ thể:

```powershell
pytest accounts/tests
pytest grades/tests/test_calculator.py
```

Một số test được đánh dấu `skip` vì phụ thuộc vào phần triển khai chưa hoàn
thành. Xem [docs/TEST_PLAN.md](docs/TEST_PLAN.md) để biết phạm vi và kế hoạch
kiểm thử chéo.

## Quy ước phát triển

- Đọc [DECISIONS.md](DECISIONS.md) và [common/contract.py](common/contract.py)
  trước khi thay đổi logic dùng chung.
- Giữ nguyên tên hàm, tham số và cấu trúc dữ liệu đã được các app sử dụng.
- Kiểm tra quyền ở phía server; không chỉ ẩn nút trên giao diện.
- Các thay đổi số lượng đăng ký phải được thực hiện trong transaction và bảo
  đảm an toàn khi có nhiều request đồng thời.
- Thay đổi model phải đi kèm migration và test phù hợp.
- Không đưa secret, file `.env`, dữ liệu cá nhân thật hoặc file build vào Git.

## Tài liệu liên quan

- [Kế hoạch kiểm thử](docs/TEST_PLAN.md)
- [Phân rã công việc](docs/WORK_BREAKDOWN.md)
- [Các quyết định thiết kế](DECISIONS.md)
- [Đặc tả và thiết kế hệ thống](../Requirement%20Specification%20and%20Design%20Document/)
