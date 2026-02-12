# NosVers - Sistema Completo de Pilotaje de Granja Regenerativa

ERP + IA + Dashboard para lombricultura con trazabilidad completa. Neuvic, Francia.

## Stack Tecnologico

| Capa | Tecnologia |
|------|-----------|
| Frontend | React 18 + Vite + Tailwind CSS |
| Backend | Python 3.12 + FastAPI |
| Base de Datos | PostgreSQL 16 (async) |
| Agentes IA | Motor de analisis integrado |
| Infraestructura | Docker Compose + Nginx |
| E-commerce | WooCommerce REST API (sync bidireccional) |
| Tests | pytest + pytest-asyncio |

## Arquitectura

```
frontend/                          # React SPA (dashboard)
├── src/
│   ├── pages/
│   │   ├── Dashboard.jsx          # Vista general con KPIs e IA
│   │   ├── Kitchen.jsx            # Materias primas + precompost
│   │   ├── Production.jsx         # IBCs + alimentacion
│   │   ├── Laboratory.jsx         # Productos + QR + trazabilidad
│   │   ├── Sales.jsx              # Ventas + objetivo mensual
│   │   ├── Agents.jsx             # Chat IA + salud + recomendaciones
│   │   └── Traceability.jsx       # Pagina publica de trazabilidad
│   ├── components/Layout.jsx      # Sidebar + navegacion
│   ├── services/api.js            # Cliente API
│   └── context/AuthContext.jsx    # Autenticacion
├── Dockerfile                     # Build multi-stage + Nginx
└── nginx.conf                     # Reverse proxy → backend

backend/
├── app/
│   ├── agents/
│   │   └── farm_agent.py          # Motor IA: salud, recomendaciones, forecast, Q&A
│   ├── api/routes/
│   │   ├── auth.py                # Login + setup
│   │   ├── kitchen.py             # Modulo Cocina
│   │   ├── production.py          # Modulo Produccion
│   │   ├── laboratory.py          # Modulo Laboratorio
│   │   ├── sales.py               # Modulo Ventas
│   │   ├── agents.py              # API de agentes IA
│   │   └── woocommerce.py         # Sync WooCommerce
│   ├── tasks/
│   │   └── scheduler.py           # Tareas programadas (sync stock, import orders, health check)
│   ├── services/
│   │   └── woocommerce.py         # Cliente WooCommerce REST API
│   ├── models/                    # SQLAlchemy ORM
│   ├── schemas/                   # Pydantic validation
│   └── core/                      # Config, DB, security
├── tests/                         # Tests completos
├── alembic/                       # Migraciones
└── Dockerfile
```

## Modulos

### 1. Cocina (`/api/v1/kitchen`)
Materias primas y lotes de precompost con madurez automatica a 21 dias.

### 2. Produccion (`/api/v1/production`)
IBCs, alimentacion de lombrices, alertas de hambre (3+ dias sin comer).

### 3. Laboratorio (`/api/v1/laboratory`)
Cosecha, envasado, QR codes, trazabilidad publica.

### 4. Ventas (`/api/v1/sales`)
Registro de ventas, descuento de stock, dashboard con objetivo 1.800 EUR/mes.

### 5. Agentes IA (`/api/v1/agents`)
- **Salud de la granja** - Puntuacion 0-100 con metricas por area
- **Recomendaciones** - Acciones priorizadas basadas en datos reales
- **Proyecciones** - Forecast de ingresos, capacidad y stock
- **Chat Q&A** - Pregunta en lenguaje natural sobre la granja

### 6. WooCommerce (`/api/v1/woo`)
- **Sync stock** - Push local → WooCommerce por SKU
- **Import pedidos** - Pull pedidos WooCommerce → ventas locales
- **Auto-sync** - Scheduler cada 15-30 minutos

## Inicio Rapido

```bash
# 1. Configurar
cp .env.example .env
# Editar .env con tus valores

# 2. Levantar todo (DB + Backend + Frontend)
docker compose up -d

# 3. Migrar base de datos
docker compose exec backend alembic revision --autogenerate -m "initial"
docker compose exec backend alembic upgrade head

# 4. Crear admin
curl -X POST http://localhost/api/v1/auth/setup \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "tu_password_seguro"}'

# 5. Abrir dashboard
# http://localhost
```

## Comandos Utiles

```bash
# Ver estado
docker compose ps

# Ver logs
docker compose logs -f backend
docker compose logs -f frontend

# Backup manual
docker compose run --rm backup

# Sync WooCommerce manual
curl -X POST http://localhost/api/v1/woo/sync-stock -H "Authorization: Bearer TOKEN"
curl -X POST http://localhost/api/v1/woo/import-orders -H "Authorization: Bearer TOKEN"

# Tests
docker compose exec backend pytest -v
```

## Modelo de Datos

```
raw_materials ──> precompost_batches ──> feedings ──> ibc_beds
                                                        │
                                                        v
                                                     products ──> sales
                                                        │            │
                                                        v            v
                                                  QR traceability   WooCommerce
                                                    (public)         (sync)
```

## API Docs

Dashboard: `http://localhost`
Swagger: `http://localhost/api/v1/docs`
Trazabilidad publica: `http://localhost/trace/{batch_code}`

## Licencia

MIT
