from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Usuario


class AuthenticationAndAuthorizationTests(TestCase):
    def setUp(self):
        self.user = Usuario.objects.create(
            nombre_completo='Estudiante de Prueba',
            codigo_institucional='EST-00000001',
            email='student@example.com',
        )
        self.user.set_password('correct-password')
        self.user.save()

    def test_jwt_login_refresh_and_logout(self):
        response = self.client.post(
            reverse('api_login'),
            {'email': self.user.email, 'password': 'correct-password'},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        tokens = response.json()['tokens']
        self.assertIn('access', tokens)
        self.assertIn('refresh', tokens)

        response = self.client.get(
            reverse('api_me'),
            HTTP_AUTHORIZATION=f"Bearer {tokens['access']}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], self.user.id)

        response = self.client.post(
            reverse('api_refresh'),
            {'refresh': tokens['refresh']},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.json()['tokens']['refresh'], tokens['refresh'])

        response = self.client.post(
            reverse('api_logout'),
            {'refresh': response.json()['tokens']['refresh']},
            content_type='application/json',
            HTTP_AUTHORIZATION=f"Bearer {tokens['access']}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            self.client.get(
                reverse('api_me'),
                HTTP_AUTHORIZATION=f"Bearer {tokens['access']}",
            ).status_code,
            401,
        )

    def test_inactive_user_cannot_login(self):
        self.user.activo = False
        self.user.save(update_fields=['activo'])
        response = self.client.post(
            reverse('api_login'),
            {'email': self.user.email, 'password': 'correct-password'},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 401)

    def test_student_cannot_access_admin_route(self):
        self.client.post(
            reverse('login'),
            {'email': self.user.email, 'password': 'correct-password'},
        )
        response = self.client.get(reverse('admin_users'))
        self.assertEqual(response.status_code, 403)
