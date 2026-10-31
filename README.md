# Take Home Challenge
[![CircleCI](https://dl.circleci.com/status-badge/img/circleci/XDAqBGGy3hmP1bSiLaNrAs/WziQdkTEG5iipEvmUQMnZa/tree/main.svg?style=svg)](https://dl.circleci.com/status-badge/redirect/circleci/XDAqBGGy3hmP1bSiLaNrAs/WziQdkTEG5iipEvmUQMnZa/tree/main)
[![Coverage Status](https://coveralls.io/repos/github/luisfernandoc/take_home_challenge/badge.svg?branch=main)](https://coveralls.io/github/luisfernandoc/take_home_challenge?branch=main)

API de usuarios construida con Python 3.13 y FastAPI.

Permite administrar usuarios y asignarles Pokémon mediante sus IDs.
Los IDs se almacenan en PostgreSQL y sus nombres se obtienen de PokéAPI.
Las contraseñas se almacenan como hashes Argon2 y no se exponen en las respuestas.

## Tecnologías

- FastAPI y Pydantic
- SQLAlchemy y PostgreSQL 17
- Alembic
- HTTPX y cachetools
- pwdlib con Argon2
- pytest y Ruff
- uv, Docker y Docker Compose

## Requisitos

Para ejecutar con contenedores:

- Docker con Docker Compose
- Bash para utilizar el script de arranque opcional

Para desarrollo y pruebas desde la computadora:

- Python 3.13
- uv
- Docker para PostgreSQL

## Configuración

Copia los archivos de ejemplo y ajusta sus valores:

```bash
cp .env.example .env
cp .env.test.example .env.test
```

En PowerShell:

```powershell
Copy-Item .env.example .env
Copy-Item .env.test.example .env.test
```

No sobrescribas archivos de configuración existentes sin revisar sus valores.

| Variable | Descripción |
|---|---|
| POSTGRES_DB | Nombre de la base de datos |
| POSTGRES_USER | Usuario de PostgreSQL |
| POSTGRES_PASSWORD | Contraseña de PostgreSQL |
| POSTGRES_HOST | Host de PostgreSQL |
| POSTGRES_PORT | Puerto de PostgreSQL |
| POKEAPI_BASE_URL | URL base de PokéAPI, con `/` final |

Desde la computadora, desarrollo utiliza `localhost:5433` y testing
`localhost:5434`. Dentro de Compose, la aplicación utiliza `db:5432`.

Los archivos `.env` y `.env.test` contienen configuración local y no se versionan.

## Ejecución con Docker Compose

```bash
docker compose up --build -d api
```

Compose espera a que PostgreSQL esté saludable, aplica las migraciones
y después inicia la API.

También puedes utilizar:

```bash
bash scripts/start.sh
```

Documentación interactiva:

- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI: http://localhost:8000/openapi.json

Consultar estado y logs:

```bash
docker compose ps -a
docker compose logs --tail=100 migrate api
```

El servicio `migrate` debe terminar con código `0`.

Para detener los servicios conservando los datos:

```bash
docker compose down
```

`docker compose down -v` elimina los volúmenes y sus datos.

## Desarrollo local

```bash
uv sync --locked
docker compose up -d db
uv run alembic upgrade head
uv run fastapi dev app/main.py
```

Detén previamente la API de Compose si está utilizando el puerto 8000:

```bash
docker compose stop api
```

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| POST | /users | Crear un usuario |
| GET | /users | Listar usuarios |
| GET | /users/by-email?email=... | Buscar por correo |
| GET | /users/{user_id} | Buscar por identificador |
| PATCH | /users/{user_id} | Actualizar parcialmente |
| DELETE | /users/{user_id} | Eliminar un usuario |

Ejemplo de creación:

```json
{
  "name": "Luis",
  "email": "luis@example.com",
  "password": "Ejemplo-de-prueba-2026!",
  "pokemon_ids": [1, 25]
}
```

Ejemplo de respuesta:

```json
{
  "id": "fa4d590d-4107-4ed7-9eee-bdfabfa817a9",
  "name": "Luis",
  "email": "luis@example.com",
  "pokemons": ["bulbasaur", "pikachu"]
}
```

En PATCH, omitir `pokemon_ids` conserva las asignaciones.
Enviar `[]` elimina todas las asignaciones y enviar otra lista las reemplaza.

Los cuerpos de PATCH vacíos y los campos enviados explícitamente como
`null` se rechazan. El PATCH general no permite cambiar la contraseña.

## Arquitectura

El código se organiza por funcionalidad y separa responsabilidades:

- `domain`: entidad de usuario, contrato del repositorio y errores de dominio.
- `application`: casos de uso y contratos de hashing y consulta de Pokémon.
- `infrastructure`: modelos ORM, repositorios y adaptadores externos.
- `presentation`: endpoints, esquemas HTTP, dependencias y manejo de errores.

El servicio depende de contratos. Las dependencias conectan esos contratos
con SQLAlchemy, Argon2 y el cliente de PokéAPI.

El repositorio almacena IDs de Pokémon; no consulta servicios externos.
El cliente de PokéAPI resuelve los nombres y mantiene una caché temporal
en memoria, independiente por proceso.

## Pruebas

Levanta PostgreSQL de testing:

```bash
docker compose --profile test up -d db_test
```

Cuando esté saludable, ejecuta:

```bash
uv run python -m tests.prepare_database
uv run python -m pytest tests -v
```

Las fixtures SQL también aplican las migraciones pendientes.

Las pruebas utilizan:

- Repositorio en memoria y mocks para el servicio.
- Overrides de dependencias para pruebas HTTP.
- PostgreSQL separado para integración SQL.
- Transacciones exteriores y savepoints para revertir las escrituras.
- MockTransport para probar el cliente HTTP sin internet.
- Argon2 real para verificar el hashing.

## Lint y formato

Comprobar:

```bash
uv run ruff check .
uv run ruff format --check .
```

Aplicar correcciones y formato:

```bash
uv run ruff check . --fix
uv run ruff format .
```

## Migraciones

Después de modificar los modelos:

```bash
uv run alembic revision --autogenerate -m "describe schema change"
```

Revisa siempre el archivo generado antes de aplicarlo:

```bash
uv run alembic upgrade head
```

## Alcance y limitaciones

- La API todavía no implementa autenticación ni autorización.
- El listado de usuarios no tiene paginación.
- Las respuestas de usuarios con Pokémon dependen de PokéAPI cuando
  los nombres no están en caché.
- Los correos se comparan según el comportamiento actual de la aplicación;
  no se implementa una política general de comparación sin distinguir mayúsculas.
- Las contraseñas se almacenan con hash, pero eso por sí solo no protege
  el acceso a los endpoints.
