from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import AlarmInfo
from app.schemas import AlarmInfoUpdate
from app.services import AlarmService
from app.utils import to_display_iso

router = APIRouter(prefix="/api/v1/alarms", tags=["alarms"])


def _serialize_alarm(alarm: AlarmInfo) -> dict:
    return {
        "id": alarm.id,
        "device_id": alarm.device_id,
        "alarm_type": alarm.alarm_type,
        "alarm_level": alarm.alarm_level,
        "threshold_value": alarm.threshold_value,
        "actual_value": alarm.actual_value,
        "description": alarm.description,
        "alarm_time": to_display_iso(alarm.alarm_time),
        "status": alarm.status,
        "resolved_time": to_display_iso(alarm.resolved_time),
        "user_id": alarm.user_id,
    }


@router.get("/pending")
async def get_pending_alarms(db: Session = Depends(get_db)) -> dict:
    try:
        alarms = AlarmService.get_pending_alarms(db)
        return {
            "status": "success",
            "count": len(alarms),
            "data": [_serialize_alarm(alarm) for alarm in alarms],
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.get("/risk-dashboard")
async def get_risk_dashboard(db: Session = Depends(get_db)) -> dict:
    try:
        return {
            "status": "success",
            "data": AlarmService.get_risk_dashboard(db),
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.get("/device/{device_id}")
async def get_device_alarms(
    device_id: int,
    limit: int = 20,
    db: Session = Depends(get_db),
) -> dict:
    try:
        alarms = AlarmService.get_recent_alarms(db, device_id, limit)
        return {
            "status": "success",
            "device_id": device_id,
            "count": len(alarms),
            "data": [_serialize_alarm(alarm) for alarm in alarms],
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.put("/{alarm_id}/acknowledge")
async def acknowledge_alarm(
    alarm_id: int,
    update_data: AlarmInfoUpdate = None,
    db: Session = Depends(get_db),
) -> dict:
    try:
        user_id = update_data.user_id if update_data else None
        alarm = AlarmService.acknowledge_alarm(db, alarm_id, user_id)
        if not alarm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alarm not found: {alarm_id}",
            )
        return {
            "status": "success",
            "message": "Alarm acknowledged",
            "data": {
                "id": alarm.id,
                "status": alarm.status,
            },
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.put("/{alarm_id}/resolve")
async def resolve_alarm(
    alarm_id: int,
    db: Session = Depends(get_db),
) -> dict:
    try:
        alarm = AlarmService.resolve_alarm(db, alarm_id)
        if not alarm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alarm not found: {alarm_id}",
            )
        return {
            "status": "success",
            "message": "Alarm resolved",
            "data": {
                "id": alarm.id,
                "status": alarm.status,
                "resolved_time": to_display_iso(alarm.resolved_time),
            },
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.get("/{alarm_id}")
async def get_alarm_detail(
    alarm_id: int,
    db: Session = Depends(get_db),
) -> dict:
    try:
        alarm = db.query(AlarmInfo).filter(AlarmInfo.id == alarm_id).first()
        if not alarm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alarm not found: {alarm_id}",
            )
        return {
            "status": "success",
            "data": _serialize_alarm(alarm),
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )
