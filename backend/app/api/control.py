from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import (
    AutomationRuleUpdate,
    ControlCommandStatusUpdate,
    DeviceControlRequest,
)
from app.services import ControlService

router = APIRouter(prefix="/api/v1/control", tags=["control"])


@router.get("/dashboard")
async def get_control_dashboard(db: Session = Depends(get_db)):
    try:
        return {
            "status": "success",
            "data": ControlService.get_control_dashboard(db),
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.post("/devices/{device_id}/commands")
async def execute_manual_command(
    device_id: str,
    payload: DeviceControlRequest,
    db: Session = Depends(get_db),
):
    try:
        result = ControlService.execute_manual_command(
            db=db,
            device_id=device_id,
            target_component=payload.target_component,
            command_type=payload.command_type,
            execution_mode=payload.execution_mode,
            reason=payload.reason,
            operator_user_id=payload.operator_user_id,
        )
        return {
            "status": "success",
            "message": "Command executed",
            "data": result,
        }
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.get("/devices/{device_id}/commands/pending")
async def get_pending_commands(
    device_id: str,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    try:
        if limit < 1 or limit > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="limit must be between 1 and 100",
            )

        result = ControlService.get_pending_commands(db, device_id, limit)
        return {
            "status": "success",
            "device_id": device_id,
            "count": len(result),
            "data": result,
        }
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.put("/commands/{command_id}/status")
async def update_command_status(
    command_id: int,
    payload: ControlCommandStatusUpdate,
    db: Session = Depends(get_db),
):
    try:
        result = ControlService.update_command_status(db, command_id, payload.status)
        return {
            "status": "success",
            "message": "Command status updated",
            "data": result,
        }
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.put("/rules/{rule_id}")
async def update_rule_status(
    rule_id: int,
    payload: AutomationRuleUpdate,
    db: Session = Depends(get_db),
):
    try:
        result = ControlService.update_rule_status(db, rule_id, payload.is_enabled)
        return {
            "status": "success",
            "message": "Rule updated",
            "data": result,
        }
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )
