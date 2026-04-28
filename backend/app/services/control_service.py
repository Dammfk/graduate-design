from __future__ import annotations

import json
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models import AutomationRule, ControlCommandLog, Device, EnvironmentData
from app.utils import to_display_iso
from .ctwing_command_service import CTWingCommandService


class ControlService:
    """智能设备控制服务。"""

    MANUAL_OVERRIDE_HOLD_MINUTES = 30

    MANAGED_COMPONENTS = [
        {
            "component_key": "fan",
            "component_name": "排风风机",
            "supported_commands": ["ON", "OFF"],
            "description": "用于快速通风换气，降低温度与有害气体浓度。",
        },
        {
            "component_key": "cooling_pad",
            "component_name": "水帘降温",
            "supported_commands": ["ON", "OFF"],
            "description": "高温天气联动开启，协同风机进行降温。",
        },
        {
            "component_key": "fill_light",
            "component_name": "补光灯",
            "supported_commands": ["ON", "OFF"],
            "description": "用于夜间补光或阴雨天气辅助照明。",
        },
    ]

    @staticmethod
    def _has_inflight_command(
        db: Session,
        device_id: int,
        target_component: str,
        command_type: str,
    ) -> bool:
        latest = (
            db.query(ControlCommandLog)
            .filter(
                ControlCommandLog.device_id == device_id,
                ControlCommandLog.target_component == target_component,
            )
            .order_by(ControlCommandLog.executed_at.desc(), ControlCommandLog.id.desc())
            .first()
        )
        if latest is None:
            return False

        if latest.command_type != command_type:
            return False

        return latest.status in ["pending", "sent", "success"]

    @staticmethod
    def _map_ctwing_command_status(dispatch_result: dict) -> str:
        status_text = ""
        if isinstance(dispatch_result, dict):
            status_text = str(dispatch_result.get("result", {}).get("commandStatus") or "")

        if status_text == "指令已送达":
            return "sent"
        if status_text == "指令已保存":
            return "pending"
        if status_text in {"指令发送超时", "失败", "发送失败"}:
            return "failed"
        return "pending"

    @staticmethod
    def _extract_ctwing_meta(payload: str | None) -> dict:
        if not payload:
            return {
                "ctwing_command_id": None,
                "ctwing_command_status": None,
                "ctwing_result": None,
            }

        try:
            payload_data = json.loads(payload)
        except (TypeError, json.JSONDecodeError):
            return {
                "ctwing_command_id": None,
                "ctwing_command_status": None,
                "ctwing_result": None,
            }

        ctwing_result = payload_data.get("ctwing_result")
        if not isinstance(ctwing_result, dict):
            return {
                "ctwing_command_id": None,
                "ctwing_command_status": None,
                "ctwing_result": None,
            }

        result = ctwing_result.get("result") or {}
        return {
            "ctwing_command_id": result.get("commandId"),
            "ctwing_command_status": result.get("commandStatus"),
            "ctwing_result": ctwing_result,
        }

    @staticmethod
    def ensure_default_rules(db: Session) -> None:
        if db.query(AutomationRule).count() > 0:
            return

        rules = [
            AutomationRule(
                rule_name="高温启动风机",
                target_component="fan",
                trigger_metric="temperature",
                comparison_operator=">",
                threshold_value=30,
                action_command="ON",
                priority=10,
                description="棚内温度超过 30°C 时自动开启排风风机。",
                is_enabled=True,
            ),
            AutomationRule(
                rule_name="高温联动水帘",
                target_component="cooling_pad",
                trigger_metric="temperature",
                comparison_operator=">",
                threshold_value=32,
                action_command="ON",
                priority=9,
                description="温度持续偏高时联动水帘进行降温。",
                is_enabled=True,
            ),
            AutomationRule(
                rule_name="氨气超标启动风机",
                target_component="fan",
                trigger_metric="ammonia_concentration",
                comparison_operator=">",
                threshold_value=20,
                action_command="ON",
                priority=10,
                description="氨气浓度超过 20 ppm 时优先开启通风。",
                is_enabled=True,
            ),
            AutomationRule(
                rule_name="温度恢复关闭风机",
                target_component="fan",
                trigger_metric="temperature",
                comparison_operator="<=",
                threshold_value=25,
                action_command="OFF",
                priority=5,
                description="温度恢复正常后关闭风机以降低能耗。",
                is_enabled=True,
            ),
            AutomationRule(
                rule_name="夜间补光开启",
                target_component="fill_light",
                trigger_metric="humidity",
                comparison_operator="<=",
                threshold_value=70,
                action_command="ON",
                priority=3,
                description="示意规则：后续可替换为真实的时间段补光策略。",
                is_enabled=False,
            ),
        ]
        db.add_all(rules)
        db.commit()

    @staticmethod
    def _compare(actual: float | None, operator: str, threshold: float) -> bool:
        if actual is None:
            return False
        if operator == ">":
            return actual > threshold
        if operator == ">=":
            return actual >= threshold
        if operator == "<":
            return actual < threshold
        if operator == "<=":
            return actual <= threshold
        if operator == "==":
            return actual == threshold
        return False

    @staticmethod
    def _build_environment_snapshot(environment_data: EnvironmentData) -> dict:
        return {
            "temperature": environment_data.temperature,
            "humidity": environment_data.humidity,
            "co2_concentration": environment_data.co2_concentration,
            "ammonia_concentration": environment_data.ammonia_concentration,
            "recorded_at": to_display_iso(environment_data.recorded_at),
        }

    @staticmethod
    def _has_active_manual_override(
        db: Session,
        device_id: int,
        target_component: str,
    ) -> bool:
        latest_manual_log = (
            db.query(ControlCommandLog)
            .filter(
                ControlCommandLog.device_id == device_id,
                ControlCommandLog.target_component == target_component,
                ControlCommandLog.execution_mode == "manual",
                ControlCommandLog.status.in_(["pending", "sent", "success"]),
            )
            .order_by(ControlCommandLog.executed_at.desc(), ControlCommandLog.id.desc())
            .first()
        )
        if latest_manual_log is None or latest_manual_log.executed_at is None:
            return False

        hold_deadline = latest_manual_log.executed_at + timedelta(
            minutes=ControlService.MANUAL_OVERRIDE_HOLD_MINUTES
        )
        return hold_deadline > datetime.utcnow()

    @staticmethod
    def _infer_component_status(device: Device, latest: EnvironmentData | None) -> dict[str, dict]:
        return {
            "fan": {
                "component_name": "排风风机",
                "status": "OFF",
                "mode": "auto",
            },
            "cooling_pad": {
                "component_name": "水帘降温",
                "status": "OFF",
                "mode": "auto",
            },
            "fill_light": {
                "component_name": "补光灯",
                "status": "OFF",
                "mode": "manual",
            },
        }

    @staticmethod
    def _get_component_status(db: Session, device: Device, latest: EnvironmentData | None) -> list[dict]:
        inferred = ControlService._infer_component_status(device, latest)

        latest_logs = (
            db.query(ControlCommandLog)
            .filter(ControlCommandLog.device_id == device.id)
            .order_by(ControlCommandLog.executed_at.desc(), ControlCommandLog.id.desc())
            .all()
        )
        latest_success_log_by_component: dict[str, ControlCommandLog] = {}
        latest_log_by_component: dict[str, ControlCommandLog] = {}
        for log in latest_logs:
            if log.target_component not in latest_log_by_component:
                latest_log_by_component[log.target_component] = log
            if log.status == "success" and log.target_component not in latest_success_log_by_component:
                latest_success_log_by_component[log.target_component] = log

        components = []
        for component_key in ["fan", "cooling_pad", "fill_light"]:
            component_log = latest_success_log_by_component.get(component_key)
            latest_command = latest_log_by_component.get(component_key)
            if component_log:
                components.append(
                    {
                        "component_key": component_key,
                        "component_name": inferred[component_key]["component_name"],
                        "status": component_log.command_type.upper(),
                        "mode": component_log.execution_mode,
                        "can_control": True,
                        "last_command_status": latest_command.status if latest_command else component_log.status,
                    }
                )
                continue

            components.append(
                {
                    "component_key": component_key,
                    "component_name": inferred[component_key]["component_name"],
                    "status": inferred[component_key]["status"],
                    "mode": inferred[component_key]["mode"],
                    "can_control": True,
                    "last_command_status": latest_command.status if latest_command else "idle",
                }
            )

        return components

    @staticmethod
    def get_control_dashboard(db: Session) -> dict:
        ControlService.ensure_default_rules(db)
        devices = db.query(Device).order_by(Device.location, Device.device_name).all()
        rules = db.query(AutomationRule).order_by(AutomationRule.priority.desc(), AutomationRule.id).all()
        recent_logs = db.query(ControlCommandLog).order_by(ControlCommandLog.executed_at.desc()).limit(20).all()

        device_panels = []
        for device in devices:
            latest = (
                db.query(EnvironmentData)
                .filter(EnvironmentData.device_id == device.id)
                .order_by(EnvironmentData.recorded_at.desc())
                .first()
            )
            device_panels.append(
                {
                    "device_id": device.device_id,
                    "device_name": device.device_name,
                    "location": device.location,
                    "device_type": device.device_type,
                    "zone_name": device.location.split()[0] if device.location else "未分区",
                    "latest_environment": ControlService._build_environment_snapshot(latest) if latest else None,
                    "components": ControlService._get_component_status(db, device, latest),
                }
            )

        return {
            "components_catalog": ControlService.MANAGED_COMPONENTS,
            "devices": device_panels,
            "automation_rules": [
                {
                    "id": rule.id,
                    "rule_name": rule.rule_name,
                    "target_component": rule.target_component,
                    "trigger_metric": rule.trigger_metric,
                    "comparison_operator": rule.comparison_operator,
                    "threshold_value": rule.threshold_value,
                    "action_command": rule.action_command,
                    "priority": rule.priority,
                    "description": rule.description,
                    "is_enabled": rule.is_enabled,
                }
                for rule in rules
            ],
            "recent_commands": [
                {
                    "id": log.id,
                    "device_id": log.device.device_id if log.device else None,
                    "device_name": log.device.device_name if log.device else None,
                    "target_component": log.target_component,
                    "command_type": log.command_type,
                    "execution_mode": log.execution_mode,
                    "status": log.status,
                    "reason": log.reason,
                    "executed_at": to_display_iso(log.executed_at),
                    **ControlService._extract_ctwing_meta(log.payload),
                }
                for log in recent_logs
            ],
        }

    @staticmethod
    def execute_manual_command(
        db: Session,
        device_id: str,
        target_component: str,
        command_type: str,
        execution_mode: str = "manual",
        reason: str | None = None,
        operator_user_id: int | None = None,
    ) -> dict:
        device = db.query(Device).filter(Device.device_id == device_id).first()
        if not device:
            raise ValueError(f"Device not found: {device_id}")

        log = ControlCommandLog(
            device_id=device.id,
            command_type=command_type.upper(),
            target_component=target_component,
            execution_mode=execution_mode,
            status="pending",
            reason=reason or "Manual control from web dashboard",
            operator_user_id=operator_user_id,
            payload=json.dumps(
                {
                    "device_id": device_id,
                    "target_component": target_component,
                    "command_type": command_type.upper(),
                },
                ensure_ascii=False,
            ),
            executed_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )
        db.add(log)
        db.commit()
        db.refresh(log)

        dispatch_result = CTWingCommandService.dispatch_command(
            command_id=log.id,
            device_id=device.device_id,
            target_component=log.target_component,
            command_type=log.command_type,
            reason=log.reason,
        )
        log.status = ControlService._map_ctwing_command_status(dispatch_result)
        log.payload = json.dumps(
            {
                "device_id": device.device_id,
                "target_component": target_component,
                "command_type": command_type.upper(),
                "ctwing_result": dispatch_result,
            },
            ensure_ascii=False,
        )
        db.commit()
        db.refresh(log)

        return {
            "id": log.id,
            "device_id": device.device_id,
            "device_name": device.device_name,
            "target_component": log.target_component,
            "command_type": log.command_type,
            "execution_mode": log.execution_mode,
            "status": log.status,
            "reason": log.reason,
            "executed_at": to_display_iso(log.executed_at),
            "ctwing_result": dispatch_result,
            "ctwing_command_id": (
                dispatch_result.get("result", {}).get("commandId")
                if isinstance(dispatch_result, dict)
                else None
            ),
            "ctwing_command_status": (
                dispatch_result.get("result", {}).get("commandStatus")
                if isinstance(dispatch_result, dict)
                else None
            ),
        }

    @staticmethod
    def update_rule_status(db: Session, rule_id: int, is_enabled: bool) -> dict:
        rule = db.query(AutomationRule).filter(AutomationRule.id == rule_id).first()
        if not rule:
            raise ValueError(f"Rule not found: {rule_id}")

        rule.is_enabled = is_enabled
        rule.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(rule)
        return {
            "id": rule.id,
            "rule_name": rule.rule_name,
            "is_enabled": rule.is_enabled,
        }

    @staticmethod
    def get_pending_commands(db: Session, device_id: str, limit: int = 10) -> list[dict]:
        device = db.query(Device).filter(Device.device_id == device_id).first()
        if not device:
            raise ValueError(f"Device not found: {device_id}")

        logs = (
            db.query(ControlCommandLog)
            .filter(
                ControlCommandLog.device_id == device.id,
                ControlCommandLog.status == "pending",
            )
            .order_by(ControlCommandLog.executed_at.asc(), ControlCommandLog.id.asc())
            .limit(limit)
            .all()
        )

        return [
            {
                "id": log.id,
                "device_id": device.device_id,
                "target_component": log.target_component,
                "command_type": log.command_type,
                "execution_mode": log.execution_mode,
                "reason": log.reason,
                "payload": json.loads(log.payload) if log.payload else None,
                "executed_at": to_display_iso(log.executed_at),
            }
            for log in logs
        ]

    @staticmethod
    def update_command_status(db: Session, command_id: int, status: str) -> dict:
        log = db.query(ControlCommandLog).filter(ControlCommandLog.id == command_id).first()
        if not log:
            raise ValueError(f"Command not found: {command_id}")

        log.status = status
        db.commit()
        db.refresh(log)

        return {
            "id": log.id,
            "status": log.status,
            "device_id": log.device.device_id if log.device else None,
            "target_component": log.target_component,
            "command_type": log.command_type,
        }

    @staticmethod
    async def generate_control_commands(db: Session, environment_data: EnvironmentData) -> list[dict]:
        ControlService.ensure_default_rules(db)
        device = db.query(Device).filter(Device.id == environment_data.device_id).first()
        if not device:
            return []

        rules = (
            db.query(AutomationRule)
            .filter(AutomationRule.is_enabled == True)
            .order_by(AutomationRule.priority.desc(), AutomationRule.id)
            .all()
        )

        commands = []
        snapshot = ControlService._build_environment_snapshot(environment_data)

        for rule in rules:
            actual = getattr(environment_data, rule.trigger_metric, None)
            if not ControlService._compare(actual, rule.comparison_operator, rule.threshold_value):
                continue

            command_type = rule.action_command.upper()
            if ControlService._has_active_manual_override(
                db=db,
                device_id=device.id,
                target_component=rule.target_component,
            ):
                continue

            if ControlService._has_inflight_command(
                db=db,
                device_id=device.id,
                target_component=rule.target_component,
                command_type=command_type,
            ):
                continue

            command = {
                "device_id": device.device_id,
                "command": f"{rule.target_component.upper()}_{command_type}",
                "target_component": rule.target_component,
                "reason": rule.description or rule.rule_name,
                "priority": rule.priority,
                "trigger_metric": rule.trigger_metric,
                "actual_value": actual,
            }
            commands.append(command)

            log = ControlCommandLog(
                device_id=device.id,
                command_type=command_type,
                target_component=rule.target_component,
                execution_mode="auto",
                status="pending",
                reason=rule.rule_name,
                payload=json.dumps(snapshot, ensure_ascii=False),
                executed_at=datetime.utcnow(),
                created_at=datetime.utcnow(),
            )
            db.add(log)
            db.flush()

            dispatch_result = CTWingCommandService.dispatch_command(
                command_id=log.id,
                device_id=device.device_id,
                target_component=log.target_component,
                command_type=log.command_type,
                reason=log.reason,
            )
            log.status = ControlService._map_ctwing_command_status(dispatch_result)
            log.payload = json.dumps(
                {
                    "environment_snapshot": snapshot,
                    "ctwing_result": dispatch_result,
                },
                ensure_ascii=False,
            )

        if commands:
            db.commit()

        return commands
