from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class RoleEnum(PyEnum):
    ADMIN = "admin"
    MANAGER = "manager"
    OPERATOR = "operator"
    VIEWER = "viewer"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.VIEWER, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    devices = relationship("Device", back_populates="owner")
    alarm_logs = relationship("AlarmInfo", back_populates="user")
    control_logs = relationship("ControlCommandLog", back_populates="operator")


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True)
    device_id = Column(String(50), unique=True, nullable=False, index=True)
    device_name = Column(String(100), nullable=False)
    device_type = Column(String(50), nullable=False)
    location = Column(String(200))
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    latest_data_timestamp = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="devices")
    environment_data = relationship("EnvironmentData", back_populates="device")
    control_logs = relationship("ControlCommandLog", back_populates="device")


class EnvironmentData(Base):
    __tablename__ = "environment_data"

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    temperature = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    co2_concentration = Column(Float, nullable=True)
    ammonia_concentration = Column(Float, nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    device = relationship("Device", back_populates="environment_data")


class LivestockArchive(Base):
    __tablename__ = "livestock_archive"

    id = Column(Integer, primary_key=True)
    batch_number = Column(String(50), unique=True, nullable=False, index=True)
    species = Column(String(50), nullable=False)
    quantity = Column(Integer, nullable=False)
    check_in_date = Column(DateTime, nullable=False)
    expected_checkout_date = Column(DateTime)
    immunization_records = Column(Text)
    notes = Column(Text)
    is_active = Column(Boolean, default=True)
    average_weight = Column(Float)
    feed_consumption = Column(Float)
    health_status = Column(String(50), default="stable")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    animal_profiles = relationship("AnimalProfile", back_populates="archive")


class AnimalProfile(Base):
    __tablename__ = "animal_profiles"

    id = Column(Integer, primary_key=True)
    archive_id = Column(Integer, ForeignKey("livestock_archive.id"), nullable=False, index=True)
    animal_code = Column(String(50), unique=True, nullable=False, index=True)
    species = Column(String(50), nullable=False)
    breed = Column(String(50))
    gender = Column(String(20))
    birth_date = Column(DateTime)
    check_in_date = Column(DateTime, nullable=False)
    weight = Column(Float)
    health_status = Column(String(50), default="stable")
    ear_tag = Column(String(50))
    source = Column(String(100))
    immunization_note = Column(Text)
    notes = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    archive = relationship("LivestockArchive", back_populates="animal_profiles")
    history_records = relationship("AnimalProfileHistory", back_populates="animal", order_by="AnimalProfileHistory.changed_at.desc()")


class AnimalProfileHistory(Base):
    __tablename__ = "animal_profile_history"

    id = Column(Integer, primary_key=True)
    animal_id = Column(Integer, ForeignKey("animal_profiles.id"), nullable=False, index=True)
    field_name = Column(String(50), nullable=False)
    old_value = Column(String(100))
    new_value = Column(String(100))
    changed_at = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    animal = relationship("AnimalProfile", back_populates="history_records")


class AlarmInfo(Base):
    __tablename__ = "alarm_info"

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    alarm_type = Column(String(50), nullable=False)
    alarm_level = Column(String(20), nullable=False)
    threshold_value = Column(Float)
    actual_value = Column(Float)
    description = Column(String(255))
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String(20), default="pending")
    alarm_time = Column(DateTime, default=datetime.utcnow, index=True)
    resolved_time = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    device = relationship("Device")
    user = relationship("User", back_populates="alarm_logs")


class ControlCommandLog(Base):
    __tablename__ = "control_command_logs"

    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    command_type = Column(String(50), nullable=False)
    target_component = Column(String(50), nullable=False)
    execution_mode = Column(String(20), default="manual")
    status = Column(String(20), default="success")
    reason = Column(String(255))
    operator_user_id = Column(Integer, ForeignKey("users.id"))
    payload = Column(Text)
    executed_at = Column(DateTime, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    device = relationship("Device", back_populates="control_logs")
    operator = relationship("User", back_populates="control_logs")


class AutomationRule(Base):
    __tablename__ = "automation_rules"

    id = Column(Integer, primary_key=True)
    rule_name = Column(String(100), unique=True, nullable=False)
    target_component = Column(String(50), nullable=False)
    trigger_metric = Column(String(50), nullable=False)
    comparison_operator = Column(String(10), nullable=False, default=">")
    threshold_value = Column(Float, nullable=False)
    action_command = Column(String(50), nullable=False)
    priority = Column(Integer, default=5)
    description = Column(String(255))
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ProductionTask(Base):
    __tablename__ = "production_tasks"

    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)
    status = Column(String(20), default="pending", nullable=False)
    priority = Column(String(20), default="medium", nullable=False)
    zone_name = Column(String(100))
    archive_id = Column(Integer, ForeignKey("livestock_archive.id"))
    assignee_user_id = Column(Integer, ForeignKey("users.id"))
    due_at = Column(DateTime)
    completed_at = Column(DateTime)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DailyTask(Base):
    __tablename__ = "daily_tasks"

    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)
    priority = Column(String(20), default="medium", nullable=False)
    zone_name = Column(String(100))
    archive_id = Column(Integer, ForeignKey("livestock_archive.id"))
    assignee_user_id = Column(Integer, ForeignKey("users.id"))
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True)
    item_name = Column(String(100), unique=True, nullable=False)
    category = Column(String(50), nullable=False)
    unit = Column(String(20), nullable=False, default="kg")
    current_stock = Column(Float, nullable=False, default=0)
    safety_stock = Column(Float, nullable=False, default=0)
    location = Column(String(100))
    supplier = Column(String(100))
    last_restocked_at = Column(DateTime)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EquipmentAsset(Base):
    __tablename__ = "equipment_assets"

    id = Column(Integer, primary_key=True)
    asset_code = Column(String(50), unique=True, nullable=False, index=True)
    asset_name = Column(String(100), nullable=False)
    asset_type = Column(String(50), nullable=False)
    zone_name = Column(String(100))
    linked_device_id = Column(Integer, ForeignKey("devices.id"))
    status = Column(String(20), default="online", nullable=False)
    installed_at = Column(DateTime)
    last_maintenance_at = Column(DateTime)
    next_maintenance_at = Column(DateTime)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class OperationLog(Base):
    __tablename__ = "operation_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    module_name = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False)
    target = Column(String(100))
    detail = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
