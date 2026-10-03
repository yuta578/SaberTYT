from django.urls import path
from . import views

urlpatterns = [
    # Portal Principal
    path('', views.home_view, name='home'),

    # Módulo Docente
    path('docente/', views.docente_dashboard_view, name='docente_dashboard'),
    path('docente/preguntas/', views.docente_preguntas_view, name='docente_preguntas'),
    path('docente/preguntas/nueva/', views.docente_pregunta_nueva_view, name='docente_pregunta_nueva'),
    path('docente/preguntas/<int:pk>/editar/', views.docente_pregunta_editar_view, name='docente_pregunta_editar'),
    path('docente/importaciones/', views.docente_importaciones_view, name='docente_importaciones'),
    path('docente/importaciones/plantilla-descargar/', views.descargar_plantilla_excel_view, name='descargar_plantilla_excel'),
    path('docente/cuestionarios/', views.docente_cuestionarios_view, name='docente_cuestionarios'),
    path('docente/cuestionarios/nuevo/', views.docente_cuestionario_nuevo_view, name='docente_cuestionario_nuevo'),
    path('docente/cuestionarios/<int:pk>/editar/', views.docente_cuestionario_editar_view, name='docente_cuestionario_editar'),
    path('docente/cuestionarios/<int:pk>/preguntas/', views.docente_cuestionario_preguntas_view, name='docente_cuestionario_preguntas'),
    path('docente/cuestionarios/<int:pk>/vincular-preguntas/', views.docente_cuestionario_vincular_pregunta_view, name='docente_cuestionario_vincular_pregunta'),
    path('docente/cuestionarios/<int:pk>/desvincular-pregunta/<int:cp_id>/', views.docente_cuestionario_desvincular_pregunta_view, name='docente_cuestionario_desvincular_pregunta'),
    path('docente/intentos/', views.docente_intentos_view, name='docente_intentos'),

    # Módulo Estudiante
    path('estudiante/', views.estudiante_catalogo_view, name='estudiante_catalogo'),
    path('estudiante/cuestionario/<int:pk>/iniciar/', views.estudiante_iniciar_view, name='estudiante_iniciar'),
    path('estudiante/simulacro/<int:intento_id>/', views.estudiante_simulacro_view, name='estudiante_simulacro'),
    path('estudiante/simulacro/<int:intento_id>/entregar/', views.estudiante_entregar_view, name='estudiante_entregar'),
    path('estudiante/simulacro/<int:intento_id>/resultado/', views.estudiante_resultado_view, name='estudiante_resultado'),

    # Arquitectura y Modelo de Datos
    path('modelo-datos/', views.modelo_datos_view, name='modelo_datos'),
]
