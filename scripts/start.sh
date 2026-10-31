#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if ! command -v docker >/dev/null 2>&1; then
    echo "Error: Docker no está instalado o no está en PATH." >&2
    exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
    echo "Error: Docker Compose no está disponible." >&2
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    echo "Error: Docker no está ejecutándose. Inicia Docker Desktop." >&2
    exit 1
fi

if [[ ! -f .env ]]; then
    echo "Error: falta el archivo .env." >&2
    echo "Copia .env.example a .env y configura sus valores." >&2
    exit 1
fi

echo "Validando Docker Compose..."
docker compose config --quiet

echo "Construyendo e iniciando los servicios..."
docker compose up --build -d api

echo
docker compose ps -a

echo
echo "Servicios iniciados. Revisa el estado mostrado arriba."
echo "Swagger: http://localhost:8000/docs"
echo "Logs: docker compose logs -f api"
echo "Detener: docker compose down"