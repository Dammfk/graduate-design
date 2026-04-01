from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.models import DailyTask, Device, EquipmentAsset, InventoryItem, LivestockArchive, ProductionTask, User


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
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
        }

    @staticmethod
    def _serialize_daily_task(task: DailyTask, archive_lookup: dict[int, LivestockArchive], user_lookup: dict[int, User]) -> dict:
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
            "description": task.description,
            "is_active": task.is_active,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
        }

    @staticmethod
    def _serialize_daily_task_as_today(task: DailyTask, archive_lookup: dict[int, LivestockArchive], user_lookup: dict[int, User]) -> dict:
        archive = archive_lookup.get(task.archive_id)
        assignee = user_lookup.get(task.assignee_user_id)
        return {
            "id": f"daily-{task.id}",
            "source": "daily",
            "source_id": task.id,
            "title": task.title,
            "category": task.category,
            "status": task.status if task.is_active else "disabled",
            "priority": task.priority,
            "zone_name": task.zone_name,
            "archive_id": task.archive_id,
            "archive_batch_number": archive.batch_number if archive else None,
            "assignee_user_id": task.assignee_user_id,
            "assignee_name": assignee.username if assignee else None,
            "due_at": None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "description": task.description,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
            "is_template": True,
            "is_active": task.is_active,
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
    def _ensure_inventory_name_unique(db: Session, item_name: str, exclude_id: int | None = None) -> None:
        query = db.query(InventoryItem).filter(InventoryItem.item_name == item_name)
        if exclude_id:
            query = query.filter(InventoryItem.id != exclude_id)
        if query.first():
            raise ValueError(f"Inventory item already exists: {item_name}")

    @staticmethod
    def _ensure_asset_code_unique(db: Session, asset_code: str, exclude_id: int | None = None) -> None:
        query = db.query(EquipmentAsset).filter(EquipmentAsset.asset_code == asset_code)
        if exclude_id:
            query = query.filter(EquipmentAsset.id != exclude_id)
        if query.first():
            raise ValueError(f"Asset code already exists: {asset_code}")

    @staticmethod
    def _validate_linked_device(db: Session, linked_device_id: int | None) -> None:
        if linked_device_id and not db.query(Device).filter(Device.id == linked_device_id).first():
            raise ValueError(f"Device not found: {linked_device_id}")

    @staticmethod
    def _build_lookup(db: Session, archive_ids: set[int], user_ids: set[int]) -> tuple[dict[int, LivestockArchive], dict[int, User]]:
        archive_lookup = {
            item.id: item for item in db.query(LivestockArchive).filter(LivestockArchive.id.in_(archive_ids)).all()
        } if archive_ids else {}
        user_lookup = {
            item.id: item for item in db.query(User).filter(User.id.in_(user_ids)).all()
        } if user_ids else {}
        return archive_lookup, user_lookup

    @staticmethod
    def get_dashboard(db: Session) -> dict:
        tasks = db.query(ProductionTask).order_by(ProductionTask.due_at.asc(), ProductionTask.created_at.desc()).all()
        daily_tasks = db.query(DailyTask).order_by(DailyTask.is_active.desc(), DailyTask.updated_at.desc()).all()
        inventory_items = db.query(InventoryItem).order_by(InventoryItem.category.asc(), InventoryItem.item_name.asc()).all()
        assets = db.query(EquipmentAsset).order_by(EquipmentAsset.zone_name.asc(), EquipmentAsset.asset_name.asc()).all()

        archive_ids = {task.archive_id for task in tasks if task.archive_id} | {task.archive_id for task in daily_tasks if task.archive_id}
        user_ids = {task.assignee_user_id for task in tasks if task.assignee_user_id} | {task.assignee_user_id for task in daily_tasks if task.assignee_user_id}
        archive_lookup, user_lookup = OperationsService._build_lookup(db, archive_ids, user_ids)

        pending_tasks = [task for task in tasks if task.status != "completed"]
        pending_daily_tasks = [task for task in daily_tasks if task.is_active and task.status != "completed"]
        low_stock_items = [item for item in inventory_items if item.current_stock <= item.safety_stock]
        maintenance_due_assets = [
            asset for asset in assets if asset.next_maintenance_at and asset.next_maintenance_at <= datetime.utcnow()
        ]
        merged_today_tasks = [
            *[OperationsService._serialize_daily_task_as_today(task, archive_lookup, user_lookup) for task in daily_tasks if task.is_active],
            *[OperationsService._serialize_task(task, archive_lookup, user_lookup) for task in tasks],
        ]
        merged_today_tasks.sort(
            key=lambda item: (
                item.get("due_at") is None,
                item.get("due_at") or item.get("updated_at") or item.get("created_at") or "",
            )
        )

        return {
            "summary": {
                "task_count": len(merged_today_tasks),
                "daily_task_count": len(daily_tasks),
                "pending_tasks": len(pending_tasks) + len(pending_daily_tasks),
                "low_stock_items": len(low_stock_items),
                "asset_count": len(assets),
                "maintenance_due_assets": len(maintenance_due_assets),
            },
            "tasks": [OperationsService._serialize_task(task, archive_lookup, user_lookup) for task in tasks],
            "today_tasks": merged_today_tasks,
            "daily_tasks": [OperationsService._serialize_daily_task(task, archive_lookup, user_lookup) for task in daily_tasks],
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
    def _validate_relations(db: Session, archive_id: int | None, assignee_user_id: int | None) -> None:
        if archive_id and not db.query(LivestockArchive).filter(LivestockArchive.id == archive_id).first():
            raise ValueError(f"Archive not found: {archive_id}")
        if assignee_user_id and not db.query(User).filter(User.id == assignee_user_id).first():
            raise ValueError(f"User not found: {assignee_user_id}")

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
        OperationsService._validate_relations(db, archive_id, assignee_user_id)
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
        archive_lookup, user_lookup = OperationsService._build_lookup(db, {task.archive_id} if task.archive_id else set(), {task.assignee_user_id} if task.assignee_user_id else set())
        return OperationsService._serialize_task(task, archive_lookup, user_lookup)

    @staticmethod
    def update_task(db: Session, task_id: int, **payload) -> dict:
        task = db.query(ProductionTask).filter(ProductionTask.id == task_id).first()
        if not task:
            raise ValueError(f"Task not found: {task_id}")

        archive_id = payload.get("archive_id", task.archive_id)
        assignee_user_id = payload.get("assignee_user_id", task.assignee_user_id)
        OperationsService._validate_relations(db, archive_id, assignee_user_id)

        for field, value in payload.items():
            if value is not None or field in {"archive_id", "assignee_user_id", "zone_name", "description"}:
                setattr(task, field, value)

        task.completed_at = datetime.utcnow() if task.status == "completed" else None
        task.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(task)
        archive_lookup, user_lookup = OperationsService._build_lookup(db, {task.archive_id} if task.archive_id else set(), {task.assignee_user_id} if task.assignee_user_id else set())
        return OperationsService._serialize_task(task, archive_lookup, user_lookup)

    @staticmethod
    def update_task_status(db: Session, task_id: int, status: str) -> dict:
        return OperationsService.update_task(db=db, task_id=task_id, status=status)

    @staticmethod
    def delete_task(db: Session, task_id: int) -> dict:
        task = db.query(ProductionTask).filter(ProductionTask.id == task_id).first()
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        serialized = {
            "id": task.id,
            "status": task.status,
        }
        db.delete(task)
        db.commit()
        return serialized

    @staticmethod
    def create_daily_task(
        db: Session,
        title: str,
        category: str,
        status: str = "pending",
        priority: str = "medium",
        zone_name: str | None = None,
        archive_id: int | None = None,
        assignee_user_id: int | None = None,
        description: str | None = None,
        is_active: bool = True,
    ) -> dict:
        OperationsService._validate_relations(db, archive_id, assignee_user_id)
        task = DailyTask(
            title=title,
            category=category,
            status=status,
            priority=priority,
            zone_name=zone_name,
            archive_id=archive_id,
            assignee_user_id=assignee_user_id,
            description=description,
            is_active=is_active,
            completed_at=datetime.utcnow() if status == "completed" else None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        archive_lookup, user_lookup = OperationsService._build_lookup(db, {task.archive_id} if task.archive_id else set(), {task.assignee_user_id} if task.assignee_user_id else set())
        return OperationsService._serialize_daily_task(task, archive_lookup, user_lookup)

    @staticmethod
    def update_daily_task(db: Session, task_id: int, **payload) -> dict:
        task = db.query(DailyTask).filter(DailyTask.id == task_id).first()
        if not task:
            raise ValueError(f"Daily task not found: {task_id}")

        archive_id = payload.get("archive_id", task.archive_id)
        assignee_user_id = payload.get("assignee_user_id", task.assignee_user_id)
        OperationsService._validate_relations(db, archive_id, assignee_user_id)

        for field, value in payload.items():
            if value is not None or field in {"archive_id", "assignee_user_id", "zone_name", "description", "is_active"}:
                setattr(task, field, value)

        if task.status == "completed":
            task.completed_at = datetime.utcnow()
        elif "status" in payload:
            task.completed_at = None
        task.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(task)
        archive_lookup, user_lookup = OperationsService._build_lookup(db, {task.archive_id} if task.archive_id else set(), {task.assignee_user_id} if task.assignee_user_id else set())
        return OperationsService._serialize_daily_task(task, archive_lookup, user_lookup)

    @staticmethod
    def delete_daily_task(db: Session, task_id: int) -> dict:
        task = db.query(DailyTask).filter(DailyTask.id == task_id).first()
        if not task:
            raise ValueError(f"Daily task not found: {task_id}")
        serialized = {
            "id": task.id,
            "is_active": task.is_active,
            "status": task.status,
        }
        db.delete(task)
        db.commit()
        return serialized

    @staticmethod
    def create_inventory_item(
        db: Session,
        item_name: str,
        category: str,
        unit: str = "kg",
        current_stock: float = 0,
        safety_stock: float = 0,
        location: str | None = None,
        supplier: str | None = None,
        last_restocked_at: datetime | None = None,
        notes: str | None = None,
    ) -> dict:
        OperationsService._ensure_inventory_name_unique(db, item_name)
        item = InventoryItem(
            item_name=item_name,
            category=category,
            unit=unit,
            current_stock=current_stock,
            safety_stock=safety_stock,
            location=location,
            supplier=supplier,
            last_restocked_at=last_restocked_at,
            notes=notes,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return OperationsService._serialize_inventory(item)

    @staticmethod
    def update_inventory_item(db: Session, item_id: int, **payload) -> dict:
        item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
        if not item:
            raise ValueError(f"Inventory item not found: {item_id}")

        next_name = payload.get("item_name", item.item_name)
        if next_name:
            OperationsService._ensure_inventory_name_unique(db, next_name, exclude_id=item_id)

        for field, value in payload.items():
            if value is not None or field in {"location", "supplier", "last_restocked_at", "notes"}:
                setattr(item, field, value)

        item.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(item)
        return OperationsService._serialize_inventory(item)

    @staticmethod
    def delete_inventory_item(db: Session, item_id: int) -> dict:
        item = db.query(InventoryItem).filter(InventoryItem.id == item_id).first()
        if not item:
            raise ValueError(f"Inventory item not found: {item_id}")
        serialized = {
            "id": item.id,
            "is_low_stock": item.current_stock <= item.safety_stock,
        }
        db.delete(item)
        db.commit()
        return serialized

    @staticmethod
    def create_equipment_asset(
        db: Session,
        asset_code: str,
        asset_name: str,
        asset_type: str,
        zone_name: str | None = None,
        linked_device_id: int | None = None,
        status: str = "online",
        installed_at: datetime | None = None,
        last_maintenance_at: datetime | None = None,
        next_maintenance_at: datetime | None = None,
        notes: str | None = None,
    ) -> dict:
        OperationsService._ensure_asset_code_unique(db, asset_code)
        OperationsService._validate_linked_device(db, linked_device_id)
        asset = EquipmentAsset(
            asset_code=asset_code,
            asset_name=asset_name,
            asset_type=asset_type,
            zone_name=zone_name,
            linked_device_id=linked_device_id,
            status=status,
            installed_at=installed_at,
            last_maintenance_at=last_maintenance_at,
            next_maintenance_at=next_maintenance_at,
            notes=notes,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(asset)
        db.commit()
        db.refresh(asset)
        return OperationsService._serialize_asset(asset)

    @staticmethod
    def update_equipment_asset(db: Session, asset_id: int, **payload) -> dict:
        asset = db.query(EquipmentAsset).filter(EquipmentAsset.id == asset_id).first()
        if not asset:
            raise ValueError(f"Asset not found: {asset_id}")

        next_code = payload.get("asset_code", asset.asset_code)
        if next_code:
            OperationsService._ensure_asset_code_unique(db, next_code, exclude_id=asset_id)
        linked_device_id = payload.get("linked_device_id", asset.linked_device_id)
        OperationsService._validate_linked_device(db, linked_device_id)

        for field, value in payload.items():
            if value is not None or field in {
                "zone_name",
                "linked_device_id",
                "installed_at",
                "last_maintenance_at",
                "next_maintenance_at",
                "notes",
            }:
                setattr(asset, field, value)

        asset.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(asset)
        return OperationsService._serialize_asset(asset)

    @staticmethod
    def delete_equipment_asset(db: Session, asset_id: int) -> dict:
        asset = db.query(EquipmentAsset).filter(EquipmentAsset.id == asset_id).first()
        if not asset:
            raise ValueError(f"Asset not found: {asset_id}")
        serialized = {"id": asset.id}
        db.delete(asset)
        db.commit()
        return serialized
