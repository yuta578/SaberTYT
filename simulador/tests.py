from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import (
    Categoria, Cuestionario, CuestionarioPregunta, Intento, OpcionRespuesta, Pregunta,
    RespuestaIntento, Usuario
)


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


class IntegracionSimuladorTests(TestCase):
    def setUp(self):
        self.docente = Usuario.objects.create(
            nombre_completo='Profesor Evaluador',
            codigo_institucional='DOC-00000001',
            email='docente@example.com',
            rol='docente',
        )
        self.docente.set_password('docente123')
        self.docente.save()

        self.estudiante = Usuario.objects.create(
            nombre_completo='Estudiante Oficial',
            codigo_institucional='EST-00000099',
            email='estudiante@example.com',
            rol='estudiante',
        )
        self.estudiante.set_password('estudiante123')
        self.estudiante.save()

        self.categoria = Categoria.objects.create(nombre='Lectura Crítica')

    def test_cuestionario_validaciones_parametros(self):
        """Fase A - Item 4: Impedir cierre anterior a apertura, duración no positiva e intentos inválidos."""
        self.client.post(reverse('login'), {'email': self.docente.email, 'password': 'docente123'})
        
        # Intento con fecha de cierre anterior a apertura
        response = self.client.post(reverse('docente_cuestionario_nuevo'), {
            'nombre': 'Prueba Fechas Invalidas',
            'asignatura': 'Lectura Crítica',
            'fecha_apertura': '2026-11-20T10:00',
            'fecha_cierre': '2026-11-19T10:00', # Cierre anterior
            'tiempo_limite_minutos': 45,
            'intentos_permitidos': 1,
            'calificacion_maxima': '5.00',
            'calificacion_aprobacion': '3.00',
            'estado': 'Borrador',
        })
        self.assertEqual(response.status_code, 200) # Re-renderiza formulario con error
        self.assertFalse(Cuestionario.objects.filter(nombre='Prueba Fechas Invalidas').exists())

        # Intento con duración no positiva (<= 0)
        response = self.client.post(reverse('docente_cuestionario_nuevo'), {
            'nombre': 'Prueba Duracion Invalida',
            'asignatura': 'Lectura Crítica',
            'fecha_apertura': '2026-11-20T10:00',
            'fecha_cierre': '2026-11-20T12:00',
            'tiempo_limite_minutos': -10, # Duración negativa
            'intentos_permitidos': 1,
            'calificacion_maxima': '5.00',
            'calificacion_aprobacion': '3.00',
            'estado': 'Borrador',
        })
        self.assertFalse(Cuestionario.objects.filter(nombre='Prueba Duracion Invalida').exists())

        # Intento con intentos <= 0
        response = self.client.post(reverse('docente_cuestionario_nuevo'), {
            'nombre': 'Prueba Intentos Invalidos',
            'asignatura': 'Lectura Crítica',
            'fecha_apertura': '2026-11-20T10:00',
            'fecha_cierre': '2026-11-20T12:00',
            'tiempo_limite_minutos': 45,
            'intentos_permitidos': 0, # Intentos inválidos
            'calificacion_maxima': '5.00',
            'calificacion_aprobacion': '3.00',
            'estado': 'Borrador',
        })
        self.assertFalse(Cuestionario.objects.filter(nombre='Prueba Intentos Invalidos').exists())

    def test_impedir_activar_cuestionario_sin_preguntas(self):
        """Fase C - Item 9: Activar el cuestionario solo cuando tenga preguntas válidas."""
        cuestionario = Cuestionario.objects.create(
            nombre='Evaluacion Vacia',
            docente=self.docente,
            fecha_apertura=timezone.now() - timezone.timedelta(days=1),
            fecha_cierre=timezone.now() + timezone.timedelta(days=1),
            tiempo_limite_minutos=30,
            estado='Borrador',
        )
        self.client.post(reverse('login'), {'email': self.docente.email, 'password': 'docente123'})
        
        # Intentar editar y activar en 'Disponible' sin preguntas
        response = self.client.post(reverse('docente_cuestionario_editar', args=[cuestionario.id]), {
            'nombre': 'Evaluacion Vacia',
            'asignatura': 'Lectura Crítica',
            'fecha_apertura': cuestionario.fecha_apertura.strftime('%Y-%m-%dT%H:%M'),
            'fecha_cierre': cuestionario.fecha_cierre.strftime('%Y-%m-%dT%H:%M'),
            'tiempo_limite_minutos': 30,
            'intentos_permitidos': 1,
            'calificacion_maxima': '5.00',
            'calificacion_aprobacion': '3.00',
            'estado': 'Disponible', # Intento de activar sin preguntas
        })
        cuestionario.refresh_from_db()
        self.assertEqual(cuestionario.estado, 'Borrador') # No se permite activar

    def test_validacion_contrasena_de_acceso(self):
        """Fase C - Item 11: Validar contraseña de acceso si aplica."""
        cuestionario = Cuestionario.objects.create(
            nombre='Prueba Con Clave',
            clave_acceso='Saber2026',
            fecha_apertura=timezone.now() - timezone.timedelta(days=1),
            fecha_cierre=timezone.now() + timezone.timedelta(days=1),
            tiempo_limite_minutos=30,
            estado='Disponible',
        )
        self.client.post(reverse('login'), {'email': self.estudiante.email, 'password': 'estudiante123'})

        # Iniciar con clave equivocada
        resp = self.client.post(reverse('estudiante_iniciar', args=[cuestionario.id]), {
            'clave_acceso': 'ClaveErronea'
        })
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Intento.objects.filter(cuestionario=cuestionario, usuario=self.estudiante).exists())

        # Iniciar con clave correcta
        resp = self.client.post(reverse('estudiante_iniciar', args=[cuestionario.id]), {
            'clave_acceso': 'Saber2026'
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Intento.objects.filter(cuestionario=cuestionario, usuario=self.estudiante).exists())

    def test_limite_intentos_y_evitar_envios_duplicados(self):
        """Fase C - Item 12 y Caso de prueba: Máximo de intentos y envíos duplicados."""
        cuestionario = Cuestionario.objects.create(
            nombre='Prueba Intentos Limite',
            fecha_apertura=timezone.now() - timezone.timedelta(days=1),
            fecha_cierre=timezone.now() + timezone.timedelta(days=1),
            tiempo_limite_minutos=30,
            intentos_permitidos=1,
            estado='Disponible',
        )
        preg = Pregunta.objects.create(categoria=self.categoria, enunciado='Capital de Colombia?')
        OpcionRespuesta.objects.create(pregunta=preg, letra='A', texto='Bogota', es_correcta=True)
        OpcionRespuesta.objects.create(pregunta=preg, letra='B', texto='Medellin', es_correcta=False)
        CuestionarioPregunta.objects.create(cuestionario=cuestionario, pregunta=preg, orden=1, puntaje_ponderado=5.00)

        self.client.post(reverse('login'), {'email': self.estudiante.email, 'password': 'estudiante123'})

        # Iniciar Intento 1
        self.client.post(reverse('estudiante_iniciar', args=[cuestionario.id]))
        intento = Intento.objects.get(cuestionario=cuestionario, usuario=self.estudiante)

        # Entregar intento
        resp_entregar = self.client.post(reverse('estudiante_entregar', args=[intento.id]), {
            f'pregunta_{preg.id}': 'A'
        })
        self.assertEqual(resp_entregar.status_code, 302)
        intento.refresh_from_db()
        self.assertEqual(intento.estado, 'Finalizado')
        self.assertEqual(float(intento.calificacion_final), 5.0)

        # Re-enviar entrega duplicada del mismo intento (debe fallar 404 porque no está En Progreso)
        resp_dup = self.client.post(reverse('estudiante_entregar', args=[intento.id]), {
            f'pregunta_{preg.id}': 'B'
        })
        self.assertEqual(resp_dup.status_code, 404)

        # Intentar iniciar un segundo intento superando el límite (debe bloquear)
        resp_bloqueo = self.client.post(reverse('estudiante_iniciar', args=[cuestionario.id]))
        self.assertEqual(resp_bloqueo.status_code, 302)
        self.assertEqual(Intento.objects.filter(cuestionario=cuestionario, usuario=self.estudiante).count(), 1)

    def test_docente_puede_ver_examen_resuelto_de_su_cuestionario(self):
        cuestionario = Cuestionario.objects.create(
            nombre='Evaluación Docente Autorizado',
            docente=self.docente,
            fecha_apertura=timezone.now() - timezone.timedelta(days=1),
            fecha_cierre=timezone.now() + timezone.timedelta(days=1),
            tiempo_limite_minutos=30,
            intentos_permitidos=1,
            estado='Disponible',
        )
        preg = Pregunta.objects.create(categoria=self.categoria, enunciado='Pregunta Examen Resuelto')
        opc_a = OpcionRespuesta.objects.create(pregunta=preg, letra='A', texto='Opcion Correcta', es_correcta=True)
        CuestionarioPregunta.objects.create(cuestionario=cuestionario, pregunta=preg, orden=1, puntaje_ponderado=5.00)

        intento = Intento.objects.create(
            cuestionario=cuestionario,
            usuario=self.estudiante,
            codigo_estudiante=self.estudiante.codigo_institucional,
            nombre_estudiante=self.estudiante.nombre_completo,
            estado='Finalizado',
            calificacion_final=5.00,
            fecha_inicio=timezone.now() - timezone.timedelta(minutes=15),
            fecha_fin=timezone.now(),
        )
        RespuestaIntento.objects.create(
            intento=intento,
            pregunta=preg,
            opcion_seleccionada=opc_a,
            es_correcta=True,
            puntaje_asignado=5.00,
        )

        # Autenticar como docente a cargo
        self.client.post(reverse('login'), {'email': self.docente.email, 'password': 'docente123'})

        # El docente accede al examen resuelto del estudiante
        response = self.client.get(reverse('estudiante_resultado', args=[intento.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['es_docente_o_admin'])
        self.assertTrue(response.context['mostrar_retroalimentacion'])
        self.assertContains(response, 'Examen Resuelto del Estudiante')
        self.assertContains(response, self.estudiante.nombre_completo)
        self.assertContains(response, 'Pregunta Examen Resuelto')

        # También debe ser accesible por la URL dedicada de docente
        response_doc = self.client.get(reverse('docente_intento_detalle', args=[intento.id]))
        self.assertEqual(response_doc.status_code, 200)

    def test_docente_bloqueado_para_ver_examen_de_cuestionario_de_otro_docente(self):
        otro_docente = Usuario.objects.create(
            nombre_completo='Otro Profesor',
            codigo_institucional='DOC-99999999',
            email='otro_docente@example.com',
            rol='docente',
        )
        otro_docente.set_password('otro123')
        otro_docente.save()

        cuestionario_ajeno = Cuestionario.objects.create(
            nombre='Evaluación Docente Ajeno',
            docente=otro_docente,
            fecha_apertura=timezone.now() - timezone.timedelta(days=1),
            fecha_cierre=timezone.now() + timezone.timedelta(days=1),
            tiempo_limite_minutos=30,
            intentos_permitidos=1,
            estado='Disponible',
        )
        intento_ajeno = Intento.objects.create(
            cuestionario=cuestionario_ajeno,
            usuario=self.estudiante,
            codigo_estudiante=self.estudiante.codigo_institucional,
            nombre_estudiante=self.estudiante.nombre_completo,
            estado='Finalizado',
            calificacion_final=4.00,
        )

        # Autenticar como self.docente (no es el dueño de cuestionario_ajeno)
        self.client.post(reverse('login'), {'email': self.docente.email, 'password': 'docente123'})

        # Intentar acceder al examen resuelto del cuestionario ajeno debe ser bloqueado con 403
        response = self.client.get(reverse('estudiante_resultado', args=[intento_ajeno.id]))
        self.assertEqual(response.status_code, 403)
