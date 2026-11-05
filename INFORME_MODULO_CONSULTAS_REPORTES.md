# Informe de implementación — Módulo de consultas, reportes y Excel

## Alcance

Se implementó el módulo solicitado en la guía **Trabajo Módulo Consultas Reportes Saber TyT** sobre el proyecto Django existente, conservando autenticación, permisos, simulacros y respuestas históricas.

La regla visible de calificación es:

- Escala: `0,00` a `5,00`.
- Aprobación: `>= 3,00`.
- Solo se incluyen en reportes los intentos `Finalizado` con calificación no nula.
- Las respuestas omitidas no se cuentan como respuestas contestadas ni como errores.
- La calificación histórica no se recalcula ni se modifica para consultar o exportar.

## Cambios realizados

### 1. Contexto académico y filtros jerárquicos

Se agregaron a `Cuestionario` los campos:

- `anio_academico`
- `periodo_academico`
- `curso_grupo`

La migración compatible es [`simulador/migrations/0004_cuestionario_contexto_academico.py`](simulador/migrations/0004_cuestionario_contexto_academico.py). El formulario docente permite registrar estos valores al crear o editar un simulacro.

La pantalla [`templates/admin/reportes.html`](templates/admin/reportes.html) presenta, en orden, los cinco filtros requeridos:

`Año → Período → Curso / grupo → Eje temático → Estudiante`

Los períodos y cursos se recalculan según el filtro padre. El enlace **Limpiar filtros** restaura la consulta general permitida.

### 2. Consultas y estadísticas

La lógica compartida está en [`simulador/views.py`](simulador/views.py):

- `_report_filter_context`: filtros ORM y ordenamiento.
- `_report_context`: indicadores y agregados.
- `_report_axis_rows`: desempeño por eje desde respuestas efectivamente contestadas.
- `_report_difficulty_rows`: preguntas con mayor dificultad.
- `admin_reportes_view`: pantalla de consultas.
- `admin_exportar_reporte_view`: exportaciones completas.

La pantalla incluye:

1. Consolidado general.
2. Resultados por año y período.
3. Resultados por curso/grupo.
4. Desempeño por eje temático.
5. Calificaciones por estudiante.
6. Historial individual filtrable por estudiante.
7. Preguntas de mayor dificultad.

La tabla principal usa paginación de 10 registros y conserva los filtros en los enlaces de página. Las métricas se calculan sobre el conjunto completo, no sobre la página visible.

### 3. Exportación real a Excel

Se agregaron estas rutas protegidas:

- `/admin-panel/reportes/exportar/A/` — consolidado general.
- `/admin-panel/reportes/exportar/B/` — desempeño por eje.
- `/admin-panel/reportes/exportar/C/` — historial individual.

Los archivos se generan con `openpyxl`, incluyen nombre del reporte, fecha de generación, filtros activos, encabezados, datos completos y formato decimal `0.00`. La exportación usa el mismo queryset filtrado que la pantalla y no queda limitada por la paginación.

### 4. Seguridad

Las rutas de consulta y exportación están protegidas con `permission_required('view_results')`. Un usuario no autenticado es redirigido al login y un usuario sin permiso recibe `403`; cambiar manualmente los parámetros de la URL no evita el filtro ni el control de permisos.

## Ruta de datos

```text
Usuario
  └── Intento.usuario / nombre_estudiante / codigo_estudiante
        └── Intento.cuestionario
              ├── anio_academico
              ├── periodo_academico
              └── curso_grupo
        └── RespuestaIntento
              └── Pregunta.categoria (eje temático)
                    └── OpcionRespuesta (contestada/correcta)
```

La nota final ya persistida en `Intento.calificacion_final` se consulta sin alterarla. La liquidación original del simulacro conserva la fórmula existente: `(puntaje obtenido / total ponderado) * calificación máxima`.

## Evidencias

### Pantalla principal con los cinco filtros

![Pantalla general de consultas](evidencias/consultas-general.png)

### Consulta con filtros aplicados

![Consulta filtrada](evidencias/consultas-filtrada.png)

### Archivos Excel generados por el sistema

- [Reporte A — Consolidado general](evidencias/reporte_A_demo.xlsx)
- [Reporte B — Desempeño por eje temático](evidencias/reporte_B_demo.xlsx)
- [Reporte C — Historial individual](evidencias/reporte_C_demo.xlsx)

Los tres archivos fueron abiertos programáticamente con `openpyxl` y se verificó que contienen hojas válidas, encabezados y filas de datos.

## Validación ejecutada

```text
python manage.py check
System check identified no issues (0 silenced).

python manage.py makemigrations --check --dry-run
No changes detected

python manage.py test simulador
Ran 5 tests in 4.660s
OK
```

Las pruebas cubren autenticación, rechazo de acceso sin permiso, filtros jerárquicos, indicadores, generación de Excel y contenido XLSX válido.
