import traceback

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import (
    DailyTaskCreate,
    DailyTaskUpdate,
    EquipmentAssetCreate,
    EquipmentAssetUpdate,
    InventoryItemCreate,
    InventoryItemUpdate,
    ProductionTaskCreate,
    ProductionTaskStatusUpdate,
    ProductionTaskUpdate,
)
from app.services import OperationsService

router = APIRouter(prefix="/api/v1/operations", tags=["operations"])


@router.get("/dashboard")
async def get_operations_dashboard(db: Session = Depends(get_db)):
    try:
        return {"status": "success", "data": OperationsService.get_dashboard(db)}
    except Exception as exc:
        traceback.print_exc()
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


@router.put("/tasks/{task_id}")
async def update_task(task_id: int, payload: ProductionTaskUpdate, db: Session = Depends(get_db)):
    try:
        result = OperationsService.update_task(db=db, task_id=task_id, **payload.model_dump(exclude_unset=True))
        return {"status": "success", "message": "Task updated", "data": result}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
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


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: int, db: Session = Depends(get_db)):
    try:
        result = OperationsService.delete_task(db=db, task_id=task_id)
        return {"status": "success", "message": "Task deleted", "data": result}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.post("/daily-tasks")
async def create_daily_task(payload: DailyTaskCreate, db: Session = Depends(get_db)):
    try:
        result = OperationsService.create_daily_task(db=db, **payload.model_dump())
        return {"status": "success", "message": "Daily task created", "data": result}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.put("/daily-tasks/{task_id}")
async def update_daily_task(task_id: int, payload: DailyTaskUpdate, db: Session = Depends(get_db)):
    try:
        result = OperationsService.update_daily_task(db=db, task_id=task_id, **payload.model_dump(exclude_unset=True))
        return {"status": "success", "message": "Daily task updated", "data": result}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.delete("/daily-tasks/{task_id}")
async def delete_daily_task(task_id: int, db: Session = Depends(get_db)):
    try:
        result = OperationsService.delete_daily_task(db=db, task_id=task_id)
        return {"status": "success", "message": "Daily task deleted", "data": result}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.post("/inventory")
async def create_inventory_item(payload: InventoryItemCreate, db: Session = Depends(get_db)):
    try:
        result = OperationsService.create_inventory_item(db=db, **payload.model_dump())
        return {"status": "success", "message": "Inventory item created", "data": result}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.put("/inventory/{item_id}")
async def update_inventory_item(item_id: int, payload: InventoryItemUpdate, db: Session = Depends(get_db)):
    try:
        result = OperationsService.update_inventory_item(db=db, item_id=item_id, **payload.model_dump(exclude_unset=True))
        return {"status": "success", "message": "Inventory item updated", "data": result}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.delete("/inventory/{item_id}")
async def delete_inventory_item(item_id: int, db: Session = Depends(get_db)):
    try:
        result = OperationsService.delete_inventory_item(db=db, item_id=item_id)
        return {"status": "success", "message": "Inventory item deleted", "data": result}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.post("/assets")
async def create_equipment_asset(payload: EquipmentAssetCreate, db: Session = Depends(get_db)):
    try:
        result = OperationsService.create_equipment_asset(db=db, **payload.model_dump())
        return {"status": "success", "message": "Equipment asset created", "data": result}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.put("/assets/{asset_id}")
async def update_equipment_asset(asset_id: int, payload: EquipmentAssetUpdate, db: Session = Depends(get_db)):
    try:
        result = OperationsService.update_equipment_asset(db=db, asset_id=asset_id, **payload.model_dump(exclude_unset=True))
        return {"status": "success", "message": "Equipment asset updated", "data": result}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.delete("/assets/{asset_id}")
async def delete_equipment_asset(asset_id: int, db: Session = Depends(get_db)):
    try:
        result = OperationsService.delete_equipment_asset(db=db, asset_id=asset_id)
        return {"status": "success", "message": "Equipment asset deleted", "data": result}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
