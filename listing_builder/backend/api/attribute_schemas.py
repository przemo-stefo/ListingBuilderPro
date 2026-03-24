# backend/api/attribute_schemas.py
# Purpose: Pydantic models for Auto-Atrybuty endpoints
# NOT for: Route logic (attribute_routes.py) or LLM logic (attribute_service.py)

from typing import Literal, Optional, List, Dict
from pydantic import BaseModel, Field


class CategoryItem(BaseModel):
    id: str
    name: str
    path: str
    leaf: bool


class CategorySearchResponse(BaseModel):
    categories: List[CategoryItem]


class ParameterOption(BaseModel):
    id: str
    value: str


class CategoryParameter(BaseModel):
    id: str
    name: str
    type: str
    required: bool
    unit: Optional[str]
    options: List[ParameterOption]


class CategoryParametersResponse(BaseModel):
    parameters: List[CategoryParameter]
    category_id: str


class AttributeGenerateRequest(BaseModel):
    product_input: str = Field(..., min_length=1, max_length=500)
    category_id: str = Field(..., min_length=1, max_length=50)
    category_name: str = Field(..., min_length=1, max_length=255)
    category_path: str = Field("", max_length=1000)
    marketplace: Literal["allegro", "kaufland"] = "allegro"


class GeneratedAttribute(BaseModel):
    name: str
    value: Optional[str]
    param_id: str
    required: bool
    type: str
    options: List[ParameterOption] = []


class AttributeGenerateResponse(BaseModel):
    id: int
    product_input: str
    category_name: str
    category_path: str
    attributes: List[GeneratedAttribute]
    params_count: int
    provider_used: str
    latency_ms: int
    created_at: Optional[str]


class AttributeHistoryItem(BaseModel):
    id: int
    product_input: str
    marketplace: str
    category_name: Optional[str]
    category_path: Optional[str]
    params_count: int
    attributes: List[Dict]
    created_at: Optional[str]


class AttributeHistoryResponse(BaseModel):
    items: List[AttributeHistoryItem]
    total: int


class ResolveUrlResponse(BaseModel):
    title: str
    category_id: str
    category_name: str
    category_path: str
    leaf: bool
