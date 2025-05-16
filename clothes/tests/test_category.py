from rest_framework.test import APITestCase, APIClient
from django.urls import reverse
from clothes.models import *

class BaseCategoryTestCase(APITestCase):
    def setUp(self):
        self.admin_user = UserAccount.objects.create_user(
            email='admin1@gmail.com',
            username='admin1',
            password='admin1',
            role='admin'
        )
        self.client = APIClient()
        self.login_url = reverse('login')
        self.category_url = reverse('create_category')

        response = self.client.post(self.login_url, {
            "username": "admin1",
            "password": "admin1"
        }, format='json')
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

class CategoryCreateTest(BaseCategoryTestCase):

    def test_create_category_as_admin(self):
        response = self.client.post(self.category_url, {"name": "Giày"}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Category.objects.count(), 1)
        self.assertEqual(Category.objects.get().name, "Giày")

class CategoryUpdateTest(BaseCategoryTestCase):
    def test_update_category_as_admin(self):
        category = Category.objects.create(name="Áo sơ mi")
        url = reverse('update_category', kwargs={'pk': category.id})
        response = self.client.put(url, {"name": "Áo sơ mi dài tay"}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Category.objects.get(id=category.id).name, "Áo sơ mi dài tay")


class CategoryDeleteTest(BaseCategoryTestCase):
    def test_delete_category_as_admin(self):
        category = Category.objects.create(name="Quần jeans")
        url = reverse('delete_category', kwargs={'pk': category.id})

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Category.objects.filter(id=category.id).exists())


class CategoryListTest(BaseCategoryTestCase):
    def test_list_categories(self):
        Category.objects.create(name="Váy")
        Category.objects.create(name="Giày thể thao")

        url = reverse('category')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        names = [cat['name'] for cat in response.data]
        self.assertIn("Váy", names)
        self.assertIn("Giày thể thao", names)


class CategoryPermissionTest(APITestCase):
    def setUp(self):
        self.normal_user = UserAccount.objects.create_user(
            email='user1@gmail.com',
            username='user1',
            password='user1',
            role='user' 
        )
        self.client = APIClient()
        self.login_url = reverse('login')

        response = self.client.post(self.login_url, {
            "username": "user1",
            "password": "user1"
        }, format='json')
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_user_cannot_create_category(self):
        url = reverse('create_category')
        response = self.client.post(url, {"name": "Không hợp lệ"}, format='json')
        self.assertEqual(response.status_code, 403)

    def test_user_cannot_update_category(self):
        category = Category.objects.create(name="Áo Hoodie")
        url = reverse('update_category', kwargs={'pk': category.id})
        response = self.client.put(url, {"name": "Hoodie mới"}, format='json')
        self.assertEqual(response.status_code, 403)

    def test_user_cannot_delete_category(self):
        category = Category.objects.create(name="Đồ ngủ")
        url = reverse('delete_category', kwargs={'pk': category.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 403)
