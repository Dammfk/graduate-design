from __future__ import annotations

import json
from datetime import datetime, timedelta

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.core.database import get_redis_client
from app.models import Device, EnvironmentData, RoleEnum, User
from app.schemas import EnvironmentDataCreate


class TelemetryService:
    AUTO_OWNER_USERNAME = "auto_device_owner"

    @staticmethod
    def _get_or_create_auto_owner(db: Session) -> User:
        owner = (
            db.query(User)
            .filter(User.username == TelemetryService.AUTO_OWNER_USERNAME)
            .first()
        )
        if owner:
            return owner

        owner = (
            db.query(User)
            .filter(User.role == RoleEnum.ADMIN)
            .order_by(User.id.asc())
            .first()
        )
        if owner:
            return owner

        owner = User(
            username=TelemetryService.AUTO_OWNER_USERNAME,
            email="auto_device_owner@example.com",
            password_hash="auto_generated_owner",
            role=RoleEnum.ADMIN,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(owner)
        db.commit()
        db.refresh(owner)
        return owner

    @staticmethod
    def _auto_register_device(db: Session, device_id_str: str) -> Device:
        owner = TelemetryService._get_or_create_auto_owner(db)
        device = Device(
            device_id=device_id_str,
            device_name=f"自动注册设备 {device_id_str}",
            device_type="stm32_controller",
            location="未分配",
            owner_id=owner.id,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(device)
        db.commit()
        db.refresh(device)
        return device

    @staticmethod
    async def save_environment_data(
        db: Session,
        device_id_str: str,
        data: EnvironmentDataCreate,
    ) -> EnvironmentData:
        device = db.query(Device).filter(Device.device_id == device_id_str).first()
        if not device:
            device = TelemetryService._auto_register_device(db, device_id_str)

        db_data = EnvironmentData(
            device_id=device.id,
            temperature=data.temperature,
            humidity=data.humidity,
            co2_concentration=data.co2_concentration,
            ammonia_concentration=data.ammonia_concentration,
            recorded_at=data.timestamp or datetime.utcnow(),
        )

        db.add(db_data)
        db.commit()
        db.refresh(db_data)

        device.latest_data_timestamp = db_data.recorded_at
        db.commit()

        await TelemetryService.cache_latest_data(device.device_id, db_data)
        return db_data

    @staticmethod
    async def cache_latest_data(device_id: str, data: EnvironmentData) -> None:
        try:
            redis_client = get_redis_client()
            cache_key = f"device:{device_id}:latest"
            cache_data = {
                "id": data.id,
                "temperature": data.temperature,
                "humidity": data.humidity,
                "co2_concentration": data.co2_concentration,
                "ammonia_concentration": data.ammonia_concentration,
                "recorded_at": data.recorded_at.isoformat() if data.recorded_at else None,
            }
            redis_client.setex(cache_key, 3600, json.dumps(cache_data))
        except Exception as exc:
            print(f"Error caching data to Redis: {exc}")

    @staticmethod
    def get_latest_data_from_cache(device_id: str) -> dict | None:
        try:
            redis_client = get_redis_client()
            cache_key = f"device:{device_id}:latest"
            data = redis_client.get(cache_key)
            if data:
                return json.loads(data)
        except Exception as exc:
            print(f"Error getting cache data from Redis: {exc}")
        return None

    @staticmethod
    def get_latest_data_from_db(db: Session, device_id: str) -> EnvironmentData | None:
        device = db.query(Device).filter(Device.device_id == device_id).first()
        if not device:
            return None

        return (
            db.query(EnvironmentData)
            .filter(EnvironmentData.device_id == device.id)
            .order_by(desc(EnvironmentData.recorded_at))
            .first()
        )

    @staticmethod
    def get_historical_data(db: Session, device_id: str, hours: int = 24) -> list[EnvironmentData]:
        device = db.query(Device).filter(Device.device_id == device_id).first()
        if not device:
            return []

        time_threshold = datetime.utcnow() - timedelta(hours=hours)
        return (
            db.query(EnvironmentData)
            .filter(
                EnvironmentData.device_id == device.id,
                EnvironmentData.recorded_at >= time_threshold,
            )
            .order_by(EnvironmentData.recorded_at)
            .all()
        )

    @staticmethod
    def _get_zone_name(location: str | None) -> str:
        if not location:
            return "未分区"
        return location.split()[0]

    @staticmethod
    def _build_device_snapshot(device: Device, latest: EnvironmentData | None) -> dict:
        zone_name = TelemetryService._get_zone_name(device.location)
        return {
            "id": device.id,
            "device_id": device.device_id,
            "device_name": device.device_name,
            "device_type": device.device_type,
            "location": device.location,
            "zone_name": zone_name,
            "is_active": device.is_active,
            "latest_data_timestamp": (
                latest.recorded_at.isoformat()
                if latest and latest.recorded_at
                else device.latest_data_timestamp.isoformat()
                if device.latest_data_timestamp
                else None
            ),
            "latest_data": {
                "temperature": latest.temperature if latest else None,
                "humidity": latest.humidity if latest else None,
                "co2_concentration": latest.co2_concentration if latest else None,
                "ammonia_concentration": latest.ammonia_concentration if latest else None,
                "recorded_at": latest.recorded_at.isoformat() if latest and latest.recorded_at else None,
            },
        }

    @staticmethod
    def get_monitoring_devices(db: Session) -> list[dict]:
        devices = db.query(Device).order_by(Device.location, Device.device_name).all()
        snapshots: list[dict] = []
        for device in devices:
            latest = (
                db.query(EnvironmentData)
                .filter(EnvironmentData.device_id == device.id)
                .order_by(desc(EnvironmentData.recorded_at))
                .first()
            )
            snapshots.append(TelemetryService._build_device_snapshot(device, latest))
        return snapshots

    @staticmethod
    def get_monitoring_overview(db: Session) -> dict:
        snapshots = TelemetryService.get_monitoring_devices(db)
        if not snapshots:
            return {
                "zones": [],
                "devices": [],
                "summary": {
                    "device_count": 0,
                    "zone_count": 0,
                    "online_count": 0,
                    "offline_count": 0,
                    "avg_temperature": None,
                    "avg_humidity": None,
                    "avg_co2": None,
                    "avg_ammonia": None,
                    "last_updated_at": None,
                },
            }

        zones: dict[str, dict] = {}
        temperatures = []
        humidity_values = []
        co2_values = []
        ammonia_values = []
        timestamps = []

        for snapshot in snapshots:
            zone_name = snapshot["zone_name"]
            zone = zones.setdefault(
                zone_name,
                {
                    "zone_name": zone_name,
                    "device_count": 0,
                    "online_count": 0,
                    "offline_count": 0,
                    "devices": [],
                },
            )
            zone["device_count"] += 1
            if snapshot["is_active"]:
                zone["online_count"] += 1
            else:
                zone["offline_count"] += 1
            zone["devices"].append(snapshot)

            latest_data = snapshot["latest_data"]
            if latest_data["temperature"] is not None:
                temperatures.append(latest_data["temperature"])
            if latest_data["humidity"] is not None:
                humidity_values.append(latest_data["humidity"])
            if latest_data["co2_concentration"] is not None:
                co2_values.append(latest_data["co2_concentration"])
            if latest_data["ammonia_concentration"] is not None:
                ammonia_values.append(latest_data["ammonia_concentration"])
            if latest_data["recorded_at"]:
                timestamps.append(latest_data["recorded_at"])

        return {
            "zones": list(zones.values()),
            "devices": snapshots,
            "summary": {
                "device_count": len(snapshots),
                "zone_count": len(zones),
                "online_count": sum(1 for item in snapshots if item["is_active"]),
                "offline_count": sum(1 for item in snapshots if not item["is_active"]),
                "avg_temperature": round(sum(temperatures) / len(temperatures), 1) if temperatures else None,
                "avg_humidity": round(sum(humidity_values) / len(humidity_values), 1) if humidity_values else None,
                "avg_co2": round(sum(co2_values) / len(co2_values), 1) if co2_values else None,
                "avg_ammonia": round(sum(ammonia_values) / len(ammonia_values), 1) if ammonia_values else None,
                "last_updated_at": max(timestamps) if timestamps else None,
            },
        }

    @staticmethod
    def get_zone_history(db: Session, zone_name: str, hours: int = 24) -> list[dict]:
        time_threshold = datetime.utcnow() - timedelta(hours=hours)
        rows = (
            db.query(
                EnvironmentData.recorded_at.label("recorded_at"),
                func.avg(EnvironmentData.temperature).label("temperature"),
                func.avg(EnvironmentData.humidity).label("humidity"),
                func.avg(EnvironmentData.co2_concentration).label("co2_concentration"),
                func.avg(EnvironmentData.ammonia_concentration).label("ammonia_concentration"),
            )
            .join(Device, Device.id == EnvironmentData.device_id)
            .filter(
                Device.location.like(f"{zone_name}%"),
                EnvironmentData.recorded_at >= time_threshold,
            )
            .group_by(EnvironmentData.recorded_at)
            .order_by(EnvironmentData.recorded_at)
            .all()
        )
        return [
            {
                "timestamp": row.recorded_at.isoformat(),
                "temperature": round(row.temperature, 1) if row.temperature is not None else None,
                "humidity": round(row.humidity, 1) if row.humidity is not None else None,
                "co2_concentration": round(row.co2_concentration, 1) if row.co2_concentration is not None else None,
                "ammonia_concentration": round(row.ammonia_concentration, 1) if row.ammonia_concentration is not None else None,
            }
            for row in rows
        ]

