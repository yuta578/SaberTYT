import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from datetime import datetime, timedelta
from django.utils import timezone
from decimal import Decimal

from simulador.models import (
    Categoria, Pregunta, OpcionRespuesta, Cuestionario,
    CuestionarioPregunta, Importacion, Intento, RespuestaIntento
)

def run_seed():
    print("Iniciando sembrado de datos pedagógicos para Simulador Saber TyT...")
    
    # 1. Categorías / Competencias
    cat_lectura, _ = Categoria.objects.get_or_create(
        nombre="Lectura Crítica",
        defaults={"descripcion": "Evalúa la capacidad de entender, interpretar y evaluar textos que pueden encontrarse en la vida cotidiana y en ámbitos académicos no especializados.", "activo": True}
    )
    cat_cuanti, _ = Categoria.objects.get_or_create(
        nombre="Razonamiento Cuantitativo",
        defaults={"descripcion": "Evalúa habilidades para comprender y transformar información cuantitativa, interpretar datos y formular soluciones matemáticas a problemas reales.", "activo": True}
    )
    cat_ciudadanas, _ = Categoria.objects.get_or_create(
        nombre="Competencias Ciudadanas",
        defaults={"descripcion": "Evalúa conocimientos sobre la Constitución Política de Colombia, derechos, deberes y el análisis reflexivo de problemáticas sociales.", "activo": True}
    )
    cat_ingles, _ = Categoria.objects.get_or_create(
        nombre="Inglés",
        defaults={"descripcion": "Evalúa la competencia para comunicarse efectivamente en inglés en niveles A1, A2, B1 de acuerdo al Marco Común Europeo.", "activo": True}
    )
    cat_comunicacion, _ = Categoria.objects.get_or_create(
        nombre="Comunicación Escrita",
        defaults={"descripcion": "Evalúa la coherencia, cohesión y estructuración argumentativa en textos de naturaleza técnica y tecnológica.", "activo": True}
    )

    # 2. Preguntas de Banco
    # P1: Lectura Crítica
    p1, created = Pregunta.objects.get_or_create(
        enunciado="Según el autor del texto, ¿cuál es el argumento central frente a la adopción indiscriminada de tecnologías emergentes en la educación técnica?",
        defaults={
            "categoria": cat_lectura,
            "tipo": "MULTIPLE",
            "texto_base": "«En la última década, la digitalización acelerada ha transformado los entornos educativos. Sin embargo, la simple incorporación de dispositivos sin una renovación pedagógica profunda produce un espejismo de modernidad: el estudiante consume información pasivamente sin desarrollar pensamiento reflexivo ni habilidades de resolución contextualizada.»",
            "retroalimentacion": "La opción correcta sintetiza la tesis del texto: la tecnología por sí sola no genera aprendizaje significativo si no viene acompañada de una transformación pedagógica estructural.",
            "puntaje_base": Decimal("1.25"),
            "activo": True
        }
    )
    if created or not p1.opciones.exists():
        p1.opciones.all().delete()
        OpcionRespuesta.objects.create(pregunta=p1, letra='A', texto="La tecnología reduce los costos operativos de las instituciones técnicas.", es_correcta=False)
        OpcionRespuesta.objects.create(pregunta=p1, letra='B', texto="El uso de dispositivos tecnológicos sin un cambio de modelo pedagógico no garantiza el aprendizaje crítico.", es_correcta=True)
        OpcionRespuesta.objects.create(pregunta=p1, letra='C', texto="Todos los estudiantes aprenden mejor mediante plataformas interactivas automatizadas.", es_correcta=False)
        OpcionRespuesta.objects.create(pregunta=p1, letra='D', texto="La digitalización debe restringirse únicamente a programas universitarios avanzados.", es_correcta=False)

    # P2: Razonamiento Cuantitativo
    p2, created = Pregunta.objects.get_or_create(
        enunciado="Una empresa de desarrollo de software estima que para entregar un proyecto en 20 días se requieren 6 programadores trabajando 8 horas diarias. Si se contratan 2 programadores más con igual rendimiento, ¿cuántos días tardará el equipo en finalizar el proyecto trabajando la misma jornada?",
        defaults={
            "categoria": cat_cuanti,
            "tipo": "MULTIPLE",
            "texto_base": "Considere una relación de proporcionalidad inversa donde el tiempo de finalización varía en proporción inversa al número de trabajadores disponibles con rendimiento homogéneo.",
            "retroalimentacion": "Se aplica una regla de tres simple inversa: (6 programadores * 20 días) / 8 programadores = 120 / 8 = 15 días.",
            "puntaje_base": Decimal("1.25"),
            "activo": True
        }
    )
    if created or not p2.opciones.exists():
        p2.opciones.all().delete()
        OpcionRespuesta.objects.create(pregunta=p2, letra='A', texto="12 días", es_correcta=False)
        OpcionRespuesta.objects.create(pregunta=p2, letra='B', texto="15 días", es_correcta=True)
        OpcionRespuesta.objects.create(pregunta=p2, letra='C', texto="18 días", es_correcta=False)
        OpcionRespuesta.objects.create(pregunta=p2, letra='D', texto="24 días", es_correcta=False)

    # P3: Competencias Ciudadanas
    p3, created = Pregunta.objects.get_or_create(
        enunciado="Ante la decisión de una alcaldía de restringir el paso de vehículos particulares en el centro histórico para reducir emisiones contaminantes, los comerciantes del sector protestan alegando una disminución drástica en sus ventas. En esta situación, ¿cuáles dimensiones o intereses están en conflicto?",
        defaults={
            "categoria": cat_ciudadanas,
            "tipo": "MULTIPLE",
            "texto_base": "El artículo 79 de la Constitución Política garantiza el derecho de todas las personas a gozar de un ambiente sano, mientras que el artículo 333 consagra la libertad de empresa y la iniciativa privada dentro de los límites del bien común.",
            "retroalimentacion": "El conflicto radica en la tensión entre la protección del medio ambiente y la salud pública (interés colectivo) frente a la libertad económica y estabilidad comercial de los locatarios.",
            "puntaje_base": Decimal("1.25"),
            "activo": True
        }
    )
    if created or not p3.opciones.exists():
        p3.opciones.all().delete()
        OpcionRespuesta.objects.create(pregunta=p3, letra='A', texto="El derecho a la libre locomoción de los peatones frente al cobro de impuestos de rodamiento.", es_correcta=False)
        OpcionRespuesta.objects.create(pregunta=p3, letra='B', texto="El interés colectivo por un ambiente sano y movilidad sostenible frente a los intereses económicos de los comerciantes.", es_correcta=True)
        OpcionRespuesta.objects.create(pregunta=p3, letra='C', texto="El presupuesto de obras públicas municipales frente a las directrices del Ministerio de Transporte.", es_correcta=False)
        OpcionRespuesta.objects.create(pregunta=p3, letra='D', texto="La autonomía del gobierno local frente a las leyes de ordenamiento territorial nacional.", es_correcta=False)

    # P4: Inglés
    p4, created = Pregunta.objects.get_or_create(
        enunciado="Complete the sentence: If the development team ______ the automated unit tests before deploying, they would have caught the critical database bug earlier.",
        defaults={
            "categoria": cat_ingles,
            "tipo": "MULTIPLE",
            "texto_base": "Third conditional structures are used to talk about unreal situations in the past and their hypothetical results.",
            "retroalimentacion": "The Third Conditional structure requires 'had + past participle' in the if-clause: 'If the team had run the automated tests...'",
            "puntaje_base": Decimal("1.25"),
            "activo": True
        }
    )
    if created or not p4.opciones.exists():
        p4.opciones.all().delete()
        OpcionRespuesta.objects.create(pregunta=p4, letra='A', texto="has run", es_correcta=False)
        OpcionRespuesta.objects.create(pregunta=p4, letra='B', texto="had run", es_correcta=True)
        OpcionRespuesta.objects.create(pregunta=p4, letra='C', texto="would run", es_correcta=False)
        OpcionRespuesta.objects.create(pregunta=p4, letra='D', texto="is running", es_correcta=False)

    # P5: Verdadero/Falso - Lectura Crítica
    p5, created = Pregunta.objects.get_or_create(
        enunciado="¿Un argumento deductivo válido garantiza necesariamente la verdad de su conclusión, siempre y cuando todas sus premisas sean verdaderas?",
        defaults={
            "categoria": cat_lectura,
            "tipo": "VERDADERO_FALSO",
            "texto_base": "En lógica formal, la validez se refiere a la estructura inferencial del razonamiento, mientras que la solidez requiere tanto validez lógica como premisas empíricamente verdaderas.",
            "retroalimentacion": "Verdadero. En un argumento deductivo válido con premisas verdaderas (argumento sólido), la conclusión es forzosamente verdadera.",
            "puntaje_base": Decimal("1.00"),
            "activo": True
        }
    )
    if created or not p5.opciones.exists():
        p5.opciones.all().delete()
        OpcionRespuesta.objects.create(pregunta=p5, letra='A', texto="Verdadero", es_correcta=True)
        OpcionRespuesta.objects.create(pregunta=p5, letra='B', texto="Falso", es_correcta=False)

    # 3. Cuestionarios
    now = timezone.now()
    c1, _ = Cuestionario.objects.get_or_create(
        nombre="Simulacro General Saber TyT 2026 - Módulo Genéricas",
        defaults={
            "descripcion": "Simulador oficial de competencias genéricas: Lectura Crítica, Razonamiento Cuantitativo, Competencias Ciudadanas e Inglés. Diseñado según los lineamientos del ICFES.",
            "fecha_apertura": now - timedelta(days=2),
            "fecha_cierre": now + timedelta(days=15),
            "tiempo_limite_minutos": 45,
            "intentos_permitidos": 2,
            "calificacion_maxima": Decimal("5.00"),
            "calificacion_aprobacion": Decimal("3.00"),
            "mezclar_preguntas": True,
            "mezclar_respuestas": True,
            "permitir_revision": True,
            "estado": "Disponible"
        }
    )

    c2, _ = Cuestionario.objects.get_or_create(
        nombre="Evaluación Diagnóstica: Razonamiento Cuantitativo y Lógica",
        defaults={
            "descripcion": "Prueba corta de diagnóstico previo a la jornada de refuerzo institucional.",
            "fecha_apertura": now - timedelta(days=5),
            "fecha_cierre": now + timedelta(days=5),
            "tiempo_limite_minutos": 30,
            "intentos_permitidos": 1,
            "calificacion_maxima": Decimal("5.00"),
            "calificacion_aprobacion": Decimal("3.50"),
            "mezclar_preguntas": False,
            "mezclar_respuestas": False,
            "permitir_revision": True,
            "estado": "Disponible"
        }
    )

    c3, _ = Cuestionario.objects.get_or_create(
        nombre="Simulacro Especial Inglés B1 - Saber TyT",
        defaults={
            "descripcion": "Batería de preguntas enfocadas en comprensión lectora y estructuras gramaticales en lengua extranjera.",
            "fecha_apertura": now + timedelta(days=3),
            "fecha_cierre": now + timedelta(days=20),
            "tiempo_limite_minutos": 60,
            "intentos_permitidos": 3,
            "calificacion_maxima": Decimal("100.00"),
            "calificacion_aprobacion": Decimal("60.00"),
            "mezclar_preguntas": True,
            "mezclar_respuestas": True,
            "permitir_revision": True,
            "estado": "Programado"
        }
    )

    # 4. Asignación de Preguntas a Cuestionarios
    for i, p in enumerate([p1, p2, p3, p4, p5], 1):
        CuestionarioPregunta.objects.get_or_create(
            cuestionario=c1,
            pregunta=p,
            defaults={"orden": i, "puntaje_ponderado": Decimal("1.00")}
        )

    # 5. Importaciones de Ejemplo
    Importacion.objects.get_or_create(
        nombre_archivo="Banco_Preguntas_Lectura_Critica_SaberTyT_2026.xlsx",
        defaults={
            "total_filas": 25,
            "total_validas": 24,
            "total_errores": 1,
            "detalle_log": "[INFO 2026-09-18 10:15:00] Procesando archivo .xlsx con 25 registros...\n[OK] Fila 1 a 14 validadas e importadas correctamente.\n[WARN] Fila 15: Opción 'D' tenía espacios sobrantes, se normalizó.\n[ERROR] Fila 22: No se especificó la clave de respuesta correcta (es_correcta = TRUE). Registro omitido.\n[OK] Fila 23 a 25 validadas con éxito.\n[SUMMARY] 24 preguntas añadidas a la base de datos, 1 error reportado."
        }
    )

    Importacion.objects.get_or_create(
        nombre_archivo="Preguntas_Razonamiento_Cuantitativo_Mod1.xlsx",
        defaults={
            "total_filas": 18,
            "total_validas": 18,
            "total_errores": 0,
            "detalle_log": "[INFO 2026-09-19 14:30:10] Validación masiva iniciada.\n[OK] Todas las 18 preguntas cumplieron con la regla R04 (Clave única de respuesta) y R05 (4 alternativas estructuradas).\n[SUCCESS] Importación finalizada con 100% de efectividad."
        }
    )

    # 6. Intentos de Ejemplo
    intento1, _ = Intento.objects.get_or_create(
        cuestionario=c1,
        codigo_estudiante="TYT-2026-0891",
        numero_intento=1,
        defaults={
            "nombre_estudiante": "Eduardo Alexander López",
            "fecha_fin": now - timedelta(hours=2),
            "puntaje_obtenido": Decimal("4.00"),
            "calificacion_final": Decimal("4.00"),
            "estado": "Finalizado"
        }
    )

    # Respuestas de Intento 1
    opc_p1_correcta = p1.opciones.filter(es_correcta=True).first()
    opc_p2_correcta = p2.opciones.filter(es_correcta=True).first()
    opc_p3_correcta = p3.opciones.filter(es_correcta=True).first()
    opc_p4_incorrecta = p4.opciones.filter(es_correcta=False).first()

    RespuestaIntento.objects.get_or_create(
        intento=intento1,
        pregunta=p1,
        defaults={"opcion_seleccionada": opc_p1_correcta, "es_correcta": True, "puntaje_asignado": Decimal("1.00"), "marcada_revision": False}
    )
    RespuestaIntento.objects.get_or_create(
        intento=intento1,
        pregunta=p2,
        defaults={"opcion_seleccionada": opc_p2_correcta, "es_correcta": True, "puntaje_asignado": Decimal("1.00"), "marcada_revision": False}
    )
    RespuestaIntento.objects.get_or_create(
        intento=intento1,
        pregunta=p3,
        defaults={"opcion_seleccionada": opc_p3_correcta, "es_correcta": True, "puntaje_asignado": Decimal("1.00"), "marcada_revision": True}
    )
    RespuestaIntento.objects.get_or_create(
        intento=intento1,
        pregunta=p4,
        defaults={"opcion_seleccionada": opc_p4_incorrecta, "es_correcta": False, "puntaje_asignado": Decimal("0.00"), "marcada_revision": False}
    )
    RespuestaIntento.objects.get_or_create(
        intento=intento1,
        pregunta=p5,
        defaults={"opcion_seleccionada": p5.opciones.filter(es_correcta=True).first(), "es_correcta": True, "puntaje_asignado": Decimal("1.00"), "marcada_revision": False}
    )

    print("Datos sembrados exitosamente!")

if __name__ == '__main__':
    run_seed()
