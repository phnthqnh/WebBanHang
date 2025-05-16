from rest_framework.test import APITestCase, APIClient
from django.urls import reverse
from clothes.models import *

class ClothesTestCase(APITestCase):
    def setUp(self):
        # Tạo user admin
        self.admin_user = UserAccount.objects.create_user(
            username='admin',
            email='admin@gmail.com',
            password='admin123',
            role='admin'
        )
        self.client = APIClient()

        # Đăng nhập
        login_url = reverse('login')  # tên url login trong urls.py
        response = self.client.post(login_url, {
            "username": "admin",
            "password": "admin123"
        }, format='json')
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        # Tạo category để gán vào clothes
        self.category = Category.objects.create(name="Áo")

    def test_create_clothes(self):
        url = reverse('create_clothes')  # Tên đường dẫn URL
        data = {
            "name": "Áo thun",
            "price": 150000,
            "image": "http://example.com/image.jpg",
            "description": "Áo thun nam tay ngắn",
            "status": "còn hàng",
            "category": self.category.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Clothes.objects.count(), 1)
        self.assertEqual(Clothes.objects.get().name, "Áo thun")

    def test_get_clothes_list(self):
        Clothes.objects.create(
            name="Áo khoác", price=200000, image="http://img.com/1.jpg",
            description="Áo khoác mùa đông", status="còn hàng", category=self.category
        )
        url = reverse('get_clothes')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data), 1)
    
    def test_clothes_detail(self):
        clothes = Clothes.objects.create(
            name="Áo khoác", price=200000, image="http://img.com/1.jpg",
            description="Áo khoác mùa đông", status="còn hàng", category=self.category
        )
        url = reverse('clothes_detail', kwargs={'pk': clothes.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data), 1)

    def test_clothes_detail_not_found(self):
        url = reverse('clothes_detail', kwargs={'pk': 9999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data.get('error'), 'Sản phẩm không tồn tại')


    def test_update_clothes(self):
        clothes = Clothes.objects.create(
            name="Áo sơ mi", price=180000, image="http://img.com/shirt.jpg",
            description="Áo sơ mi trắng", status="còn hàng", category=self.category
        )
        url = reverse('update_clothes', kwargs={'pk': clothes.id})
        response = self.client.put(url, {
            "name": "Áo sơ mi tay dài",
            "price": 190000,
            "image": clothes.image,
            "description": clothes.description,
            "status": clothes.status,
            "category": self.category.id
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Clothes.objects.get(id=clothes.id).name, "Áo sơ mi tay dài")

    def test_delete_clothes(self):
        clothes = Clothes.objects.create(
            name="Đồ ngủ", price=100000, image="http://img.com/sleep.jpg",
            description="Bộ đồ ngủ", status="còn hàng", category=self.category
        )
        url = reverse('delete_clothes', kwargs={'pk': clothes.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Clothes.objects.filter(id=clothes.id).exists())


class ClothesPermissionUserTest(APITestCase):
    def setUp(self):
        # Tạo user thường
        self.normal_user = UserAccount.objects.create_user(
            email='user@gmail.com',
            username='user',
            password='user123',
            role='user'
        )
        self.client = APIClient()

        # Đăng nhập để lấy token
        login_url = reverse('login')
        response = self.client.post(login_url, {
            "username": "user",
            "password": "user123"
        }, format='json')
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        # Tạo category để dùng trong test
        self.category = Category.objects.create(name="Đồ mặc nhà")

    def test_user_cannot_create_clothes(self):
        url = reverse('create_clothes')
        data = {
            "name": "Áo ba lỗ",
            "price": 120000,
            "image": "http://img.com/ba_lo.jpg",
            "description": "Áo ba lỗ mùa hè",
            "status": "còn hàng",
            "category": self.category.id
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 403)

    def test_user_cannot_update_clothes(self):
        clothes = Clothes.objects.create(
            name="Đồ ngủ nữ", price=100000,
            image="http://img.com/pjs.jpg",
            description="Đồ ngủ mùa đông",
            status="còn hàng", category=self.category
        )
        url = reverse('update_clothes', kwargs={'pk': clothes.id})
        data = {
            "name": "Đồ ngủ nữ dài tay",
            "price": 105000,
            "image": clothes.image,
            "description": clothes.description,
            "status": clothes.status,
            "category": self.category.id
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, 403)

    def test_user_cannot_delete_clothes(self):
        clothes = Clothes.objects.create(
            name="Bộ đồ thể thao", price=150000,
            image="http://img.com/sport.jpg",
            description="Thể thao nam",
            status="còn hàng", category=self.category
        )
        url = reverse('delete_clothes', kwargs={'pk': clothes.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 403)

    def test_user_can_view_clothes_list(self):
        Clothes.objects.create(
            name="Áo hoodie", price=200000,
            image="http://img.com/hoodie.jpg",
            description="Áo hoodie ấm",
            status="còn hàng", category=self.category
        )
        url = reverse('get_clothes')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data), 1)