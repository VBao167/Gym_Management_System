# Gym Management System

Dự án hướng đến việc quản lý hoạt động của **một phòng gym**, bao gồm quản lý người dùng, Hội viên, nhân viên, gói tập, đăng ký và gia hạn gói, hóa đơn, điểm danh, lịch tập PT, khu vực Hội viên và báo cáo thống kê.

## Công nghệ sử dụng

- Python 3.14.6
- Django 6.0.7
- Microsoft SQL Server
- mssql-django
- pyodbc
- Django Template
- HTML
- CSS tùy chỉnh

Frontend của hệ thống sử dụng Django Template kết hợp HTML/CSS thuần, không sử dụng Bootstrap hay JavaScript framework cho nghiệp vụ chính.

## Nhóm người dùng

Hệ thống có 4 vai trò:

- **Admin**
- **Lễ tân**
- **Huấn luyện viên**
- **Hội viên**

Mỗi vai trò có khu vực chức năng và quyền truy cập riêng.

## Chức năng chính

### Quản trị viên

- Xem dashboard tổng quan
- Quản lý tài khoản
- Quản lý Hội viên
- Quản lý Lễ tân và Huấn luyện viên
- Quản lý gói tập
- Xem đăng ký và hóa đơn
- Xem điểm danh
- Xem lịch tập PT
- Xem báo cáo và thống kê
- Khóa/mở tài khoản
- Đặt lại mật khẩu cho người dùng

### Lễ tân

- Tra cứu và quản lý Hội viên
- Tạo Hội viên mới
- Đăng ký gói tập
- Gia hạn/mua tiếp gói
- Lập hóa đơn
- Điểm danh Hội viên
- Xếp lịch PT
- Hủy buổi PT
- Theo dõi hoạt động vận hành theo ngày

### Huấn luyện viên

- Xem lịch tập được phân công
- Lọc lịch theo ngày và trạng thái
- Xem chi tiết buổi tập
- Xác nhận buổi tập hoàn thành
- Ghi nhận Hội viên vắng

### Hội viên

- Xem tổng quan tài khoản
- Xem gói tập của mình
- Xem thông tin thanh toán
- Xem lịch tập PT
- Xem lịch sử điểm danh
- Đổi mật khẩu

## Một số nghiệp vụ chính

- Mỗi Hội viên có thể có nhiều đăng ký gói tập nhưng thời hạn các đăng ký không được chồng nhau.
- Gia hạn được thực hiện bằng cách tạo đăng ký mới nối tiếp, không sửa thời hạn đăng ký cũ.
- Giá gói và số buổi PT được lưu theo dạng snapshot tại thời điểm đăng ký.
- Một đăng ký có tối đa một hóa đơn.
- Trạng thái quyền tập của Hội viên được tách biệt với trạng thái đăng nhập của tài khoản.
- Hệ thống kiểm tra quyền vào phòng gym trước khi điểm danh.
- Lịch PT kiểm tra trùng thời gian của cả Hội viên và Huấn luyện viên.
- Số buổi PT đã dùng, đã lên lịch và còn có thể xếp được tính từ dữ liệu thực tế.
- Dữ liệu lịch sử được giữ lại để phục vụ tra cứu và báo cáo.

## Kiến trúc xử lý

Dự án tổ chức nghiệp vụ theo hướng:

```text
Model
  ↓
Service
  ↓
Form
  ↓
View
  ↓
Template
  ↓
Test
```

Trong đó:

- **Model** định nghĩa dữ liệu, quan hệ và constraint.
- **Service** xử lý các nghiệp vụ chính và transaction.
- **Form** kiểm tra dữ liệu nhập từ giao diện.
- **View** xử lý phân quyền, điều phối request và gọi service.
- **Template** chịu trách nhiệm trình bày giao diện.
- **Test** bảo vệ business rule, permission và regression.

## Cấu trúc chính

```text
src/
├── accounts/
│   ├── services/
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   └── tests.py
│
├── gym/
│   ├── services/
│   ├── tests/
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   └── urls.py
│
├── common/
│   └── ma_tu_dong.py
│
├── config/
│   └── settings.py
│
├── templates/
├── static/
│   ├── css/
│   └── images/
│
└── manage.py
```

Các sơ đồ phân tích hệ thống được lưu trong:

```text
docs/diagrams/
```

Bao gồm các sơ đồ BFD, DFD và ERD của hệ thống.

## Cơ sở dữ liệu

Hệ thống sử dụng Microsoft SQL Server với database:

```text
GymManagementDB
```

Các bảng nghiệp vụ chính:

1. `TaiKhoan`
2. `HoiVien`
3. `LeTan`
4. `HuanLuyenVien`
5. `GoiTap`
6. `DangKyGoiTap`
7. `HoaDon`
8. `BuoiTapPT`
9. `DiemDanh`

Custom User Model:

```text
accounts.TaiKhoan
```

## Cài đặt

Clone repository:

```powershell
git clone https://github.com/VBao167/Gym_Management_System.git
cd Gym_Management_System
```

Tạo và kích hoạt virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Cài dependency:

```powershell
pip install -r requirements.txt
```

Tạo file `.env` ở thư mục gốc và cấu hình:

```env
DJANGO_SECRET_KEY=your-secret-key
```

Đảm bảo máy đã cài:

- Microsoft SQL Server
- ODBC Driver 18 for SQL Server

Sau đó cấu hình SQL Server instance phù hợp trong:

```text
src/config/settings.py
```

## Chạy dự án

Từ thư mục gốc:

```powershell
python .\src\manage.py runserver
```

Truy cập:

```text
http://127.0.0.1:8000/
```

## Kiểm thử

Kiểm tra cấu hình Django:

```powershell
python .\src\manage.py check
```

Kiểm tra migration:

```powershell
python .\src\manage.py makemigrations --check --dry-run
```

Chạy toàn bộ test:

```powershell
python .\src\manage.py test accounts gym --verbosity 1
```

Baseline kiểm thử hiện tại:

```text
235 / 235 tests PASS
```
