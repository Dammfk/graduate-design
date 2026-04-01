from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import SystemService

router = APIRouter(prefix="/api/v1/system", tags=["system"])


@router.get("/dashboard")
async def get_system_dashboard(db: Session = Depends(get_db)):
    try:
        return {"status": "success", "data": SystemService.get_dashboard(db)}
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get("/users/{user_id}/logs")
async def get_user_operation_logs(user_id: int, limit: int = 20, db: Session = Depends(get_db)):
    try:
        return {"status": "success", "data": SystemService.get_user_operation_logs(db, user_id, limit)}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.put("/users/{user_id}")
async def update_user(user_id: int, payload: dict, db: Session = Depends(get_db)):
    try:
        result = SystemService.update_user(
            db=db,
            user_id=user_id,
            role=payload.get("role"),
            is_active=payload.get("is_active"),
        )
        return {"status": "success", "message": "User updated", "data": result}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
