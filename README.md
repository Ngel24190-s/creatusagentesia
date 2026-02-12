# NosVers - Sistema de Gestión Integral de Granja Regenerativa

ERP + IoT para lombricultura con trazabilidad completa. Ubicación: Neuvic, Francia.

## Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend | Python 3.12 + FastAPI |
| Base de Datos | PostgreSQL 16 |
| Migraciones | Alembic |
| Auth | JWT (python-jose + bcrypt) |
| Infraestructura | Docker Compose |
| E-commerce | WooCommerce REST API |
| Frontend (futuro) | Flutter |

## Arquitectura

```
backend/
├── app/
│   ├── api/
│   │   ├── deps.py          # Dependencias (auth, DB session)
│   │   └── routes/
│   │       ├── auth.py       # Login, setup inicial
│   │       ├── kitchen.py    # Módulo Cocina (insumos, precompost)
│   │       ├── production.py # Módulo Producción (IBCs, alimentación)
│   │       ├── laboratory.py # Módulo Laboratorio (productos, QR, trazabilidad)
│   │       └── sales.py      # Módulo Dinero (ventas, dashboard)
│   ├── core/
│   │   ├── config.py         # Settings (Pydantic)
│   │   ├── database.py       # AsyncSession PostgreSQL
│   │   └── security.py       # JWT + bcrypt
│   ├── models/
│   │   ├── user.py           # User (admin/operator)
│   │   └── farm.py           # RawMaterial, PrecompostBatch, IBCBed, Feeding, Product, Sale
│   ├── schemas/              # Pydantic request/response models
│   ├── services/
│   │   └── woocommerce.py    # Sync bidireccional de stock
│   └── main.py               # FastAPI app entry point
├── alembic/                   # Migraciones de DB
├── tests/
├── Dockerfile
└── requirements.txt
```

## Módulos (PRD)

1. **Cocina** (`/api/v1/kitchen`) - Gestión de materias primas y lotes de precompost con alerta automática a 21 días.
2. **Producción** (`/api/v1/production`) - CRUD de camas IBC, registro de alimentación, alerta si un IBC no come en 3 días.
3. **Laboratorio** (`/api/v1/laboratory`) - Cosecha, envasado, generación de QR con trazabilidad pública.
4. **Dinero** (`/api/v1/sales`) - Ventas, descuento de stock, dashboard con progreso vs objetivo 1.800€/mes.

## Inicio Rápido

```bash
# 1. Copiar configuración
cp .env.example .env
# Editar .env con tus valores reales

# 2. Levantar servicios
docker compose up -d

# 3. Crear migración inicial
docker compose exec backend alembic revision --autogenerate -m "initial"
docker compose exec backend alembic upgrade head

# 4. Crear usuario admin
curl -X POST http://localhost:8000/api/v1/auth/setup \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "tu_password_seguro"}'

# 5. Ver documentación API
# http://localhost:8000/api/v1/docs
```

## Backup Manual

```bash
docker compose run --rm backup
```

## Modelo de Datos

```
raw_materials ──┐
                ├──> precompost_batches ──> feedings ──> ibc_beds
                │                                          │
                │                                          v
                │                                       products ──> sales
                │                                          │
                │                                          v
                └──────────────────────────────────── QR traceability (public)
```

## API Docs

Con el servidor corriendo: `http://localhost:8000/api/v1/docs` (Swagger UI automático).

## Licencia

MIT
