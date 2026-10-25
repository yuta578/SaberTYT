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

    # P6: Razonamiento Cuantitativo - Porcentajes e IVA
    p6, created = Pregunta.objects.get_or_create(
        enunciado="Un comerciante compra un lote de mercancías por un valor neto de $4.500.000 COP antes de impuestos. El proveedor le aplica un descuento comercial del 10% por pago de contado, y sobre el valor resultante se liquida el IVA del 19%. ¿Cuál es el valor total que debe pagar el comerciante?",
        defaults={
            "categoria": cat_cuanti,
            "tipo": "MULTIPLE",
            "texto_base": "En operaciones comerciales formales, los descuentos comerciales pactados se descuentan de la base gravable antes de calcular el Impuesto sobre las Ventas (IVA).",
            "retroalimentacion": "Base neta con descuento: $4.500.000 * 0.90 = $4.050.000. Total con IVA: $4.050.000 * 1.19 = $4.819.500 COP.",
            "puntaje_base": Decimal("1.00"),
            "activo": True
        }
    )
    if created or not p6.opciones.exists():
        p6.opciones.all().delete()
        OpcionRespuesta.objects.create(pregunta=p6, letra='A', texto="$4.819.500 COP", es_correcta=True)
        OpcionRespuesta.objects.create(pregunta=p6, letra='B', texto="$4.500.000 COP", es_correcta=False)
        OpcionRespuesta.objects.create(pregunta=p6, letra='C', texto="$5.355.000 COP", es_correcta=False)
        OpcionRespuesta.objects.create(pregunta=p6, letra='D', texto="$4.050.000 COP", es_correcta=False)

    # P7: Razonamiento Cuantitativo - Estadística y Personal
    p7, created = Pregunta.objects.get_or_create(
        enunciado="En una empresa de 200 empleados, el 40% pertenece al área operativa, el 25% al área administrativa, el 20% a ventas y el 15% restante a soporte técnico. Si se capacita únicamente a los trabajadores de las dos áreas con mayor número de personal, ¿cuántos trabajadores asistirán?",
        defaults={
            "categoria": cat_cuanti,
            "tipo": "MULTIPLE",
            "texto_base": "La distribución porcentual de una población permite calcular subconjuntos multiplicando el porcentaje correspondiente por el total poblacional.",
            "retroalimentacion": "Las dos áreas con más personal son Operativa (40% de 200 = 80) y Administrativa (25% de 200 = 50). Total = 80 + 50 = 130 empleados.",
            "puntaje_base": Decimal("1.00"),
            "activo": True
        }
    )
    if created or not p7.opciones.exists():
        p7.opciones.all().delete()
        OpcionRespuesta.objects.create(pregunta=p7, letra='A', texto="130 empleados", es_correcta=True)
        OpcionRespuesta.objects.create(pregunta=p7, letra='B', texto="110 empleados", es_correcta=False)
        OpcionRespuesta.objects.create(pregunta=p7, letra='C', texto="120 empleados", es_correcta=False)
        OpcionRespuesta.objects.create(pregunta=p7, letra='D', texto="90 empleados", es_correcta=False)

    # P8: Razonamiento Cuantitativo - Punto de Equilibrio
    p8, created = Pregunta.objects.get_or_create(
        enunciado="Un taller de confección tiene costos fijos mensuales de $3.000.000 COP. Cada prenda producida tiene un costo variable de $15.000 y se vende en el mercado a $25.000. ¿Cuántas prendas debe producir y vender al mes como mínimo para no tener pérdidas (punto de equilibrio)?",
        defaults={
            "categoria": cat_cuanti,
            "tipo": "MULTIPLE",
            "texto_base": "El punto de equilibrio en unidades se calcula como: Costos Fijos / (Precio de Venta Unitario - Costo Variable Unitario).",
            "retroalimentacion": "Margen de contribución = $25.000 - $15.000 = $10.000. Punto de equilibrio = $3.000.000 / $10.000 = 300 prendas.",
            "puntaje_base": Decimal("1.00"),
            "activo": True
        }
    )
    if created or not p8.opciones.exists():
        p8.opciones.all().delete()
        OpcionRespuesta.objects.create(pregunta=p8, letra='A', texto="250 prendas", es_correcta=False)
        OpcionRespuesta.objects.create(pregunta=p8, letra='B', texto="300 prendas", es_correcta=True)
        OpcionRespuesta.objects.create(pregunta=p8, letra='C', texto="200 prendas", es_correcta=False)
        OpcionRespuesta.objects.create(pregunta=p8, letra='D', texto="350 prendas", es_correcta=False)

    # P9: Razonamiento Cuantitativo - Probabilidad
    p9, created = Pregunta.objects.get_or_create(
        enunciado="En un lote de 500 componentes electrónicos para ensamble técnico, se identificó que 25 presentan fallas de soldadura y 15 presentan defectos de encapsulado, sin que ningún componente tenga ambos defectos a la vez. Al seleccionar un componente al azar, ¿cuál es la probabilidad de que esté defectuoso?",
        defaults={
            "categoria": cat_cuanti,
            "tipo": "MULTIPLE",
            "texto_base": "La probabilidad clásica de un evento mutuamente excluyente se calcula como el número de casos favorables dividido entre el número total de casos posibles.",
            "retroalimentacion": "Total componentes defectuosos = 25 + 15 = 40. Probabilidad = 40 / 500 = 0.08 = 8%.",
            "puntaje_base": Decimal("1.00"),
            "activo": True
        }
    )
    if created or not p9.opciones.exists():
        p9.opciones.all().delete()
        OpcionRespuesta.objects.create(pregunta=p9, letra='A', texto="5%", es_correcta=False)
        OpcionRespuesta.objects.create(pregunta=p9, letra='B', texto="8%", es_correcta=True)
        OpcionRespuesta.objects.create(pregunta=p9, letra='C', texto="10%", es_correcta=False)
        OpcionRespuesta.objects.create(pregunta=p9, letra='D', texto="12%", es_correcta=False)

    # P10: Lógica Proposicional
    p10, created = Pregunta.objects.get_or_create(
        enunciado="Considere la siguiente regla operativa de infraestructura: 'Si el servidor principal supera el 90% de uso de memoria RAM, entonces se activa automáticamente el nodo de contingencia'. Si se comprueba que el nodo de contingencia NO se activó, ¿qué conclusión se desprende con certeza lógica?",
        defaults={
            "categoria": cat_cuanti,
            "tipo": "MULTIPLE",
            "texto_base": "En lógica formal, la regla de inferencia Modus Tollens establece que si P implica Q, y la consecuencia Q es falsa, el antecedente P necesariamente es falso.",
            "retroalimentacion": "Por regla de Modus Tollens: Si (P -> Q) y (No Q), entonces (No P). Por lo tanto, el servidor principal no superó el 90% de uso de memoria.",
            "puntaje_base": Decimal("1.00"),
            "activo": True
        }
    )
    if created or not p10.opciones.exists():
        p10.opciones.all().delete()
        OpcionRespuesta.objects.create(pregunta=p10, letra='A', texto="El servidor principal no superó el 90% de uso de memoria RAM.", es_correcta=True)
        OpcionRespuesta.objects.create(pregunta=p10, letra='B', texto="El servidor principal colapsó por exceso de peticiones concurrentes.", es_correcta=False)
        OpcionRespuesta.objects.create(pregunta=p10, letra='C', texto="El nodo de contingencia presenta desconfiguración en sus puertos.", es_correcta=False)
        OpcionRespuesta.objects.create(pregunta=p10, letra='D', texto="El uso de memoria alcanzó exactamente el 95%.", es_correcta=False)

    # P11: Inglés - Comprensión Lectora
    p11, created = Pregunta.objects.get_or_create(
        enunciado="According to the passage, why are cloud-native architectures becoming essential for modern organizations?",
        defaults={
            "categoria": cat_ingles,
            "tipo": "MULTIPLE",
            "texto_base": "Cloud-native computing empowers organizations to build and run scalable applications in modern, dynamic environments such as public, private, and hybrid clouds. Technologies such as containers, service meshes, and microservices enable loosely coupled systems that are resilient, manageable, and observable. Coupled with robust automation, they allow engineers to make high-impact changes frequently and predictably with minimal toil.",
            "retroalimentacion": "The text directly states that cloud-native architectures allow engineers to build scalable, resilient systems and make frequent, predictable changes with minimal effort.",
            "puntaje_base": Decimal("20.00"),
            "activo": True
        }
    )
    if created or not p11.opciones.exists():
        p11.opciones.all().delete()
        OpcionRespuesta.objects.create(pregunta=p11, letra='A', texto="Because they eliminate the need for software engineering teams.", es_correcta=False)
        OpcionRespuesta.objects.create(pregunta=p11, letra='B', texto="Because they enable scalable, resilient systems with predictable and frequent deployment.", es_correcta=True)
        OpcionRespuesta.objects.create(pregunta=p11, letra='C', texto="Because they are completely free of operational infrastructure costs.", es_correcta=False)
        OpcionRespuesta.objects.create(pregunta=p11, letra='D', texto="Because they restrict applications to local non-networked servers.", es_correcta=False)

    # P12: Inglés - Vocabulario Técnico
    p12, created = Pregunta.objects.get_or_create(
        enunciado="Choose the word that best completes the sentence: The external cybersecurity audit revealed several vulnerabilities that must be ______ before the production release.",
        defaults={
            "categoria": cat_ingles,
            "tipo": "MULTIPLE",
            "texto_base": "In software development and cybersecurity, fixing vulnerabilities is referred to as patching them.",
            "retroalimentacion": "The correct technical verb is 'patched', which means to fix or remediate software security defects.",
            "puntaje_base": Decimal("20.00"),
            "activo": True
        }
    )
    if created or not p12.opciones.exists():
        p12.opciones.all().delete()
        OpcionRespuesta.objects.create(pregunta=p12, letra='A', texto="patched", es_correcta=True)
        OpcionRespuesta.objects.create(pregunta=p12, letra='B', texto="erased", es_correcta=False)
        OpcionRespuesta.objects.create(pregunta=p12, letra='C', texto="delayed", es_correcta=False)
        OpcionRespuesta.objects.create(pregunta=p12, letra='D', texto="neglected", es_correcta=False)

    # P13: Inglés - Conectores Gramaticales
    p13, created = Pregunta.objects.get_or_create(
        enunciado="Choose the correct connector: The web application experienced severe latency during peak traffic hours ______ the database queries had not been properly indexed.",
        defaults={
            "categoria": cat_ingles,
            "tipo": "MULTIPLE",
            "texto_base": "Clauses of reason and cause explain why an event occurred.",
            "retroalimentacion": "'Because' introduces the cause of the high latency: the unindexed database queries.",
            "puntaje_base": Decimal("20.00"),
            "activo": True
        }
    )
    if created or not p13.opciones.exists():
        p13.opciones.all().delete()
        OpcionRespuesta.objects.create(pregunta=p13, letra='A', texto="despite", es_correcta=False)
        OpcionRespuesta.objects.create(pregunta=p13, letra='B', texto="because", es_correcta=True)
        OpcionRespuesta.objects.create(pregunta=p13, letra='C', texto="however", es_correcta=False)
        OpcionRespuesta.objects.create(pregunta=p13, letra='D', texto="unless", es_correcta=False)

    # P14: Inglés - Modales
    p14, created = Pregunta.objects.get_or_create(
        enunciado="According to institutional security compliance policies, all employees ______ update their multi-factor authentication credentials every semester.",
        defaults={
            "categoria": cat_ingles,
            "tipo": "MULTIPLE",
            "texto_base": "Modal verbs of strong obligation express institutional rules and mandatory duties.",
            "retroalimentacion": "'Must' is the modal verb that expresses mandatory obligation according to security policy.",
            "puntaje_base": Decimal("20.00"),
            "activo": True
        }
    )
    if created or not p14.opciones.exists():
        p14.opciones.all().delete()
        OpcionRespuesta.objects.create(pregunta=p14, letra='A', texto="might", es_correcta=False)
        OpcionRespuesta.objects.create(pregunta=p14, letra='B', texto="must", es_correcta=True)
        OpcionRespuesta.objects.create(pregunta=p14, letra='C', texto="could", es_correcta=False)
        OpcionRespuesta.objects.create(pregunta=p14, letra='D', texto="would", es_correcta=False)

    # P15: Inglés - Phrasal Verbs
    p15, created = Pregunta.objects.get_or_create(
        enunciado="When the client requested unexpected modifications to the contract, the lead engineer scheduled a meeting to ______ the technical feasibility of each request.",
        defaults={
            "categoria": cat_ingles,
            "tipo": "MULTIPLE",
            "texto_base": "Phrasal verbs in workplace communication express specific collaborative actions.",
            "retroalimentacion": "'Go over' means to examine or review something in detail.",
            "puntaje_base": Decimal("20.00"),
            "activo": True
        }
    )
    if created or not p15.opciones.exists():
        p15.opciones.all().delete()
        OpcionRespuesta.objects.create(pregunta=p15, letra='A', texto="look up", es_correcta=False)
        OpcionRespuesta.objects.create(pregunta=p15, letra='B', texto="go over", es_correcta=True)
        OpcionRespuesta.objects.create(pregunta=p15, letra='C', texto="call off", es_correcta=False)
        OpcionRespuesta.objects.create(pregunta=p15, letra='D', texto="give up", es_correcta=False)

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
            "descripcion": "Prueba corta de diagnóstico de Razonamiento Cuantitativo, proporciones, costos y lógica para estudiantes Saber TyT.",
            "fecha_apertura": now - timedelta(days=5),
            "fecha_cierre": now + timedelta(days=15),
            "tiempo_limite_minutos": 30,
            "intentos_permitidos": 2,
            "calificacion_maxima": Decimal("5.00"),
            "calificacion_aprobacion": Decimal("3.50"),
            "mezclar_preguntas": False,
            "mezclar_respuestas": False,
            "permitir_revision": True,
            "estado": "Disponible"
        }
    )
    c2.estado = "Disponible"
    c2.fecha_cierre = now + timedelta(days=15)
    c2.save()

    c3, _ = Cuestionario.objects.get_or_create(
        nombre="Simulacro Especial Inglés B1 - Saber TyT",
        defaults={
            "descripcion": "Batería de reactivos de inglés técnico nivel B1: lectura, vocabulario especializado, conectores y sintaxis.",
            "fecha_apertura": now - timedelta(days=1),
            "fecha_cierre": now + timedelta(days=20),
            "tiempo_limite_minutos": 45,
            "intentos_permitidos": 3,
            "calificacion_maxima": Decimal("5.00"),
            "calificacion_aprobacion": Decimal("3.00"),
            "mezclar_preguntas": True,
            "mezclar_respuestas": True,
            "permitir_revision": True,
            "estado": "Disponible"
        }
    )
    c3.estado = "Disponible"
    c3.fecha_apertura = now - timedelta(days=1)
    c3.fecha_cierre = now + timedelta(days=20)
    c3.save()

    # 4. Asignación de Preguntas a Cuestionarios
    # Cuestionario 1: Genéricas (p1 a p5)
    for i, p in enumerate([p1, p2, p3, p4, p5], 1):
        CuestionarioPregunta.objects.get_or_create(
            cuestionario=c1,
            pregunta=p,
            defaults={"orden": i, "puntaje_ponderado": Decimal("1.00")}
        )

    # Cuestionario 2: Razonamiento Cuantitativo y Lógica (p6 a p10)
    for i, p in enumerate([p6, p7, p8, p9, p10], 1):
        CuestionarioPregunta.objects.get_or_create(
            cuestionario=c2,
            pregunta=p,
            defaults={"orden": i, "puntaje_ponderado": Decimal("1.00")}
        )

    # Cuestionario 3: Inglés B1 (p11 a p15)
    for i, p in enumerate([p11, p12, p13, p14, p15], 1):
        CuestionarioPregunta.objects.get_or_create(
            cuestionario=c3,
            pregunta=p,
            defaults={"orden": i, "puntaje_ponderado": Decimal("20.00")}
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

    # 6. Cuentas de Usuarios de Prueba
    from django.core.management import call_command
    call_command('seed_usuarios')

    print("¡Datos pedagógicos y usuarios de prueba sembrados exitosamente!")

if __name__ == '__main__':
    run_seed()
