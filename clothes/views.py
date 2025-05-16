from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .permissions import IsAdmin, IsUser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.shortcuts import render, get_object_or_404
from .models import *
from .serializers import *
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.db import transaction


# Create your views here.
@api_view(['POST'])
def login(request):
    
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        try:
            user = UserAccount.objects.get(username=username)
            if user.check_password(password):
                # Tạo token nếu mật khẩu đúng
                refresh = RefreshToken.for_user(user)
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'userID': user.id,
                    'email': user.email,
                    'username': user.username,
                    'role': user.role
                }, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Mật khẩu không chính xác.'}, status=status.HTTP_400_BAD_REQUEST)
        except UserAccount.DoesNotExist:
            return Response({'error': 'Người dùng không tồn tại.'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def register(request):
    password = request.data.get('password')
    confirm_password = request.data.get('confirm_password')

    if password != confirm_password:
        return Response({'error': 'Mật khẩu xác nhận không khớp.'}, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Đăng ký thành công!"}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

token_generator = PasswordResetTokenGenerator()


@api_view(['POST'])
def request_password_reset(request):
    serializer = PasswordResetRequestSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        try:
            user = UserAccount.objects.get(email=email)
        except UserAccount.DoesNotExist:
            return Response({'error': 'Không tìm thấy người dùng.'}, status=404)

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = token_generator.make_token(user)

        reset_link = f"http://localhost:8001/clothes/password-confirm/{uid}/{token}/"

        html = render_to_string('email_template.html', {'username': user.username,
                                                        'reset_link': reset_link})
        send_mail(
            subject='Yêu cầu đặt lại mật khẩu',
            message=f'Xin chào {user.username},\n\n'
                    f'Vui lòng nhấn vào liên kết sau để đặt lại mật khẩu:\n{reset_link}\n\n'
                    'Nếu bạn không yêu cầu điều này, hãy bỏ qua email này.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
            html_message=html
        )

        return Response({"message": "Email đặt lại mật khẩu đã được gửi."}, status=200)
    return Response(serializer.errors, status=400)


@api_view(['POST'])
def reset_password_confirm(request, uid, token):
    serializer = PasswordResetConfirmSerializer(data=request.data)
    if serializer.is_valid():
        new_password = serializer.validated_data['new_password']

        try:
            uid_decoded = force_str(urlsafe_base64_decode(uid))
            user = UserAccount.objects.get(pk=uid_decoded)
        except (UserAccount.DoesNotExist, ValueError, TypeError):
            return Response({"error": "Người dùng không hợp lệ."}, status=status.HTTP_400_BAD_REQUEST)

        if token_generator.check_token(user, token):
            user.set_password(new_password)
            user.save()
            return Response({"message": "Mật khẩu đã được đặt lại thành công."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Token không hợp lệ hoặc đã hết hạn."}, status=status.HTTP_400_BAD_REQUEST)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_categories(request):
    try: 
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)
    except Category.DoesNotExist:
        return Response({'error': 'Không tìm thấy danh mục.'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdmin])
def create_category(request):
    serializer = CategorySerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes([IsAuthenticated, IsAdmin])
def update_category(request, pk):
    try:
        category = Category.objects.get(pk=pk)
    except Category.DoesNotExist:
        return Response({'error': 'Danh mục không tồn tại.'}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = CategorySerializer(category, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsAdmin])
def delete_category(request, pk):
    try:
        category = Category.objects.get(pk=pk)
        category.delete()
        return Response({'message': 'Danh mục đã được xóa thành công.'}, status=status.HTTP_204_NO_CONTENT)
    except Category.DoesNotExist:
        return Response({'error': 'Danh mục không tồn tại.'}, status=status.HTTP_404_NOT_FOUND)
    
@api_view(['GET'])
def get_clothes(request):
    try: 
        clothes = Clothes.objects.all()
        serializer = ClothesSerializer(clothes, many=True)
        return Response(serializer.data)
    except Category.DoesNotExist:
        return Response({'error': 'Không tìm thấy sản phẩm.'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def clothes_detail(request, pk):
    try:
        product = Clothes.objects.get(pk = pk)
        serializers = ClothesSerializer(product)
        return Response(serializers.data)
    except Clothes.DoesNotExist:
        return Response({'error': 'Sản phẩm không tồn tại'}, status=404)
    
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdmin])
def create_clothes(request):
    serializer = ClothesSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes([IsAuthenticated, IsAdmin])
def update_clothes(request, pk):
    try:
        clothes = Clothes.objects.get(pk=pk)
    except Clothes.DoesNotExist:
        return Response({'error': 'Sản phẩm không tồn tại.'}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = ClothesSerializer(clothes, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsAdmin])
def delete_clothes(request, pk):
    try:
        clothes = Clothes.objects.get(pk=pk)
        clothes.delete()
        return Response({'message': 'Sản phẩm đã được xóa thành công.'}, status=status.HTTP_204_NO_CONTENT)
    except Category.DoesNotExist:
        return Response({'error': 'Sản phẩm không tồn tại.'}, status=status.HTTP_404_NOT_FOUND)
        
@api_view(['GET'])
def search_clothes(request):
    keyword = request.query_params.get('q', '')
    clothes = Clothes.objects.filter(name__icontains=keyword)
    serializer = ClothesSerializer(clothes, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsUser])
def user_cart(request):
    try:
        
        cart = Cart.objects.filter(user=request.user).order_by('id')

        serializer = CartSerializer(cart, many=True)
        
        return Response({"carts": serializer.data}, status=status.HTTP_200_OK)
    except UserAccount.DoesNotExist:
        return Response({'error': f'Người dùng {request.user} không có giỏ hàng'}, 
                        status=status.HTTP_400_BAD_REQUEST)
    except AttributeError:
        return Response(
            {"detail": "Không tìm thấy thông tin khách hàng."},
            status=status.HTTP_400_BAD_REQUEST
        )

# {
#     "clothes_id": 1,
#     "quantity": 2
# }
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsUser])
def add_to_cart(request):
    try:
        
        cart, created = Cart.objects.get_or_create(user=request.user)
        
        data = request.data
        clothes_id = data.get('clothes_id')
        quantity = data.get('quantity', 1)
        
        if not clothes_id:
            return Response({'error': 'Clothes ID không được để trống'}, status=status.HTTP_400_BAD_REQUEST)

        product = get_object_or_404(Clothes, id=clothes_id)
        
        if product.quantity_in_stock < quantity:
            return Response({'error': 'Sản phẩm trong kho không đủ'}, status=status.HTTP_400_BAD_REQUEST)
        
        cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)
        
        if not item_created:
            cart_item.quantity += int(quantity)
        else:
            cart_item.quantity = int(quantity)
        cart_item.save()
        
        
        cart.save()
        
        if product not in cart.products.all():
            cart.products.add(product)
        
        cart.total_value = sum(item.quantity * item.product.price for item in CartItem.objects.filter(cart=cart))
        cart.quantity = cart.total_product_type()
        cart.save()

        
        return Response({
            'message': 'Thêm sản phẩm vào giỏ hàng thành công',
            'product': {
                'name': product.name,
                'quantity': cart_item.quantity
            }
        }, status=status.HTTP_200_OK)

    except Clothes.DoesNotExist:
        return Response({'error': 'Sản phẩm không tồn tại'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def remove_from_cart(request):
    try:

        cart = get_object_or_404(Cart, user=request.user)

        data = request.data
        clothes_id = data.get('clothes_id')

        if not clothes_id:
            return Response({'error': 'Clothes ID không được để trống'}, status=status.HTTP_400_BAD_REQUEST)

        product = get_object_or_404(Clothes, id=clothes_id)

        cart_item = CartItem.objects.filter(cart=cart, product=product).first()
        if not cart_item:
            return Response({'error': 'Không có sản phẩm nào trong giỏ hàng'}, status=status.HTTP_404_NOT_FOUND)

        cart_item.delete()

        if product in cart.products.all():
            cart.products.remove(product)

        cart.total_value = sum(item.quantity * item.product.price for item in CartItem.objects.filter(cart=cart))
        cart.quantity = cart.total_product_type()
        cart.save()

        return Response({
            'message': 'Xóa sản phẩm khỏi giỏ hàng thành công',
            'product': {
                'name': product.name
            }
        }, status=status.HTTP_200_OK)

    except Clothes.DoesNotExist:
        return Response({'error': 'Sản phẩm không tồn tại'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsUser])
def change_product_quantity(request):
    try:
        cart = get_object_or_404(Cart, user = request.user)


        data = request.data
        clothes_id = data.get('clothes_id')
        new_quantity = data.get('quantity')

        if not clothes_id or not new_quantity:
            return Response({'error': 'Clothes ID và số lượng không được để trống'}, 
                            status=status.HTTP_400_BAD_REQUEST)

        product = get_object_or_404(Clothes, id=clothes_id)

        cart_item = CartItem.objects.filter(cart=cart, product=product).first()
        if not cart_item:
            return Response({'error': 'Không có sản phẩm nào trong giỏ hàng'}, status=status.HTTP_404_NOT_FOUND)

        if cart_item:
            cart_item.quantity = int(new_quantity)
            cart_item.save()
            cart.save()
            
            total_product_type = cart.total_product_type()

            return Response({
                'message': 'Số lượng sản phẩm đã được thay đổi thành công',
                'total_product_type': total_product_type,
                'product': {
                    'name': product.name,
                    'quantity': cart_item.quantity
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Giỏ hàng không có sản phẩm'}, status=status.HTTP_404_NOT_FOUND)
        
    except Clothes.DoesNotExist:
        return Response({'error': 'Sản phẩm không tồn tại'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_orders(request):
    try:
        orders = Order.objects.filter(user=request.user).order_by('-created_at')

        serializer = OrderSerializer(orders, many=True)
        return Response({"orders": serializer.data}, status=status.HTTP_200_OK)
    except AttributeError:
        return Response(
            {"detail": "Không tìm thấy thông tin khách hàng."},
            status=status.HTTP_400_BAD_REQUEST
        )
        
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsUser])
@transaction.atomic
def create_order(request):
    try:
        user = request.user
        cart = Cart.objects.get(user=user)
        data = request.data
        products_data = data.get('products', [])
        source = data.get('source')
        payment_method_id = data.get('payment_method')
        user_info = data.get('userInfo', {})

        if not source or source not in ['cart', 'detail']:
            return Response({'error': 'Nguồn mua hàng không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            payment = PaymentMethod.objects.get(id=payment_method_id)
        except PaymentMethod.DoesNotExist:
            return Response({'error': 'Phương thức thanh toán không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)

        if not products_data:
            return Response({'error': 'Danh sách sản phẩm không được để trống.'}, 
                            status=status.HTTP_400_BAD_REQUEST)

        if source == 'detail' and len(products_data) > 1:
            return Response({'error': 'Chỉ được mua 1 sản phẩm khi đặt hàng từ trang chi tiết.'}, 
                            status=status.HTTP_400_BAD_REQUEST)

        total_price = 0.0
        order_items = []

        for item_data in products_data:

            product_id = item_data.get('id')
            quantity = item_data.get('quantity', 1)

            if not product_id:
                return Response({'error': 'Sản phẩm không có ID.'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                product = Clothes.objects.select_for_update().get(id=product_id)
                
                if product.quantity_in_stock < quantity:
                    return Response({'error': f"Sản phẩm '{product.name}' không đủ số lượng trong kho."},
                                    status=status.HTTP_400_BAD_REQUEST)
                
                if source == 'cart':
                    if not CartItem.objects.filter(cart__user=user, product=product).exists():
                        return Response({'error': f"Sản phẩm '{product.name}' không có trong giỏ hàng."},
                                        status=status.HTTP_400_BAD_REQUEST)
                product.quantity_in_stock -= quantity
                product.save()
                item_total = product.price * quantity
                total_price += item_total
                
                order_items.append({
                    'product': product,
                    'quantity': quantity,
                    'total_value': product.price * quantity
                })
                
            except Clothes.DoesNotExist:
                return Response({'error': f'Sản phẩm với ID {product_id} không tồn tại.'}, 
                                status=status.HTTP_400_BAD_REQUEST)

        hoVaTen = user_info.get('hovaten')
        SDT = user_info.get('sdt')
        diaChi = user_info.get('diachi')

        order_new = Order.objects.create(
            user=user,
            tongtien=total_price,
            hovaten = hoVaTen,
            sdt = SDT,
            diachi = diaChi,
            status='Chờ xác nhận',
            payment_method=payment
        )
        
        for item in order_items:
            OrderItem.objects.create(
                order=order_new,
                product=item['product'],
                quantity=item['quantity'],
                total_value=item['total_value']
            )
            if item['product'] not in order_new.products.all():
                order_new.products.add(item['product'])

            if source == 'cart':
                CartItem.objects.filter(cart__user=user, product=item['product']).delete()
                cart.save()
        
        serializer = OrderSerializer(order_new)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    
@api_view(['PUT'])
@permission_classes([IsAuthenticated, IsUser])
def cancel_order(request, pk):
    try:
        order = Order.objects.get(pk=pk)
        if order.user != request.user:
            return Response({'error': 'Bạn không có quyền hủy đơn hàng này.'}, status=status.HTTP_403_FORBIDDEN)
        if order.status != 'Chờ xác nhận':
            return Response({'error': 'Đơn hàng không thể hủy bây giờ.'}, status=status.HTTP_400_BAD_REQUEST)
        order.status = 'Hủy'
        order.save()
        return Response({'message': 'Đơn hàng đã hủy thành công.'}, status=status.HTTP_200_OK)
    except Order.DoesNotExist:
        return Response({'error': 'Đơn hàng không tồn tại.'}, status=status.HTTP_404_NOT_FOUND)
    except AttributeError:
        return Response({"detail": "Không tìm thấy thông tin khách hàng."}, status=status.HTTP_400_BAD_REQUEST)   
    

@api_view(['POST'])
@permission_classes([IsAuthenticated, IsUser])
def rate_product(request, pk):
    try:
        order = Order.objects.get(pk=pk)
        if order.user!= request.user:
            return Response({'error': 'Bạn không có quyền đánh giá đơn hàng này.'}, status=status.HTTP_403_FORBIDDEN)
        if order.status!= 'Hoàn thành':
            return Response({'error': 'Đơn hàng không thể đánh giá bây giờ.'}, status=status.HTTP_400_BAD_REQUEST)
        product_id = request.data.get('product_id')
        product = Clothes.objects.get(id=product_id)
        rating = request.data.get('rating')
        user = UserAccount.objects.get(id = request.user.id)
        if int(rating) < 1 or int(rating) > 5:
            return Response({'error': 'Đánh giá phải trong khoảng từ 1 đến 5.'}, status=status.HTTP_400_BAD_REQUEST)
        orderitem = OrderItem.objects.get(order=order, product=product)
        if orderitem.rating is not None:
            return Response({'error': 'Bạn đã đánh giá sản phẩm này rồi.'}, status=status.HTTP_400_BAD_REQUEST)
        orderitem.rating = rating
        orderitem.save()
        
        return Response({
                    'message': 'Đánh giá đơn hàng thành công',
                    'người đánh giá': user.username,
                    'sản phẩm' : product.name,
                    'đánh giá' : rating
                }, status=status.HTTP_200_OK)
    except Order.DoesNotExist:
        return Response({'error': 'Đơn hàng không tồn tại.'}, status=status.HTTP_404_NOT_FOUND)
    except Clothes.DoesNotExist:
        return Response({'error': 'Sản phẩm không tồn tại.'}, status=status.HTTP_404_NOT_FOUND)
    except OrderItem.DoesNotExist:
        return Response({'error': 'Sản phẩm không nằm trong đơn hàng này.'}, status=status.HTTP_404_NOT_FOUND)
    except AttributeError:
        return Response(
            {"detail": "Không tìm thấy thông tin khách hàng."},
            status=status.HTTP_400_BAD_REQUEST
        )