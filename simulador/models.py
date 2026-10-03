from django.db import models

class Categoria(models.Model):
    nombre = models.CharField(max_length=120, verbose_name="Nombre de Competencia / Categoría")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'categorias'
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'

    def __str__(self):
        return self.nombre


class Pregunta(models.Model):
    TIPO_CHOICES = [
        ('MULTIPLE', 'Opción Múltiple con Única Respuesta'),
        ('VERDADERO_FALSO', 'Verdadero / Falso'),
    ]

    categoria = models.ForeignKey(Categoria, on_delete=models.RESTRICT, related_name='preguntas', verbose_name="Categoría / Módulo")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='MULTIPLE', verbose_name="Tipo de Pregunta")
    texto_base = models.TextField(blank=True, null=True, verbose_name="Texto Base / Contexto de Lectura")
    enunciado = models.TextField(verbose_name="Enunciado de la Pregunta")
    retroalimentacion = models.TextField(blank=True, null=True, verbose_name="Retroalimentación Pedagógica")
    puntaje_base = models.DecimalField(max_digits=5, decimal_places=2, default=1.00, verbose_name="Puntaje Base")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'preguntas'
        verbose_name = 'Pregunta'
        verbose_name_plural = 'Preguntas'

    def __str__(self):
        return f"[{self.categoria.nombre}] {self.enunciado[:60]}..."


class OpcionRespuesta(models.Model):
    LETRA_CHOICES = [
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
    ]

    pregunta = models.ForeignKey(Pregunta, on_delete=models.CASCADE, related_name='opciones', verbose_name="Pregunta")
    letra = models.CharField(max_length=1, choices=LETRA_CHOICES, verbose_name="Letra de Opción")
    texto = models.TextField(verbose_name="Texto de la Alternativa")
    es_correcta = models.BooleanField(default=False, verbose_name="¿Es la opción correcta?")

    class Meta:
        db_table = 'opciones_respuesta'
        verbose_name = 'Opción de Respuesta'
        verbose_name_plural = 'Opciones de Respuesta'

    def __str__(self):
        return f"({self.letra}) {self.texto[:40]}"


class Cuestionario(models.Model):
    ESTADO_CHOICES = [
        ('Borrador', 'Borrador'),
        ('Programado', 'Programado'),
        ('Disponible', 'Disponible'),
        ('Cerrado', 'Cerrado'),
    ]

    nombre = models.CharField(max_length=150, verbose_name="Nombre de la Evaluación / Simulacro")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción o Instrucciones")
    fecha_apertura = models.DateTimeField(verbose_name="Fecha y Hora de Apertura")
    fecha_cierre = models.DateTimeField(verbose_name="Fecha y Hora de Cierre")
    tiempo_limite_minutos = models.IntegerField(verbose_name="Tiempo Límite (Minutos)")
    intentos_permitidos = models.IntegerField(default=1, verbose_name="Intentos Permitidos")
    calificacion_maxima = models.DecimalField(max_digits=5, decimal_places=2, default=5.00, verbose_name="Calificación Máxima")
    calificacion_aprobacion = models.DecimalField(max_digits=5, decimal_places=2, default=3.00, verbose_name="Calificación Mínima Aprobatoria")
    mezclar_preguntas = models.BooleanField(default=False, verbose_name="Mezclar Preguntas Aleatoriamente")
    mezclar_respuestas = models.BooleanField(default=False, verbose_name="Mezclar Respuestas Aleatoriamente")
    permitir_revision = models.BooleanField(default=True, verbose_name="Permitir Ver Retroalimentación tras Entrega")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='Disponible', verbose_name="Estado")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'cuestionarios'
        verbose_name = 'Cuestionario'
        verbose_name_plural = 'Cuestionarios'

    def __str__(self):
        return self.nombre


class CuestionarioPregunta(models.Model):
    cuestionario = models.ForeignKey(Cuestionario, on_delete=models.CASCADE, related_name='cuestionario_preguntas')
    pregunta = models.ForeignKey(Pregunta, on_delete=models.RESTRICT, related_name='cuestionarios_asignados')
    orden = models.IntegerField(default=1, verbose_name="Orden de Aparición")
    puntaje_ponderado = models.DecimalField(max_digits=5, decimal_places=2, default=1.00, verbose_name="Puntaje Ponderado")

    class Meta:
        db_table = 'cuestionario_preguntas'
        unique_together = ('cuestionario', 'pregunta')
        verbose_name = 'Pregunta de Cuestionario'
        verbose_name_plural = 'Preguntas de Cuestionario'
        ordering = ['orden']


class Importacion(models.Model):
    nombre_archivo = models.CharField(max_length=255, verbose_name="Nombre del Archivo")
    fecha_carga = models.DateTimeField(auto_now_add=True, verbose_name="Fecha y Hora de Carga")
    total_filas = models.IntegerField(default=0, verbose_name="Total Filas Evaluadas")
    total_validas = models.IntegerField(default=0, verbose_name="Filas Válidas Importadas")
    total_errores = models.IntegerField(default=0, verbose_name="Filas con Error")
    detalle_log = models.TextField(blank=True, null=True, verbose_name="Bitácora Detallada de Validación")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'importaciones'
        verbose_name = 'Importación Masiva'
        verbose_name_plural = 'Importaciones Masivas'
        ordering = ['-fecha_carga']

    def __str__(self):
        return f"{self.nombre_archivo} ({self.fecha_carga.strftime('%Y-%m-%d %H:%M')})"


class Intento(models.Model):
    ESTADO_INTENTO = [
        ('En Progreso', 'En Progreso'),
        ('Finalizado', 'Finalizado'),
        ('Anulado', 'Anulado'),
    ]

    cuestionario = models.ForeignKey(Cuestionario, on_delete=models.RESTRICT, related_name='intentos')
    nombre_estudiante = models.CharField(max_length=120, verbose_name="Nombre del Estudiante")
    codigo_estudiante = models.CharField(max_length=30, verbose_name="Código Institucional")
    numero_intento = models.IntegerField(default=1, verbose_name="Número de Intento")
    fecha_inicio = models.DateTimeField(auto_now_add=True, verbose_name="Fecha y Hora de Inicio")
    fecha_fin = models.DateTimeField(blank=True, null=True, verbose_name="Fecha y Hora de Finalización")
    puntaje_obtenido = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name="Puntaje Obtenido")
    calificacion_final = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name="Calificación Final")
    estado = models.CharField(max_length=20, choices=ESTADO_INTENTO, default='En Progreso', verbose_name="Estado de la Sesión")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'intentos'
        verbose_name = 'Intento de Estudiante'
        verbose_name_plural = 'Intentos de Estudiantes'
        ordering = ['-fecha_inicio']

    def __str__(self):
        return f"Intento #{self.numero_intento} - {self.nombre_estudiante} ({self.codigo_estudiante})"


class RespuestaIntento(models.Model):
    intento = models.ForeignKey(Intento, on_delete=models.CASCADE, related_name='respuestas')
    pregunta = models.ForeignKey(Pregunta, on_delete=models.RESTRICT, related_name='respuestas_evaluadas')
    opcion_seleccionada = models.ForeignKey(OpcionRespuesta, on_delete=models.SET_NULL, blank=True, null=True, verbose_name="Opción Seleccionada (NULL si omisión)")
    es_correcta = models.BooleanField(default=False, verbose_name="¿Es correcta?")
    puntaje_asignado = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, verbose_name="Puntaje Asignado")
    marcada_revision = models.BooleanField(default=False, verbose_name="Marcada para Revisión")

    class Meta:
        db_table = 'respuestas_intento'
        unique_together = ('intento', 'pregunta')
        verbose_name = 'Respuesta de Intento'
        verbose_name_plural = 'Respuestas de Intento'
