from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import AutomationRuleUpdate, DeviceControlRequest
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
