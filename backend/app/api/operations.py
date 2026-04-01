from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import ProductionTaskCreate, ProductionTaskStatusUpdate
from app.services import OperationsService

router = APIRouter(prefix="/api/v1/operations", tags=["operations"])


@router.get("/dashboard")
async def get_operations_dashboard(db: Session = Depends(get_db)):
    try:
        return {"status": "success", "data": OperationsService.get_dashboard(db)}
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.post("/tasks")
async def create_task(payload: ProductionTaskCreate, db: Session = Depends(get_db)):
    try:
        result = OperationsService.create_task(
            db=db,
            title=payload.title,
            category=payload.category,
            priority=payload.priority,
            status=payload.status,
            zone_name=payload.zone_name,
            archive_id=payload.archive_id,
            assignee_user_id=payload.assignee_user_id,
            due_at=payload.due_at,
            description=payload.description,
        )
        return {"status": "success", "message": "Task created", "data": result}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.put("/tasks/{task_id}/status")
async def update_task_status(task_id: int, payload: ProductionTaskStatusUpdate, db: Session = Depends(get_db)):
    try:
        result = OperationsService.update_task_status(db=db, task_id=task_id, status=payload.status)
        return {"status": "success", "message": "Task updated", "data": result}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
