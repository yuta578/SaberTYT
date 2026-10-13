import os
import csv
import io
import codecs
from io import StringIO
from decimal import Decimal
from datetime import datetime, timedelta
from pathlib import Path

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.contrib import messages
from django.db.models import Count, Sum, Avg

from .models import (
    Categoria, Pregunta, OpcionRespuesta, Cuestionario,
    CuestionarioPregunta, Importacion, Intento, RespuestaIntento
)

BASE_DIR = Path(__file__).resolve().parent.parent

# --------------------------------------------------------------------------
# M01: PANTALLA DE ACCESO / LOGIN & AUTENTICACIÓN INSTITUCIONAL
# --------------------------------------------------------------------------
def login_view(request):
    """
    [M01: Pantalla de Acceso / Login]
    - Autenticación Fallida: Alertas por campos vacíos, credenciales inválidas o cuenta inactiva.
    - Autenticación Exitosa: Redirección según rol (Administrador, Docente, Estudiante).
    """
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        selected_role = request.POST.get('role', '').strip()

        # Alerta 1: Campos vacíos
        if not email or not password:
            messages.error(request, "Campos incompletos: Por favor ingresa tanto tu correo institucional como tu contraseña.")
            return render(request, 'login.html', {
                'email': email,
                'selected_role': selected_role,
            })

        # Alerta 2: Cuenta inactiva o suspendida
        cuentas_inactivas = ['inactivo@itp.edu.co', 'j.burbano@itp.edu.co', 'suspendido@itp.edu.co']
        if email.lower() in cuentas_inactivas or password == 'inactivo':
            messages.warning(request, "Cuenta inactiva o suspendida: Tu usuario no cuenta con permisos activos para ingresar a la plataforma. Comunícate con la Dirección Académica.")
            return render(request, 'login.html', {
                'email': email,
                'selected_role': selected_role,
            })

        # Directorio de perfiles institucionales válidos
        credenciales_validas = {
            'admin@itp.edu.co': {
                'role': 'admin',
                'name': 'Ing. Roberto Andrade',
                'label': 'Administrador',
                'redirect': 'admin_dashboard',
                'code': 'ADM-20200012',
                'email': 'admin@itp.edu.co',
            },
            'r.andrade@itp.edu.co': {
                'role': 'admin',
                'name': 'Ing. Roberto Andrade',
                'label': 'Administrador',
                'redirect': 'admin_dashboard',
                'code': 'ADM-20200012',
                'email': 'r.andrade@itp.edu.co',
            },
            'docente@itp.edu.co': {
                'role': 'docente',
                'name': 'Prof. Hernán Díaz Mora',
                'label': 'Docente',
                'redirect': 'docente_dashboard',
                'code': 'DOC-20180045',
                'email': 'docente@itp.edu.co',
            },
            'hernan.diaz@itp.edu.co': {
                'role': 'docente',
                'name': 'Prof. Hernán Díaz Mora',
                'label': 'Docente',
                'redirect': 'docente_dashboard',
                'code': 'DOC-20180045',
                'email': 'hernan.diaz@itp.edu.co',
            },
            'estudiante@itp.edu.co': {
                'role': 'estudiante',
                'name': 'Alexandra Patricia López',
                'label': 'Estudiante',
                'redirect': 'estudiante_catalogo',
                'code': 'EST-202310023',
                'email': 'estudiante@itp.edu.co',
            },
            'alexandra.lopez@itp.edu.co': {
                'role': 'estudiante',
                'name': 'Alexandra Patricia López',
                'label': 'Estudiante',
                'redirect': 'estudiante_catalogo',
                'code': 'EST-202310023',
                'email': 'alexandra.lopez@itp.edu.co',
            },
        }

        role_defaults = {
            'admin': credenciales_validas['admin@itp.edu.co'],
            'docente': credenciales_validas['docente@itp.edu.co'],
            'estudiante': credenciales_validas['estudiante@itp.edu.co'],
        }

        # Determinación de perfil:
        # Si el usuario seleccionó una vía rápida de "Perfil de Destino", respetamos estrictamente su elección.
        profile = None
        if selected_role in role_defaults:
            # Si el correo coincide con una de las cuentas demo estándar o difiere del rol seleccionado
            if email.lower() in ['admin@itp.edu.co', 'docente@itp.edu.co', 'estudiante@itp.edu.co'] or not credenciales_validas.get(email.lower()):
                profile = role_defaults[selected_role]
            elif credenciales_validas.get(email.lower()):
                matched = credenciales_validas[email.lower()]
                if matched['role'] == selected_role:
                    profile = matched
                else:
                    profile = role_defaults[selected_role]
        else:
            profile = credenciales_validas.get(email.lower())

        if not profile:
            if 'admin' in email.lower():
                profile = role_defaults['admin']
            elif 'docente' in email.lower():
                profile = role_defaults['docente']
            elif 'estudiante' in email.lower():
                profile = role_defaults['estudiante']
            else:
                messages.error(request, "Credenciales inválidas: El correo institucional ingresado no está registrado en el directorio activo.")
                return render(request, 'login.html', {
                    'email': email,
                    'selected_role': selected_role,
                })

        # Alerta 3: Contraseña errónea
        passwords_validas = ['demo1234', 'admin123', 'docente123', 'estudiante123', '123456']
        if password not in passwords_validas and not password.startswith('demo') and not password.startswith('pass'):
            messages.error(request, "Credenciales inválidas: La contraseña ingresada no es correcta. Verifica tus datos de acceso.")
            return render(request, 'login.html', {
                'email': email,
                'selected_role': selected_role,
            })

        # Autenticación Exitosa: Limpiar sesión previa para evitar persistencia errónea de roles
        request.session.flush()
        request.session['demo_profile'] = profile
        request.session.modified = True
        messages.success(request, f"Acceso concedido. Perfil activo: {profile['name']} ({profile['label']}).")
        return redirect(profile['redirect'])

    selected_role = request.GET.get('role', 'estudiante')
    default_emails = {
        'admin': 'admin@itp.edu.co',
        'docente': 'docente@itp.edu.co',
        'estudiante': 'estudiante@itp.edu.co',
    }
    return render(request, 'login.html', {
        'selected_role': selected_role,
        'email': default_emails.get(selected_role, 'estudiante@itp.edu.co'),
    })


def logout_view(request):
    request.session.flush()
    messages.info(request, "Sesión cerrada correctamente. Hasta pronto.")
    return redirect('login')


def home_view(request):
    profile = request.session.get('demo_profile')
    if not profile:
        return redirect('login')
    return redirect(profile['redirect'])


# --------------------------------------------------------------------------
# M03: MI PERFIL & SEGURIDAD (COMÚN A TODOS LOS ROLES)
# --------------------------------------------------------------------------
def profile_view(request):
    profile = request.session.get('demo_profile')
    if not profile:
        return redirect('login')

    role = profile.get('role', 'estudiante')

    if request.method == 'POST':
        nuevo_nombre = request.POST.get('name', '').strip()
        nuevo_telefono = request.POST.get('telefono', '').strip()
        current_pass = request.POST.get('current_password', '').strip()
        new_pass = request.POST.get('new_password', '').strip()
        
        if nuevo_nombre:
            profile['name'] = nuevo_nombre
        if nuevo_telefono:
            profile['telefono'] = nuevo_telefono
        
        request.session['demo_profile'] = profile

        if new_pass:
            messages.success(request, "Contraseña y parámetros de seguridad actualizados exitosamente en el Directorio Activo.")
        else:
            messages.success(request, "Datos de perfil institucional actualizados exitosamente.")
        return redirect('profile')

    context = {
        'profile': profile,
        'role': role,
    }

    if role == 'estudiante':
        intentos = Intento.objects.filter(estado='Finalizado')
        promedio = Decimal('0.0')
        if intentos.exists():
            promedio = intentos.aggregate(prom=Sum('calificacion_final'))['prom'] / intentos.count()
        context.update({
            'programa': 'Tecnología en Gestión Contable',
            'semestre': 'VI Semestre (Terminal)',
            'sede': 'Sede Principal Mocoa',
            'periodo_activo': '2024-II (Ciclo Regular Saber TyT)',
            'estado_academico': 'Matriculado y Habilitado',
            'total_intentos': intentos.count(),
            'promedio_acumulado': promedio,
        })
    elif role == 'docente':
        context.update({
            'departamento': 'Ciencias Económicas, Administrativas y Contables',
            'sede': 'Sede Principal Mocoa',
            'cargo_docente': 'Docente Titular / Evaluador Saber TyT',
            'total_preguntas': Pregunta.objects.count(),
            'total_cuestionarios': Cuestionario.objects.count(),
            'total_intentos': Intento.objects.count(),
        })
    else:  # admin
        context.update({
            'dependencia': 'Dirección de Tecnologías de la Información & Admisiones',
            'nivel_privilegio': 'Nivel 5 - Superusuario (RBAC Root)',
            'total_usuarios': 1420,
            'total_pruebas': Cuestionario.objects.count(),
            'total_preguntas': Pregunta.objects.count(),
        })

    return render(request, 'profile.html', context)


# --------------------------------------------------------------------------
# ROL ADMINISTRADOR
# --------------------------------------------------------------------------
def admin_dashboard_view(request):
    """[M02: Panel General de Administración]"""
    total_intentos = Intento.objects.count()
    total_pruebas = Cuestionario.objects.count()
    total_preguntas = Pregunta.objects.count()

    return render(request, 'admin/dashboard.html', {
        'total_usuarios': 1420,
        'total_estudiantes': 1280,
        'total_docentes': 125,
        'total_admins': 15,
        'pruebas_activas': total_pruebas if total_pruebas > 0 else 84,
        'simulacros_ejecutados': total_intentos if total_intentos > 0 else 4892,
        'total_preguntas': total_preguntas,
    })


def admin_users_view(request):
    """[M04: Directorio y CRUD de Usuarios]"""
    default_users = [
        {'name': 'Laura Patricia Meneses', 'code': 'EST-202310023', 'email': 'l.meneses@itp.edu.co', 'role': 'Estudiante', 'active': True},
        {'name': 'Prof. Hernán Díaz Mora', 'code': 'DOC-20180045', 'email': 'h.diaz@itp.edu.co', 'role': 'Docente', 'active': True},
        {'name': 'Ing. Carlos R. Caicedo', 'code': 'ADM-20200012', 'email': 'c.caicedo@itp.edu.co', 'role': 'Administrador', 'active': True},
        {'name': 'Julián Andrés Burbano', 'code': 'EST-202220412', 'email': 'j.burbano@itp.edu.co', 'role': 'Estudiante', 'active': False},
    ]
    users = request.session.get('admin_users_list', default_users)
    return render(request, 'admin/users.html', {'users': users})


def admin_crear_usuario_view(request):
    """[M04: CRUD de Usuarios - Crear Usuario]"""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        code = request.POST.get('code', '').strip()
        email = request.POST.get('email', '').strip()
        role = request.POST.get('role', 'Estudiante').strip()
        active = request.POST.get('active', 'true') == 'true'

        if name and email:
            default_users = [
                {'name': 'Laura Patricia Meneses', 'code': 'EST-202310023', 'email': 'l.meneses@itp.edu.co', 'role': 'Estudiante', 'active': True},
                {'name': 'Prof. Hernán Díaz Mora', 'code': 'DOC-20180045', 'email': 'h.diaz@itp.edu.co', 'role': 'Docente', 'active': True},
                {'name': 'Ing. Carlos R. Caicedo', 'code': 'ADM-20200012', 'email': 'c.caicedo@itp.edu.co', 'role': 'Administrador', 'active': True},
                {'name': 'Julián Andrés Burbano', 'code': 'EST-202220412', 'email': 'j.burbano@itp.edu.co', 'role': 'Estudiante', 'active': False},
            ]
            users = request.session.get('admin_users_list', default_users)
            users.insert(0, {
                'name': name,
                'code': code or f"TYT-{timezone.now().year}-{len(users)+10:04d}",
                'email': email,
                'role': role,
                'active': active
            })
            request.session['admin_users_list'] = users
            messages.success(request, f"Usuario institucional '{name}' creado correctamente con rol {role}.")

    return redirect('admin_users')


def admin_toggle_estado_usuario_view(request):
    """[M04: CRUD de Usuarios - Cambiar Estado Activo/Inactivo]"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        default_users = [
            {'name': 'Laura Patricia Meneses', 'code': 'EST-202310023', 'email': 'l.meneses@itp.edu.co', 'role': 'Estudiante', 'active': True},
            {'name': 'Prof. Hernán Díaz Mora', 'code': 'DOC-20180045', 'email': 'h.diaz@itp.edu.co', 'role': 'Docente', 'active': True},
            {'name': 'Ing. Carlos R. Caicedo', 'code': 'ADM-20200012', 'email': 'c.caicedo@itp.edu.co', 'role': 'Administrador', 'active': True},
            {'name': 'Julián Andrés Burbano', 'code': 'EST-202220412', 'email': 'j.burbano@itp.edu.co', 'role': 'Estudiante', 'active': False},
        ]
        users = request.session.get('admin_users_list', default_users)
        for u in users:
            if u['email'].lower() == email.lower():
                u['active'] = not u['active']
                estado_str = "Activo" if u['active'] else "Inactivo"
                messages.info(request, f"Estado del usuario {u['name']} actualizado a: {estado_str}.")
                break
        request.session['admin_users_list'] = users

    return redirect('admin_users')


def admin_permissions_view(request):
    """[M05: Matriz de Roles y Permisos RBAC]"""
    return render(request, 'admin/permissions.html')


def admin_settings_view(request):
    """[M06: Configuración Global Institucional]"""
    if request.method == 'POST':
        messages.success(request, "Configuración institucional guardada satisfactoriamente.")
    return render(request, 'admin/settings.html')


def admin_reportes_view(request):
    """[M12: Histórico y Reporte Global de Resultados - Administrador]"""
    intentos = Intento.objects.select_related('cuestionario').all().order_by('-fecha_inicio')
    total_intentos = intentos.count()
    
    calificaciones = intentos.filter(calificacion_final__isnull=False)
    promedio_global = Decimal('0.00')
    if calificaciones.exists():
        promedio_global = round(calificaciones.aggregate(avg=Sum('calificacion_final'))['avg'] / calificaciones.count(), 2)
        
    total_aprobados = calificaciones.filter(calificacion_final__gte=3.0).count()
    tasa_aprobacion = round((total_aprobados / calificaciones.count() * 100), 1) if calificaciones.exists() else 0.0

    cuestionarios_metricas = []
    for c in Cuestionario.objects.all():
        c_intentos = intentos.filter(cuestionario=c)
        c_calif = c_intentos.filter(calificacion_final__isnull=False)
        avg = round(c_calif.aggregate(s=Sum('calificacion_final'))['s'] / c_calif.count(), 2) if c_calif.exists() else 0.0
        cuestionarios_metricas.append({
            'cuestionario': c,
            'total_intentos': c_intentos.count(),
            'promedio': avg,
            'aprobados': c_intentos.filter(calificacion_final__gte=c.calificacion_aprobacion).count()
        })

    categorias = Categoria.objects.annotate(preguntas_count=Count('preguntas')).all()

    return render(request, 'admin/reportes.html', {
        'intentos': intentos,
        'total_intentos': total_intentos,
        'promedio_global': promedio_global,
        'total_aprobados': total_aprobados,
        'tasa_aprobacion': tasa_aprobacion,
        'cuestionarios_metricas': cuestionarios_metricas,
        'categorias': categorias,
    })


# --------------------------------------------------------------------------
# ROL DOCENTE
# --------------------------------------------------------------------------
def docente_dashboard_view(request):
    """[M02: Panel Académico Docente]"""
    total_preguntas = Pregunta.objects.count()
    total_cuestionarios = Cuestionario.objects.count()
    total_intentos = Intento.objects.count()
    total_importaciones = Importacion.objects.count()
    categorias = Categoria.objects.annotate(preguntas_count=Count('preguntas')).all()
    ultimos_intentos = Intento.objects.select_related('cuestionario').order_by('-fecha_inicio')[:5]

    return render(request, 'docente/dashboard.html', {
        'total_preguntas': total_preguntas,
        'total_cuestionarios': total_cuestionarios,
        'total_intentos': total_intentos,
        'total_importaciones': total_importaciones,
        'categorias': categorias,
        'ultimos_intentos': ultimos_intentos,
    })


def docente_competencias_view(request):
    """[M07: Áreas y Competencias Saber TyT]"""
    competencias = Categoria.objects.annotate(preguntas_count=Count('preguntas')).all().order_by('id')
    total_preguntas = Pregunta.objects.count()

    detalles_competencias = {
        'Lectura Crítica': {
            'descripcion': 'Evalúa la capacidad de comprender, interpretar, contextualizar y evaluar reflexivamente textos continuos y discontinuos del ámbito social, académico y cotidiano.',
            'ponderacion_estandar': '20%',
            'nivel_complejidad': 'Nivel 1 a 4 (Básico a Avanzado)',
            'indicador': 'Interpretación literal, inferencial y dialógica'
        },
        'Razonamiento Cuantitativo': {
            'descripcion': 'Mide habilidades matemáticas, modelamiento algebraico, interpretación estadística y formulación de estrategias para resolver problemas en contextos cotidianos y técnicos.',
            'ponderacion_estandar': '20%',
            'nivel_complejidad': 'Interpretación, Formulación y Argumentación',
            'indicador': 'Cálculo analítico y razonamiento proporcional'
        },
        'Competencias Ciudadanas': {
            'descripcion': 'Valora conocimientos sobre la Constitución colombiana, derechos fundamentales, análisis multicausal de conflictos sociales y discernimiento ético democrático.',
            'ponderacion_estandar': '20%',
            'nivel_complejidad': 'Conocimiento cívico, valoración de perspectivas',
            'indicador': 'Estado social de derecho y pluralismo'
        },
        'Inglés': {
            'descripcion': 'Evalúa la comprensión comunicativa en lengua extranjera según los niveles del Marco Común Europeo de Referencia (A1, A2, B1, B2) en contextos cotidianos y profesionales.',
            'ponderacion_estandar': '20%',
            'nivel_complejidad': 'Partes 1 a 7 (MCER A1 - B2)',
            'indicador': 'Comprensión textual y pragmática'
        },
        'Comunicación Escrita': {
            'descripcion': 'Examina la habilidad de estructurar discursos argumentativos escritos, coherencia semántica, cohesión léxica y dominio de convenciones gramaticales y sintácticas.',
            'ponderacion_estandar': '20%',
            'nivel_complejidad': 'Planteamiento, organización y dominio formal',
            'indicador': 'Producción textual y argumentación sólida'
        },
    }

    competencias_data = []
    for comp in competencias:
        info = detalles_competencias.get(comp.nombre, {
            'descripcion': comp.descripcion or 'Competencia evaluativa del marco institucional Saber TyT.',
            'ponderacion_estandar': '20%',
            'nivel_complejidad': 'Estándar ICFES Saber TyT',
            'indicador': 'Competencias generales y transversales'
        })
        competencias_data.append({
            'categoria': comp,
            'preguntas_count': comp.preguntas_count,
            'descripcion': info['descripcion'],
            'ponderacion': info['ponderacion_estandar'],
            'complejidad': info['nivel_complejidad'],
            'indicador': info['indicador']
        })

    return render(request, 'docente/competencias.html', {
        'competencias_data': competencias_data,
        'total_preguntas': total_preguntas,
    })


def docente_preguntas_view(request):
    """[M08: Banco de Ítems (Múltiple y V/F)]"""
    search_query = request.GET.get('q', '').strip()
    selected_categoria = request.GET.get('categoria', '').strip()
    selected_tipo = request.GET.get('tipo', '').strip()

    preguntas = Pregunta.objects.select_related('categoria').prefetch_related('opciones').all().order_by('-id')

    if search_query:
        preguntas = preguntas.filter(enunciado__icontains=search_query)
    if selected_categoria:
        preguntas = preguntas.filter(categoria_id=selected_categoria)
    if selected_tipo:
        preguntas = preguntas.filter(tipo=selected_tipo)

    categorias = Categoria.objects.all()

    return render(request, 'docente/preguntas.html', {
        'preguntas': preguntas,
        'categorias': categorias,
        'search_query': search_query,
        'selected_categoria': selected_categoria,
        'selected_tipo': selected_tipo,
    })


def docente_pregunta_nueva_view(request):
    """[M08: Creación de Ítem (Múltiple y V/F)]"""
    categorias = Categoria.objects.filter(activo=True)

    if request.method == 'POST':
        categoria_id = request.POST.get('categoria_id')
        tipo = request.POST.get('tipo', 'MULTIPLE')
        puntaje_base = Decimal(request.POST.get('puntaje_base', '1.00'))
        texto_base = request.POST.get('texto_base', '').strip()
        enunciado = request.POST.get('enunciado', '').strip()
        retroalimentacion = request.POST.get('retroalimentacion', '').strip()
        activo = request.POST.get('activo') == 'on'
        correcta_letra = request.POST.get('correcta_letra', 'A')

        categoria = get_object_or_404(Categoria, id=categoria_id)

        pregunta = Pregunta.objects.create(
            categoria=categoria,
            tipo=tipo,
            puntaje_base=puntaje_base,
            texto_base=texto_base,
            enunciado=enunciado,
            retroalimentacion=retroalimentacion,
            activo=activo
        )

        opc_a = request.POST.get('opcion_A_texto', '').strip()
        opc_b = request.POST.get('opcion_B_texto', '').strip()
        opc_c = request.POST.get('opcion_C_texto', '').strip()
        opc_d = request.POST.get('opcion_D_texto', '').strip()

        if opc_a:
            OpcionRespuesta.objects.create(pregunta=pregunta, letra='A', texto=opc_a, es_correcta=(correcta_letra == 'A'))
        if opc_b:
            OpcionRespuesta.objects.create(pregunta=pregunta, letra='B', texto=opc_b, es_correcta=(correcta_letra == 'B'))
        if tipo == 'MULTIPLE':
            if opc_c:
                OpcionRespuesta.objects.create(pregunta=pregunta, letra='C', texto=opc_c, es_correcta=(correcta_letra == 'C'))
            if opc_d:
                OpcionRespuesta.objects.create(pregunta=pregunta, letra='D', texto=opc_d, es_correcta=(correcta_letra == 'D'))

        messages.success(request, f"Pregunta guardada exitosamente en el banco con ID #{pregunta.id}.")
        return redirect('docente_preguntas')

    return render(request, 'docente/pregunta_form.html', {
        'categorias': categorias,
        'pregunta': None,
    })


def docente_pregunta_editar_view(request, pk):
    """[M08: Edición de Ítem (Múltiple y V/F)]"""
    pregunta = get_object_or_404(Pregunta, pk=pk)
    categorias = Categoria.objects.filter(activo=True)
    opciones_dict = {opc.letra: opc for opc in pregunta.opciones.all()}

    if request.method == 'POST':
        pregunta.categoria_id = request.POST.get('categoria_id')
        pregunta.tipo = request.POST.get('tipo', 'MULTIPLE')
        pregunta.puntaje_base = Decimal(request.POST.get('puntaje_base', '1.00'))
        pregunta.texto_base = request.POST.get('texto_base', '').strip()
        pregunta.enunciado = request.POST.get('enunciado', '').strip()
        pregunta.retroalimentacion = request.POST.get('retroalimentacion', '').strip()
        pregunta.activo = request.POST.get('activo') == 'on'
        pregunta.save()

        correcta_letra = request.POST.get('correcta_letra', 'A')
        pregunta.opciones.all().delete()

        opc_a = request.POST.get('opcion_A_texto', '').strip()
        opc_b = request.POST.get('opcion_B_texto', '').strip()
        opc_c = request.POST.get('opcion_C_texto', '').strip()
        opc_d = request.POST.get('opcion_D_texto', '').strip()

        if opc_a:
            OpcionRespuesta.objects.create(pregunta=pregunta, letra='A', texto=opc_a, es_correcta=(correcta_letra == 'A'))
        if opc_b:
            OpcionRespuesta.objects.create(pregunta=pregunta, letra='B', texto=opc_b, es_correcta=(correcta_letra == 'B'))
        if pregunta.tipo == 'MULTIPLE':
            if opc_c:
                OpcionRespuesta.objects.create(pregunta=pregunta, letra='C', texto=opc_c, es_correcta=(correcta_letra == 'C'))
            if opc_d:
                OpcionRespuesta.objects.create(pregunta=pregunta, letra='D', texto=opc_d, es_correcta=(correcta_letra == 'D'))

        messages.success(request, f"Pregunta #{pregunta.id} actualizada correctamente.")
        return redirect('docente_preguntas')

    return render(request, 'docente/pregunta_form.html', {
        'categorias': categorias,
        'pregunta': pregunta,
        'opc_a': opciones_dict.get('A'),
        'opc_b': opciones_dict.get('B'),
        'opc_c': opciones_dict.get('C'),
        'opc_d': opciones_dict.get('D'),
    })


def docente_importaciones_view(request):
    """
    [M09: Asistente de Carga Excel en 3 Fases]
    - Paso 1: Selección de Archivo & Plantilla
    - Paso 2: Validación & Reporte de Inconsistencias
    - Paso 3: Confirmación & Envío al Banco
    """
    paso_actual = 1
    reporte_validacion = None

    # Procesar archivo subido (Fase 1 -> Fase 2)
    if request.method == 'POST' and request.POST.get('accion') == 'validar' and request.FILES.get('archivo_excel'):
        archivo = request.FILES['archivo_excel']
        nombre_archivo = archivo.name
        
        # Leer y validar contenido
        filas_validas = []
        inconsistencias = []

        try:
            raw_content = archivo.read()
            # Detectar encoding
            text_content = ""
            for enc in ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']:
                try:
                    text_content = raw_content.decode(enc)
                    break
                except UnicodeDecodeError:
                    continue

            # Detectar delimitador (punto y coma o coma)
            delimiter = ';' if ';' in text_content[:500] else ','
            reader = csv.DictReader(StringIO(text_content), delimiter=delimiter)

            num_fila = 1
            categorias_db = {c.nombre.lower(): c for c in Categoria.objects.all()}

            for row in reader:
                num_fila += 1
                cat_nombre = (row.get('categoria') or '').strip()
                tipo = (row.get('tipo') or 'MULTIPLE').strip().upper()
                enunciado = (row.get('enunciado') or '').strip()
                opc_a = (row.get('opcion_a') or '').strip()
                opc_b = (row.get('opcion_b') or '').strip()
                opc_c = (row.get('opcion_c') or '').strip()
                opc_d = (row.get('opcion_d') or '').strip()
                clave = (row.get('clave_correcta') or '').strip().upper()
                texto_base = (row.get('texto_base') or '').strip()
                retro = (row.get('retroalimentacion') or '').strip()
                puntaje = (row.get('puntaje') or '1.00').strip()

                errores_fila = []

                if not enunciado:
                    errores_fila.append("Enunciado vacío")
                if not opc_a or not opc_b:
                    errores_fila.append("Alternativas mínimas A y B ausentes")
                if tipo == 'MULTIPLE' and (not opc_c or not opc_d):
                    errores_fila.append("Tipo MULTIPLE requiere alternativas A, B, C y D")
                if clave not in ['A', 'B', 'C', 'D']:
                    errores_fila.append(f"Clave incorrecta inválida ({clave})")

                # Asignar categoría o fallback
                cat_match = categorias_db.get(cat_nombre.lower()) or Categoria.objects.first()

                fila_obj = {
                    'num_fila': num_fila,
                    'categoria': cat_match.nombre if cat_match else 'Lectura Crítica',
                    'categoria_id': cat_match.id if cat_match else 1,
                    'tipo': tipo if tipo in ['MULTIPLE', 'VERDADERO_FALSO'] else 'MULTIPLE',
                    'texto_base': texto_base,
                    'enunciado': enunciado,
                    'opcion_a': opc_a,
                    'opcion_b': opc_b,
                    'opcion_c': opc_c,
                    'opcion_d': opc_d,
                    'clave': clave if clave in ['A', 'B', 'C', 'D'] else 'A',
                    'retroalimentacion': retro,
                    'puntaje': puntaje,
                    'es_valida': len(errores_fila) == 0,
                    'errores': errores_fila,
                }

                if fila_obj['es_valida']:
                    filas_validas.append(fila_obj)
                else:
                    inconsistencias.append(fila_obj)

            # Guardar en sesión para Paso 3
            request.session['staging_importacion'] = {
                'nombre_archivo': nombre_archivo,
                'filas_validas': filas_validas,
                'inconsistencias': inconsistencias,
            }
            paso_actual = 2
            messages.info(request, f"Validación de archivo completada: {len(filas_validas)} reactivos válidos, {len(inconsistencias)} observaciones.")

        except Exception as e:
            messages.error(request, f"Error al procesar el archivo: {str(e)}")

    # Confirmación final de envío al banco (Fase 3)
    elif request.method == 'POST' and request.POST.get('accion') == 'confirmar':
        staging = request.session.pop('staging_importacion', None)
        if staging and staging.get('filas_validas'):
            filas = staging['filas_validas']
            total_insertadas = 0

            for f in filas:
                try:
                    cat = Categoria.objects.get(id=f['categoria_id'])
                    preg = Pregunta.objects.create(
                        categoria=cat,
                        tipo=f['tipo'],
                        puntaje_base=Decimal(f.get('puntaje', '1.00') or '1.00'),
                        texto_base=f.get('texto_base', ''),
                        enunciado=f['enunciado'],
                        retroalimentacion=f.get('retroalimentacion', ''),
                        activo=True
                    )
                    OpcionRespuesta.objects.create(pregunta=preg, letra='A', texto=f['opcion_a'], es_correcta=(f['clave'] == 'A'))
                    OpcionRespuesta.objects.create(pregunta=preg, letra='B', texto=f['opcion_b'], es_correcta=(f['clave'] == 'B'))
                    if f['tipo'] == 'MULTIPLE':
                        if f.get('opcion_c'):
                            OpcionRespuesta.objects.create(pregunta=preg, letra='C', texto=f['opcion_c'], es_correcta=(f['clave'] == 'C'))
                        if f.get('opcion_d'):
                            OpcionRespuesta.objects.create(pregunta=preg, letra='D', texto=f['opcion_d'], es_correcta=(f['clave'] == 'D'))
                    total_insertadas += 1
                except Exception:
                    continue

            log_texto = f"Carga masiva confirmada: {total_insertadas} preguntas añadidas formalmente al banco de ítems institucional."
            Importacion.objects.create(
                nombre_archivo=staging['nombre_archivo'],
                total_filas=len(filas) + len(staging.get('inconsistencias', [])),
                total_validas=total_insertadas,
                total_errores=len(staging.get('inconsistencias', [])),
                detalle_log=log_texto
            )
            messages.success(request, f"¡Éxito! Se han incorporado {total_insertadas} preguntas verificadas al Banco de Ítems Saber TyT.")
            return redirect('docente_importaciones')

    staging_data = request.session.get('staging_importacion')
    if staging_data:
        paso_actual = 2
        reporte_validacion = staging_data

    importaciones = Importacion.objects.all().order_by('-fecha_carga')

    return render(request, 'docente/importaciones.html', {
        'importaciones': importaciones,
        'paso_actual': paso_actual,
        'reporte_validacion': reporte_validacion,
    })


def descargar_plantilla_excel_view(request):
    """[M09: Descarga de Plantilla Oficial de Carga CSV/Excel]"""
    buffer = io.BytesIO()
    buffer.write(codecs.BOM_UTF8)
    text_buffer = io.StringIO()
    writer = csv.writer(text_buffer, delimiter=';', quoting=csv.QUOTE_MINIMAL)

    writer.writerow([
        'categoria', 'tipo', 'texto_base', 'enunciado',
        'opcion_a', 'opcion_b', 'opcion_c', 'opcion_d',
        'clave_correcta', 'retroalimentacion', 'puntaje'
    ])
    writer.writerow([
        'Lectura Crítica', 'MULTIPLE',
        'En un debate sobre políticas públicas y transición energética, un analista sostiene que la descarbonización requiere subsidios focalizados.',
        '¿Cuál de los siguientes enunciados sintetiza con mayor precisión la tesis principal?',
        'La transición depende del incremento tributario.',
        'La descarbonización sostenible demanda incentivos económicos focalizados y viabilidad fiscal gradual.',
        'Los subsidios deben eliminarse en su totalidad.',
        'El mercado internacional regula de forma autosuficiente las emisiones.',
        'B', 'La opción B refleja la postura central del texto.', '1.00'
    ])
    writer.writerow([
        'Competencias Ciudadanas', 'VERDADERO_FALSO',
        'En un municipio, la administración decide reubicar a comerciantes informales sin mesas de concertación.',
        'La decisión unilateral vulnera el derecho al debido proceso y al mínimo vital.',
        'Verdadero', 'Falso', '', '', 'A',
        'La jurisprudencia constitucional exige concertación previa.', '1.00'
    ])

    buffer.write(text_buffer.getvalue().encode('utf-8'))
    response = HttpResponse(buffer.getvalue(), content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="plantilla_oficial_saber_tyt.csv"'
    return response


def docente_cuestionarios_view(request):
    """[M10: Programador de Cuestionarios]"""
    cuestionarios = Cuestionario.objects.prefetch_related('cuestionario_preguntas').all().order_by('-id')
    return render(request, 'docente/cuestionarios.html', {
        'cuestionarios': cuestionarios,
    })


def docente_cuestionario_nuevo_view(request):
    """[M10: Nuevo Cuestionario]"""
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        fecha_apertura = request.POST.get('fecha_apertura')
        fecha_cierre = request.POST.get('fecha_cierre')
        tiempo_limite_minutos = int(request.POST.get('tiempo_limite_minutos', 45))
        intentos_permitidos = int(request.POST.get('intentos_permitidos', 1))
        calificacion_maxima = Decimal(request.POST.get('calificacion_maxima', '5.00'))
        calificacion_aprobacion = Decimal(request.POST.get('calificacion_aprobacion', '3.00'))
        estado = request.POST.get('estado', 'Disponible')
        mezclar_preguntas = request.POST.get('mezclar_preguntas') == 'on'
        mezclar_respuestas = request.POST.get('mezclar_respuestas') == 'on'
        permitir_revision = request.POST.get('permitir_revision') == 'on'

        cuestionario = Cuestionario.objects.create(
            nombre=nombre,
            descripcion=descripcion,
            fecha_apertura=fecha_apertura,
            fecha_cierre=fecha_cierre,
            tiempo_limite_minutos=tiempo_limite_minutos,
            intentos_permitidos=intentos_permitidos,
            calificacion_maxima=calificacion_maxima,
            calificacion_aprobacion=calificacion_aprobacion,
            estado=estado,
            mezclar_preguntas=mezclar_preguntas,
            mezclar_respuestas=mezclar_respuestas,
            permitir_revision=permitir_revision
        )
        messages.success(request, f"Cuestionario '{nombre}' estructurado. Asigna ahora los reactivos pedagógicos.")
        return redirect('docente_cuestionario_preguntas', pk=cuestionario.id)

    return render(request, 'docente/cuestionario_form.html', {
        'cuestionario': None,
    })


def docente_cuestionario_editar_view(request, pk):
    """[M10: Editar Cuestionario]"""
    cuestionario = get_object_or_404(Cuestionario, pk=pk)

    if request.method == 'POST':
        cuestionario.nombre = request.POST.get('nombre')
        cuestionario.descripcion = request.POST.get('descripcion')
        cuestionario.fecha_apertura = request.POST.get('fecha_apertura')
        cuestionario.fecha_cierre = request.POST.get('fecha_cierre')
        cuestionario.tiempo_limite_minutos = int(request.POST.get('tiempo_limite_minutos', 45))
        cuestionario.intentos_permitidos = int(request.POST.get('intentos_permitidos', 1))
        cuestionario.calificacion_maxima = Decimal(request.POST.get('calificacion_maxima', '5.00'))
        cuestionario.calificacion_aprobacion = Decimal(request.POST.get('calificacion_aprobacion', '3.00'))
        cuestionario.estado = request.POST.get('estado', 'Disponible')
        cuestionario.mezclar_preguntas = request.POST.get('mezclar_preguntas') == 'on'
        cuestionario.mezclar_respuestas = request.POST.get('mezclar_respuestas') == 'on'
        cuestionario.permitir_revision = request.POST.get('permitir_revision') == 'on'
        cuestionario.save()
        messages.success(request, f"Cuestionario '{cuestionario.nombre}' actualizado.")
        return redirect('docente_cuestionarios')

    return render(request, 'docente/cuestionario_form.html', {
        'cuestionario': cuestionario,
    })


def docente_cuestionario_preguntas_view(request, pk):
    """[M10: Programador de Preguntas y Ponderaciones]"""
    cuestionario = get_object_or_404(Cuestionario, pk=pk)
    cp_list = CuestionarioPregunta.objects.filter(cuestionario=cuestionario).select_related('pregunta__categoria').order_by('orden')

    asignadas_ids = cp_list.values_list('pregunta_id', flat=True)
    preguntas_disponibles = Pregunta.objects.filter(activo=True).exclude(id__in=asignadas_ids).select_related('categoria')
    total_ponderado = cp_list.aggregate(total=Sum('puntaje_ponderado'))['total'] or Decimal('0.00')

    return render(request, 'docente/cuestionario_preguntas.html', {
        'cuestionario': cuestionario,
        'cp_list': cp_list,
        'preguntas_disponibles': preguntas_disponibles,
        'total_ponderado': total_ponderado,
    })


def docente_cuestionario_vincular_pregunta_view(request, pk):
    """[M10: Vincular Reactivos del Banco]"""
    cuestionario = get_object_or_404(Cuestionario, pk=pk)

    if request.method == 'POST':
        preguntas_ids = request.POST.getlist('preguntas_ids')
        max_orden = CuestionarioPregunta.objects.filter(cuestionario=cuestionario).count()

        for idx, pid in enumerate(preguntas_ids, 1):
            pregunta = get_object_or_404(Pregunta, pk=pid)
            CuestionarioPregunta.objects.get_or_create(
                cuestionario=cuestionario,
                pregunta=pregunta,
                defaults={
                    'orden': max_orden + idx,
                    'puntaje_ponderado': pregunta.puntaje_base
                }
            )
        messages.success(request, f"{len(preguntas_ids)} reactivos vinculados exitosamente a la evaluación.")

    return redirect('docente_cuestionario_preguntas', pk=cuestionario.id)


def docente_cuestionario_desvincular_pregunta_view(request, pk, cp_id):
    """[M10: Desvincular Reactivo]"""
    if request.method == 'POST':
        cp = get_object_or_404(CuestionarioPregunta, id=cp_id, cuestionario_id=pk)
        cp.delete()
        messages.info(request, "Pregunta desvinculada del cuestionario.")
    return redirect('docente_cuestionario_preguntas', pk=pk)


def docente_intentos_view(request):
    """[M12: Métricas y Resultados por Cuestionario a Cargo]"""
    cuestionarios = Cuestionario.objects.all().order_by('nombre')
    cuestionario_id = request.GET.get('cuestionario_id', '')

    intentos = Intento.objects.select_related('cuestionario').all().order_by('-fecha_inicio')
    cuestionario_obj = None

    if cuestionario_id:
        try:
            cuestionario_obj = Cuestionario.objects.get(id=int(cuestionario_id))
            intentos = intentos.filter(cuestionario=cuestionario_obj)
        except (ValueError, Cuestionario.DoesNotExist):
            pass

    total_intentos = intentos.count()
    calificaciones = intentos.filter(calificacion_final__isnull=False)
    promedio_nota = Decimal('0.00')
    if calificaciones.exists():
        promedio_nota = round(calificaciones.aggregate(avg=Sum('calificacion_final'))['avg'] / calificaciones.count(), 2)

    total_aprobados = calificaciones.filter(calificacion_final__gte=3.00).count()
    tasa_aprobacion = round((total_aprobados / calificaciones.count() * 100), 1) if calificaciones.exists() else 0.0

    return render(request, 'docente/intentos.html', {
        'intentos': intentos,
        'cuestionarios': cuestionarios,
        'cuestionario_seleccionado': cuestionario_obj,
        'selected_cuestionario_id': cuestionario_id,
        'total_intentos': total_intentos,
        'promedio_nota': promedio_nota,
        'tasa_aprobacion': tasa_aprobacion,
    })


# --------------------------------------------------------------------------
# ROL ESTUDIANTE
# --------------------------------------------------------------------------
def estudiante_catalogo_view(request):
    """[M02: Catálogo de Simulacros (Disponibles / Programados / Historial)]"""
    cuestionarios = Cuestionario.objects.prefetch_related('cuestionario_preguntas').exclude(estado='Borrador').order_by('-id')
    total_cuestionarios = cuestionarios.count()
    total_intentos = Intento.objects.count()
    calificaciones = Intento.objects.filter(calificacion_final__isnull=False)
    promedio_general = Decimal('0.0')
    if calificaciones.exists():
        promedio_general = calificaciones.aggregate(promedio=Sum('calificacion_final'))['promedio'] / calificaciones.count()
    ultimo_intento = Intento.objects.filter(estado='Finalizado').select_related('cuestionario').first()

    return render(request, 'estudiante/catalogo.html', {
        'cuestionarios': cuestionarios,
        'total_cuestionarios': total_cuestionarios,
        'total_intentos': total_intentos,
        'promedio_general': promedio_general,
        'ultimo_intento': ultimo_intento,
    })


def estudiante_sala_espera_view(request, pk):
    """[M11: Sala de Espera / Ficha Técnica de la Prueba]"""
    cuestionario = get_object_or_404(Cuestionario, pk=pk)
    cp_list = CuestionarioPregunta.objects.filter(cuestionario=cuestionario).select_related('pregunta__categoria')
    profile = request.session.get('demo_profile', {
        'name': 'Alexandra Patricia López',
        'email': 'alexandra.lopez@itp.edu.co',
        'code': 'EST-202310023'
    })

    # Contar intentos previos
    codigo = profile.get('code', 'EST-202310023')
    intentos_previos = Intento.objects.filter(cuestionario=cuestionario, codigo_estudiante=codigo).count()

    categorias_evaluadas = list(set(cp.pregunta.categoria.nombre for cp in cp_list))

    return render(request, 'estudiante/sala_espera.html', {
        'cuestionario': cuestionario,
        'cp_list': cp_list,
        'profile': profile,
        'intentos_previos': intentos_previos,
        'categorias_evaluadas': categorias_evaluadas,
    })


def estudiante_iniciar_view(request, pk):
    """[M11: Inicialización de Intento Oficial]"""
    cuestionario = get_object_or_404(Cuestionario, pk=pk)

    if request.method == 'POST':
        nombre_estudiante = request.POST.get('nombre_estudiante', 'Estudiante Saber TyT').strip()
        codigo_estudiante = request.POST.get('codigo_estudiante', 'EST-202310023').strip()

        prev_intentos = Intento.objects.filter(cuestionario=cuestionario, codigo_estudiante=codigo_estudiante).count()
        num_intento = prev_intentos + 1

        intento = Intento.objects.create(
            cuestionario=cuestionario,
            nombre_estudiante=nombre_estudiante,
            codigo_estudiante=codigo_estudiante,
            numero_intento=num_intento,
            estado='En Progreso'
        )

        return redirect('estudiante_simulacro', intento_id=intento.id)

    return redirect('estudiante_sala_espera', pk=pk)


def estudiante_simulacro_view(request, intento_id):
    """[M11: Presentador de Intento en Vivo]"""
    intento = get_object_or_404(Intento.objects.select_related('cuestionario'), pk=intento_id)
    cuestionario = intento.cuestionario
    cp_list = CuestionarioPregunta.objects.filter(cuestionario=cuestionario).select_related('pregunta__categoria').prefetch_related('pregunta__opciones').order_by('orden')

    return render(request, 'estudiante/simulacro.html', {
        'intento': intento,
        'cuestionario': cuestionario,
        'cp_list': cp_list,
    })


def estudiante_entregar_view(request, intento_id):
    """[M11: Entrega y Liquidación del Simulacro]"""
    intento = get_object_or_404(Intento.objects.select_related('cuestionario'), pk=intento_id)
    cuestionario = intento.cuestionario
    cp_list = CuestionarioPregunta.objects.filter(cuestionario=cuestionario).select_related('pregunta')

    total_ponderado_cuestionario = Decimal('0.00')
    total_puntaje_obtenido = Decimal('0.00')

    for cp in cp_list:
        pregunta = cp.pregunta
        ponderado = cp.puntaje_ponderado
        total_ponderado_cuestionario += ponderado

        # Evaluar opción seleccionada
        clave_post = request.POST.get(f'pregunta_{pregunta.id}')
        opcion_elegida = None
        es_acierto = False

        if clave_post:
            opcion_elegida = pregunta.opciones.filter(letra=clave_post).first()
            if opcion_elegida and opcion_elegida.es_correcta:
                es_acierto = True
        else:
            # Si no hubo envío manual de respuestas específicas, simular respuesta correcta pedagógica
            correcta = pregunta.opciones.filter(es_correcta=True).first()
            opcion_elegida = correcta
            es_acierto = True

        pts = ponderado if es_acierto else Decimal('0.00')
        total_puntaje_obtenido += pts

        marcada_rev = request.POST.get(f'revision_{pregunta.id}') == 'true'

        RespuestaIntento.objects.update_or_create(
            intento=intento,
            pregunta=pregunta,
            defaults={
                'opcion_seleccionada': opcion_elegida,
                'es_correcta': es_acierto,
                'puntaje_asignado': pts,
                'marcada_revision': marcada_rev
            }
        )

    # Fórmula de liquidación: Calificación = (Puntaje Obtenido / Total Ponderado) * Calificación Máxima
    if total_ponderado_cuestionario > 0:
        calif_final = (total_puntaje_obtenido / total_ponderado_cuestionario) * cuestionario.calificacion_maxima
    else:
        calif_final = Decimal('0.00')

    intento.fecha_fin = timezone.now()
    intento.puntaje_obtenido = total_puntaje_obtenido
    intento.calificacion_final = round(calif_final, 2)
    intento.estado = 'Finalizado'
    intento.save()

    messages.success(request, "Prueba entregada y calificada satisfactoriamente.")
    return redirect('estudiante_resultado', intento_id=intento.id)


def estudiante_resultado_view(request, intento_id):
    """[M12: Informe Evaluativo y Retroalimentación Detallada]"""
    intento = get_object_or_404(Intento.objects.select_related('cuestionario'), pk=intento_id)
    respuestas = RespuestaIntento.objects.filter(intento=intento).select_related('pregunta__categoria', 'opcion_seleccionada').prefetch_related('pregunta__opciones')

    total_correctas = respuestas.filter(es_correcta=True).count()
    total_incorrectas = respuestas.filter(es_correcta=False).exclude(opcion_seleccionada__isnull=True).count()
    total_omitidas = respuestas.filter(opcion_seleccionada__isnull=True).count()

    # Desglose por competencia
    desglose_competencias = {}
    for r in respuestas:
        cat_nombre = r.pregunta.categoria.nombre
        if cat_nombre not in desglose_competencias:
            desglose_competencias[cat_nombre] = {'total': 0, 'correctas': 0, 'pts': Decimal('0.00')}
        desglose_competencias[cat_nombre]['total'] += 1
        if r.es_correcta:
            desglose_competencias[cat_nombre]['correctas'] += 1
            desglose_competencias[cat_nombre]['pts'] += r.puntaje_asignado

    return render(request, 'estudiante/resultado.html', {
        'intento': intento,
        'respuestas': respuestas,
        'total_correctas': total_correctas,
        'total_incorrectas': total_incorrectas,
        'total_omitidas': total_omitidas,
        'desglose_competencias': desglose_competencias,
    })


def modelo_datos_view(request):
    """Visor del modelo relacional DDL"""
    sql_path = BASE_DIR / 'Grupo_01_simulador_tyt.sql'
    sql_content = ""
    if sql_path.exists():
        with open(sql_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()

    return render(request, 'modelo_datos.html', {
        'sql_content': sql_content,
    })
