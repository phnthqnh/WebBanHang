from django.urls import path
from clothes.views import *

urlpatterns = [
    path('login/', login, name='login'),
    path('register/', register, name='register'),
    path('password-reset/', request_password_reset, name='password-reset'),
    path('password-confirm/<str:uid>/<str:token>/', reset_password_confirm, name='password-confirm'),
    path('category/', get_categories, name='category'),
    path('category/create/', create_category, name='create_category'),
    path('category/<int:pk>/update/', update_category, name='update_category'),
    path('category/<int:pk>/delete/', delete_category, name='delete_category'),
    path('product/', get_clothes, name='get_clothes'),
    path('product/<int:pk>/', clothes_detail, name='clothes_detail'),
    path('product/create/', create_clothes, name='create_clothes'),
    path('product/<int:pk>/update/', update_clothes, name='update_clothes'),
    path('product/<int:pk>/delete/', delete_clothes, name='delete_clothes'),
    path('search/', search_clothes, name='search_clothes'),
    path('cart/', user_cart, name='user_cart'),
    path('add_to_cart/', add_to_cart, name='add_to_cart'),
    path('remove_from_cart/', remove_from_cart, name='remove_from_cart'),
    path('change_product_quantity/', change_product_quantity, name='change_product_quantity'),
    path('user_orders/', user_orders, name='user_orders'),
    path('create_order/', create_order, name='create_order'),
    path('cancel_order/<int:pk>/', cancel_order, name='cancel_order'),
    path('rate_product/<int:pk>/', rate_product, name='rate_product'),
]
