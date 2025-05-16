from rest_framework import serializers
from .models import *

class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(max_length=50, write_only=True)
    
    def validate(self, data):
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return serializers.ValidationError('Username và mật khẩu là bắt buộc.')

        return data
    
class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    username = serializers.CharField()

    def validate_email(self, value):
        if not UserAccount.objects.filter(email=value).exists():
            raise serializers.ValidationError("Không tìm thấy người dùng với email này.")
        return value

class PasswordResetConfirmSerializer(serializers.Serializer):
    # new_password = serializers.CharField(min_length=8, write_only=True)
    new_password = serializers.CharField(max_length=50, write_only=True)
    
class RegisterSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserAccount
        fields = ['username', 'email', 'password']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def create(self, validated_data):
        user = UserAccount.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data['email'],
        )
        user.role = 'user'
        user.save()
        return user
    
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAccount
        fields = ['username', 'email']
        
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'
        
class ClothesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clothes
        fields = '__all__'

class CartItemSerializer(serializers.ModelSerializer):
    product = ClothesSerializer()  # Serialize thông tin sản phẩm
    class Meta:
        model = CartItem
        fields = '__all__'
        
class CartSerializer(serializers.ModelSerializer):
    products = CartItemSerializer(source='cartitem_set', many=True, read_only=True)
    class Meta:
        model = Cart
        fields = ['id', 'user', 'quantity', 'total_value', 'products',
        ]
        
class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = '__all__'
        
class OrderItemSerializer(serializers.ModelSerializer):
    product = ClothesSerializer()

    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'total_value']

class OrderSerializer(serializers.ModelSerializer):
    products = OrderItemSerializer(source='orderitem_set', many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'tracking_number', 'status', 'created_at', 'updated_at',
                  'hovaten', 'sdt', 'diachi', 'tongtien', 'products']