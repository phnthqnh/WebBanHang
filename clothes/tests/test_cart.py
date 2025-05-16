from rest_framework.test import APITestCase, APIClient
from django.urls import reverse
from clothes.models import *

class UserCartViewTest(APITestCase):
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

        self.cart = Cart.objects.get(user=self.user)
        
        self.product = Clothes.objects.create(
            name='Áo sơ mi',
            price=100000,
            quantity_in_stock=10
        )

        self.cart_item = CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=1
        )
        self.cart.products.add(self.product)
        self.cart.total_value = self.cart_item.quantity * self.product.price
        self.cart.quantity = self.cart.total_product_type()
        self.cart.save()

    def test_user_can_view_own_cart(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        url = reverse('user_cart')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn('carts', response.data)
        self.assertEqual(len(response.data['carts']), 1)
        self.assertEqual(response.data['carts'][0]['id'], self.cart.id)

    def test_unauthenticated_user_cannot_view_cart(self):
        url = reverse('user_cart')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)
        
    def test_add_to_cart_successfully(self):
        url = reverse('add_to_cart')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)

        payload = {
            'clothes_id': self.product.id,
            'quantity': 1
        }

        response = self.client.post(url, payload, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['message'], 'Thêm sản phẩm vào giỏ hàng thành công')
        self.assertEqual(response.data['product']['name'], self.product.name)
        self.assertEqual(response.data['product']['quantity'], 2)

        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.quantity, 1)
        self.assertEqual(cart.total_value, self.product.price * 2)

    def test_add_to_cart_without_clothes_id(self):
        url = reverse('add_to_cart')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)

        payload = {
            'quantity': 1
        }

        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'], 'Clothes ID không được để trống')

    def test_add_to_cart_insufficient_stock(self):
        url = reverse('add_to_cart')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)

        payload = {
            'clothes_id': self.product.id,
            'quantity': 100
        }

        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'], 'Sản phẩm trong kho không đủ')

    def test_unauthenticated_user_cannot_add_to_cart(self):
        url = reverse('add_to_cart')
        payload = {
            'clothes_id': self.product.id,
            'quantity': 1
        }

        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, 401)
        
    def test_remove_from_cart_successfully(self):
        url = reverse('remove_from_cart')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        payload = {
            'clothes_id': self.product.id
        }
        response = self.client.post(url, payload, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['message'], 'Xóa sản phẩm khỏi giỏ hàng thành công')
        self.assertEqual(response.data['product']['name'], self.product.name)

        self.assertFalse(CartItem.objects.filter(cart=self.cart, product=self.product).exists())
        self.assertNotIn(self.product, self.cart.products.all())
        self.cart.refresh_from_db()
        self.assertEqual(self.cart.total_value, 0)
        self.assertEqual(self.cart.quantity, 0)

    def test_remove_from_cart_without_clothes_id(self):
        url = reverse('remove_from_cart')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        payload = {}
        response = self.client.post(url, payload, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'], 'Clothes ID không được để trống')

    def test_remove_nonexistent_cart_item(self):
        url = reverse('remove_from_cart')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        CartItem.objects.all().delete()
        payload = {
            'clothes_id': self.product.id
        }
        response = self.client.post(url, payload, format='json')

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['error'], 'Không có sản phẩm nào trong giỏ hàng')

    def test_unauthenticated_user_cannot_remove(self):
        url = reverse('remove_from_cart')
        payload = {
            'clothes_id': self.product.id
        }
        response = self.client.post(url, payload, format='json')

        self.assertEqual(response.status_code, 401)

    def test_change_quantity_successfully(self):
        url = reverse('change_product_quantity')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        payload = {
            'clothes_id': self.product.id,
            'quantity': 5
        }
        response = self.client.post(url, payload, format='json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['message'], 'Số lượng sản phẩm đã được thay đổi thành công')
        self.assertEqual(response.data['product']['name'], self.product.name)
        self.assertEqual(response.data['product']['quantity'], 5)

        self.cart_item.refresh_from_db()
        self.assertEqual(self.cart_item.quantity, 5)

    def test_change_quantity_without_clothes_id(self):
        url = reverse('change_product_quantity')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        payload = {
            'quantity': 5
        }
        response = self.client.post(url, payload, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error'], 'Clothes ID và số lượng không được để trống')

    def test_change_quantity_item_not_in_cart(self):
        url = reverse('change_product_quantity')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        CartItem.objects.all().delete()
        payload = {
            'clothes_id': self.product.id,
            'quantity': 2
        }
        response = self.client.post(url, payload, format='json')

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data['error'], 'Không có sản phẩm nào trong giỏ hàng')

    def test_unauthenticated_user_cannot_change_quantity(self):
        url = reverse('change_product_quantity')
        payload = {
            'clothes_id': self.product.id,
            'quantity': 4
        }
        response = self.client.post(url, payload, format='json')

        self.assertEqual(response.status_code, 401)