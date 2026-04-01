from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.models import EquipmentAsset, InventoryItem, LivestockArchive, ProductionTask, User


class OperationsService:
    @staticmethod
    def _serialize_task(task: ProductionTask, archive_lookup: dict[int, LivestockArchive], user_lookup: dict[int, User]) -> dict:
        archive = archive_lookup.get(task.archive_id)
        assignee = user_lookup.get(task.assignee_user_id)
        return {
            "id": task.id,
            "title": task.title,
            "category": task.category,
            "status": task.status,
            "priority": task.priority,
            "zone_name": task.zone_name,
            "archive_id": task.archive_id,
            "archive_batch_number": archive.batch_number if archive else None,
            "assignee_user_id": task.assignee_user_id,
            "assignee_name": assignee.username if assignee else None,
            "due_at": task.due_at.isoformat() if task.due_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "description": task.description,
            "created_at": task.created_at.isoformat() if task.created_at else None,
        }

    @staticmethod
    def _serialize_inventory(item: InventoryItem) -> dict:
        shortage = item.current_stock <= item.safety_stock
        return {
            "id": item.id,
            "item_name": item.item_name,
            "category": item.category,
            "unit": item.unit,
            "current_stock": item.current_stock,
            "safety_stock": item.safety_stock,
            "location": item.location,
            "supplier": item.supplier,
            "is_low_stock": shortage,
            "last_restocked_at": item.last_restocked_at.isoformat() if item.last_restocked_at else None,
            "notes": item.notes,
        }

    @staticmethod
    def _serialize_asset(asset: EquipmentAsset) -> dict:
        return {
            "id": asset.id,
            "asset_code": asset.asset_code,
            "asset_name": asset.asset_name,
            "asset_type": asset.asset_type,
            "zone_name": asset.zone_name,
            "linked_device_id": asset.linked_device_id,
            "status": asset.status,
            "installed_at": asset.installed_at.isoformat() if asset.installed_at else None,
            "last_maintenance_at": asset.last_maintenance_at.isoformat() if asset.last_maintenance_at else None,
            "next_maintenance_at": asset.next_maintenance_at.isoformat() if asset.next_maintenance_at else None,
            "notes": asset.notes,
        }

    @staticmethod
    def get_dashboard(db: Session) -> dict:
        tasks = db.query(ProductionTask).order_by(ProductionTask.due_at.asc(), ProductionTask.created_at.desc()).all()
        inventory_items = db.query(InventoryItem).order_by(InventoryItem.category.asc(), InventoryItem.item_name.asc()).all()
        assets = db.query(EquipmentAsset).order_by(EquipmentAsset.zone_name.asc(), EquipmentAsset.asset_name.asc()).all()

        archive_ids = {task.archive_id for task in tasks if task.archive_id}
        user_ids = {task.assignee_user_id for task in tasks if task.assignee_user_id}
        archive_lookup = {
            item.id: item for item in db.query(LivestockArchive).filter(LivestockArchive.id.in_(archive_ids)).all()
        } if archive_ids else {}
        user_lookup = {
            item.id: item for item in db.query(User).filter(User.id.in_(user_ids)).all()
        } if user_ids else {}

        pending_tasks = [task for task in tasks if task.status != "completed"]
        low_stock_items = [item for item in inventory_items if item.current_stock <= item.safety_stock]
        maintenance_due_assets = [
            asset for asset in assets if asset.next_maintenance_at and asset.next_maintenance_at <= datetime.utcnow()
        ]

        return {
            "summary": {
                "task_count": len(tasks),
                "pending_tasks": len(pending_tasks),
                "low_stock_items": len(low_stock_items),
                "asset_count": len(assets),
                "maintenance_due_assets": len(maintenance_due_assets),
            },
            "tasks": [OperationsService._serialize_task(task, archive_lookup, user_lookup) for task in tasks],
            "inventory": [OperationsService._serialize_inventory(item) for item in inventory_items],
            "assets": [OperationsService._serialize_asset(asset) for asset in assets],
            "users": [
                {
                    "id": user.id,
                    "username": user.username,
                    "role": user.role.value if hasattr(user.role, "value") else str(user.role),
                }
                for user in db.query(User).filter(User.is_active == True).order_by(User.id.asc()).all()
            ],
        }

    @staticmethod
    def create_task(
        db: Session,
        title: str,
        category: str,
        priority: str = "medium",
        status: str = "pending",
        zone_name: str | None = None,
        archive_id: int | None = None,
        assignee_user_id: int | None = None,
        due_at: datetime | None = None,
        description: str | None = None,
    ) -> dict:
        if archive_id and not db.query(LivestockArchive).filter(LivestockArchive.id == archive_id).first():
            raise ValueError(f"Archive not found: {archive_id}")
        if assignee_user_id and not db.query(User).filter(User.id == assignee_user_id).first():
            raise ValueError(f"User not found: {assignee_user_id}")

        task = ProductionTask(
            title=title,
            category=category,
            priority=priority,
            status=status,
            zone_name=zone_name,
            archive_id=archive_id,
            assignee_user_id=assignee_user_id,
            due_at=due_at,
            description=description,
            completed_at=datetime.utcnow() if status == "completed" else None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return OperationsService._serialize_task(task, {}, {})

    @staticmethod
    def update_task_status(db: Session, task_id: int, status: str) -> dict:
        task = db.query(ProductionTask).filter(ProductionTask.id == task_id).first()
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        task.status = status
        task.completed_at = datetime.utcnow() if status == "completed" else None
        task.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(task)
        return OperationsService._serialize_task(task, {}, {})
