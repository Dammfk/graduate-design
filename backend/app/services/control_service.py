from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.models import AutomationRule, ControlCommandLog, Device, EnvironmentData


class ControlService:
    """智能设备控制服务。"""

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
                description="示意规则：夜间巡检时可自动补光，后续可接真实时段策略。",
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
            "recorded_at": environment_data.recorded_at.isoformat() if environment_data.recorded_at else None,
        }

    @staticmethod
    def _get_component_status(device_type: str, latest: EnvironmentData | None) -> list[dict]:
        latest = latest or EnvironmentData()
        temp = latest.temperature
        ammonia = latest.ammonia_concentration
        co2 = latest.co2_concentration

        fan_status = "ON" if ((temp is not None and temp > 30) or (ammonia is not None and ammonia > 20) or (co2 is not None and co2 > 1800)) else "OFF"
        cooling_status = "ON" if temp is not None and temp > 32 else "OFF"
        light_status = "ON" if device_type == "controller" else "OFF"

        return [
          {
              "component_key": "fan",
              "component_name": "排风风机",
              "status": fan_status,
              "mode": "auto",
              "can_control": True,
          },
          {
              "component_key": "cooling_pad",
              "component_name": "水帘降温",
              "status": cooling_status,
              "mode": "auto",
              "can_control": True,
          },
          {
              "component_key": "fill_light",
              "component_name": "补光灯",
              "status": light_status,
              "mode": "manual",
              "can_control": True,
          },
        ]

    @staticmethod
    def get_control_dashboard(db: Session) -> dict:
        ControlService.ensure_default_rules(db)
        devices = db.query(Device).order_by(Device.location, Device.device_name).all()
        rules = db.query(AutomationRule).order_by(AutomationRule.priority.desc(), AutomationRule.id).all()
        recent_logs = (
            db.query(ControlCommandLog)
            .order_by(ControlCommandLog.executed_at.desc())
            .limit(20)
            .all()
        )

        device_panels = []
        for device in devices:
            latest = (
                db.query(EnvironmentData)
                .filter(EnvironmentData.device_id == device.id)
                .order_by(EnvironmentData.recorded_at.desc())
                .first()
            )
            device_panels.append({
                "device_id": device.device_id,
                "device_name": device.device_name,
                "location": device.location,
                "device_type": device.device_type,
                "zone_name": device.location.split()[0] if device.location else "未分区",
                "latest_environment": ControlService._build_environment_snapshot(latest) if latest else None,
                "components": ControlService._get_component_status(device.device_type, latest),
            })

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
                    "executed_at": log.executed_at.isoformat() if log.executed_at else None,
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
            status="success",
            reason=reason or "Manual control from web dashboard",
            operator_user_id=operator_user_id,
            payload=json.dumps({
                "device_id": device_id,
                "target_component": target_component,
                "command_type": command_type.upper(),
            }, ensure_ascii=False),
            executed_at=datetime.utcnow(),
            created_at=datetime.utcnow(),
        )
        db.add(log)
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
            "executed_at": log.executed_at.isoformat(),
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

            command = {
                "device_id": device.device_id,
                "command": f"{rule.target_component.upper()}_{rule.action_command.upper()}",
                "target_component": rule.target_component,
                "reason": rule.description or rule.rule_name,
                "priority": rule.priority,
                "trigger_metric": rule.trigger_metric,
                "actual_value": actual,
            }
            commands.append(command)

            log = ControlCommandLog(
                device_id=device.id,
                command_type=rule.action_command.upper(),
                target_component=rule.target_component,
                execution_mode="auto",
                status="success",
                reason=rule.rule_name,
                payload=json.dumps(snapshot, ensure_ascii=False),
                executed_at=datetime.utcnow(),
                created_at=datetime.utcnow(),
            )
            db.add(log)

        if commands:
            db.commit()

        return commands
