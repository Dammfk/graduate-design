"""
自动化控制逻辑模块
实现多条件的智能联动控制和节能优化
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Optional
from enum import Enum
from app.utils import get_display_now, to_display_iso


class ControlAction(str, Enum):
    """控制动作枚举"""
    FAN_ON = "FAN_ON"
    FAN_OFF = "FAN_OFF"
    PUMP_ON = "PUMP_ON"
    PUMP_OFF = "PUMP_OFF"
    ALERT = "ALERT"


@dataclass
class ControlRule:
    """控制规则"""
    name: str
    conditions: Dict[str, any]  # 条件
    actions: List[ControlAction]  # 执行的动作
    priority: int = 5  # 优先级（1-10，10最高）
    enabled: bool = True


class SmartController:
    """智能控制器"""
    
    def __init__(self):
        """初始化智能控制器"""
        self.rules: List[ControlRule] = []
        self.action_history: List[Dict] = []
        self.energy_stats = {
            "fan_runtime": 0,  # 排风扇运行时间（秒）
            "pump_runtime": 0,
            "total_energy_consumption": 0  # 总能耗（Wh）
        }
        self._init_default_rules()
    
    def _init_default_rules(self):
        """初始化默认规则"""
        
        # 规则1：高温情况下打开排风扇
        rule1 = ControlRule(
            name="Temperature High Control",
            conditions={
                "temperature": {"operator": ">", "value": 30},
            },
            actions=[ControlAction.FAN_ON],
            priority=8
        )
        
        # 规则2：氨气浓度过高时打开排风扇（最高优先级）
        rule2 = ControlRule(
            name="Ammonia High Alert",
            conditions={
                "ammonia_concentration": {"operator": ">", "value": 25},
            },
            actions=[ControlAction.FAN_ON, ControlAction.ALERT],
            priority=10
        )
        
        # 规则3：温度正常时关闭排风扇（节能）
        rule3 = ControlRule(
            name="Temperature Normal Control",
            conditions={
                "temperature": {"operator": "<=", "value": 25},
                "ammonia_concentration": {"operator": "<=", "value": 20}
            },
            actions=[ControlAction.FAN_OFF],
            priority=5
        )
        
        # 规则4：CO2浓度过高时打开排风扇
        rule4 = ControlRule(
            name="CO2 High Control",
            conditions={
                "co2_concentration": {"operator": ">", "value": 2000},
            },
            actions=[ControlAction.FAN_ON],
            priority=7
        )
        
        # 规则5：湿度过高时打开排风扇
        rule5 = ControlRule(
            name="Humidity High Control",
            conditions={
                "humidity": {"operator": ">", "value": 90},
            },
            actions=[ControlAction.FAN_ON],
            priority=6
        )
        
        self.rules = [rule1, rule2, rule3, rule4, rule5]
    
    def evaluate_conditions(self, data: Dict, conditions: Dict) -> bool:
        """
        评估条件是否满足
        
        Args:
            data: 环境数据
            conditions: 条件规则
        
        Returns:
            所有条件是否都满足
        """
        for key, condition in conditions.items():
            if key not in data:
                return False
            
            value = data[key]
            operator = condition.get("operator")
            threshold = condition.get("value")
            
            if operator == ">":
                if not (value > threshold):
                    return False
            elif operator == "<":
                if not (value < threshold):
                    return False
            elif operator == ">=":
                if not (value >= threshold):
                    return False
            elif operator == "<=":
                if not (value <= threshold):
                    return False
            elif operator == "==":
                if not (value == threshold):
                    return False
            else:
                return False
        
        return True
    
    def execute_rules(self, environment_data: Dict) -> List[Dict]:
        """
        执行所有启用的规则
        
        Args:
            environment_data: 环境数据
        
        Returns:
            需要执行的控制动作列表
        """
        matched_actions = []
        
        # 排序规则（按优先级降序）
        sorted_rules = sorted(
            [r for r in self.rules if r.enabled],
            key=lambda r: r.priority,
            reverse=True
        )
        
        # 评估每个规则
        for rule in sorted_rules:
            if self.evaluate_conditions(environment_data, rule.conditions):
                for action in rule.actions:
                    matched_actions.append({
                        "action": action,
                        "rule": rule.name,
                        "priority": rule.priority,
                        "timestamp": to_display_iso(datetime.utcnow())
                    })
                
                # 记录日志
                print(f"[CONTROL] Rule '{rule.name}' matched with priority {rule.priority}")
        
        # 记录动作历史
        self.action_history.extend(matched_actions)
        
        return matched_actions
    
    def optimize_energy(self, environment_data: Dict) -> Dict:
        """
        能耗优化计算
        
        基于环境数据对设备运行时间进行优化，计算节能效果
        
        Args:
            environment_data: 环境数据
        
        Returns:
            能耗优化建议
        """
        optimization = {
            "current_temp": environment_data.get("temperature", 0),
            "target_temp": 27,  # 目标温度
            "energy_saving": 0,
            "recommendations": []
        }
        
        temp_diff = environment_data.get("temperature", 0) - optimization["target_temp"]
        
        # 节能计算
        if -2 <= temp_diff <= 2:
            # 温度在目标范围内，可以考虑关闭排风扇
            optimization["energy_saving"] = 15  # 预计省电 15%
            optimization["recommendations"].append({
                "action": "Consider reducing fan speed when temperature is optimal",
                "potential_savings": "15% energy reduction"
            })
        
        # 时间段优化
        current_hour = get_display_now().hour
        if 0 <= current_hour < 6 or 22 <= current_hour <= 23:
            # 夜间时段，通常更冷
            if environment_data.get("temperature", 0) < 20:
                optimization["energy_saving"] += 20
                optimization["recommendations"].append({
                    "action": "Night period detected - lower ambient temperature",
                    "potential_savings": "Additional 20% energy reduction"
                })
        
        return optimization
    
    def add_rule(self, rule: ControlRule):
        """添加自定义规则"""
        self.rules.append(rule)
        print(f"[CONTROL] Rule '{rule.name}' added with priority {rule.priority}")
    
    def disable_rule(self, rule_name: str):
        """禁用规则"""
        for rule in self.rules:
            if rule.name == rule_name:
                rule.enabled = False
                print(f"[CONTROL] Rule '{rule_name}' disabled")
                break
    
    def enable_rule(self, rule_name: str):
        """启用规则"""
        for rule in self.rules:
            if rule.name == rule_name:
                rule.enabled = True
                print(f"[CONTROL] Rule '{rule_name}' enabled")
                break
    
    def get_action_history(self, limit: int = 100) -> List[Dict]:
        """获取动作历史"""
        return self.action_history[-limit:]
    
    def export_energy_report(self) -> Dict:
        """导出能耗报告"""
        return {
            "report_time": to_display_iso(datetime.utcnow()),
            "fan_runtime_hours": self.energy_stats["fan_runtime"] / 3600,
            "total_energy_consumption_kwh": self.energy_stats["total_energy_consumption"] / 1000000,
            "co2_equivalent": self._calculate_co2_equivalent()
        }
    
    def _calculate_co2_equivalent(self) -> float:
        """
        计算等效 CO2 排放量
        
        假设：100W 排风扇，中国平均电网碳强度 0.5kg CO2/kWh
        """
        energy_kwh = self.energy_stats["total_energy_consumption"] / 1000000
        co2_per_kwh = 0.5  # kg/kWh
        return energy_kwh * co2_per_kwh


# 全局控制器实例
smart_controller = SmartController()


def process_environment_data(environment_data: Dict) -> Dict:
    """
    处理环境数据并执行智能控制
    
    Args:
        environment_data: 环境数据字典
    
    Returns:
        控制结果
    """
    # 执行规则
    actions = smart_controller.execute_rules(environment_data)
    
    # 能耗优化
    energy_opt = smart_controller.optimize_energy(environment_data)
    
    return {
        "actions": actions,
        "energy_optimization": energy_opt,
        "timestamp": to_display_iso(datetime.utcnow())
    }


def get_energy_efficiency_report() -> Dict:
    """获取能耗效率报告"""
    return smart_controller.export_energy_report()
