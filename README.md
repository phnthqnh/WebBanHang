# 🛍️ Backend - Django + PostgreSQL

Dự án Backend cho nền tảng bán hàng, được phát triển bằng **Django REST Framework** và **PostgreSQL**.

## 🚀 Tính năng chính

- ✅ Đăng ký / Đăng nhập / Quên mật khẩu / Xác thực người dùng (JWT)
- ✅ Quản lý sản phẩm (Clothes), Quản lý danh mục (Category)
- ✅ Giỏ hàng và đặt hàng
- ✅ Tìm kiếm, đánh giá sản phẩm
- ✅ Lọc đơn hàng theo người dùng
- ✅ Phương thức thanh toán linh hoạt
- ✅ RESTful API được kiểm thử tự động (unit test)

## 🛠️ Công nghệ sử dụng

- [Django](https://www.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [PostgreSQL](https://www.postgresql.org/)
- [JWT Authentication](https://jwt.io/)

## ⚙️ Cài đặt nhanh

### 1. Clone project

```bash
git clone https://github.com/phnthqnh/WebBanHang.git
cd InternWeb
```

### 2. Tạo virtual environment và cài dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Cấu hình môi trường

- Tạo file .env:
```
# Email config
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email
EMAIL_HOST_PASSWORD=your-password
DEFAULT_FROM_EMAIL=InternWeb <noreply@gmail.com>

# Database
DB_NAME=your-database
DB_USER=your-db_username
DB_PASSWORD=your-db_password
DB_HOST=localhost
DB_PORT=5432
```

### 4. Migrate và tạo superuser

```
python manage.py migrate
python manage.py createsuperuser
```

### 5. Chạy server

```
python manage.py runserver
```

## 🧪 Chạy test

```
python manage.py test
```

## 📂 Cấu trúc thư mục chính

```
gozic/
├── clothes/
├── InternWeb/
├── manage.py
├── requirements.txt
└── .env
```