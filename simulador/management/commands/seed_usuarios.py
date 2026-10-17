from django.core.management.base import BaseCommand
from simulador.models import Usuario
from simulador.views import generate_random_user_code

INITIAL_USERS = [
    {
        'nombre_completo': 'Ing. Roberto Andrade',
        'codigo_institucional': 'ADM-20200012',
        'email': 'admin@itp.edu.co',
        'password': 'demo1234',
        'rol': 'admin',
        'telefono': '3104509988',
        'programa_academico': 'Dirección TIC y Admisiones',
        'activo': True,
    },
    {
        'nombre_completo': 'Prof. Hernán Díaz Mora',
        'codigo_institucional': 'DOC-20180045',
        'email': 'docente@itp.edu.co',
        'password': 'demo1234',
        'rol': 'docente',
        'telefono': '3128901122',
        'programa_academico': 'Ciencias Económicas, Administrativas y Contables',
        'activo': True,
    },
    {
        'nombre_completo': 'Alexandra Patricia López',
        'codigo_institucional': 'EST-202310023',
        'email': 'estudiante@itp.edu.co',
        'password': 'demo1234',
        'rol': 'estudiante',
        'telefono': '3142234567',
        'programa_academico': 'Tecnología en Gestión Contable',
        'activo': True,
    },
    {
        'nombre_completo': 'Carlos Mario Gómez',
        'codigo_institucional': 'EST-20269988',
        'email': 'carlos.gomez@itp.edu.co',
        'password': 'demo1234',
        'rol': 'estudiante',
        'telefono': '3118902233',
        'programa_academico': 'Tecnología en Gestión Contable',
        'activo': True,
    },
    {
        'nombre_completo': 'Julián Andrés Burbano',
        'codigo_institucional': 'EST-202220412',
        'email': 'julian.burbano@itp.edu.co',
        'password': 'demo1234',
        'rol': 'estudiante',
        'telefono': '3167789900',
        'programa_academico': 'Tecnología en Gestión Contable',
        'activo': True,
    },
]

class Command(BaseCommand):
    help = 'Carga y restaura las cuentas de usuario de prueba institucionales en MySQL'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Elimina y recrea las cuentas institucionales de prueba por defecto'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Verificando y cargando cuentas de prueba institucionales en MySQL..."))
        creados = 0
        actualizados = 0

        for data in INITIAL_USERS:
            email = data['email']
            desired_code = data['codigo_institucional']
            
            # Buscar por email primero
            user = Usuario.objects.filter(email__iexact=email).first()
            
            if user:
                # Ya existe este usuario por email: restablecer contraseña, rol y activo
                user.set_password(data['password'])
                user.rol = data['rol']
                user.activo = True
                user.save()
                actualizados += 1
                self.stdout.write(self.style.WARNING(f"  [~] Restablecido: {user.nombre_completo} ({user.codigo_institucional}) | Email: {email} | Pass: {data['password']}"))
            else:
                # Si el código institucional deseado ya está en uso por otro usuario, generamos uno nuevo con las letras de su rol y 8 dígitos aleatorios
                if Usuario.objects.filter(codigo_institucional=desired_code).exists():
                    code_to_use = generate_random_user_code(data['rol'])
                else:
                    code_to_use = desired_code

                user = Usuario(
                    nombre_completo=data['nombre_completo'],
                    codigo_institucional=code_to_use,
                    email=email,
                    rol=data['rol'],
                    telefono=data['telefono'],
                    programa_academico=data['programa_academico'],
                    activo=data['activo'],
                )
                user.set_password(data['password'])
                user.save()
                creados += 1
                self.stdout.write(self.style.SUCCESS(f"  [+] Creado: {user.nombre_completo} ({code_to_use}) | Email: {email} | Pass: {data['password']}"))

        self.stdout.write(self.style.SUCCESS(f"\nOperación finalizada: {creados} cuentas creadas, {actualizados} cuentas restablecidas con éxito."))
