from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Categoria, Cuestionario, Intento, OpcionRespuesta, Pregunta, RespuestaIntento, Usuario


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


class ReportesTests(TestCase):
    def setUp(self):
        self.admin = Usuario.objects.create(
            nombre_completo='Administrador de Prueba',
            codigo_institucional='ADM-00000001',
            email='admin@example.com',
            rol='admin',
        )
        self.admin.set_password('admin-password')
        self.admin.save()
        self.categoria = Categoria.objects.create(nombre='Lectura Crítica')
        self.pregunta = Pregunta.objects.create(
            categoria=self.categoria, enunciado='Pregunta de prueba'
        )
        self.opcion = OpcionRespuesta.objects.create(
            pregunta=self.pregunta, letra='A', texto='Correcta', es_correcta=True
        )
        self.cuestionario = Cuestionario.objects.create(
            nombre='Simulacro 2026-1',
            fecha_apertura=timezone.now(),
            fecha_cierre=timezone.now(),
            tiempo_limite_minutos=45,
            anio_academico=2026,
            periodo_academico='2026-1',
            curso_grupo='Sexto A',
        )
        self.intento = Intento.objects.create(
            cuestionario=self.cuestionario,
            usuario=None,
            nombre_estudiante='Ana de Prueba',
            codigo_estudiante='EST-00000002',
            estado='Finalizado',
            fecha_fin=timezone.now(),
            calificacion_final='4.50',
        )
        RespuestaIntento.objects.create(
            intento=self.intento, pregunta=self.pregunta,
            opcion_seleccionada=self.opcion, es_correcta=True,
        )
        self.client.post(
            reverse('login'),
            {'email': self.admin.email, 'password': 'admin-password'},
        )

    def test_hierarchical_report_filters_and_excel(self):
        response = self.client.get(
            reverse('admin_reportes'),
            {'anio': '2026', 'periodo': '2026-1', 'curso': 'Sexto A', 'eje': str(self.categoria.pk)},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ana de Prueba')
        self.assertContains(response, 'Lectura Crítica')

        export = self.client.get(
            reverse('admin_exportar_reporte', kwargs={'report_type': 'A'}),
            {'anio': '2026', 'curso': 'Sexto A'},
        )
        self.assertEqual(export.status_code, 200)
        self.assertEqual(
            export['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        self.assertIn(b'PK', export.content[:2])

    def test_report_and_export_require_permission(self):
        self.client.get(reverse('logout'))
        response = self.client.get(reverse('admin_reportes'))
        self.assertEqual(response.status_code, 302)
        export = self.client.get(
            reverse('admin_exportar_reporte', kwargs={'report_type': 'A'})
        )
        self.assertEqual(export.status_code, 302)
