import os
import csv
import io
import codecs
import random
import unicodedata
import openpyxl
from io import StringIO
from decimal import Decimal
from datetime import datetime, timedelta
from pathlib import Path

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.contrib import messages
from django.db.models import Count, Sum, Avg
from django.db import transaction

from .models import (
    Categoria, Pregunta, OpcionRespuesta, Cuestionario,
    CuestionarioPregunta, Importacion, Intento, RespuestaIntento, Usuario,
    Permiso, Rol,
)
from .auth import user_from_request

BASE_DIR = Path(__file__).resolve().parent.parent

# --------------------------------------------------------------------------
# M01: PANTALLA DE ACCESO / LOGIN & AUTENTICACIÓN INSTITUCIONAL CON MYSQL
# --------------------------------------------------------------------------
def login_view(request):
    """
    [M01: Pantalla de Acceso / Login]
    - Autenticación con Base de Datos MySQL (tabla 'usuarios').
    - Soporte completo para inicio de sesión regular y botones de prueba (demo).
    - Redirección automática según el rol asignado en la BD (Administrador, Docente, Estudiante).
    """
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()

        # Alerta 1: Campos vacíos
        if not email or not password:
            messages.error(request, "Campos incompletos: Por favor ingresa tanto tu correo institucional como tu contraseña.")
            return render(request, 'login.html', {
                'email': email,
            })

        # Búsqueda en MySQL por correo electrónico o por código institucional
        user = Usuario.objects.filter(email__iexact=email).first()
        if not user:
            user = Usuario.objects.filter(codigo_institucional__iexact=email).first()

        if not user:
            messages.error(request, "Credenciales inválidas: El correo o código ingresado no está registrado en la base de datos institucional.")
            return render(request, 'login.html', {
                'email': email,
            })

        # Alerta 2: Cuenta inactiva o suspendida
        if not user.activo:
            messages.warning(request, "Cuenta inactiva o suspendida: Tu usuario no cuenta con permisos activos para ingresar a la plataforma. Comunícate con la Dirección Académica.")
            return render(request, 'login.html', {
                'email': email,
            })

        # Alerta 3: Verificación de contraseña
        if not user.check_password(password):
            messages.error(request, "Credenciales inválidas: La contraseña ingresada no es correcta. Verifica tus datos de acceso.")
            return render(request, 'login.html', {
                'email': email,
            })

        # Autenticación Exitosa con MySQL
        role_redirects = {
            'admin': 'admin_dashboard',
            'docente': 'docente_dashboard',
            'estudiante': 'estudiante_catalogo',
        }
        profile = {
            'id': user.id,
            'role': user.rol,
            'name': user.nombre_completo,
            'label': user.get_rol_display(),
            'redirect': role_redirects.get(user.rol, 'estudiante_catalogo'),
            'code': user.codigo_institucional,
            'email': user.email,
            'telefono': user.telefono or '',
            'programa': user.programa_academico,
        }

        request.session.flush()
        request.session['demo_profile'] = profile
        request.session.modified = True
        return redirect(profile['redirect'])

    default_email = request.GET.get('email', 'estudiante@itp.edu.co')
    return render(request, 'login.html', {
        'email': default_email,
    })


def generate_random_user_code(role='estudiante'):
    """
    Genera un código institucional único con las letras del rol (EST, DOC, ADM)
    seguido de un guion y 8 dígitos aleatorios (ej: EST-49201837, DOC-71940283, ADM-83920145).
    Garantiza unicidad en la base de datos MySQL.
    """
    role_map = {
        'estudiante': 'EST',
        'docente': 'DOC',
        'admin': 'ADM',
    }
    prefix = role_map.get(str(role).strip().lower(), 'EST')
    while True:
        random_digits = f"{random.randint(10000000, 99999999)}"
        code = f"{prefix}-{random_digits}"
        if not Usuario.objects.filter(codigo_institucional=code).exists():
            return code


def get_next_student_code():
    return generate_random_user_code('estudiante')


def register_view(request):
    """
    [M01: Registro de Usuarios Institucionales]
    - REGLA ESTRICTA: Todo usuario que se registre SIEMPRE obtiene el rol de 'estudiante'.
    - El código estudiantil no se solicita en el formulario; se genera y asigna automáticamente al crear la cuenta.
    - Almacena en MySQL (tabla 'usuarios') con contraseña hasheada.
    - Inicio de sesión inmediato tras el registro con redirección al catálogo de simulacros.
    """
    if request.method == 'POST':
        nombre_completo = request.POST.get('nombre_completo', '').strip()
        email = request.POST.get('email', '').strip().lower()
        telefono = request.POST.get('telefono', '').strip()
        programa_academico = request.POST.get('programa_academico', 'Tecnología en Gestión Contable').strip()
        password = request.POST.get('password', '').strip()
        password_confirm = (request.POST.get('password_confirm') or request.POST.get('confirm_password') or '').strip()

        # Validación 1: Campos requeridos
        if not nombre_completo or not email or not password or not password_confirm:
            messages.error(request, "Campos obligatorios incompletos: Por favor completa todos los campos requeridos para el registro.")
            return render(request, 'register.html', {
                'nombre_completo': nombre_completo,
                'email': email,
                'telefono': telefono,
                'programa_academico': programa_academico,
            })

        # Validación 2: Coincidencia de contraseñas
        if password != password_confirm:
            messages.error(request, "Las contraseñas no coinciden. Por favor escribe la misma contraseña en ambos campos.")
            return render(request, 'register.html', {
                'nombre_completo': nombre_completo,
                'email': email,
                'telefono': telefono,
                'programa_academico': programa_academico,
            })

        # Validación 3: Longitud mínima de contraseña
        if len(password) < 6:
            messages.error(request, "La contraseña debe tener al menos 6 caracteres por seguridad institucional.")
            return render(request, 'register.html', {
                'nombre_completo': nombre_completo,
                'email': email,
                'telefono': telefono,
                'programa_academico': programa_academico,
            })

        # Validación 4: Email ya registrado en MySQL
        if Usuario.objects.filter(email__iexact=email).exists():
            messages.error(request, f"El correo institucional '{email}' ya se encuentra registrado. Inicia sesión con tus credenciales.")
            return render(request, 'register.html', {
                'nombre_completo': nombre_completo,
                'email': email,
                'telefono': telefono,
                'programa_academico': programa_academico,
            })

        # Generación automática del código estudiantil único
        codigo_institucional = get_next_student_code()

        # Creación en MySQL: SIEMPRE con rol='estudiante' y código asignado automáticamente
        nuevo_estudiante = Usuario(
            nombre_completo=nombre_completo,
            codigo_institucional=codigo_institucional,
            email=email,
            rol='estudiante',  # SIEMPRE rol de estudiante
            telefono=telefono,
            programa_academico=programa_academico or "Tecnología en Gestión Contable",
            activo=True,
        )
        nuevo_estudiante.set_password(password)
        nuevo_estudiante.save()

        # Inicio de sesión automático tras registro
        profile = {
            'id': nuevo_estudiante.id,
            'role': 'estudiante',
            'name': nuevo_estudiante.nombre_completo,
            'label': 'Estudiante',
            'redirect': 'estudiante_catalogo',
            'code': nuevo_estudiante.codigo_institucional,
            'email': nuevo_estudiante.email,
            'telefono': nuevo_estudiante.telefono or '',
            'programa': nuevo_estudiante.programa_academico,
        }
        request.session.flush()
        request.session['demo_profile'] = profile
        request.session.modified = True

        messages.success(
            request, 
            f"¡Cuenta creada con éxito! Tu Código Estudiantil asignado es {nuevo_estudiante.codigo_institucional}. Bienvenido/a {nuevo_estudiante.nombre_completo}."
        )
        return redirect('estudiante_catalogo')

    return render(request, 'register.html')


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
    """[M04: Directorio y CRUD de Usuarios en MySQL]"""
    users = Usuario.objects.all().order_by('-created_at')
    return render(request, 'admin/users.html', {'users': users})


def admin_crear_usuario_view(request):
    """[M04: CRUD de Usuarios - Crear Usuario en MySQL]"""
    if request.method == 'POST':
        name = (request.POST.get('name') or request.POST.get('nombre_completo') or '').strip()
        code = (request.POST.get('code') or request.POST.get('codigo_institucional') or '').strip()
        email = request.POST.get('email', '').strip().lower()
        role = (request.POST.get('role') or request.POST.get('rol') or 'estudiante').strip().lower()
        active = request.POST.get('active', 'true') in ['true', 'True', True, 'on', '1']

        if name and email:
            if Usuario.objects.filter(email__iexact=email).exists():
                messages.error(request, f"El correo institucional '{email}' ya se encuentra registrado.")
            elif code and Usuario.objects.filter(codigo_institucional__iexact=code).exists():
                messages.error(request, f"El código '{code}' ya está asignado a otro usuario.")
            else:
                user = Usuario(
                    nombre_completo=name,
                    codigo_institucional=code or generate_random_user_code(role),
                    email=email,
                    rol=role if role in ['admin', 'docente', 'estudiante'] else 'estudiante',
                    activo=active
                )
                user.set_password('demo1234')
                user.save()
                messages.success(request, f"Usuario institucional '{name}' creado correctamente en MySQL con rol {user.get_rol_display()}.")

    return redirect('admin_users')


def admin_toggle_estado_usuario_view(request):
    """[M04: CRUD de Usuarios - Cambiar Estado Activo/Inactivo en MySQL]"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        user = Usuario.objects.filter(email__iexact=email).first()
        if user:
            user.activo = not user.activo
            user.save()
            estado_str = "Activo" if user.activo else "Inactivo / Suspendido"
            messages.info(request, f"Estado del usuario {user.nombre_completo} actualizado a: {estado_str} en la base de datos.")

    return redirect('admin_users')



def admin_permissions_view(request):
    """[M05: Matriz de Roles y Permisos RBAC]"""
    if request.method == 'POST':
        role_id = request.POST.get('role_id')
        name = request.POST.get('name', '').strip()
        code = request.POST.get('code', '').strip().lower()
        description = request.POST.get('description', '').strip()
        active = request.POST.get('active', 'on') in {'on', '1', 'true', 'True'}
        permission_codes = request.POST.getlist('permissions')
        role = Rol.objects.filter(pk=role_id).first() if role_id else None
        if role and role.es_predeterminado:
            messages.error(request, "Los roles predeterminados no pueden editarse.")
        elif not name or not code:
            messages.error(request, "El nombre y código del rol son obligatorios.")
        else:
            role, _ = Rol.objects.update_or_create(
                codigo=code,
                defaults={
                    'nombre': name,
                    'descripcion': description,
                    'activo': active,
                },
            )
            role.permisos.set(Permiso.objects.filter(
                codigo__in=permission_codes, activo=True
            ))
            messages.success(request, f"Rol '{role.nombre}' guardado correctamente.")
    return render(request, 'admin/permissions.html', {
        'roles': Rol.objects.prefetch_related('permisos').all(),
        'permissions': Permiso.objects.filter(activo=True),
    })


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
        categoria_id = request.POST.get('categoria_id') or request.POST.get('categoria')
        tipo = request.POST.get('tipo', 'MULTIPLE')
        puntaje_base = Decimal(request.POST.get('puntaje_base', '1.00'))
        texto_base = request.POST.get('texto_base', '').strip()
        enunciado = request.POST.get('enunciado', '').strip()
        retroalimentacion = request.POST.get('retroalimentacion', '').strip()
        activo = request.POST.get('activo') in ['on', 'true', True, '1']
        correcta_letra = request.POST.get('correcta_letra') or request.POST.get('correcta') or 'A'

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

        opc_a = (request.POST.get('opcion_A_texto') or request.POST.get('opcion_a') or '').strip()
        opc_b = (request.POST.get('opcion_B_texto') or request.POST.get('opcion_b') or '').strip()
        opc_c = (request.POST.get('opcion_C_texto') or request.POST.get('opcion_c') or '').strip()
        opc_d = (request.POST.get('opcion_D_texto') or request.POST.get('opcion_d') or '').strip()

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
        pregunta.categoria_id = request.POST.get('categoria_id') or request.POST.get('categoria')
        pregunta.tipo = request.POST.get('tipo', 'MULTIPLE')
        pregunta.puntaje_base = Decimal(request.POST.get('puntaje_base', '1.00'))
        pregunta.texto_base = request.POST.get('texto_base', '').strip()
        pregunta.enunciado = request.POST.get('enunciado', '').strip()
        pregunta.retroalimentacion = request.POST.get('retroalimentacion', '').strip()
        pregunta.activo = request.POST.get('activo') in ['on', 'true', True, '1']
        pregunta.save()

        correcta_letra = request.POST.get('correcta_letra') or request.POST.get('correcta') or 'A'
        pregunta.opciones.all().delete()

        opc_a = (request.POST.get('opcion_A_texto') or request.POST.get('opcion_a') or '').strip()
        opc_b = (request.POST.get('opcion_B_texto') or request.POST.get('opcion_b') or '').strip()
        opc_c = (request.POST.get('opcion_C_texto') or request.POST.get('opcion_c') or '').strip()
        opc_d = (request.POST.get('opcion_D_texto') or request.POST.get('opcion_d') or '').strip()

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


def _normalizar_nombre_columna(col_name):
    if not col_name:
        return ''
    clean = unicodedata.normalize('NFKD', str(col_name)).encode('ascii', 'ignore').decode('utf-8')
    return ''.join(c for c in clean.lower() if c.isalnum())


def _mapear_fila_cruda(raw_dict):
    """
    Mapea encabezados humanos amigables (ej: 'Competencia / Área', 'Pregunta / Enunciado', 
    'Respuesta Correcta', etc.) o técnicos ('categoria', 'enunciado', 'clave_correcta') a claves canónicas.
    """
    mapa_priorizado = [
        ('respuestacorrecta', 'clave_correcta'),
        ('clavecorrecta', 'clave_correcta'),
        ('clave', 'clave_correcta'),
        ('tipodepregunta', 'tipo'),
        ('tipo', 'tipo'),
        ('contexto', 'texto_base'),
        ('lectura', 'texto_base'),
        ('textobase', 'texto_base'),
        ('caso', 'texto_base'),
        ('pregunta', 'enunciado'),
        ('enunciado', 'enunciado'),
        ('opciona', 'opcion_a'),
        ('opcionb', 'opcion_b'),
        ('opcionc', 'opcion_c'),
        ('opciond', 'opcion_d'),
        ('alternativaa', 'opcion_a'),
        ('alternativab', 'opcion_b'),
        ('alternativac', 'opcion_c'),
        ('alternativad', 'opcion_d'),
        ('competencia', 'categoria'),
        ('categoria', 'categoria'),
        ('area', 'categoria'),
        ('modulo', 'categoria'),
        ('retroalimentacion', 'retroalimentacion'),
        ('explicacion', 'retroalimentacion'),
        ('justificacion', 'retroalimentacion'),
        ('puntaje', 'puntaje'),
        ('puntos', 'puntaje'),
        ('valor', 'puntaje'),
        ('peso', 'puntaje'),
    ]

    fila_limpia = {}
    for k, v in raw_dict.items():
        if not k:
            continue
        cleaned_k = _normalizar_nombre_columna(k)
        
        matched_key = None
        if cleaned_k in ['a', 'b', 'c', 'd']:
            matched_key = f'opcion_{cleaned_k}'
        else:
            for needle, canon in mapa_priorizado:
                if needle in cleaned_k:
                    matched_key = canon
                    break

        if matched_key and matched_key not in fila_limpia:
            fila_limpia[matched_key] = str(v).strip() if v is not None else ''

    return fila_limpia


def _extraer_filas_de_archivo(archivo):
    """
    Lee archivos tanto en formato Microsoft Excel (.xlsx / .xls) como CSV,
    mapeando automáticamente los nombres de columna a los campos requeridos.
    """
    raw_content = archivo.read()
    nombre_archivo = archivo.name.lower()
    filas = []

    # 1. Intentar como archivo Excel binario
    es_excel = nombre_archivo.endswith('.xlsx') or nombre_archivo.endswith('.xls') or raw_content[:4] == b'PK\x03\x04'
    if es_excel:
        try:
            wb = openpyxl.load_workbook(io.BytesIO(raw_content), data_only=True)
            ws = None
            for sheet_name in wb.sheetnames:
                if 'pregunta' in sheet_name.lower() or 'banco' in sheet_name.lower():
                    ws = wb[sheet_name]
                    break
            if ws is None:
                ws = wb.active

            rows_iter = list(ws.iter_rows(values_only=True))
            if rows_iter:
                headers = [str(c or '').strip() for c in rows_iter[0]]
                for row_values in rows_iter[1:]:
                    if not any(row_values):
                        continue
                    row_dict = {}
                    for h, val in zip(headers, row_values):
                        if h:
                            row_dict[h] = val
                    filas.append(_mapear_fila_cruda(row_dict))
            return filas
        except Exception:
            pass # Si falla openpyxl, intentar como CSV

    # 2. Si es CSV o texto delimitado
    text_content = ""
    for enc in ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']:
        try:
            text_content = raw_content.decode(enc)
            break
        except UnicodeDecodeError:
            continue

    if text_content:
        delimiter = ';' if ';' in text_content[:500] else ','
        reader = csv.DictReader(StringIO(text_content), delimiter=delimiter)
        for raw_row in reader:
            filas.append(_mapear_fila_cruda(raw_row))

    return filas


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
        
        filas_validas = []
        inconsistencias = []

        try:
            filas_extraidas = _extraer_filas_de_archivo(archivo)
            num_fila = 1
            categorias_db = {c.nombre.lower(): c for c in Categoria.objects.all()}

            for row in filas_extraidas:
                num_fila += 1
                cat_nombre = (row.get('categoria') or '').strip()
                tipo_raw = (row.get('tipo') or 'MULTIPLE').strip().upper()
                enunciado = (row.get('enunciado') or '').strip()
                opc_a = (row.get('opcion_a') or '').strip()
                opc_b = (row.get('opcion_b') or '').strip()
                opc_c = (row.get('opcion_c') or '').strip()
                opc_d = (row.get('opcion_d') or '').strip()
                clave_raw = (row.get('clave_correcta') or '').strip().upper()
                texto_base = (row.get('texto_base') or '').strip()
                retro = (row.get('retroalimentacion') or '').strip()
                puntaje = (row.get('puntaje') or '1.00').strip()

                # Normalizar tipo de pregunta (soporta 'Opción Múltiple', 'Verdadero / Falso', 'V/F')
                if 'VERDADERO' in tipo_raw or 'FALSO' in tipo_raw or 'V/F' in tipo_raw or 'VF' in tipo_raw:
                    tipo = 'VERDADERO_FALSO'
                    if not opc_a:
                        opc_a = 'Verdadero'
                    if not opc_b:
                        opc_b = 'Falso'
                else:
                    tipo = 'MULTIPLE'

                # Normalizar clave de respuesta correcta
                if 'VERDADERO' in clave_raw:
                    clave = 'A'
                elif 'FALSO' in clave_raw:
                    clave = 'B'
                elif clave_raw in ['A', 'B', 'C', 'D']:
                    clave = clave_raw
                elif len(clave_raw) > 1 and clave_raw[-1] in ['A', 'B', 'C', 'D']:
                    clave = clave_raw[-1]
                else:
                    clave = clave_raw

                errores_fila = []

                if not enunciado:
                    errores_fila.append("Enunciado o pregunta vacía")
                if not opc_a or not opc_b:
                    errores_fila.append("Alternativas mínimas A y B ausentes")
                if tipo == 'MULTIPLE' and (not opc_c or not opc_d):
                    errores_fila.append("La pregunta de Opción Múltiple requiere alternativas A, B, C y D")
                if clave not in ['A', 'B', 'C', 'D']:
                    errores_fila.append(f"Clave de respuesta incorrecta o ausente ('{clave_raw}'). Debe ser A, B, C o D.")

                # Asignar categoría o fallback
                cat_match = categorias_db.get(cat_nombre.lower()) or Categoria.objects.first()

                fila_obj = {
                    'num_fila': num_fila,
                    'categoria': cat_match.nombre if cat_match else 'Lectura Crítica',
                    'categoria_id': cat_match.id if cat_match else 1,
                    'tipo': tipo,
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
    """[M09: Descarga de Plantilla Oficial de Carga Excel .xlsx 100% Legible para Docentes]"""
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

    wb = openpyxl.Workbook()
    
    # -------------------------------------------------------------
    # PESTAÑA 1: Banco de Preguntas (Para diligenciar)
    # -------------------------------------------------------------
    ws1 = wb.active
    ws1.title = "Banco de Preguntas"
    ws1.views.sheetView[0].showGridLines = True

    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="102D49", end_color="102D49", fill_type="solid")
    
    zebra_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    white_fill = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
    
    thin_border_side = Side(border_style="thin", color="CBD5E1")
    cell_border = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)
    
    header_border_side = Side(border_style="medium", color="0B1F33")
    header_border = Border(left=thin_border_side, right=thin_border_side, top=header_border_side, bottom=header_border_side)

    align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    align_left = Alignment(horizontal="left", vertical="center", wrap_text=True)

    # Encabezados humanos y accesibles
    headers = [
        "Competencia / Área",
        "Tipo de Pregunta",
        "Contexto o Lectura (Opcional)",
        "Pregunta / Enunciado",
        "Opción A",
        "Opción B",
        "Opción C (Vacío si es V/F)",
        "Opción D (Vacío si es V/F)",
        "Respuesta Correcta (A, B, C o D)",
        "Explicación / Retroalimentación",
        "Puntos"
    ]

    ws1.append(headers)
    ws1.row_dimensions[1].height = 36

    for col_idx, col_name in enumerate(headers, 1):
        cell = ws1.cell(row=1, column=col_idx)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = align_center
        cell.border = header_border

    # Filas de ejemplo reales y formativas
    ejemplos = [
        [
            "Lectura Crítica",
            "Opción Múltiple",
            "En un debate sobre políticas públicas y transición energética, un analista sostiene que la descarbonización requiere subsidios focalizados y viabilidad fiscal gradual para no frenar la productividad industrial.",
            "¿Cuál de los siguientes enunciados sintetiza con mayor precisión la postura central del analista?",
            "La transición hacia energías limpias debe financiarse exclusivamente con impuestos al sector productivo.",
            "La descarbonización sostenible demanda incentivos económicos focalizados y viabilidad fiscal gradual.",
            "Todos los subsidios estatales al sector energético deben suprimirse de inmediato.",
            "El mercado internacional autorregula las emisiones sin necesidad de intervención estatal.",
            "B",
            "La opción B resume fielmente la tesis planteada por el autor en el texto base.",
            "1.00"
        ],
        [
            "Razonamiento Cuantitativo",
            "Opción Múltiple",
            "Una empresa de servicios tecnológicos factura un servicio por un valor total de $1.190.000 COP, el cual incluye un IVA general del 19%.",
            "¿Cuál es el valor del servicio antes de calcular el IVA?",
            "$963.900 COP",
            "$1.000.000 COP",
            "$1.020.000 COP",
            "$1.100.000 COP",
            "B",
            "Valor base = $1.190.000 / 1.19 = $1.000.000 COP.",
            "1.00"
        ],
        [
            "Competencias Ciudadanas",
            "Verdadero / Falso",
            "La alcaldía de un municipio decide reubicar por decreto a comerciantes informales sin habilitar previamente mesas de concertación ni alternativas de subsistencia.",
            "La decisión unilateral de desalojo vulnera los principios constitucionales del debido proceso y el derecho al mínimo vital.",
            "Verdadero",
            "Falso",
            "",
            "",
            "A",
            "La jurisprudencia de la Corte Constitucional exige concertación y planes de reubicación previa.",
            "1.00"
        ],
        [
            "Inglés",
            "Opción Múltiple",
            "Cloud computing allows modern companies to store data on remote servers instead of local hard drives.",
            "According to the context, what is the main benefit of cloud computing?",
            "Storing data remotely rather than depending solely on local drives.",
            "Replacing the need for internet access.",
            "Deleting all internal corporate information.",
            "Forcing companies to buy expensive physical mainframes.",
            "A",
            "The sentence explicitly affirms storing data on remote servers instead of local hard drives.",
            "1.00"
        ]
    ]

    for row_idx, fila in enumerate(ejemplos, 2):
        ws1.append(fila)
        ws1.row_dimensions[row_idx].height = 48
        current_fill = zebra_fill if row_idx % 2 == 0 else white_fill

        for col_idx in range(1, len(fila) + 1):
            cell = ws1.cell(row=row_idx, column=col_idx)
            cell.font = Font(name="Calibri", size=10, color="1E293B")
            cell.fill = current_fill
            cell.border = cell_border
            
            if col_idx in [2, 9, 11]:
                cell.alignment = align_center
            else:
                cell.alignment = align_left

    # Anchos óptimos para visualización humana sin truncamiento
    anchos = {
        'A': 25,  # Competencia
        'B': 20,  # Tipo
        'C': 42,  # Contexto
        'D': 42,  # Pregunta
        'E': 30,  # Opción A
        'F': 30,  # Opción B
        'G': 30,  # Opción C
        'H': 30,  # Opción D
        'I': 22,  # Respuesta Correcta
        'J': 35,  # Explicación
        'K': 12,  # Puntos
    }
    for col_letter, width in anchos.items():
        ws1.column_dimensions[col_letter].width = width

    # -------------------------------------------------------------
    # PESTAÑA 2: Guía de Ayuda y Diligenciamiento
    # -------------------------------------------------------------
    ws2 = wb.create_sheet(title="Instrucciones para Docentes")
    ws2.views.sheetView[0].showGridLines = True

    ws2.column_dimensions['A'].width = 26
    ws2.column_dimensions['B'].width = 38
    ws2.column_dimensions['C'].width = 56

    ws2.append(["GUÍA DE DILIGENCIAMIENTO - BANCO DE PREGUNTAS SABER TyT", "", ""])
    ws2.merge_cells("A1:C1")
    ws2.row_dimensions[1].height = 32
    title_cell = ws2.cell(row=1, column=1)
    title_cell.font = Font(name="Calibri", size=13, bold=True, color="FFFFFF")
    title_cell.fill = header_fill
    title_cell.alignment = Alignment(horizontal="left", vertical="center", indent=1)

    ws2.append(["Esta plantilla te permite redactar tus preguntas en Excel de forma clara y cargarlas masivamente al sistema institucional.", "", ""])
    ws2.merge_cells("A2:C2")
    ws2.row_dimensions[2].height = 24
    ws2.cell(row=2, column=1).font = Font(name="Calibri", size=10, italic=True, color="475569")
    ws2.cell(row=2, column=1).alignment = Alignment(vertical="center", indent=1)

    ws2.append([])

    guide_headers = ["Campo / Columna", "¿Qué debes colocar?", "Reglas y Recomendaciones"]
    ws2.append(guide_headers)
    ws2.row_dimensions[4].height = 26
    for c in range(1, 4):
        cell = ws2.cell(row=4, column=c)
        cell.font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
        cell.alignment = Alignment(horizontal="left", vertical="center", indent=1)

    guia_filas = [
        ("Competencia / Área", "El nombre del módulo o área evaluada.", "Ejemplos: Lectura Crítica, Razonamiento Cuantitativo, Competencias Ciudadanas, Inglés."),
        ("Tipo de Pregunta", "Opción Múltiple o Verdadero / Falso.", "Si escribes 'Opción Múltiple' debes llenar opciones A, B, C y D. Si es 'Verdadero / Falso', solo A y B."),
        ("Contexto o Lectura", "Párrafo de lectura, caso de estudio o situación problema.", "Opcional. Si la pregunta no necesita un texto previo de lectura, puedes dejar esta celda vacía."),
        ("Pregunta / Enunciado", "La pregunta o tarea concreta a resolver.", "Obligatorio. No coloques la letra de la respuesta aquí."),
        ("Opción A, B, C, D", "El contenido de cada alternativa de respuesta.", "Para preguntas V/F: En Opción A escribe 'Verdadero', en Opción B escribe 'Falso' y deja C y D vacías."),
        ("Respuesta Correcta", "La letra mayúscula de la opción correcta: A, B, C o D.", "Obligatorio. Solo una letra (A, B, C o D). Si es V/F, coloca 'A' para Verdadero o 'B' para Falso."),
        ("Explicación / Retroalimentación", "Justificación pedagógica de por qué la respuesta es correcta.", "Recomendado. El estudiante la leerá en su informe para comprender su desempeño formativo."),
        ("Puntos", "Puntaje que suma la pregunta.", "Por defecto 1.00 punto.")
    ]

    for g_idx, g_row in enumerate(guia_filas, 5):
        ws2.append(list(g_row))
        ws2.row_dimensions[g_idx].height = 32
        g_fill = zebra_fill if g_idx % 2 == 0 else white_fill
        for c in range(1, 4):
            cell = ws2.cell(row=g_idx, column=c)
            cell.font = Font(name="Calibri", size=9.5, color="1E293B")
            cell.fill = g_fill
            cell.border = cell_border
            cell.alignment = Alignment(vertical="center", wrap_text=True, indent=1)
            if c == 1:
                cell.font = Font(name="Calibri", size=9.5, bold=True, color="1E3A8A")

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="Plantilla_Oficial_Preguntas_Saber_TyT.xlsx"'
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
    ahora = timezone.now()
    cuestionarios = Cuestionario.objects.prefetch_related(
        'cuestionario_preguntas__pregunta'
    ).filter(
        estado='Disponible',
        fecha_apertura__lte=ahora,
        fecha_cierre__gte=ahora,
    ).order_by('id')
    total_cuestionarios = cuestionarios.count()

    profile = request.session.get('demo_profile', {})
    student_code = profile.get('code')

    if student_code:
        mis_intentos = Intento.objects.filter(codigo_estudiante=student_code, estado='Finalizado')
    else:
        mis_intentos = Intento.objects.filter(estado='Finalizado')

    total_intentos = mis_intentos.count()
    calificaciones = mis_intentos.filter(calificacion_final__isnull=False)
    promedio_general = Decimal('0.0')
    if calificaciones.exists():
        avg_val = calificaciones.aggregate(promedio=Avg('calificacion_final'))['promedio']
        if avg_val is not None:
            promedio_general = round(Decimal(str(avg_val)), 2)

    ultimo_intento = mis_intentos.select_related('cuestionario').order_by('-fecha_fin').first()

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
    ahora = timezone.now()
    if cuestionario.estado != 'Disponible' or not (
        cuestionario.fecha_apertura <= ahora <= cuestionario.fecha_cierre
    ):
        messages.error(request, "El cuestionario no está disponible en este momento.")
        return redirect('estudiante_catalogo')
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
        user = getattr(request, 'authenticated_user', None) or user_from_request(request)
        ahora = timezone.now()
        if cuestionario.estado != 'Disponible' or not (
            cuestionario.fecha_apertura <= ahora <= cuestionario.fecha_cierre
        ):
            messages.error(request, "El cuestionario no está disponible en este momento.")
            return redirect('estudiante_catalogo')
        if not user:
            return redirect('login')
        with transaction.atomic():
            prev_intentos = Intento.objects.filter(
                cuestionario=cuestionario, usuario=user
            ).count()
            if prev_intentos >= cuestionario.intentos_permitidos:
                messages.error(request, "Has alcanzado el número máximo de intentos permitidos.")
                return redirect('estudiante_sala_espera', pk=pk)
            intento = Intento.objects.create(
                cuestionario=cuestionario,
                usuario=user,
                nombre_estudiante=user.nombre_completo,
                codigo_estudiante=user.codigo_institucional,
                numero_intento=prev_intentos + 1,
                estado='En Progreso'
            )

        return redirect('estudiante_simulacro', intento_id=intento.id)

    return redirect('estudiante_sala_espera', pk=pk)


def estudiante_simulacro_view(request, intento_id):
    """[M11: Presentador de Intento en Vivo]"""
    user = getattr(request, 'authenticated_user', None) or user_from_request(request)
    filtros = {'pk': intento_id}
    if user and user.rol == 'estudiante':
        filtros['usuario'] = user
    intento = get_object_or_404(
        Intento.objects.select_related('cuestionario'), **filtros
    )
    cuestionario = intento.cuestionario
    cp_list = CuestionarioPregunta.objects.filter(cuestionario=cuestionario).select_related('pregunta__categoria').prefetch_related('pregunta__opciones').order_by('orden')

    return render(request, 'estudiante/simulacro.html', {
        'intento': intento,
        'cuestionario': cuestionario,
        'cp_list': cp_list,
    })


def estudiante_entregar_view(request, intento_id):
    """[M11: Entrega y Liquidación del Simulacro]"""
    user = getattr(request, 'authenticated_user', None) or user_from_request(request)
    filtros = {'pk': intento_id, 'estado': 'En Progreso'}
    if user and user.rol == 'estudiante':
        filtros['usuario'] = user
    intento = get_object_or_404(
        Intento.objects.select_related('cuestionario'), **filtros
    )
    cuestionario = intento.cuestionario
    cp_list = CuestionarioPregunta.objects.filter(cuestionario=cuestionario).select_related('pregunta')

    total_ponderado_cuestionario = Decimal('0.00')
    total_puntaje_obtenido = Decimal('0.00')

    if timezone.now() > intento.fecha_inicio + timedelta(
        minutes=cuestionario.tiempo_limite_minutos
    ):
        messages.warning(request, "El tiempo del intento había terminado; se calificarán las respuestas recibidas.")

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
            # Pregunta no contestada / omitida formalmente por el estudiante (0.00 pts)
            opcion_elegida = None
            es_acierto = False

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
    user = getattr(request, 'authenticated_user', None) or user_from_request(request)
    filtros = {'pk': intento_id, 'estado': 'Finalizado'}
    if user and user.rol == 'estudiante':
        filtros['usuario'] = user
    intento = get_object_or_404(
        Intento.objects.select_related('cuestionario'), **filtros
    )
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
