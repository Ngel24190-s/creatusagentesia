"""
NosVers Farm AI Agent - Intelligent farm management assistant.

Analyzes farm data to provide:
- Health scoring and diagnostics
- Feeding recommendations
- Production forecasts
- Natural language Q&A about farm operations
"""
from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.farm import IBCBed, Feeding, PrecompostBatch, Product, Sale, RawMaterial


class FarmAgent:
    """AI agent for intelligent farm pilotage."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_farm_snapshot(self) -> dict:
        """Gather all current farm data for analysis."""
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # IBCs
        ibcs_result = await self.db.execute(select(IBCBed))
        ibcs = ibcs_result.scalars().all()

        # Recent feedings (last 14 days)
        two_weeks_ago = now - timedelta(days=14)
        feedings_result = await self.db.execute(
            select(Feeding).where(Feeding.timestamp >= two_weeks_ago)
        )
        feedings = feedings_result.scalars().all()

        # Batches
        batches_result = await self.db.execute(select(PrecompostBatch))
        batches = batches_result.scalars().all()

        # Products & stock
        products_result = await self.db.execute(select(Product))
        products = products_result.scalars().all()

        # Monthly sales
        sales_result = await self.db.execute(
            select(Sale).where(Sale.date >= month_start)
        )
        sales = sales_result.scalars().all()

        # Materials
        materials_result = await self.db.execute(select(RawMaterial))
        materials = materials_result.scalars().all()

        return {
            "ibcs": ibcs,
            "feedings": feedings,
            "batches": batches,
            "products": products,
            "sales": sales,
            "materials": materials,
            "now": now,
        }

    async def get_health_score(self) -> dict:
        """Calculate overall farm health score (0-100)."""
        data = await self.get_farm_snapshot()
        now = data["now"]
        scores = {}
        alerts = []

        # 1. Feeding regularity (0-100)
        ibcs = data["ibcs"]
        feedings = data["feedings"]
        if ibcs:
            feeding_by_ibc = {}
            for f in feedings:
                if f.ibc_id not in feeding_by_ibc or f.timestamp > feeding_by_ibc[f.ibc_id]:
                    feeding_by_ibc[f.ibc_id] = f.timestamp

            fed_recently = 0
            for ibc in ibcs:
                last_fed = feeding_by_ibc.get(ibc.id)
                if last_fed and (now - last_fed).days <= 3:
                    fed_recently += 1
                elif not last_fed:
                    alerts.append(f"{ibc.code} nunca ha sido alimentado")
                else:
                    days_hungry = (now - last_fed).days
                    alerts.append(f"{ibc.code} lleva {days_hungry} dias sin comer")

            scores["alimentacion"] = int((fed_recently / len(ibcs)) * 100) if ibcs else 0
        else:
            scores["alimentacion"] = 0
            alerts.append("No hay IBCs registrados - crea tu primer IBC")

        # 2. Precompost pipeline (0-100)
        batches = data["batches"]
        fermenting = [b for b in batches if b.status == "FERMENTING"]
        ready = [b for b in batches if b.status == "READY"]
        if fermenting or ready:
            scores["precompost"] = min(100, (len(ready) * 40) + (len(fermenting) * 20))
            if not ready:
                alerts.append("No hay precompost listo - planifica la siguiente receta")
        else:
            scores["precompost"] = 0
            alerts.append("No hay lotes de precompost activos")

        # 3. Stock health (0-100)
        products = data["products"]
        total_stock = sum(p.stock_qty for p in products)
        if products:
            scores["stock"] = min(100, total_stock * 10)
            low_stock = [p for p in products if p.stock_qty <= 2]
            for p in low_stock:
                alerts.append(f"Stock bajo: {p.batch_code} ({p.stock_qty} unidades)")
        else:
            scores["stock"] = 0

        # 4. Revenue progress (0-100)
        sales = data["sales"]
        revenue = sum(s.amount_eur for s in sales)
        target = 1800.0
        scores["ingresos"] = min(100, int((revenue / target) * 100))
        if revenue < target * 0.5:
            days_left = 30 - now.day
            needed = target - revenue
            alerts.append(f"Faltan {needed:.0f} EUR para el objetivo ({days_left} dias restantes)")

        # Overall score
        weights = {"alimentacion": 0.35, "precompost": 0.20, "stock": 0.20, "ingresos": 0.25}
        overall = sum(scores.get(k, 0) * w for k, w in weights.items())

        return {
            "overall_score": int(overall),
            "metrics": scores,
            "alerts": alerts,
            "timestamp": now.isoformat(),
        }

    async def get_recommendations(self) -> dict:
        """Generate actionable recommendations based on farm state."""
        data = await self.get_farm_snapshot()
        now = data["now"]
        items = []

        # Feeding recommendations
        feeding_by_ibc = {}
        for f in data["feedings"]:
            if f.ibc_id not in feeding_by_ibc or f.timestamp > feeding_by_ibc[f.ibc_id]:
                feeding_by_ibc[f.ibc_id] = f.timestamp

        for ibc in data["ibcs"]:
            last_fed = feeding_by_ibc.get(ibc.id)
            if not last_fed or (now - last_fed).days >= 3:
                days = (now - last_fed).days if last_fed else 999
                items.append({
                    "title": f"Alimentar {ibc.code}",
                    "description": f"Lleva {days} dias sin comer. Las lombrices necesitan alimentacion regular cada 2-3 dias.",
                    "action": f"Ir a Produccion y alimentar {ibc.code}",
                    "priority": "high" if days >= 5 else "medium",
                    "category": "feeding",
                })

        # Precompost recommendations
        ready_batches = [b for b in data["batches"] if b.status == "READY"]
        fermenting = [b for b in data["batches"] if b.status == "FERMENTING"]

        if not ready_batches and not fermenting:
            items.append({
                "title": "Crear nuevo precompost",
                "description": "No hay lotes de precompost. Sin precompost no puedes alimentar los IBCs.",
                "action": "Ir a Cocina y crear un nuevo lote",
                "priority": "high",
                "category": "precompost",
            })
        elif not ready_batches and fermenting:
            soonest = min(fermenting, key=lambda b: b.maturity_date or now + timedelta(days=999))
            if soonest.maturity_date:
                days_to_ready = (soonest.maturity_date - now.date()).days if hasattr(soonest.maturity_date, 'day') else 0
                items.append({
                    "title": "Precompost en fermentacion",
                    "description": f"El lote {soonest.code} estara listo en ~{max(0, days_to_ready)} dias.",
                    "action": "Verifica la temperatura y humedad del lote",
                    "priority": "low",
                    "category": "precompost",
                })

        # Harvest recommendations
        for ibc in data["ibcs"]:
            if ibc.start_date:
                age_days = (now.date() - ibc.start_date).days if hasattr(ibc.start_date, 'day') else 0
                if age_days >= 60:
                    items.append({
                        "title": f"Evaluar cosecha {ibc.code}",
                        "description": f"Este IBC tiene {age_days} dias. Podria estar listo para cosechar lixiviado o vermicompost.",
                        "action": "Revisar el IBC y registrar cosecha en Laboratorio",
                        "priority": "medium",
                        "category": "harvest",
                    })

        # Stock & sales recommendations
        low_stock = [p for p in data["products"] if p.stock_qty <= 3]
        for p in low_stock:
            items.append({
                "title": f"Reponer stock {p.batch_code}",
                "description": f"Solo quedan {p.stock_qty} unidades de {p.packaging_size}.",
                "action": "Planifica nueva cosecha para reponer",
                "priority": "medium" if p.stock_qty > 0 else "high",
                "category": "stock",
            })

        # Revenue push
        sales = data["sales"]
        revenue = sum(s.amount_eur for s in sales)
        if revenue < 900 and now.day > 15:
            items.append({
                "title": "Impulsar ventas",
                "description": f"A mitad de mes solo llevas {revenue:.0f} EUR de los 1.800 EUR objetivo.",
                "action": "Considera promociones en WooCommerce o ventas directas",
                "priority": "high",
                "category": "sales",
            })

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        items.sort(key=lambda x: priority_order.get(x["priority"], 1))

        return {"items": items, "total": len(items), "timestamp": now.isoformat()}

    async def get_forecast(self) -> dict:
        """Generate production and revenue forecasts."""
        data = await self.get_farm_snapshot()
        now = data["now"]

        # Revenue forecast
        sales = data["sales"]
        revenue = sum(s.amount_eur for s in sales)
        days_elapsed = max(now.day, 1)
        daily_avg = revenue / days_elapsed
        days_in_month = 30
        projected_revenue = daily_avg * days_in_month

        # Production capacity
        ibcs = data["ibcs"]
        total_biomass = sum(ibc.worm_biomass_kg for ibc in ibcs)
        # Rough estimate: 1kg worms processes ~0.5kg/day of food waste
        daily_capacity_kg = total_biomass * 0.5
        monthly_capacity_kg = daily_capacity_kg * 30

        # Stock projection
        products = data["products"]
        total_stock = sum(p.stock_qty for p in products)
        sales_count = len(sales)
        daily_sales_rate = sales_count / max(days_elapsed, 1)
        days_of_stock = total_stock / max(daily_sales_rate, 0.01)

        projections = [
            {
                "label": "Ingresos proyectados",
                "value": f"{projected_revenue:.0f} EUR",
                "detail": f"Media diaria: {daily_avg:.1f} EUR/dia",
            },
            {
                "label": "Capacidad procesamiento",
                "value": f"{monthly_capacity_kg:.0f} kg/mes",
                "detail": f"{len(ibcs)} IBCs con {total_biomass:.1f} kg biomasa total",
            },
            {
                "label": "Stock para",
                "value": f"{days_of_stock:.0f} dias",
                "detail": f"{total_stock} unidades | {daily_sales_rate:.1f} ventas/dia",
            },
        ]

        return {
            "projections": projections,
            "summary": {
                "monthly_revenue_projected": round(projected_revenue, 2),
                "daily_average": round(daily_avg, 2),
                "processing_capacity_kg": round(monthly_capacity_kg, 1),
                "stock_days_remaining": round(days_of_stock, 1),
            },
            "timestamp": now.isoformat(),
        }

    async def answer_question(self, question: str) -> dict:
        """Answer natural language questions about the farm using data analysis."""
        data = await self.get_farm_snapshot()
        now = data["now"]
        q = question.lower()

        # Feeding questions
        if any(w in q for w in ["alimentar", "comer", "hambre", "comida", "feeding"]):
            feeding_by_ibc = {}
            for f in data["feedings"]:
                if f.ibc_id not in feeding_by_ibc or f.timestamp > feeding_by_ibc[f.ibc_id]:
                    feeding_by_ibc[f.ibc_id] = f.timestamp

            lines = []
            for ibc in data["ibcs"]:
                last_fed = feeding_by_ibc.get(ibc.id)
                if last_fed:
                    days = (now - last_fed).days
                    status = "OK" if days <= 3 else "NECESITA COMIDA"
                    lines.append(f"- {ibc.code}: ultima comida hace {days} dias [{status}]")
                else:
                    lines.append(f"- {ibc.code}: NUNCA alimentado")

            return {"answer": "Estado de alimentacion de los IBCs:\n" + "\n".join(lines) if lines else "No hay IBCs registrados."}

        # Production/capacity questions
        if any(w in q for w in ["producir", "produccion", "capacidad", "cuanto"]):
            total_biomass = sum(ibc.worm_biomass_kg for ibc in data["ibcs"])
            capacity = total_biomass * 0.5 * 30
            return {
                "answer": f"Con {len(data['ibcs'])} IBCs y {total_biomass:.1f} kg de biomasa, "
                          f"la capacidad estimada es de {capacity:.0f} kg de procesamiento al mes. "
                          f"Esto puede generar aproximadamente {capacity * 0.3:.0f} kg de vermicompost "
                          f"y {capacity * 0.2:.0f} litros de lixiviado."
            }

        # Revenue/sales questions
        if any(w in q for w in ["venta", "ingreso", "dinero", "revenue", "euros", "objetivo"]):
            revenue = sum(s.amount_eur for s in data["sales"])
            target = 1800
            remaining = target - revenue
            daily_needed = remaining / max(30 - now.day, 1)
            return {
                "answer": f"Ingresos del mes: {revenue:.2f} EUR de {target} EUR objetivo ({(revenue/target*100):.1f}%).\n"
                          f"Faltan {remaining:.2f} EUR. Necesitas {daily_needed:.2f} EUR/dia para alcanzar el objetivo."
            }

        # Stock questions
        if any(w in q for w in ["stock", "inventario", "producto", "quedan"]):
            lines = []
            for p in data["products"]:
                emoji = "OK" if p.stock_qty > 5 else ("BAJO" if p.stock_qty > 0 else "AGOTADO")
                lines.append(f"- {p.batch_code} ({p.packaging_size}): {p.stock_qty} unidades [{emoji}]")
            total = sum(p.stock_qty for p in data["products"])
            return {"answer": f"Stock total: {total} unidades\n" + "\n".join(lines) if lines else "No hay productos en stock."}

        # Precompost questions
        if any(w in q for w in ["precompost", "lote", "ferment", "receta", "batch"]):
            lines = []
            for b in data["batches"]:
                maturity = b.maturity_date.strftime("%d/%m/%Y") if b.maturity_date else "?"
                lines.append(f"- {b.code}: {b.status} (madurez: {maturity})")
            return {"answer": "Lotes de precompost:\n" + "\n".join(lines) if lines else "No hay lotes de precompost."}

        # IBC questions
        if any(w in q for w in ["ibc", "lombriz", "lombri", "worm", "contenedor"]):
            lines = []
            for ibc in data["ibcs"]:
                lines.append(f"- {ibc.code}: {ibc.location} | {ibc.worm_biomass_kg} kg biomasa")
            return {"answer": "IBCs activos:\n" + "\n".join(lines) if lines else "No hay IBCs registrados."}

        # Generic summary
        health = await self.get_health_score()
        return {
            "answer": f"Estado general de la granja: {health['overall_score']}/100.\n"
                      f"IBCs: {len(data['ibcs'])} | Lotes precompost: {len(data['batches'])} | "
                      f"Productos: {len(data['products'])} | Ventas del mes: {len(data['sales'])}\n\n"
                      f"Alertas: {', '.join(health['alerts'][:3]) if health['alerts'] else 'Ninguna'}\n\n"
                      f"Puedes preguntarme sobre: alimentacion, produccion, ventas, stock, precompost o IBCs."
        }
