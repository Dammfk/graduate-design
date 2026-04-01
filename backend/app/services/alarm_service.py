from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models import AlarmInfo, Device, LivestockArchive


class AlarmService:
    """智能告警与风险预警服务。"""

    ALARM_CONFIG = {
        "temperature_high": {"threshold": 30, "level": "warning", "label": "温度过高"},
        "temperature_low": {"threshold": 5, "level": "warning", "label": "温度过低"},
        "humidity_high": {"threshold": 90, "level": "warning", "label": "湿度过高"},
        "humidity_low": {"threshold": 20, "level": "warning", "label": "湿度过低"},
        "co2_high": {"threshold": 2000, "level": "warning", "label": "二氧化碳超标"},
        "ammonia_high": {"threshold": 20, "level": "critical", "label": "氨气超标"},
    }

    @staticmethod
    async def check_and_create_alarms(db: Session, environment_data) -> list[AlarmInfo]:
        alarms = []
        device = db.query(Device).filter(Device.id == environment_data.device_id).first()
        if not device:
            return alarms

        if environment_data.temperature is not None:
            if environment_data.temperature > 30:
                alarms.append(AlarmService._create_alarm(db, device, "temperature_high", environment_data.temperature))
            elif environment_data.temperature < 5:
                alarms.append(AlarmService._create_alarm(db, device, "temperature_low", environment_data.temperature))

        if environment_data.humidity is not None:
            if environment_data.humidity > 90:
                alarms.append(AlarmService._create_alarm(db, device, "humidity_high", environment_data.humidity))
            elif environment_data.humidity < 20:
                alarms.append(AlarmService._create_alarm(db, device, "humidity_low", environment_data.humidity))

        if environment_data.co2_concentration is not None and environment_data.co2_concentration > 2000:
            alarms.append(AlarmService._create_alarm(db, device, "co2_high", environment_data.co2_concentration))

        if environment_data.ammonia_concentration is not None and environment_data.ammonia_concentration > 20:
            alarms.append(AlarmService._create_alarm(db, device, "ammonia_high", environment_data.ammonia_concentration))

        return alarms

    @staticmethod
    def _create_alarm(db: Session, device: Device, alarm_type: str, actual_value: float) -> AlarmInfo:
        config = AlarmService.ALARM_CONFIG.get(alarm_type, {})
        alarm = AlarmInfo(
            device_id=device.id,
            alarm_type=alarm_type,
            alarm_level=config.get("level", "info"),
            threshold_value=config.get("threshold", 0),
            actual_value=actual_value,
            description=f"{config.get('label', alarm_type)}，实际值 {actual_value}",
            status="pending",
        )
        db.add(alarm)
        db.commit()
        db.refresh(alarm)
        return alarm

    @staticmethod
    def get_recent_alarms(db: Session, device_id: int, limit: int = 20) -> list[AlarmInfo]:
        return (
            db.query(AlarmInfo)
            .filter(AlarmInfo.device_id == device_id)
            .order_by(desc(AlarmInfo.alarm_time))
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_pending_alarms(db: Session, limit: int = 50) -> list[AlarmInfo]:
        return (
            db.query(AlarmInfo)
            .filter(AlarmInfo.status == "pending")
            .order_by(desc(AlarmInfo.alarm_time))
            .limit(limit)
            .all()
        )

    @staticmethod
    def acknowledge_alarm(db: Session, alarm_id: int, user_id: int = None) -> AlarmInfo | None:
        alarm = db.query(AlarmInfo).filter(AlarmInfo.id == alarm_id).first()
        if alarm:
            alarm.status = "acknowledged"
            alarm.user_id = user_id
            db.commit()
            db.refresh(alarm)
        return alarm

    @staticmethod
    def resolve_alarm(db: Session, alarm_id: int) -> AlarmInfo | None:
        alarm = db.query(AlarmInfo).filter(AlarmInfo.id == alarm_id).first()
        if alarm:
            alarm.status = "resolved"
            alarm.resolved_time = datetime.utcnow()
            db.commit()
            db.refresh(alarm)
        return alarm

    @staticmethod
    def get_risk_dashboard(db: Session) -> dict:
        alarms = db.query(AlarmInfo).order_by(desc(AlarmInfo.alarm_time)).all()
        now = datetime.utcnow()
        last_24h = now - timedelta(hours=24)
        recent_alarms = [alarm for alarm in alarms if alarm.alarm_time and alarm.alarm_time >= last_24h]

        level_counts = {"critical": 0, "warning": 0, "info": 0}
        type_counts = {}
        zone_counts = {}
        for alarm in recent_alarms:
            level_counts[alarm.alarm_level] = level_counts.get(alarm.alarm_level, 0) + 1
            type_counts[alarm.alarm_type] = type_counts.get(alarm.alarm_type, 0) + 1
            zone_name = alarm.device.location.split()[0] if alarm.device and alarm.device.location else "未分区"
            zone_counts[zone_name] = zone_counts.get(zone_name, 0) + 1

        highest_zone = max(zone_counts.items(), key=lambda item: item[1])[0] if zone_counts else None

        active_archives = db.query(LivestockArchive).filter(LivestockArchive.is_active == True).all()
        archive_risks = []
        for archive in active_archives:
            risk_level = "medium" if archive.health_status in {"observe"} else "low"
            if archive.health_status in {"observe"}:
                archive_risks.append({
                    "batch_number": archive.batch_number,
                    "species": archive.species,
                    "health_status": archive.health_status,
                    "risk_level": risk_level,
                    "reason": archive.notes or "健康状态需持续观察",
                })

        history = (
            db.query(
                func.date(AlarmInfo.alarm_time).label("day"),
                func.count(AlarmInfo.id).label("count"),
            )
            .filter(AlarmInfo.alarm_time >= now - timedelta(days=7))
            .group_by(func.date(AlarmInfo.alarm_time))
            .order_by(func.date(AlarmInfo.alarm_time))
            .all()
        )

        return {
            "summary": {
                "total_alarms": len(alarms),
                "pending_alarms": len([alarm for alarm in alarms if alarm.status == "pending"]),
                "critical_alarms_24h": level_counts.get("critical", 0),
                "highest_risk_zone": highest_zone,
            },
            "level_distribution": level_counts,
            "type_distribution": type_counts,
            "zone_distribution": zone_counts,
            "archive_risks": archive_risks,
            "history": [
                {"date": str(row.day), "count": row.count}
                for row in history
            ],
        }
