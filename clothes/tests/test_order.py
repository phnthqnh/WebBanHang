from rest_framework.test import APITestCase, APIClient
from django.urls import reverse
from clothes.models import *

class UserOrdersViewTest(APITestCase):
    def setUp(self):
        self.user = UserAccount.objects.create_user(
            email='user@example.com',
            username='testuser',
            password='testpassword',
            role='user'
        )
        self.client = APIClient()
        self.login_url = reverse('login')
        response = self.client.post(self.login_url, {
            "username": "testuser",
            "password": "testpassword"
        }, format='json')
        self.access_token = response.data['access']

        self.payment_method = PaymentMethod.objects.create(methodname='COD')

        Order.objects.create(
            user=self.user,
            payment_method=self.payment_method,
            tongtien=100000,
            hovaten='Nguyen Van A',
            sdt='0123456789',
            diachi='Hanoi'
        )
        Order.objects.create(
            user=self.user,
            payment_method=self.payment_method,
            tongtien=200000,
            hovaten='Nguyen Van B',
            sdt='0987654321',
            diachi='HCM'
        )

        

    def test_authenticated_user_can_view_orders(self):
        url = reverse('user_orders')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn('orders', response.data)
        self.assertEqual(len(response.data['orders']), 2)
        
    def test_unauthenticated_user_cannot_view_orders(self):
        url = reverse('user_orders')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)


class CreateOrderViewTest(APITestCase):
    def setUp(self):
        # Tạo user
        self.user = UserAccount.objects.create_user(
            email='user@example.com',
            username='testuser',
            password='testpassword',
            role='user'
        )
        self.login_url = reverse('login')
        response = self.client.post(self.login_url, {
            "username": "testuser",
            "password": "testpassword"
        }, format='json')
        self.access_token = response.data['access']

        self.payment_method = PaymentMethod.objects.create(methodname='COD')

        self.product1 = Clothes.objects.create(name='Áo 1', price=100000, quantity_in_stock=10)
        self.product2 = Clothes.objects.create(name='Quần 1', price=150000, quantity_in_stock=5)

        self.cart = Cart.objects.get(user=self.user)
        CartItem.objects.create(cart=self.cart, product=self.product1, quantity=2)
        CartItem.objects.create(cart=self.cart, product=self.product2, quantity=1)

        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        self.url = reverse('create_order')

    def test_create_order_from_cart_success(self):
        data = {
            "source": "cart",
            "payment_method": self.payment_method.id,
            "products": [
                {"id": self.product1.id, "quantity": 2},
                {"id": self.product2.id, "quantity": 1}
            ],
            "userInfo": {
                "hovaten": "Nguyen Van A",
                "sdt": "0123456789",
                "diachi": "Ha Noi"
            }
        }

        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Order.objects.filter(user=self.user).count(), 1)
        order = Order.objects.get(user=self.user)
        self.assertEqual(order.tongtien, 2*100000 + 1*150000)
        self.assertEqual(order.hovaten, "Nguyen Van A")
        self.product1.refresh_from_db()
        self.product2.refresh_from_db()
        self.assertEqual(self.product1.quantity_in_stock, 8)
        self.assertEqual(self.product2.quantity_in_stock, 4)
        self.assertFalse(CartItem.objects.filter(cart=self.cart, product=self.product1).exists())
        self.assertFalse(CartItem.objects.filter(cart=self.cart, product=self.product2).exists())

    def test_create_order_from_detail_success(self):
        data = {
            "source": "detail",
            "payment_method": self.payment_method.id,
            "products": [
                {"id": self.product1.id, "quantity": 3}
            ],
            "userInfo": {
                "hovaten": "Nguyen Van B",
                "sdt": "0987654321",
                "diachi": "HCM"
            }
        }

        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, 201)
        order = Order.objects.get(user=self.user)
        self.assertEqual(order.tongtien, 3*100000)
        self.assertEqual(order.hovaten, "Nguyen Van B")
        self.assertTrue(CartItem.objects.filter(cart=self.cart, product=self.product1).exists())

    def test_create_order_invalid_source(self):
        data = {
            "source": "invalid_source",
            "payment_method": self.payment_method.id,
            "products": [{"id": self.product1.id, "quantity": 1}],
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('Nguồn mua hàng không hợp lệ', response.data.get('error', ''))

    def test_create_order_product_not_in_cart_when_source_cart(self):
        product_not_in_cart = Clothes.objects.create(name='Giày', price=500000, quantity_in_stock=5)
        data = {
            "source": "cart",
            "payment_method": self.payment_method.id,
            "products": [{"id": product_not_in_cart.id, "quantity": 1}],
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('không có trong giỏ hàng', response.data.get('error', '').lower())

    def test_create_order_product_out_of_stock(self):
        data = {
            "source": "detail",
            "payment_method": self.payment_method.id,
            "products": [{"id": self.product1.id, "quantity": 1000}],
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('không đủ số lượng trong kho', response.data.get('error', '').lower())
        
        
class CancelOrderViewTest(APITestCase):
    def setUp(self):
        self.user = UserAccount.objects.create_user(
            email='user1@example.com', username='user1', password='user1', role='user'
        )
        self.other_user = UserAccount.objects.create_user(
            email='user2@example.com', username='user2', password='user2', role='user'
        )
        self.payment_method = PaymentMethod.objects.create(methodname='COD')
        
        self.order = Order.objects.create(
            user=self.user,
            tongtien=200000,
            hovaten='Nguyen Van A',
            sdt='0123456789',
            diachi='Hanoi',
            status='Chờ xác nhận',
            payment_method=self.payment_method
        )

        self.client = APIClient()
        self.login_url = reverse('login')
        response = self.client.post(self.login_url, {
            "username": "user1",
            "password": "user1"
        }, format='json')
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(self.token))

        self.cancel_url = reverse('cancel_order', kwargs={'pk': self.order.pk})

    def test_cancel_order_success(self):
        response = self.client.put(self.cancel_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['message'], 'Đơn hàng đã hủy thành công.')
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, 'Hủy')

    def test_cancel_order_not_owner(self):
        response = self.client.post(self.login_url, {
            "username": "user2",
            "password": "user2"
        }, format='json')
        self.token_other = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(self.token_other))
        response = self.client.put(self.cancel_url)
        self.assertEqual(response.status_code, 403)
        self.assertIn('không có quyền', response.data['error'])

    def test_cancel_order_not_pending(self):
        self.order.status = 'Đang giao'
        self.order.save()
        response = self.client.put(self.cancel_url)
        self.assertEqual(response.status_code, 400)
        self.assertIn('không thể hủy', response.data['error'].lower())

    def test_cancel_order_not_found(self):
        invalid_url = reverse('cancel_order', kwargs={'pk': 9999})
        response = self.client.put(invalid_url)
        self.assertEqual(response.status_code, 404)
        self.assertIn('không tồn tại', response.data['error'])

    def test_cancel_order_unauthenticated(self):
        self.client.credentials()
        response = self.client.put(self.cancel_url)
        self.assertEqual(response.status_code, 401)
        self.assertIn('credentials', response.data.get('detail', '').lower())
        
        
class RateProductTest(APITestCase):
    def setUp(self):
        self.user = UserAccount.objects.create_user(
            email="user1@example.com", username="user1", password="user1", role='user'
        )
        self.other_user = UserAccount.objects.create_user(
            email="user2@example.com", username="user2", password="user2", role='user'
        )
        self.payment = PaymentMethod.objects.create(methodname="COD")
        self.product = Clothes.objects.create(name="Áo sơ mi", price=200000, quantity_in_stock=50)
        self.order = Order.objects.create(
            user=self.user,
            tongtien=200000,
            hovaten="Nguyen Van A",
            sdt="0123456789",
            diachi="Hà Nội",
            status="Hoàn thành",
            payment_method=self.payment
        )
        self.order_item = OrderItem.objects.create(
            order=self.order, product=self.product, quantity=1, total_value=200000
        )
        
        self.client = APIClient()
        self.login_url = reverse('login')
        response = self.client.post(self.login_url, {
            "username": "user1",
            "password": "user1"
        }, format='json')
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(self.token))
        self.url = reverse('rate_product', kwargs={'pk': self.order.pk})

    def test_successful_rating(self):
        response = self.client.post(self.url, data={
            'product_id': self.product.id,
            'rating': 4
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(int(response.data['đánh giá']), 4)
        self.order_item.refresh_from_db()
        self.assertEqual(self.order_item.rating, 4)

    def test_rating_twice_should_fail(self):
        self.order_item.rating = 5
        self.order_item.save()
        response = self.client.post(self.url, data={
            'product_id': self.product.id,
            'rating': 4
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('đã đánh giá', response.data['error'])

    def test_rating_order_not_owned(self):
        response = self.client.post(self.login_url, {
            "username": "user2",
            "password": "user2"
        }, format='json')
        self.token_other = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(self.token_other))
        response = self.client.post(self.url, data={
            'product_id': self.product.id,
            'rating': 5
        })
        self.assertEqual(response.status_code, 403)
        self.assertIn('không có quyền', response.data['error'])

    def test_rating_on_uncompleted_order(self):
        self.order.status = "Đang giao"
        self.order.save()
        response = self.client.post(self.url, data={
            'product_id': self.product.id,
            'rating': 4
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('không thể đánh giá', response.data['error'])

    def test_rating_product_not_in_order(self):
        other_product = Clothes.objects.create(name="Quần jeans", price=300000, quantity_in_stock=40)
        response = self.client.post(self.url, data={
            'product_id': other_product.id,
            'rating': 4
        })
        self.assertEqual(response.status_code, 404)
        self.assertIn('không nằm trong đơn hàng', response.data['error'])

    def test_rating_out_of_bounds(self):
        response = self.client.post(self.url, data={
            'product_id': self.product.id,
            'rating': 6
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('trong khoảng từ 1 đến 5', response.data['error'])

    def test_order_does_not_exist(self):
        url = reverse('rate_product', kwargs={'pk': 999})
        response = self.client.post(url, data={
            'product_id': self.product.id,
            'rating': 5
        })
        self.assertEqual(response.status_code, 404)
        self.assertIn('không tồn tại', response.data['error'])

    def test_unauthenticated_user(self):
        self.client.credentials()  # Clear auth
        response = self.client.post(self.url, data={
            'product_id': self.product.id,
            'rating': 5
        })
        self.assertEqual(response.status_code, 401)
        self.assertIn('credentials', response.data.get('detail', '').lower())