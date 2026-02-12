from datetime import date, datetime
from pydantic import BaseModel, ConfigDict

from app.models.farm import PrecompostStatus, ProductType, SaleSource


# --- Raw Materials ---

class RawMaterialCreate(BaseModel):
    type: str
    origin: str | None = None
    quantity_kg: float
    date_received: date
    notes: str | None = None


class RawMaterialOut(RawMaterialCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


# --- Precompost Batches ---

class PrecompostBatchCreate(BaseModel):
    code: str
    creation_date: date
    recipe_details: dict | None = None
    notes: str | None = None


class PrecompostBatchOut(PrecompostBatchCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: PrecompostStatus
    maturity_date: date | None
    created_at: datetime


# --- IBC Beds ---

class IBCBedCreate(BaseModel):
    code: str
    location: str | None = None
    start_date: date
    worm_biomass_kg: float = 0.0
    notes: str | None = None


class IBCBedOut(IBCBedCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


# --- Feedings ---

class FeedingCreate(BaseModel):
    ibc_id: int
    batch_id: int
    quantity_kg: float
    operator_id: int | None = None


class FeedingOut(FeedingCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    timestamp: datetime


# --- Products ---

class ProductCreate(BaseModel):
    batch_code: str
    type: ProductType
    packaging_size: str | None = None
    stock_qty: int = 0
    sku: str | None = None
    source_ibc_id: int | None = None
    harvest_date: date | None = None
    notes: str | None = None


class ProductOut(ProductCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


# --- Sales ---

class SaleCreate(BaseModel):
    product_id: int
    source: SaleSource
    quantity: int = 1
    amount_eur: float
    woocommerce_order_id: str | None = None


class SaleOut(SaleCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    date: datetime


# --- Dashboard ---

class DashboardOut(BaseModel):
    total_revenue_eur: float
    monthly_target_eur: float = 1800.0
    progress_pct: float
    total_ibc_beds: int
    total_products_in_stock: int
    pending_precompost_batches: int
