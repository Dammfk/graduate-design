from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.models import OperationLog, RoleEnum, User
from app.utils import to_display_iso


class SystemService:
    ROLE_PERMISSIONS = {
        "admin": ["查看全部数据", "管理用户权限", "配置自动控制", "查看操作日志"],
        "manager": ["查看环境与档案", "分配生产任务", "查看风险预警", "更新设备状态"],
        "operator": ["执行生产任务", "录入档案信息", "确认告警处理"],
        "viewer": ["只读查看看板", "查看历史趋势"],
    }

    @staticmethod
    def _serialize_user(user: User) -> dict:
        role_value = user.role.value if hasattr(user.role, "value") else str(user.role)
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": role_value,
            "is_active": user.is_active,
            "created_at": to_display_iso(user.created_at),
            "updated_at": to_display_iso(user.updated_at),
            "permissions": SystemService.ROLE_PERMISSIONS.get(role_value, []),
        }

    @staticmethod
    def _serialize_log(log: OperationLog, user_lookup: dict[int, User]) -> dict:
        user = user_lookup.get(log.user_id)
        return {
            "id": log.id,
            "user_id": log.user_id,
            "username": user.username if user else "system",
            "module_name": log.module_name,
            "action": log.action,
            "target": log.target,
            "detail": log.detail,
            "created_at": to_display_iso(log.created_at),
        }

    @staticmethod
    def get_dashboard(db: Session) -> dict:
        users = db.query(User).order_by(User.id.asc()).all()
        logs = db.query(OperationLog).order_by(OperationLog.created_at.desc()).limit(12).all()
        user_lookup = {user.id: user for user in users}

        role_distribution = {}
        for user in users:
          role_value = user.role.value if hasattr(user.role, "value") else str(user.role)
          role_distribution[role_value] = role_distribution.get(role_value, 0) + 1

        return {
            "summary": {
                "user_count": len(users),
                "active_users": len([user for user in users if user.is_active]),
                "role_count": len(role_distribution),
                "log_count": len(logs),
            },
            "role_permissions": [
                {"role": role, "permissions": permissions}
                for role, permissions in SystemService.ROLE_PERMISSIONS.items()
            ],
            "users": [SystemService._serialize_user(user) for user in users],
            "role_distribution": role_distribution,
            "operation_logs": [SystemService._serialize_log(log, user_lookup) for log in logs],
        }

    @staticmethod
    def get_user_operation_logs(db: Session, user_id: int, limit: int = 20) -> dict:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User not found: {user_id}")

        logs = (
            db.query(OperationLog)
            .filter(OperationLog.user_id == user_id)
            .order_by(OperationLog.created_at.desc())
            .limit(limit)
            .all()
        )
        user_lookup = {user.id: user}
        return {
            "user": SystemService._serialize_user(user),
            "logs": [SystemService._serialize_log(log, user_lookup) for log in logs],
        }

    @staticmethod
    def update_user(
        db: Session,
        user_id: int,
        role: str | None = None,
        is_active: bool | None = None,
    ) -> dict:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User not found: {user_id}")

        changes: list[str] = []

        if role is not None:
            valid_roles = {item.value for item in RoleEnum}
            if role not in valid_roles:
                raise ValueError(f"Invalid role: {role}")
            previous_role = user.role.value if hasattr(user.role, "value") else str(user.role)
            user.role = RoleEnum(role)
            if previous_role != role:
                changes.append(f"role: {previous_role} -> {role}")

        if is_active is not None:
            previous_active = user.is_active
            user.is_active = is_active
            if previous_active != is_active:
                changes.append(f"is_active: {previous_active} -> {is_active}")

        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)

        if changes:
            SystemService.create_operation_log(
                db=db,
                user_id=user.id,
                module_name="system",
                action="update_user",
                target=user.username,
                detail="; ".join(changes),
            )
        return SystemService._serialize_user(user)

    @staticmethod
    def create_operation_log(
        db: Session,
        user_id: int | None,
        module_name: str,
        action: str,
        target: str | None = None,
        detail: str | None = None,
    ) -> dict:
        log = OperationLog(
            user_id=user_id,
            module_name=module_name,
            action=action,
            target=target,
            detail=detail,
            created_at=datetime.utcnow(),
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        user_lookup = {}
        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user_lookup[user_id] = user
        return SystemService._serialize_log(log, user_lookup)
