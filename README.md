# 🎓 Simulador de Cuestionarios Saber TyT - Grupo 01

Plataforma web integral diseñada para la preparación, evaluación y retroalimentación pedagógica en las pruebas de Estado **Saber TyT** (Técnicos y Tecnológicos) en Colombia.

El sistema cuenta con gestión de bancos de preguntas por competencias, creador de cuestionarios parametrizables, importación masiva de preguntas con validación y compatibilidad para Excel, módulo interactivo para estudiantes con temporizador en tiempo real y visor arquitectónico del modelo relacional de datos.

---

## 🚀 Tecnologías Utilizadas

- **Backend:** Python 3.10+ / Django 5.2 (Arquitectura MVT)
- **Base de Datos:** SQLite (por defecto en desarrollo) / Compatible con MySQL y MariaDB (Script DDL incluido)
- **Frontend:** Django Templates + Tailwind CSS + Vanilla JS + Lucide Icons
- **Tipografías:** Inter / Outfit (Google Fonts)

---

## 📋 Requisitos Previos

Antes de comenzar, asegúrate de tener instalado en tu sistema:

1. **Python 3.10 o superior**: [Descargar Python](https://www.python.org/downloads/) *(Asegúrate de marcar la casilla **"Add Python to PATH"** durante la instalación)*.
2. **Git** (Opcional, para clonar el repositorio): [Descargar Git](https://git-scm.com/).
3. Un navegador web moderno (Google Chrome, Firefox, Microsoft Edge, Brave, etc.).

---

## 🛠️ Guía de Instalación y Puesta en Marcha (Desde Cero)

Sigue estos sencillos pasos en tu terminal (PowerShell, CMD, Git Bash o Terminal de macOS/Linux) para poner a funcionar el proyecto desde cero:

### 1. Clonar o Descargar el Repositorio

Si usas Git:
```bash
git clone https://github.com/yuta578/SaberTYT.git
cd SaberTYT
```
*(Si descargaste el código en un archivo ZIP, descomprímelo y abre la terminal dentro de la carpeta del proyecto)*.

---

### 2. Crear el Entorno Virtual de Python

Crear un entorno virtual aísla las dependencias del proyecto de las librerías globales de tu equipo.

- **En Windows (PowerShell / CMD):**
  ```powershell
  python -m venv .venv
  ```

- **En macOS / Linux:**
  ```bash
  python3 -m venv .venv
  ```

---

### 3. Activar el Entorno Virtual

- **En Windows con PowerShell:**
  ```powershell
  .\.venv\Scripts\Activate.ps1
  ```
  > 💡 *Si PowerShell muestra un error de directiva de ejecución de scripts, ejecuta primero:*
  > ```powershell
  > Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  > .\.venv\Scripts\Activate.ps1
  > ```

- **En Windows con CMD (Símbolo del sistema):**
  ```cmd
  .\.venv\Scripts\activate.bat
  ```

---

### 4. Instalar las Dependencias del Proyecto

Con el entorno virtual activado, instala las librerías necesarias ejecutando:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

### 5. Aplicar las Migraciones a la Base de Datos

Genera y aplica la estructura relacional de la base de datos:

```bash
python manage.py makemigrations
python manage.py migrate
```

---

### 6. Cargar Datos de Prueba Pedagógicos (Sembrado / Seed)

Para disponer inmediatamente de un banco de preguntas oficial de Saber TyT (Lectura Crítica, Razonamiento Cuantitativo, Competencias Ciudadanas, Inglés y Comunicación Escrita), cuestionarios configurados e intentos de simulación, ejecuta el script de sembrado:

```bash
python simulador/seed_data.py
```

> **Salida esperada:**
> ```text
> Iniciando sembrado de datos pedagógicos para Simulador Saber TyT...
> Datos sembrados exitosamente!
> ```

---

### 7. (Opcional) Crear un Superusuario para el Administrador de Django

Si deseas acceder al panel de administración nativo de Django (`/admin/`):

```bash
python manage.py createsuperuser
```
*(Ingresa un nombre de usuario, correo y contraseña cuando te lo solicite)*.

---

### 8. Iniciar el Servidor de Desarrollo

Inicia el servidor local de Django:

```bash
python manage.py runserver
```

---

### 9. Abrir la Aplicación en el Navegador

Abre tu navegador e ingresa a:

👉 **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)** *(o [http://localhost:8000/](http://localhost:8000/))*

---
