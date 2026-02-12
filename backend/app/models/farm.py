"""
NosVers - Farm Data Models
Implements the relational schema from PRD Section 4.
"""
import enum
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Date, Enum, ForeignKey, JSON, Text,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


# --- Enums ---

class PrecompostStatus(str, enum.Enum):
    FERMENTING = "fermenting"
    READY = "ready"
    DEPLETED = "depleted"


class ProductType(str, enum.Enum):
    LEACHATE = "leachate"      # Lombrithé (líquido)
    SOLID = "solid"            # Humus sólido


class SaleSource(str, enum.Enum):
    WEB = "web"
    DIRECT = "direct"


# --- Models (PRD §4) ---

class RawMaterial(Base):
    """raw_materials: Materias primas recibidas (estiércol, cartón, café, etc.)"""
    __tablename__ = "raw_materials"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(100), nullable=False)          # e.g. "estiércol", "cartón"
    origin = Column(String(200))                         # Proveedor / origen
    quantity_kg = Column(Float, nullable=False)
    date_received = Column(Date, nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PrecompostBatch(Base):
    """precompost_batches: Lotes de precompost (Módulo Cocina)"""
    __tablename__ = "precompost_batches"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    creation_date = Column(Date, nullable=False)
    status = Column(
        Enum(PrecompostStatus), default=PrecompostStatus.FERMENTING, nullable=False
    )
    recipe_details = Column(JSON)   # {"estiércol_kg": 20, "cartón_kg": 5, ...}
    maturity_date = Column(Date)    # creation_date + 21 days
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    feedings = relationship("Feeding", back_populates="batch")


class IBCBed(Base):
    """ibc_beds: Contenedores IBC de lombricultura (Módulo Producción)"""
    __tablename__ = "ibc_beds"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    location = Column(String(100))
    start_date = Column(Date, nullable=False)
    worm_biomass_kg = Column(Float, default=0.0)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    feedings = relationship("Feeding", back_populates="ibc")


class Feeding(Base):
    """feedings: Eventos de alimentación IBC <- Precompost"""
    __tablename__ = "feedings"

    id = Column(Integer, primary_key=True, index=True)
    ibc_id = Column(Integer, ForeignKey("ibc_beds.id"), nullable=False)
    batch_id = Column(Integer, ForeignKey("precompost_batches.id"), nullable=False)
    quantity_kg = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    operator_id = Column(Integer, ForeignKey("users.id"))

    ibc = relationship("IBCBed", back_populates="feedings")
    batch = relationship("PrecompostBatch", back_populates="feedings")


class Product(Base):
    """products: Producto final envasado (Módulo Laboratorio)"""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    batch_code = Column(String(50), unique=True, nullable=False)  # Batch ID para QR
    type = Column(Enum(ProductType), nullable=False)
    packaging_size = Column(String(50))    # e.g. "1L", "5L", "25kg"
    stock_qty = Column(Integer, default=0)
    sku = Column(String(100))              # WooCommerce SKU sync
    source_ibc_id = Column(Integer, ForeignKey("ibc_beds.id"))
    harvest_date = Column(Date)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Sale(Base):
    """sales: Registro de ventas (Módulo Dinero)"""
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    source = Column(Enum(SaleSource), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    amount_eur = Column(Float, nullable=False)
    date = Column(DateTime(timezone=True), server_default=func.now())
    woocommerce_order_id = Column(String(100))

    product = relationship("Product")
