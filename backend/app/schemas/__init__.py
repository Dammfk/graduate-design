from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class RoleEnum(str, Enum):
    """用户角色"""
    ADMIN = "admin"
    MANAGER = "manager"
    OPERATOR = "operator"
    VIEWER = "viewer"


# ===== User Schemas =====
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(...)
    role: RoleEnum = RoleEnum.VIEWER


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    email: Optional[str] = None
    role: Optional[RoleEnum] = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ===== Device Schemas =====
class DeviceBase(BaseModel):
    device_id: str = Field(..., max_length=50)
    device_name: str = Field(..., max_length=100)
    device_type: str = Field(..., max_length=50)
    location: Optional[str] = None


class DeviceCreate(DeviceBase):
    pass


class DeviceUpdate(BaseModel):
    device_name: Optional[str] = None
    location: Optional[str] = None
    is_active: Optional[bool] = None


class DeviceResponse(DeviceBase):
    id: int
    owner_id: int
    is_active: bool
    latest_data_timestamp: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ===== EnvironmentData Schemas =====
class EnvironmentDataBase(BaseModel):
    device_id: str
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    co2_concentration: Optional[float] = None
    ammonia_concentration: Optional[float] = None


class EnvironmentDataCreate(EnvironmentDataBase):
    pass


class EnvironmentDataResponse(BaseModel):
    id: int
    device_id: int
    temperature: Optional[float]
    humidity: Optional[float]
    co2_concentration: Optional[float]
    ammonia_concentration: Optional[float]
    recorded_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


# ===== LivestockArchive Schemas =====
class LivestockArchiveBase(BaseModel):
    batch_number: str = Field(..., max_length=50)
    species: str = Field(..., max_length=50)
    quantity: int = Field(..., gt=0)
    check_in_date: datetime
    expected_checkout_date: Optional[datetime] = None
    immunization_records: Optional[str] = None
    notes: Optional[str] = None
    average_weight: Optional[float] = None
    feed_consumption: Optional[float] = None
    health_status: Optional[str] = None


class LivestockArchiveCreate(LivestockArchiveBase):
    pass


class LivestockArchiveUpdate(BaseModel):
    batch_number: Optional[str] = Field(default=None, max_length=50)
    species: Optional[str] = Field(default=None, max_length=50)
    quantity: Optional[int] = Field(default=None, gt=0)
    expected_checkout_date: Optional[datetime] = None
    immunization_records: Optional[str] = None
    notes: Optional[str] = None
    average_weight: Optional[float] = None
    feed_consumption: Optional[float] = None
    health_status: Optional[str] = None
    is_active: Optional[bool] = None


class LivestockArchiveResponse(LivestockArchiveBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ===== AlarmInfo Schemas =====
class AlarmInfoBase(BaseModel):
    device_id: int
    alarm_type: str = Field(..., max_length=50)
    alarm_level: str = Field(..., max_length=20)
    threshold_value: Optional[float] = None
    actual_value: Optional[float] = None
    description: Optional[str] = None


class AlarmInfoCreate(AlarmInfoBase):
    pass


class AlarmInfoUpdate(BaseModel):
    status: Optional[str] = None
    user_id: Optional[int] = None


class AlarmInfoResponse(AlarmInfoBase):
    id: int
    status: str
    alarm_time: datetime
    resolved_time: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ===== Telemetry Schema =====
class TelemetryData(BaseModel):
    """物联网平台转发的遥测数据"""
    device_id: str
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    co2_concentration: Optional[float] = None
    ammonia_concentration: Optional[float] = None
    timestamp: Optional[datetime] = None


# ===== Control Schemas =====
class DeviceControlRequest(BaseModel):
    target_component: str = Field(..., max_length=50)
    command_type: str = Field(..., max_length=50)
    execution_mode: str = Field(default="manual", max_length=20)
    reason: Optional[str] = Field(default=None, max_length=255)
    operator_user_id: Optional[int] = None


class AutomationRuleUpdate(BaseModel):
    is_enabled: bool


class ArchiveMetricsUpdate(BaseModel):
    average_weight: Optional[float] = None
    feed_consumption: Optional[float] = None
    health_status: Optional[str] = None
    notes: Optional[str] = None


class ArchiveDeleteResponse(BaseModel):
    id: int
    is_active: bool


class AnimalProfileResponse(BaseModel):
    id: int
    archive_id: int
    animal_code: str
    species: str
    breed: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[datetime] = None
    check_in_date: datetime
    weight: Optional[float] = None
    health_status: Optional[str] = None
    ear_tag: Optional[str] = None
    source: Optional[str] = None
    immunization_note: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool


class AnimalProfileUpdate(BaseModel):
    animal_code: Optional[str] = None
    species: Optional[str] = None
    breed: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[datetime] = None
    check_in_date: Optional[datetime] = None
    weight: Optional[float] = None
    health_status: Optional[str] = None
    ear_tag: Optional[str] = None
    source: Optional[str] = None
    immunization_note: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class AnimalProfileCreate(BaseModel):
    archive_id: int
    animal_code: str = Field(..., max_length=50)
    species: str = Field(..., max_length=50)
    breed: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[datetime] = None
    check_in_date: datetime
    weight: Optional[float] = None
    health_status: Optional[str] = None
    ear_tag: Optional[str] = None
    source: Optional[str] = None
    immunization_note: Optional[str] = None
    notes: Optional[str] = None


class ProductionTaskCreate(BaseModel):
    title: str = Field(..., max_length=100)
    category: str = Field(..., max_length=50)
    priority: str = Field(default="medium", max_length=20)
    status: str = Field(default="pending", max_length=20)
    zone_name: Optional[str] = None
    archive_id: Optional[int] = None
    assignee_user_id: Optional[int] = None
    due_at: Optional[datetime] = None
    description: Optional[str] = None


class ProductionTaskStatusUpdate(BaseModel):
    status: str = Field(..., max_length=20)


class ProductionTaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=100)
    category: Optional[str] = Field(default=None, max_length=50)
    priority: Optional[str] = Field(default=None, max_length=20)
    status: Optional[str] = Field(default=None, max_length=20)
    zone_name: Optional[str] = None
    archive_id: Optional[int] = None
    assignee_user_id: Optional[int] = None
    due_at: Optional[datetime] = None
    description: Optional[str] = None


class DailyTaskCreate(BaseModel):
    title: str = Field(..., max_length=100)
    category: str = Field(..., max_length=50)
    status: str = Field(default="pending", max_length=20)
    priority: str = Field(default="medium", max_length=20)
    zone_name: Optional[str] = None
    archive_id: Optional[int] = None
    assignee_user_id: Optional[int] = None
    description: Optional[str] = None
    is_active: bool = True


class DailyTaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=100)
    category: Optional[str] = Field(default=None, max_length=50)
    status: Optional[str] = Field(default=None, max_length=20)
    priority: Optional[str] = Field(default=None, max_length=20)
    zone_name: Optional[str] = None
    archive_id: Optional[int] = None
    assignee_user_id: Optional[int] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class InventoryItemCreate(BaseModel):
    item_name: str = Field(..., max_length=100)
    category: str = Field(..., max_length=50)
    unit: str = Field(default="kg", max_length=20)
    current_stock: float = 0
    safety_stock: float = 0
    location: Optional[str] = None
    supplier: Optional[str] = None
    last_restocked_at: Optional[datetime] = None
    notes: Optional[str] = None


class InventoryItemUpdate(BaseModel):
    item_name: Optional[str] = Field(default=None, max_length=100)
    category: Optional[str] = Field(default=None, max_length=50)
    unit: Optional[str] = Field(default=None, max_length=20)
    current_stock: Optional[float] = None
    safety_stock: Optional[float] = None
    location: Optional[str] = None
    supplier: Optional[str] = None
    last_restocked_at: Optional[datetime] = None
    notes: Optional[str] = None


class EquipmentAssetCreate(BaseModel):
    asset_code: str = Field(..., max_length=50)
    asset_name: str = Field(..., max_length=100)
    asset_type: str = Field(..., max_length=50)
    zone_name: Optional[str] = None
    linked_device_id: Optional[int] = None
    status: str = Field(default="online", max_length=20)
    installed_at: Optional[datetime] = None
    last_maintenance_at: Optional[datetime] = None
    next_maintenance_at: Optional[datetime] = None
    notes: Optional[str] = None


class EquipmentAssetUpdate(BaseModel):
    asset_code: Optional[str] = Field(default=None, max_length=50)
    asset_name: Optional[str] = Field(default=None, max_length=100)
    asset_type: Optional[str] = Field(default=None, max_length=50)
    zone_name: Optional[str] = None
    linked_device_id: Optional[int] = None
    status: Optional[str] = Field(default=None, max_length=20)
    installed_at: Optional[datetime] = None
    last_maintenance_at: Optional[datetime] = None
    next_maintenance_at: Optional[datetime] = None
    notes: Optional[str] = None
