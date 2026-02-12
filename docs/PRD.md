# DOCUMENTO DE ESPECIFICACIONES TÉCNICAS (PRD)

## Proyecto: NosVers - Sistema de Gestión Integral de Granja Regenerativa (ERP + IoT)

**Versión:** 1.0
**Ubicación:** Neuvic, Francia
**Objetivo de Negocio:** Escalar la producción de lombricompostaje para alcanzar 1.800€/mes de facturación recurrente mediante trazabilidad total y venta automatizada.

---

### 1. RESUMEN EJECUTIVO

El sistema "NosVers" es una plataforma híbrida (Móvil/Web) para la gestión de una granja de lombricultura. Debe gestionar el ciclo de vida completo: desde la recepción de insumos (residuos orgánicos), pasando por el precompostaje y la alimentación de camas IBC, hasta la cosecha, envasado y venta online (WooCommerce).

**Punto Clave:** La trazabilidad es el valor añadido. El cliente final debe poder escanear un QR en la botella y ver la historia del lote.

---

### 2. ARQUITECTURA DEL SISTEMA

Arquitectura modular con funcionamiento offline-first (en el hangar) y sincronización con la nube.

* **Frontend (App Operativa):** PWA o Flutter/React Native. Funcional en Android en condiciones de campo.
* **Backend (Core):** Python (FastAPI). Alojado en VPS (KVM4 Hostinger).
* **Base de Datos:** PostgreSQL.
* **E-commerce:** WordPress + WooCommerce (Existente).
* **Hardware Edge:** Servidor local (Ubuntu PC) para impresoras de etiquetas y sensores futuros.

---

### 3. MÓDULOS FUNCIONALES

#### 3.1. Gestión de Insumos y Precompostaje (Módulo "Cocina")

* **Entradas:** Registro de materias primas (estiércol, cartón, café). Campos: Origen, Peso, Fecha.
* **Lotes de Precompost:** Creación de lotes mezclando insumos.
* **Lógica de Negocio:** Alerta automática tras 21 días de maduración (ciclo térmico).
* **Estado:** `Fermentando` -> `Listo` -> `Agotado`.

#### 3.2. Gestión de Camas IBC (Módulo "Producción")

* **Inventario:** CRUD de contenedores IBC (ID único, Fecha Inicio, Biomasa Inicial).
* **Alimentación:** Registro de eventos: `Fecha`, `ID_IBC`, `ID_Lote_Precompost`, `Kg_Aportados`.
* **Alertas:**
  * Si un IBC no ha comido en 3 días -> Notificación Push.
  * Cálculo de densidad de población estimada.

#### 3.3. Cosecha y Trazabilidad (Módulo "Laboratorio")

* **Evento de Cosecha:** Transformación de `Biomasa/Insumo` a `Producto Final` (Lombrithé o Humus Sólido).
* **Generación de Lotes Finales:** Cada botella/saco recibe un ID único (Batch ID).
* **Generador QR:** QR público → `nosvers.com/trace/{batch_id}`, mostrando insumos usados.

#### 3.4. Sincronización de Ventas (Módulo "Dinero")

* **Integración Bidireccional:**
  * Stock Físico (App) -> Actualiza Stock WooCommerce (API).
  * Venta Web (WooCommerce) -> Descuenta Inventario Físico.
* **Dashboard Financiero:** Visualización en tiempo real de ingresos vs. Objetivo (1.800€).

---

### 4. MODELO DE DATOS (ESQUEMA RELACIONAL)

* **`raw_materials`**: id, type, origin, quantity, date_received.
* **`precompost_batches`**: id, creation_date, status, recipe_details (JSON).
* **`ibc_beds`**: id, location, start_date, worm_biomass_kg.
* **`feedings`**: id, ibc_id (FK), batch_id (FK), quantity_kg, timestamp, operator_id.
* **`products`**: id, type (leachate/solid), packaging_size, stock_qty, sku (WooCommerce sync).
* **`sales`**: id, source (web/direct), amount, date.

---

### 5. REQUISITOS NO FUNCIONALES

1. **Seguridad:** Autenticación vía JWT. Roles de usuario (Admin vs. Operario).
2. **Backup:** Copias de seguridad diarias automatizadas de la DB PostgreSQL.
3. **Performance:** Lectura del código QR instantánea (<1 seg).
4. **UX/UI:** Interfaz de alto contraste (Dark Mode) y botones grandes para uso con guantes.

---

### 6. ENTREGABLES ESPERADOS

1. **Código Fuente:** Repositorio Git con control de versiones.
2. **Documentación API:** Swagger/OpenAPI.
3. **Scripts de Despliegue:** Docker Compose para levantar el entorno en el VPS Hostinger.
4. **Manual de Usuario:** Guía rápida para formación del personal.

---

### 7. STACK TECNOLÓGICO

* **Frontend:** Flutter (un solo código para iOS/Android).
* **Backend:** Python (FastAPI).
* **Base de Datos:** PostgreSQL.
* **Infraestructura:** Docker containers sobre Ubuntu Server 22.04 (Hostinger VPS).
