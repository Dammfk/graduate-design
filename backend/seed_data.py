from __future__ import annotations

from datetime import datetime, timedelta

from app.core.database import Base, SessionLocal, engine
from app.models import (
    AlarmInfo,
    AnimalProfile,
    Device,
    EnvironmentData,
    EquipmentAsset,
    InventoryItem,
    LivestockArchive,
    ProductionTask,
    RoleEnum,
    User,
    OperationLog,
)


def get_or_create_user(session, username: str, **kwargs) -> User:
    user = session.query(User).filter(User.username == username).first()
    if user:
        return user

    user = User(username=username, **kwargs)
    session.add(user)
    session.flush()
    return user


def get_or_create_device(session, device_code: str, **kwargs) -> Device:
    device = session.query(Device).filter(Device.device_id == device_code).first()
    if device:
        return device

    device = Device(device_id=device_code, **kwargs)
    session.add(device)
    session.flush()
    return device


def seed_users(session) -> list[User]:
    now = datetime.utcnow()
    return [
        get_or_create_user(
            session,
            "admin",
            email="admin@example.com",
            password_hash="demo_admin_hash",
            role=RoleEnum.ADMIN,
            is_active=True,
            created_at=now - timedelta(days=30),
            updated_at=now - timedelta(days=2),
        ),
        get_or_create_user(
            session,
            "manager_zhang",
            email="zhang@example.com",
            password_hash="demo_manager_hash",
            role=RoleEnum.MANAGER,
            is_active=True,
            created_at=now - timedelta(days=24),
            updated_at=now - timedelta(days=1),
        ),
        get_or_create_user(
            session,
            "operator_li",
            email="li@example.com",
            password_hash="demo_operator_hash",
            role=RoleEnum.OPERATOR,
            is_active=True,
            created_at=now - timedelta(days=20),
            updated_at=now - timedelta(hours=12),
        ),
    ]


def seed_devices(session, users: list[User]) -> list[Device]:
    now = datetime.utcnow()
    owner_map = {user.username: user for user in users}
    devices = [
        get_or_create_device(
            session,
            "DEVICE_001",
            device_name="1号舍温湿度传感器",
            device_type="temperature_humidity_sensor",
            location="A区 1号棚",
            owner_id=owner_map["manager_zhang"].id,
            is_active=True,
            created_at=now - timedelta(days=18),
            updated_at=now - timedelta(hours=2),
        ),
        get_or_create_device(
            session,
            "DEVICE_002",
            device_name="2号舍气体监测器",
            device_type="gas_sensor",
            location="A区 2号棚",
            owner_id=owner_map["operator_li"].id,
            is_active=True,
            created_at=now - timedelta(days=16),
            updated_at=now - timedelta(hours=3),
        ),
        get_or_create_device(
            session,
            "DEVICE_003",
            device_name="通风联动控制器",
            device_type="controller",
            location="B区 主控室",
            owner_id=owner_map["admin"].id,
            is_active=True,
            created_at=now - timedelta(days=14),
            updated_at=now - timedelta(hours=4),
        ),
    ]
    return devices


def seed_environment_data(session, devices: list[Device]) -> int:
    existing_count = session.query(EnvironmentData).count()
    if existing_count > 0:
        return 0

    now = datetime.utcnow()
    rows_added = 0

    device_profiles = {
        "DEVICE_001": (25.5, 63.0, 820.0, 8.0),
        "DEVICE_002": (27.2, 68.0, 1180.0, 16.0),
        "DEVICE_003": (24.8, 59.0, 760.0, 5.0),
    }

    for device in devices:
        base_temp, base_humidity, base_co2, base_ammonia = device_profiles[device.device_id]
        latest_time = None

        for hours_ago in range(23, -1, -1):
            recorded_at = now - timedelta(hours=hours_ago)
            offset = 23 - hours_ago
            temperature = round(base_temp + ((offset % 6) - 2) * 0.4, 1)
            humidity = round(base_humidity + ((offset % 5) - 2) * 1.3, 1)
            co2 = round(base_co2 + ((offset % 7) - 3) * 45, 1)
            ammonia = round(base_ammonia + ((offset % 4) - 1) * 1.8, 1)

            session.add(
                EnvironmentData(
                    device_id=device.id,
                    temperature=temperature,
                    humidity=humidity,
                    co2_concentration=co2,
                    ammonia_concentration=ammonia,
                    recorded_at=recorded_at,
                    created_at=recorded_at,
                )
            )
            latest_time = recorded_at
            rows_added += 1

        device.latest_data_timestamp = latest_time

    return rows_added


def seed_livestock_archives(session) -> int:
    existing_batches = {
        row[0] for row in session.query(LivestockArchive.batch_number).all()
    }
    now = datetime.utcnow()
    records = [
        LivestockArchive(
            batch_number="BATCH-CHICK-001",
            species="肉鸡",
            quantity=1200,
            check_in_date=now - timedelta(days=18),
            expected_checkout_date=now + timedelta(days=22),
            immunization_records='{"vaccines":["新城疫","传支"],"last_date":"2026-03-20"}',
            notes="生长状态稳定，采食正常",
            average_weight=1.85,
            feed_consumption=2.6,
            health_status="stable",
            is_active=True,
            created_at=now - timedelta(days=18),
            updated_at=now - timedelta(days=1),
        ),
        LivestockArchive(
            batch_number="BATCH-PIG-002",
            species="仔猪",
            quantity=320,
            check_in_date=now - timedelta(days=35),
            expected_checkout_date=now + timedelta(days=55),
            immunization_records='{"vaccines":["猪瘟","口蹄疫"],"last_date":"2026-03-12"}',
            notes="需持续关注夜间温差",
            average_weight=18.4,
            feed_consumption=31.2,
            health_status="observe",
            is_active=True,
            created_at=now - timedelta(days=35),
            updated_at=now - timedelta(days=2),
        ),
        LivestockArchive(
            batch_number="BATCH-CALF-003",
            species="犊牛",
            quantity=48,
            check_in_date=now - timedelta(days=42),
            expected_checkout_date=now + timedelta(days=90),
            immunization_records='{"vaccines":["牛肺疫"],"last_date":"2026-03-05"}',
            notes="个别栏位已加装保温设施",
            average_weight=72.8,
            feed_consumption=118.0,
            health_status="good",
            is_active=True,
            created_at=now - timedelta(days=42),
            updated_at=now - timedelta(days=3),
        ),
    ]

    rows_added = 0
    for record in records:
        if record.batch_number in existing_batches:
            continue
        session.add(record)
        rows_added += 1
    return rows_added


def seed_animal_profiles(session) -> int:
    existing_codes = {row[0] for row in session.query(AnimalProfile.animal_code).all()}
    archives = {item.batch_number: item for item in session.query(LivestockArchive).all()}
    if not archives:
        return 0

    now = datetime.utcnow()
    animals = [
        AnimalProfile(
            archive_id=archives["BATCH-CALF-003"].id,
            animal_code="CATTLE-001",
            species="犊牛",
            breed="西门塔尔",
            gender="母",
            birth_date=now - timedelta(days=210),
            check_in_date=now - timedelta(days=42),
            weight=71.5,
            health_status="good",
            ear_tag="EAR-C-001",
            source="北牧育种场",
            immunization_note="2026-03-05 已完成牛肺疫免疫",
            notes="采食稳定，精神状态良好",
            is_active=True,
        ),
        AnimalProfile(
            archive_id=archives["BATCH-CALF-003"].id,
            animal_code="CATTLE-002",
            species="犊牛",
            breed="荷斯坦",
            gender="公",
            birth_date=now - timedelta(days=225),
            check_in_date=now - timedelta(days=42),
            weight=74.2,
            health_status="observe",
            ear_tag="EAR-C-002",
            source="北牧育种场",
            immunization_note="2026-03-05 已完成牛肺疫免疫",
            notes="轻微应激反应，需持续观察",
            is_active=True,
        ),
        AnimalProfile(
            archive_id=archives["BATCH-CALF-003"].id,
            animal_code="SHEEP-001",
            species="肉羊",
            breed="杜泊羊",
            gender="母",
            birth_date=now - timedelta(days=160),
            check_in_date=now - timedelta(days=30),
            weight=38.6,
            health_status="stable",
            ear_tag="EAR-S-001",
            source="西北示范牧场",
            immunization_note="2026-03-10 已完成三联四防",
            notes="活动正常",
            is_active=True,
        ),
        AnimalProfile(
            archive_id=archives["BATCH-CALF-003"].id,
            animal_code="SHEEP-002",
            species="肉羊",
            breed="小尾寒羊",
            gender="公",
            birth_date=now - timedelta(days=175),
            check_in_date=now - timedelta(days=30),
            weight=41.1,
            health_status="good",
            ear_tag="EAR-S-002",
            source="西北示范牧场",
            immunization_note="2026-03-10 已完成三联四防",
            notes="增重表现良好",
            is_active=True,
        ),
    ]

    rows_added = 0
    for animal in animals:
        if animal.animal_code in existing_codes:
            continue
        session.add(animal)
        rows_added += 1
    return rows_added


def seed_alarms(session, devices: list[Device], users: list[User]) -> int:
    if session.query(AlarmInfo).count() > 0:
        return 0

    device_map = {device.device_id: device for device in devices}
    user_map = {user.username: user for user in users}
    now = datetime.utcnow()

    alarms = [
        AlarmInfo(
            device_id=device_map["DEVICE_002"].id,
            alarm_type="ammonia_high",
            alarm_level="critical",
            threshold_value=20.0,
            actual_value=24.6,
            description="A区 2号棚氨气浓度过高，请立即检查通风。",
            user_id=None,
            status="pending",
            alarm_time=now - timedelta(minutes=35),
            created_at=now - timedelta(minutes=35),
        ),
        AlarmInfo(
            device_id=device_map["DEVICE_001"].id,
            alarm_type="temperature_high",
            alarm_level="warning",
            threshold_value=30.0,
            actual_value=31.4,
            description="1号棚温度偏高，建议启动降温。",
            user_id=user_map["operator_li"].id,
            status="acknowledged",
            alarm_time=now - timedelta(hours=4),
            created_at=now - timedelta(hours=4),
        ),
        AlarmInfo(
            device_id=device_map["DEVICE_003"].id,
            alarm_type="co2_high",
            alarm_level="info",
            threshold_value=1500.0,
            actual_value=1535.0,
            description="主控室 CO2 短时偏高，已恢复正常。",
            user_id=user_map["manager_zhang"].id,
            status="resolved",
            alarm_time=now - timedelta(hours=10),
            resolved_time=now - timedelta(hours=9, minutes=20),
            created_at=now - timedelta(hours=10),
        ),
    ]

    for alarm in alarms:
        session.add(alarm)
    return len(alarms)


def seed_operations(session, users: list[User]) -> tuple[int, int, int]:
    task_count = 0
    inventory_count = 0
    asset_count = 0
    now = datetime.utcnow()

    user_map = {user.username: user for user in users}
    archive_map = {archive.batch_number: archive for archive in session.query(LivestockArchive).all()}
    device_map = {device.device_id: device for device in session.query(Device).all()}

    existing_task_titles = {row[0] for row in session.query(ProductionTask.title).all()}
    existing_inventory_names = {row[0] for row in session.query(InventoryItem.item_name).all()}
    existing_asset_codes = {row[0] for row in session.query(EquipmentAsset.asset_code).all()}

    tasks = [
        ProductionTask(
            title="早班饲喂巡检",
            category="feeding",
            status="pending",
            priority="high",
            zone_name="A区",
            archive_id=archive_map.get("BATCH-PIG-002").id if archive_map.get("BATCH-PIG-002") else None,
            assignee_user_id=user_map["operator_li"].id,
            due_at=now + timedelta(hours=2),
            description="检查自动料线运行情况，并记录上午投喂完成状态。",
        ),
        ProductionTask(
            title="鸡舍消毒记录",
            category="sanitation",
            status="in_progress",
            priority="medium",
            zone_name="A区",
            archive_id=archive_map.get("BATCH-CHICK-001").id if archive_map.get("BATCH-CHICK-001") else None,
            assignee_user_id=user_map["manager_zhang"].id,
            due_at=now + timedelta(hours=6),
            description="完成 1 号和 2 号鸡舍喷雾消毒，并登记药剂使用量。",
        ),
        ProductionTask(
            title="控制柜月度保养",
            category="maintenance",
            status="completed",
            priority="medium",
            zone_name="B区",
            assignee_user_id=user_map["admin"].id,
            due_at=now - timedelta(days=1),
            completed_at=now - timedelta(hours=3),
            description="检查主控制柜接线、风机联动和告警蜂鸣器。",
        ),
    ]

    for task in tasks:
        if task.title in existing_task_titles:
            continue
        session.add(task)
        task_count += 1

    inventory_items = [
        InventoryItem(
            item_name="育肥饲料",
            category="feed",
            unit="kg",
            current_stock=680,
            safety_stock=500,
            location="饲料仓 A",
            supplier="新牧饲料",
            last_restocked_at=now - timedelta(days=2),
            notes="适用于育肥阶段。",
        ),
        InventoryItem(
            item_name="消毒液",
            category="medicine",
            unit="L",
            current_stock=18,
            safety_stock=25,
            location="药品柜 1",
            supplier="绿安防疫",
            last_restocked_at=now - timedelta(days=7),
            notes="库存偏低，需要补货。",
        ),
        InventoryItem(
            item_name="疫苗冷藏包",
            category="vaccine",
            unit="盒",
            current_stock=12,
            safety_stock=8,
            location="冷藏柜 B",
            supplier="牧康生物",
            last_restocked_at=now - timedelta(days=5),
            notes="本周免疫任务可覆盖。",
        ),
    ]

    for item in inventory_items:
        if item.item_name in existing_inventory_names:
            continue
        session.add(item)
        inventory_count += 1

    assets = [
        EquipmentAsset(
            asset_code="ASSET-FAN-001",
            asset_name="一号通风风机",
            asset_type="fan",
            zone_name="A区",
            linked_device_id=device_map.get("DEVICE_003").id if device_map.get("DEVICE_003") else None,
            status="online",
            installed_at=now - timedelta(days=180),
            last_maintenance_at=now - timedelta(days=20),
            next_maintenance_at=now + timedelta(days=10),
            notes="联动温控规则运行正常。",
        ),
        EquipmentAsset(
            asset_code="ASSET-SENSOR-002",
            asset_name="二号气体传感器",
            asset_type="sensor",
            zone_name="A区",
            linked_device_id=device_map.get("DEVICE_002").id if device_map.get("DEVICE_002") else None,
            status="maintenance_due",
            installed_at=now - timedelta(days=240),
            last_maintenance_at=now - timedelta(days=95),
            next_maintenance_at=now - timedelta(days=2),
            notes="建议本周完成标定。",
        ),
        EquipmentAsset(
            asset_code="ASSET-LIGHT-003",
            asset_name="补光灯组",
            asset_type="fill_light",
            zone_name="B区",
            linked_device_id=device_map.get("DEVICE_003").id if device_map.get("DEVICE_003") else None,
            status="online",
            installed_at=now - timedelta(days=120),
            last_maintenance_at=now - timedelta(days=30),
            next_maintenance_at=now + timedelta(days=20),
            notes="夜间按策略启停。",
        ),
    ]

    for asset in assets:
        if asset.asset_code in existing_asset_codes:
            continue
        session.add(asset)
        asset_count += 1

    return task_count, inventory_count, asset_count


def seed_operation_logs(session, users: list[User]) -> int:
    existing = session.query(OperationLog).count()
    if existing > 0:
        return 0

    user_map = {user.username: user for user in users}
    now = datetime.utcnow()
    logs = [
        OperationLog(
            user_id=user_map["admin"].id,
            module_name="system",
            action="更新自动控制规则",
            target="rule:temperature_high",
            detail="调整高温联动阈值为 30℃。",
            created_at=now - timedelta(hours=5),
        ),
        OperationLog(
            user_id=user_map["manager_zhang"].id,
            module_name="archives",
            action="新增牛羊个体档案",
            target="animal:CATTLE-002",
            detail="录入耳标和健康状态。",
            created_at=now - timedelta(hours=3),
        ),
        OperationLog(
            user_id=user_map["operator_li"].id,
            module_name="operations",
            action="完成消毒任务",
            target="task:鸡舍消毒记录",
            detail="已登记药剂使用量和执行时间。",
            created_at=now - timedelta(hours=1),
        ),
    ]

    for log in logs:
        session.add(log)
    return len(logs)


def main() -> None:
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        users = seed_users(session)
        devices = seed_devices(session, users)
        env_rows = seed_environment_data(session, devices)
        archive_rows = seed_livestock_archives(session)
        animal_rows = seed_animal_profiles(session)
        alarm_rows = seed_alarms(session, devices, users)
        task_rows, inventory_rows, asset_rows = seed_operations(session, users)
        log_rows = seed_operation_logs(session, users)
        session.commit()

        print("Seed completed")
        print(f"users: {session.query(User).count()}")
        print(f"devices: {session.query(Device).count()}")
        print(f"environment_data added: {env_rows}")
        print(f"livestock_archive added: {archive_rows}")
        print(f"animal_profiles added: {animal_rows}")
        print(f"alarm_info added: {alarm_rows}")
        print(f"production_tasks added: {task_rows}")
        print(f"inventory_items added: {inventory_rows}")
        print(f"equipment_assets added: {asset_rows}")
        print(f"operation_logs added: {log_rows}")
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
