"""
更新服务导入，将自动化控制逻辑集成到遥测处理中
"""

# 修改 telemetry_service.py 最后添加以下内容，集成自动化控制

# 在 main.py 中的 telemetry 路由中添加以下代码：

from app.services.automation_service import process_environment_data

# 在 POST /api/v1/telemetry/ 路由中，保存数据后添加：

async def receive_telemetry(telemetry: TelemetryData, db: Session = Depends(get_db)):
    """
    接收物联网平台转发的遥测数据
    """
    try:
        # ... 现有代码 ...
        
        # 执行智能控制逻辑
        control_result = process_environment_data({
            "temperature": telemetry.temperature,
            "humidity": telemetry.humidity,
            "co2_concentration": telemetry.co2_concentration,
            "ammonia_concentration": telemetry.ammonia_concentration
        })
        
        # 处理生成的控制动作
        for action_item in control_result.get("actions", []):
            action = action_item["action"]
            # 这里可以将控制指令发送给硬件
            print(f"[AUTOMATION] {action} triggered by {action_item['rule']}")
        
        return {
            "status": "success",
            "message": "Telemetry data received and processed",
            "data": {
                "data_id": environment_data.id,
                "device_id": telemetry.device_id,
                "alarms_created": len(alarms),
                "commands_generated": len(control_result.get("actions", [])),
                "control_actions": [a["action"] for a in control_result.get("actions", [])],
                "energy_optimization": control_result.get("energy_optimization"),
                "timestamp": environment_data.recorded_at
            }
        }
    except Exception as e:
        # ... 错误处理 ...
        pass
