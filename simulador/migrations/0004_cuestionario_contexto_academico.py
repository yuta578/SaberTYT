from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("simulador", "0003_permiso_tokenrevocado_intento_usuario_rol_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="cuestionario",
            name="anio_academico",
            field=models.PositiveIntegerField(default=2026, verbose_name="Año académico"),
        ),
        migrations.AddField(
            model_name="cuestionario",
            name="periodo_academico",
            field=models.CharField(
                default="2026-1", max_length=20, verbose_name="Período académico"
            ),
        ),
        migrations.AddField(
            model_name="cuestionario",
            name="curso_grupo",
            field=models.CharField(
                default="General", max_length=100, verbose_name="Curso / grupo"
            ),
        ),
    ]
