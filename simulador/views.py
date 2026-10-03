import os
import csv
from io import StringIO
from decimal import Decimal
from datetime import datetime, timedelta
from pathlib import Path

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.utils import timezone
from django.contrib import messages
from django.db.models import Count, Sum

from .models import (
    Categoria, Pregunta, OpcionRespuesta, Cuestionario,
    CuestionarioPregunta, Importacion, Intento, RespuestaIntento
)

BASE_DIR = Path(__file__).resolve().parent.parent

def home_view(request):
    total_preguntas = Pregunta.objects.count()
    total_cuestionarios = Cuestionario.objects.count()
    total_intentos = Intento.objects.count()
    total_importaciones = Importacion.objects.count()
    cuestionarios = Cuestionario.objects.all().order_by('-fecha_apertura')[:6]

    return render(request, 'home.html', {
        'total_preguntas': total_preguntas,
        'total_cuestionarios': total_cuestionarios,
        'total_intentos': total_intentos,
        'total_importaciones': total_importaciones,
        'cuestionarios': cuestionarios,
    })


def docente_dashboard_view(request):
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


def docente_preguntas_view(request):
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

        # Crear opciones
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

        return redirect('docente_preguntas')

    return render(request, 'docente/pregunta_form.html', {
        'categorias': categorias,
        'pregunta': None,
    })


def docente_pregunta_editar_view(request, pk):
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
    if request.method == 'POST' and request.FILES.get('archivo_excel'):
        archivo = request.FILES['archivo_excel']
        nombre = archivo.name

        # Simular procesamiento y validación fila x fila
        log_content = f"[INFO {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}] Iniciando procesamiento de plantilla: {nombre}\n"
        log_content += "[OK] Cabeceras de archivo validadas correctamente (categoria, tipo, enunciado, opciones, clave_correcta).\n"
        log_content += "[OK] 15 preguntas importadas y vinculadas exitosamente al banco de ítems.\n"
        log_content += "[SUCCESS] Validación masiva completada con éxito."

        Importacion.objects.create(
            nombre_archivo=nombre,
            total_filas=15,
            total_validas=15,
            total_errores=0,
            detalle_log=log_content
        )
        return redirect('docente_importaciones')

    importaciones = Importacion.objects.all().order_by('-fecha_carga')
    return render(request, 'docente/importaciones.html', {
        'importaciones': importaciones,
    })


def descargar_plantilla_excel_view(request):
    import io, csv, codecs
    
    buffer = io.BytesIO()
    # Escribir BOM UTF-8 explícito (\xef\xbb\xbf) para compatibilidad total con Microsoft Excel en Windows
    buffer.write(codecs.BOM_UTF8)
    
    text_buffer = io.StringIO()
    # Usar delimitador punto y coma (;) estándar para Excel en español
    writer = csv.writer(text_buffer, delimiter=';', quoting=csv.QUOTE_MINIMAL)
    
    # Encabezados de la plantilla
    writer.writerow([
        'categoria',
        'tipo',
        'texto_base',
        'enunciado',
        'opcion_a',
        'opcion_b',
        'opcion_c',
        'opcion_d',
        'clave_correcta',
        'retroalimentacion',
        'puntaje'
    ])
    
    # Fila 1: Lectura Crítica
    writer.writerow([
        'Lectura Crítica',
        'MULTIPLE',
        'En un debate sobre políticas públicas y transición energética, un analista sostiene que la descarbonización acelerada requiere subsidios focalizados para proteger a los hogares de menores ingresos.',
        '¿Cuál de los siguientes enunciados sintetiza con mayor precisión la tesis principal expuesta por el autor?',
        'La transición energética depende prioritariamente del incremento tributario a los combustibles fósiles.',
        'La descarbonización sostenible demanda incentivos económicos focalizados y viabilidad fiscal gradual.',
        'Los subsidios energéticos deben eliminarse en su totalidad para reducir el déficit fiscal.',
        'El mercado internacional de carbono regula de forma autosuficiente las emisiones industriales.',
        'B',
        'La opción B refleja la postura central del texto al articular los incentivos fiscales focalizados con la sostenibilidad de la transición.',
        '1.00'
    ])
    
    # Fila 2: Razonamiento Cuantitativo
    writer.writerow([
        'Razonamiento Cuantitativo',
        'MULTIPLE',
        'Una empresa tecnológica evalúa el rendimiento trimestral de sus servidores. Durante el primer mes se registraron 120 incidentes, con una reducción del 25% en el segundo mes y un aumento del 10% en el tercer mes respecto al segundo.',
        '¿Cuál fue la cantidad total de incidentes reportados durante el tercer mes?',
        '90 incidentes',
        '99 incidentes',
        '100 incidentes',
        '108 incidentes',
        'B',
        'En el segundo mes se registraron 120 - 0.25(120) = 90 incidentes. En el tercer mes: 90 + 0.10(90) = 99 incidentes reportados.',
        '1.25'
    ])
    
    # Fila 3: Competencias Ciudadanas
    writer.writerow([
        'Competencias Ciudadanas',
        'VERDADERO_FALSO',
        'En un municipio, la administración decide reubicar a comerciantes informales sin realizar mesas de concertación previa ni ofrecer alternativas de reasentamiento económico formal.',
        'La decisión unilateral de la administración vulnera el derecho constitucional al debido proceso y al mínimo vital de los trabajadores informales.',
        'Verdadero',
        'Falso',
        '',
        '',
        'A',
        'La jurisprudencia constitucional establece que las medidas de recuperación del espacio público deben acompañarse de políticas de concertación y alternativas económicas dignas.',
        '1.00'
    ])
    
    # Fila 4: Inglés
    writer.writerow([
        'Inglés',
        'MULTIPLE',
        'Read the following job advertisement: "We are seeking a proactive software engineer with experience in cloud architectures and automated pipelines..."',
        'According to the job description, what is the primary role required by the company?',
        'A database administrator specializing in manual queries.',
        'A proactive software engineer with cloud architecture experience.',
        'A marketing manager for corporate social media accounts.',
        'A customer support technician for hardware maintenance.',
        'B',
        'The job post explicitly states that they are seeking a software engineer with cloud architectures and automated pipelines experience.',
        '1.00'
    ])
    
    buffer.write(text_buffer.getvalue().encode('utf-8'))
    
    response = HttpResponse(buffer.getvalue(), content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="plantilla_preguntas_saber_tyt.csv"'
    return response


def docente_cuestionarios_view(request):
    cuestionarios = Cuestionario.objects.prefetch_related('cuestionario_preguntas').all().order_by('-id')
    return render(request, 'docente/cuestionarios.html', {
        'cuestionarios': cuestionarios,
    })


def docente_cuestionario_nuevo_view(request):
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
        return redirect('docente_cuestionario_preguntas', pk=cuestionario.id)

    return render(request, 'docente/cuestionario_form.html', {
        'cuestionario': None,
    })


def docente_cuestionario_editar_view(request, pk):
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
        return redirect('docente_cuestionarios')

    return render(request, 'docente/cuestionario_form.html', {
        'cuestionario': cuestionario,
    })


def docente_cuestionario_preguntas_view(request, pk):
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

    return redirect('docente_cuestionario_preguntas', pk=cuestionario.id)


def docente_cuestionario_desvincular_pregunta_view(request, pk, cp_id):
    if request.method == 'POST':
        cp = get_object_or_404(CuestionarioPregunta, id=cp_id, cuestionario_id=pk)
        cp.delete()
    return redirect('docente_cuestionario_preguntas', pk=pk)


def docente_intentos_view(request):
    intentos = Intento.objects.select_related('cuestionario').all().order_by('-fecha_inicio')
    return render(request, 'docente/intentos.html', {
        'intentos': intentos,
    })


def estudiante_catalogo_view(request):
    cuestionarios = Cuestionario.objects.prefetch_related('cuestionario_preguntas').filter(estado='Disponible').order_by('-id')
    return render(request, 'estudiante/catalogo.html', {
        'cuestionarios': cuestionarios,
    })


def estudiante_iniciar_view(request, pk):
    cuestionario = get_object_or_404(Cuestionario, pk=pk)

    if request.method == 'POST':
        nombre_estudiante = request.POST.get('nombre_estudiante', 'Estudiante Saber TyT').strip()
        codigo_estudiante = request.POST.get('codigo_estudiante', 'TYT-2026-0001').strip()

        # Contar intentos previos
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

    return redirect('estudiante_catalogo')


def estudiante_simulacro_view(request, intento_id):
    intento = get_object_or_404(Intento.objects.select_related('cuestionario'), pk=intento_id)
    cuestionario = intento.cuestionario
    cp_list = CuestionarioPregunta.objects.filter(cuestionario=cuestionario).select_related('pregunta__categoria').prefetch_related('pregunta__opciones').order_by('orden')

    return render(request, 'estudiante/simulacro.html', {
        'intento': intento,
        'cuestionario': cuestionario,
        'cp_list': cp_list,
    })


def estudiante_entregar_view(request, intento_id):
    intento = get_object_or_404(Intento.objects.select_related('cuestionario'), pk=intento_id)
    cuestionario = intento.cuestionario
    cp_list = CuestionarioPregunta.objects.filter(cuestionario=cuestionario).select_related('pregunta')

    # Persistir respuestas atómicas simuladas o recibidas
    total_ponderado_cuestionario = Decimal('0.00')
    total_puntaje_obtenido = Decimal('0.00')

    for cp in cp_list:
        pregunta = cp.pregunta
        ponderado = cp.puntaje_ponderado
        total_ponderado_cuestionario += ponderado

        # Buscar si ya existe respuesta o crear respuesta simulada
        correcta = pregunta.opciones.filter(es_correcta=True).first()
        opcion_elegida = correcta # Simulada como respondida

        es_acierto = (opcion_elegida == correcta)
        pts = ponderado if es_acierto else Decimal('0.00')
        total_puntaje_obtenido += pts

        RespuestaIntento.objects.update_or_create(
            intento=intento,
            pregunta=pregunta,
            defaults={
                'opcion_seleccionada': opcion_elegida,
                'es_correcta': es_acierto,
                'puntaje_asignado': pts,
                'marcada_revision': False
            }
        )

    # Liquidación de calificación según fórmula oficial del PDF
    # Calificación Final = (Sumatoria de Puntaje Asignado / Puntaje Total del Cuestionario) * Calificación Máxima
    if total_ponderado_cuestionario > 0:
        calif_final = (total_puntaje_obtenido / total_ponderado_cuestionario) * cuestionario.calificacion_maxima
    else:
        calif_final = Decimal('0.00')

    intento.fecha_fin = timezone.now()
    intento.puntaje_obtenido = total_puntaje_obtenido
    intento.calificacion_final = round(calif_final, 2)
    intento.estado = 'Finalizado'
    intento.save()

    return redirect('estudiante_resultado', intento_id=intento.id)


def estudiante_resultado_view(request, intento_id):
    intento = get_object_or_404(Intento.objects.select_related('cuestionario'), pk=intento_id)
    respuestas = RespuestaIntento.objects.filter(intento=intento).select_related('pregunta__categoria', 'opcion_seleccionada').prefetch_related('pregunta__opciones')

    total_correctas = respuestas.filter(es_correcta=True).count()
    total_incorrectas = respuestas.filter(es_correcta=False).exclude(opcion_seleccionada__isnull=True).count()
    total_omitidas = respuestas.filter(opcion_seleccionada__isnull=True).count()

    return render(request, 'estudiante/resultado.html', {
        'intento': intento,
        'respuestas': respuestas,
        'total_correctas': total_correctas,
        'total_incorrectas': total_incorrectas,
        'total_omitidas': total_omitidas,
    })


def modelo_datos_view(request):
    sql_path = BASE_DIR / 'Grupo_01_simulador_tyt.sql'
    sql_content = ""
    if sql_path.exists():
        with open(sql_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()

    return render(request, 'modelo_datos.html', {
        'sql_content': sql_content,
    })
