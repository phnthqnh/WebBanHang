from django.contrib import admin
from clothes.models import *
from typing import Any
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib import admin
from django.conf import settings

# Register your models here.
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'role', 'email', 'is_staff', 'is_active', 'is_superuser']
    list_filter = ['role', 'is_active', 'is_staff']

    search_fields = ['username', 'email']

    # Các trường cần hiển thị trong form thêm/sửa người dùng
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )

    add_fieldsets = (
        (None, {'fields': ('username', 'email', 'role', 'password1', 'password2')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )
    
    
    def get_action(self, action):
        return super().get_action(action)
    def get_list_editable(self, request):
        if settings.ALLOW_EDIT_BY_ADMIN_ONLY and not request.user.is_superuser:
            return None
        return super().get_list_editable(request)

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        readonly_fields = ['username', 'email', 'password']

        if obj and obj != request.user:
            return readonly_fields

        return []
        
    def has_view_permission(self, request, obj=None):
        if request.user.is_staff:
            return True

    def has_add_permission(self, request):
        if request.user.is_superuser:
            return True

    
    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return False

    def has_module_permission(self, request):
        if request.user.is_staff or request.user.is_superuser:
            return True
        return False

admin.site.register(UserAccount, UserAdmin)


class ClothesAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', '_price', 'quantity_in_stock', 'status_view']
    list_filter = ['status', 'category']
    search_fields = ('name', 'status')
    def not_allow_edit(modeladmin, request, queryset):
        settings.ALLOW_EDIT_BY_ADMIN_ONLY = True
    def allow_edit(modeladmin, request, queryset):
        settings.ALLOW_EDIT_BY_ADMIN_ONLY = False
    not_allow_edit.short_description = "Not Allow Edit"
    allow_edit.short_description = 'Allow Edit'
    actions = [not_allow_edit, allow_edit]
    def get_action(self, action):
        return super().get_action(action)
    def get_list_editable(self, request):
        if settings.ALLOW_EDIT_BY_ADMIN_ONLY and not request.user.is_superuser:
            return None
        return super().get_list_editable(request)
        
    def has_view_permission(self, request, obj=None):
        if request.user.is_staff:
            return True

    def has_add_permission(self, request):
        if request.user.is_superuser:
            return True

    
    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser or request.user.is_staff:
            return True
        return False

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True

    def has_module_permission(self, request):
        if request.user.is_staff:
            return True
admin.site.register(Clothes, ClothesAdmin)
admin.site.register(Category)

class CartItemInLine(admin.TabularInline):
    model = CartItem
    extra=0
    show_change_link=True
    fields = ['cart', 'product', 'quantity', '_price']
    readonly_fields=['cart', 'product', 'quantity', '_price']
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
    
    def has_module_permission(self, request):
        if request.user.is_staff or request.user.is_superuser:
            return True
        return False
    def has_view_permission(self, request, obj=None):
        if request.user.is_staff:
            return True
        
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'quantity', '_total_value']
    list_filter = ['user']
    search_fields = ['user']
    autocomplete_fields=('products',)
    inlines = [CartItemInLine]
    fieldsets= (
        (
            None, {
            "fields": ['user', 'quantity', '_total_value']
        }),
    )
    def get_action(self, action):
        return super().get_action(action)

    def has_view_permission(self, request, obj=None):
        if request.user.is_staff:
            return True

    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_module_permission(self, request):
        return True
admin.site.register(Cart, CartAdmin)

admin.site.register(PaymentMethod)

class OrderItemInLine(admin.TabularInline):
    model = OrderItem
    extra=0
    show_change_link=True
    fields = ['order', 'product', 'get_price', 'quantity', 'rating', '_total_value']
    readonly_fields=['order', 'product', 'get_price', 'quantity', 'rating', '_total_value']
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
    def has_module_permission(self, request):
        if request.user.is_staff or request.user.is_superuser:
            return True
        return False
    def has_view_permission(self, request, obj=None):
        if request.user.is_staff:
            return True
        
        
class OrderAdmin(admin.ModelAdmin):
    list_display = ['tracking_number', 'user', '_tongtien', 'status_view']
    list_filter = ['status']
    # search_fields = ['tracking_number', 'customer']
    autocomplete_fields=('products',)
    inlines = [OrderItemInLine]
    fieldsets= (
        (
            None, {
            "fields": ['status', 'hovaten', 'sdt', 'diachi', '_tongtien', 'payment_method']
        }),
    )
    def get_action(self, action):
        return super().get_action(action)
    def get_list_editable(self, request):
        if settings.ALLOW_EDIT_BY_ADMIN_ONLY and not request.user.is_superuser:
            return None
        return super().get_list_editable(request)

    def get_readonly_fields(self, request, obj=None):
        
        if request.user.is_superuser:
            readonly_fields = list(super().get_readonly_fields(request, obj))
            return readonly_fields + ['hovaten', 'sdt', 'diachi', 'tongtien',
                                      '_tongtien', 'products', 'user']
        return super().get_readonly_fields(request, obj)
        
    def has_view_permission(self, request, obj=None):
        if request.user.is_staff:
            return True

    def has_add_permission(self, request):
        return False

    
    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        return False

    # def has_delete_permission(self, request, obj=None):
    #     return False

    def has_module_permission(self, request):
        if request.user.is_staff:
            return True
admin.site.register(Order, OrderAdmin)