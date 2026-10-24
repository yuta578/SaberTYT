from django.urls import path
from . import views
from . import api_views
from .auth import permission_required

urlpatterns = [
    # M01: Portal Principal & Acceso Institucional
    path('', views.home_view, name='home'),
    path('login/', views.login_view, name='login'),
    path('registro/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('api/auth/login/', api_views.login, name='api_login'),
    path('api/auth/refresh/', api_views.refresh, name='api_refresh'),
    path('api/auth/logout/', api_views.logout, name='api_logout'),
    path('api/auth/me/', api_views.me, name='api_me'),
    
    # M03: Mi Perfil & Seguridad
    path('perfil/', views.profile_view, name='profile'),

    # Módulo Administrador
    # M02: Panel General de Administración
    path('admin-panel/', permission_required('view_admin')(views.admin_dashboard_view), name='admin_dashboard'),
    # M04: Directorio y CRUD de Usuarios
    path('admin-panel/usuarios/', permission_required('manage_users')(views.admin_users_view), name='admin_users'),
    path('admin-panel/usuarios/crear/', permission_required('manage_users')(views.admin_crear_usuario_view), name='admin_crear_usuario'),
    path('admin-panel/usuarios/toggle-estado/', permission_required('manage_users')(views.admin_toggle_estado_usuario_view), name='admin_toggle_estado_usuario'),
    # M05: Matriz de Roles y Permisos
    path('admin-panel/permisos/', permission_required('manage_roles')(views.admin_permissions_view), name='admin_permissions'),
    # M06: Configuración Global Institucional
    path('admin-panel/configuracion/', permission_required('manage_settings')(views.admin_settings_view), name='admin_settings'),
    # M12: Histórico y Reporte Global de Resultados (Administrador)
    path('admin-panel/reportes/', permission_required('view_results')(views.admin_reportes_view), name='admin_reportes'),

    # Módulo Docente
    # M02: Panel Académico Docente
    path('docente/', permission_required('manage_questions')(views.docente_dashboard_view), name='docente_dashboard'),
    # M07: Áreas y Competencias Saber TyT
    path('docente/competencias/', permission_required('manage_questions')(views.docente_competencias_view), name='docente_competencias'),
    # M08: Banco de Ítems (Múltiple y V/F)
    path('docente/preguntas/', permission_required('manage_questions')(views.docente_preguntas_view), name='docente_preguntas'),
    path('docente/preguntas/nueva/', permission_required('manage_questions')(views.docente_pregunta_nueva_view), name='docente_pregunta_nueva'),
    path('docente/preguntas/<int:pk>/editar/', permission_required('manage_questions')(views.docente_pregunta_editar_view), name='docente_pregunta_editar'),
    # M09: Asistente de Carga Excel en 3 Fases
    path('docente/importaciones/', permission_required('import_questions')(views.docente_importaciones_view), name='docente_importaciones'),
    path('docente/importaciones/plantilla-descargar/', permission_required('import_questions')(views.descargar_plantilla_excel_view), name='descargar_plantilla_excel'),
    # M10: Programador de Cuestionarios y Ponderaciones
    path('docente/cuestionarios/', permission_required('manage_quizzes')(views.docente_cuestionarios_view), name='docente_cuestionarios'),
    path('docente/cuestionarios/nuevo/', permission_required('manage_quizzes')(views.docente_cuestionario_nuevo_view), name='docente_cuestionario_nuevo'),
    path('docente/cuestionarios/<int:pk>/editar/', permission_required('manage_quizzes')(views.docente_cuestionario_editar_view), name='docente_cuestionario_editar'),
    path('docente/cuestionarios/<int:pk>/preguntas/', permission_required('manage_quizzes')(views.docente_cuestionario_preguntas_view), name='docente_cuestionario_preguntas'),
    path('docente/cuestionarios/<int:pk>/vincular-preguntas/', permission_required('manage_quizzes')(views.docente_cuestionario_vincular_pregunta_view), name='docente_cuestionario_vincular_pregunta'),
    path('docente/cuestionarios/<int:pk>/desvincular-pregunta/<int:cp_id>/', permission_required('manage_quizzes')(views.docente_cuestionario_desvincular_pregunta_view), name='docente_cuestionario_desvincular_pregunta'),
    # M12: Métricas y Resultados por Cuestionario a Cargo
    path('docente/intentos/', permission_required('view_results')(views.docente_intentos_view), name='docente_intentos'),

    # Módulo Estudiante
    # M02: Catálogo de Simulacros (Disponibles / Programados / Historial)
    path('estudiante/', permission_required('view_quiz')(views.estudiante_catalogo_view), name='estudiante_catalogo'),
    # M11: Sala de Espera / Ficha Técnica de la Prueba
    path('estudiante/cuestionario/<int:pk>/sala-espera/', permission_required('view_quiz')(views.estudiante_sala_espera_view), name='estudiante_sala_espera'),
    path('estudiante/cuestionario/<int:pk>/iniciar/', permission_required('start_attempt')(views.estudiante_iniciar_view), name='estudiante_iniciar'),
    # M11: Presentador de Intento en Vivo
    path('estudiante/simulacro/<int:intento_id>/', permission_required('start_attempt')(views.estudiante_simulacro_view), name='estudiante_simulacro'),
    path('estudiante/simulacro/<int:intento_id>/entregar/', permission_required('submit_attempt')(views.estudiante_entregar_view), name='estudiante_entregar'),
    # M12: Informe Evaluativo y Retroalimentación Detallada
    path('estudiante/simulacro/<int:intento_id>/resultado/', permission_required('view_own_results')(views.estudiante_resultado_view), name='estudiante_resultado'),

    # Arquitectura y Modelo de Datos
    path('modelo-datos/', views.modelo_datos_view, name='modelo_datos'),
]
