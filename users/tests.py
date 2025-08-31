from django.test import TestCase
from .models import CustomUser


class UserModelTest(TestCase):

    def test_create_user(self):
        user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password'
        )
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.check_password('password'))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
