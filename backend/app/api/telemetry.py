from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import TelemetryData
from app.services import AlarmService, ControlService, TelemetryService

router = APIRouter(prefix="/api/v1/telemetry", tags=["telemetry"])


@router.post("/")
async def receive_telemetry(
    telemetry: TelemetryData,
    db: Session = Depends(get_db),
):
    try:
        if not telemetry.timestamp:
            telemetry.timestamp = datetime.utcnow()

        environment_data = await TelemetryService.save_environment_data(
            db, telemetry.device_id, telemetry
        )
        alarms = await AlarmService.check_and_create_alarms(db, environment_data)
        commands = await ControlService.generate_control_commands(db, environment_data)

        return {
            "status": "success",
            "message": "Telemetry data received and processed",
            "data": {
                "data_id": environment_data.id,
                "device_id": telemetry.device_id,
                "alarms_created": len(alarms),
                "commands_generated": len(commands),
                "timestamp": environment_data.recorded_at,
            },
        }
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process telemetry data: {str(exc)}",
        )


@router.get("/overview")
async def get_monitoring_overview(db: Session = Depends(get_db)):
    try:
        return {
            "status": "success",
            "data": TelemetryService.get_monitoring_overview(db),
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.get("/zones/{zone_name}/history")
async def get_zone_history(
    zone_name: str,
    hours: int = 24,
    db: Session = Depends(get_db),
):
    try:
        if hours < 1 or hours > 720:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="hours must be between 1 and 720",
            )

        data_list = TelemetryService.get_zone_history(db, zone_name, hours)
        if not data_list:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No historical data found for zone: {zone_name}",
            )

        return {
            "status": "success",
            "zone_name": zone_name,
            "hours": hours,
            "count": len(data_list),
            "data": data_list,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.get("/latest/{device_id}")
async def get_latest_telemetry(
    device_id: str,
    db: Session = Depends(get_db),
):
    try:
        cached_data = TelemetryService.get_latest_data_from_cache(device_id)
        if cached_data:
            return {
                "status": "success",
                "source": "cache",
                "data": cached_data,
            }

        db_data = TelemetryService.get_latest_data_from_db(db, device_id)
        if not db_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No telemetry data found for device: {device_id}",
            )

        return {
            "status": "success",
            "source": "database",
            "data": {
                "id": db_data.id,
                "temperature": db_data.temperature,
                "humidity": db_data.humidity,
                "co2_concentration": db_data.co2_concentration,
                "ammonia_concentration": db_data.ammonia_concentration,
                "recorded_at": db_data.recorded_at.isoformat(),
            },
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.get("/history/{device_id}")
async def get_telemetry_history(
    device_id: str,
    hours: int = 24,
    db: Session = Depends(get_db),
):
    try:
        if hours < 1 or hours > 720:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="hours must be between 1 and 720",
            )

        data_list = TelemetryService.get_historical_data(db, device_id, hours)
        if not data_list:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No historical data found for device: {device_id}",
            )

        return {
            "status": "success",
            "device_id": device_id,
            "hours": hours,
            "count": len(data_list),
            "data": [
                {
                    "timestamp": item.recorded_at.isoformat(),
                    "temperature": item.temperature,
                    "humidity": item.humidity,
                    "co2_concentration": item.co2_concentration,
                    "ammonia_concentration": item.ammonia_concentration,
                }
                for item in data_list
            ],
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )

