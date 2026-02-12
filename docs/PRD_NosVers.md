# Documento de Especificaciones Técnicas (PRD)

## Proyecto: NosVers - Sistema de Gestión Integral de Granja Regenerativa (ERP + IoT)

**Versión:** 1.0  
**Ubicación:** Neuvic, Francia  
**Objetivo de negocio:** Escalar la producción de lombricompostaje para alcanzar 1.800€/mes de facturación recurrente mediante trazabilidad total y venta automatizada.

---

## 1. Resumen ejecutivo

El sistema **NosVers** es una plataforma híbrida (móvil/web) para la gestión de una granja de lombricultura. Debe gestionar el ciclo de vida completo: desde la recepción de insumos (residuos orgánicos), pasando por el precompostaje y la alimentación de camas IBC, hasta la cosecha, envasado y venta online (WooCommerce).

**Punto clave:** La trazabilidad es el valor añadido. El cliente final debe poder escanear un QR en la botella y ver la historia del lote.

---

## 2. Arquitectura del sistema

Se requiere una arquitectura modular que garantice funcionamiento **offline-first** (en el hangar) y sincronización con la nube.

- **Frontend (app operativa):** PWA (Progressive Web App) o Flutter/React Native. Debe funcionar en móviles Android en condiciones de campo (manos sucias, poca luz).
- **Backend (core):** Python (Django/FastAPI) o Node.js. Alojado en VPS (KVM4 Hostinger).
- **Base de datos:** PostgreSQL (relacional, vital para la integridad de datos).
- **E-commerce:** WordPress + WooCommerce (existente).
- **Hardware edge:** Servidor local (Ubuntu PC) para gestión de impresoras de etiquetas y sensores futuros.

---

## 3. Módulos funcionales

### 3.1 Gestión de insumos y precompostaje (Módulo "Cocina")

- **Entradas:** Registro de materias primas (estiércol, cartón, café). Campos: origen, peso, fecha.
- **Lotes de precompost:** Creación de lotes mezclando insumos.
- **Lógica de negocio:** Alerta automática tras 21 días de maduración (ciclo térmico).
- **Estado:** `Fermentando` → `Listo` → `Agotado`.

### 3.2 Gestión de camas IBC (Módulo "Producción")

- **Inventario:** CRUD de contenedores IBC (ID único, fecha inicio, biomasa inicial).
- **Alimentación:** Registro de eventos: `Fecha`, `ID_IBC`, `ID_Lote_Precompost`, `Kg_Aportados`.
- **Alertas:**
  - Si un IBC no ha comido en 3 días → notificación push.
  - Cálculo de densidad de población estimada.

### 3.3 Cosecha y trazabilidad (Módulo "Laboratorio")

- **Evento de cosecha:** Transformación de `Biomasa/Insumo` a `Producto Final` (Lombrithé o Humus Sólido).
- **Generación de lotes finales:** Cada botella/saco recibe un ID único (Batch ID).
- **Generador QR:** El sistema debe generar un QR público que enlace a una URL `nosvers.com/trace/{batch_id}`, mostrando gráficamente los insumos usados.

### 3.4 Sincronización de ventas (Módulo "Dinero")

- **Integración bidireccional:**
  - Stock físico (app) → actualiza stock WooCommerce (API).
  - Venta web (WooCommerce) → descuenta inventario físico.
- **Dashboard financiero:** Visualización en tiempo real de ingresos vs. objetivo (1.800€).

---

## 4. Modelo de datos (esquema relacional)

El equipo de desarrollo debe implementar, como mínimo, estas entidades:

- **`raw_materials`**: `id`, `type`, `origin`, `quantity`, `date_received`.
- **`precompost_batches`**: `id`, `creation_date`, `status`, `recipe_details` (JSON).
- **`ibc_beds`**: `id`, `location`, `start_date`, `worm_biomass_kg`.
- **`feedings`**: `id`, `ibc_id` (FK), `batch_id` (FK), `quantity_kg`, `timestamp`, `operator_id`.
- **`products`**: `id`, `type` (leachate/solid), `packaging_size`, `stock_qty`, `sku` (WooCommerce sync).
- **`sales`**: `id`, `source` (web/direct), `amount`, `date`.

---

## 5. Requisitos no funcionales

1. **Seguridad:** Autenticación vía JWT. Roles de usuario (Admin vs. Operario).
2. **Backup:** Copias de seguridad diarias automatizadas de la DB PostgreSQL a un bucket S3 o almacenamiento externo.
3. **Performance:** La lectura del código QR debe ser instantánea (< 1 seg).
4. **UX/UI:** Interfaz de alto contraste (Dark Mode) y botones grandes para uso con guantes.

---

## 6. Entregables esperados

1. **Código fuente:** Repositorio Git (GitHub/GitLab) con control de versiones.
2. **Documentación API:** Swagger/OpenAPI.
3. **Scripts de despliegue:** Docker Compose para levantar el entorno en el VPS Hostinger.
4. **Manual de usuario:** Guía rápida para formación del personal (África).

---

## 7. Stack tecnológico recomendado

- **Frontend:** Flutter (un solo código para iOS/Android).
- **Backend:** Python (FastAPI) o Node.js (NestJS).
- **Base de datos:** PostgreSQL.
- **Infraestructura:** Docker containers sobre Ubuntu Server 22.04 (Hostinger VPS).

---

## Nota para el equipo de desarrollo

Este proyecto busca robustez y simplicidad operativa. La prioridad no son gráficos complejos, sino la integridad de los datos para garantizar la trazabilidad del producto final. El sistema debe ser capaz de escalar de 2 IBCs a 50 IBCs sin refactorización.
