from django.test import TestCase, Client
from django.urls import reverse
from users.models import CustomUser


class DashboardViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password'
        )
        self.client.login(email='test@example.com', password='password')

    def test_dashboard_view_for_logged_in_user(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'mailings/dashboard.html')
