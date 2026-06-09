# Certify Backend

Este es el backend para la plataforma **Certify**, construido con **FastAPI**, **SQLAlchemy** (async) y **PostgreSQL**.

## Características Principales

El proyecto gestiona las siguientes entidades:
- **Usuarios (Users) y Autenticación**
- **Cursos (Courses)**
- **Módulos (Modules)**
- **Lecciones (Lessons)**
- **Inscripciones (Course Enrollments)**
- **Progreso del Usuario (User Progress)**
- **Certificados (Certificates)** y sus **Tipos (Certificate Types)**
- **Auditoría de Certificados (Certificate Audit)**

## Requisitos

- Python 3.10+
- `uv` (Recomendado para manejar paquetes y el entorno virtual)
- PostgreSQL (opcional para desarrollo local, soporta SQLite temporal)

## Instalación y Configuración

1. **Clonar o descargar** el repositorio.
2. **Crear y activar entorno virtual**:
   ```bash
   uv venv
   source .venv/bin/activate
   ```
3. **Instalar dependencias**:
   ```bash
   uv pip sync requirements.txt
   ```
4. **Variables de entorno**:
   Copia el archivo `.env.example` a `.env` y configura los valores (por ejemplo, `DATABASE_URL`, JWT secret, etc.).
   ```bash
   cp .env.example .env
   ```

## Ejecución

Puedes iniciar el servidor de desarrollo utilizando el CLI de FastAPI o Uvicorn:

```bash
fastapi dev app/main.py
```
O usando uvicorn directamente:
```bash
uvicorn app.main:app --reload
```

## Documentación de la API

Una vez que la aplicación esté corriendo, la documentación interactiva generada por FastAPI estará disponible en:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
