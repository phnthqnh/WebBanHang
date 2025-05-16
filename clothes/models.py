from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.contrib.auth import get_user_model
from django.utils.html import format_html
import random
import string

# Create your models here.
class UserAccountManager(BaseUserManager):
    def create_user(self, username, email, password=None, role='user', **extra_fields):
        if not email:
            raise ValueError('Người dùng phải có một địa chỉ email')
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, role=role, **extra_fields)
        user.set_password(password)
        if role == 'user':
            user.is_staff = False
        else:
            user.is_staff = True
        user.save(using=self._db)
        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email=email, username=username, password=password, **extra_fields)
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserAccount = get_user_model() 
        try:
            user = UserAccount.objects.get(username=username) 
        except UserAccount.DoesNotExist:
            return None
        if user.check_password(password):
            return user
        return None

class UserAccount(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('user', 'user'),
        ('admin', 'admin'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    email = models.EmailField(max_length=255, unique=True)
    username = models.CharField(max_length=255, unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False) 

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email'] 

    objects = UserAccountManager()
    
    class Meta:
        db_table = "useraccount"
        verbose_name = "UserAccount"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.username
    
    def save(self, *args, **kwargs):
        if self.role == 'admin':
            self.is_staff = True
        else:
            self.is_staff = False

        super(UserAccount, self).save(*args, **kwargs)

        if not self.is_staff:
            Cart.objects.get_or_create(user=self)
        
            
class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name='Loại')

    def __str__(self):
        return self.name
    
class Clothes(models.Model):
    name = models.CharField(max_length=255, verbose_name="Tên")
    price = models.IntegerField(verbose_name="Giá")
    image = models.URLField(verbose_name="Ảnh")
    description = models.TextField(null=True, blank=True, verbose_name="Mô tả")
    STATUS_CHOICES = [
        ('còn hàng', 'còn hàng'),
        ('hết hàng', 'hết hàng'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='còn hàng', verbose_name="Trạng thái")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Loại")
    quantity_in_stock = models.IntegerField(null=True, default=10, blank=True, verbose_name="SL trong kho")
    rating = models.FloatField(null=True, blank=True)
    
    def __str__(self):
        return self.name
    
    def status_view(self):
        try:
            if self.status == 'còn hàng':
                status_color= '#000000'
                status = self.status
            else:
                status_color= '#FF0000'
                status = self.status

            html= f'<span style="color: {status_color};">{status}</span>'
            return format_html(html)
        except:
            return 0
    status_view.short_description = 'Trạng thái'
    
    def _price(self):
        try:
            return "{:,.0f} đồng".format(self.price)
        except:
            return None
    _price.short_description = 'Giá'
    
    def save(self, *args, **kwargs):
        quantity = self.quantity_in_stock
        if quantity == 0:
            self.status = 'hết hàng'
        else:
            self.status = 'còn hàng'
        super(Clothes, self).save(*args, **kwargs)
        ratings = OrderItem.objects.filter(product = self).exclude(rating__isnull=True).values_list('rating', flat=True)
        if len(ratings):
            mean_ratings = sum(ratings)/len(ratings)
        else:
            mean_ratings = None
        self.rating = mean_ratings
        super().save(update_fields=["rating"])

class Cart(models.Model):
    user = models.OneToOneField(UserAccount, on_delete=models.CASCADE, verbose_name='Khách hàng')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Số lượng loại sản phẩm')
    products = models.ManyToManyField(Clothes, blank=True, verbose_name='Sản phẩm') 
    total_value = models.PositiveIntegerField(default=0, verbose_name='Tổng tiền')
    
    def __str__(self):
        return f"Cart of {self.user.username}"
    
    def total_product_type(self):
        items = CartItem.objects.filter(cart=self)
        return items.count()
    
    def _total_value(self):
        try:
            return "{:,.0f} đồng".format(self.total_value)
        except:
            return None
    _total_value.short_description = 'Tổng tiền'
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        items = CartItem.objects.filter(cart=self)
        self.quantity = items.count()
        self.total_value = sum(item.price for item in items)
        super().save(update_fields=["quantity", "total_value"])
    

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, verbose_name='Giỏ hàng')
    product = models.ForeignKey(Clothes, on_delete=models.CASCADE, verbose_name='Sản phẩm')
    quantity = models.PositiveBigIntegerField(default=1, verbose_name='Số lượng')
    price = models.PositiveIntegerField(default=0, verbose_name='Giá')
    
    def __str__(self):
        return f"{self.quantity} of {self.product.name} in {self.cart}"
    
    
    def save(self, *args, **kwargs):
        self.price = self.product.price * self.quantity
        super().save(*args, **kwargs)
        
    def _price(self):
        try:
            return "{:,.0f} đồng".format(self.price)
        except:
            return None
    _price.short_description = 'Giá'
    
    # class Meta:
    #      verbose_name_plural = 'Hệ Số Lương'
        
class PaymentMethod(models.Model):
    id = models.AutoField(primary_key=True)
    METHOD_CHOICES = [
        ('COD', 'COD'),
        ('QRPay', 'QRPay'),
    ]
    methodname = models.CharField(max_length=20, choices=METHOD_CHOICES, default='COD')
    QRcode = models.FileField(null=True, blank=True)
    
    def __str__(self):
        return self.methodname
    
class Order(models.Model):
    STATUS_CHOICES = [
        ("Chờ xác nhận", 'Chờ xác nhận'),
        ("Đang chuẩn bị", 'Đang chuẩn bị'),
        ("Đang giao", 'Đang giao'),
        ("Hoàn thành", 'Hoàn thành'),
        ("Hủy", 'Hủy'),
    ]

    tracking_number = models.CharField(max_length=10, unique=True, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Chờ xác nhận')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    hovaten = models.CharField(max_length=200, null=True, blank=True)
    sdt = models.CharField(max_length=12, null=True, blank=True)
    diachi = models.CharField(max_length=255, null=True, blank=True)
    tongtien = models.PositiveIntegerField(default=0)
    products = models.ManyToManyField(Clothes, blank=True)
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.tracking_number
    
    def save(self, *args, **kwargs):
        if not self.hovaten:
            self.hovaten = self.user.username

        if not self.tracking_number:
            self.tracking_number = self.generate_tracking_number()
        super().save(*args, **kwargs)

    def generate_tracking_number(self):
        return ''.join(random.choices(string.digits, k=10)) 
    
    def _tongtien(self):
        try:
            return "{:,.0f} đồng".format(self.tongtien)
        except:
            return None
    _tongtien.short_description = 'tongtien'
    
    def status_view(self):
        try:
            if self.status == 'Hủy':
                status_color= '#FF0000'
                status = self.status
            elif self.status == 'Hoàn thành':
                status_color= '#00FF00'
                status = self.status
            elif self.status == 'Chờ xác nhận':
                status_color= '#000000'
                status = self.status
            else:
                status_color= '#FFC000'
                status = self.status

            html= f'<span style="color: {status_color};">{status}</span>'
            return format_html(html)
        except:
            return 0
    status_view.short_description = 'Status'
    

    
class OrderItem(models.Model):
    RATING_CHOICES = (
        (1, '1'),
        (2, '2'),
        (3, '3'),
        (4, '4'),
        (5, '5'),
    )
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Clothes, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(choices=RATING_CHOICES, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    total_value = models.PositiveIntegerField(default=0)
    
    # def __str__(self):
    #     return self.order.tracking_number
    
    def clean(self):
        if self.product not in self.order.products.all():
            raise ValidationError("Sản phẩm này không thuộc đơn hàng hiện tại")
    
    def save(self, *args, **kwargs):
        self.total_value = self.product.price * self.quantity
        super().save(*args, **kwargs)
        if self.order.status == 'Hoàn thành':
            product = Clothes.objects.get(id=self.product.id)
            # product.sold = self.quantity
            product.save()
            
    def get_price(self):
        try:
            return "{:,.0f} đồng".format(self.product.price)
        except:
            return None
    get_price.short_description = 'price'
    
    def _total_value(self):
        try:
            return "{:,.0f} đồng".format(self.total_value)
        except:
            return None
    _total_value.short_description = 'total_value'
            
