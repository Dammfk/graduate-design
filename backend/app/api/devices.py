from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import Device, User
from app.schemas import DeviceCreate, DeviceUpdate, DeviceResponse
from app.utils import to_display_iso

router = APIRouter(prefix="/api/v1/devices", tags=["devices"])


@router.post("/", response_model=DeviceResponse)
async def create_device(
    device: DeviceCreate,
    owner_id: int,
    db: Session = Depends(get_db)
):
    """创建新设备"""
    try:
        # 检查用户是否存在
        user = db.query(User).filter(User.id == owner_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # 检查设备 ID 是否已存在
        existing_device = db.query(Device).filter(
            Device.device_id == device.device_id
        ).first()
        if existing_device:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Device with ID {device.device_id} already exists"
            )
        
        # 创建设备
        db_device = Device(
            device_id=device.device_id,
            device_name=device.device_name,
            device_type=device.device_type,
            location=device.location,
            owner_id=owner_id
        )
        
        db.add(db_device)
        db.commit()
        db.refresh(db_device)
        
        return db_device
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: str,
    db: Session = Depends(get_db)
):
    """获取设备详情"""
    try:
        device = db.query(Device).filter(Device.device_id == device_id).first()
        
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device not found: {device_id}"
            )
        
        return device
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/")
async def list_devices(
    owner_id: int = None,
    db: Session = Depends(get_db)
):
    """列出设备"""
    try:
        query = db.query(Device)
        
        if owner_id:
            query = query.filter(Device.owner_id == owner_id)
        
        devices = query.all()
        
        return {
            "status": "success",
            "count": len(devices),
            "data": [
                {
                    "id": d.id,
                    "device_id": d.device_id,
                    "device_name": d.device_name,
                    "device_type": d.device_type,
                    "location": d.location,
                    "owner_id": d.owner_id,
                    "is_active": d.is_active,
                    "latest_data_timestamp": to_display_iso(d.latest_data_timestamp),
                    "created_at": to_display_iso(d.created_at)
                }
                for d in devices
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{device_id}")
async def update_device(
    device_id: str,
    device_update: DeviceUpdate,
    db: Session = Depends(get_db)
):
    """更新设备信息"""
    try:
        device = db.query(Device).filter(Device.device_id == device_id).first()
        
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device not found: {device_id}"
            )
        
        # 更新字段
        update_data = device_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(device, key, value)
        
        db.commit()
        db.refresh(device)
        
        return {
            "status": "success",
            "message": "Device updated",
            "data": {
                "id": device.id,
                "device_id": device.device_id,
                "device_name": device.device_name,
                "location": device.location,
                "is_active": device.is_active
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{device_id}")
async def delete_device(
    device_id: str,
    db: Session = Depends(get_db)
):
    """删除设备"""
    try:
        device = db.query(Device).filter(Device.device_id == device_id).first()
        
        if not device:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Device not found: {device_id}"
            )
        
        db.delete(device)
        db.commit()
        
        return {
            "status": "success",
            "message": f"Device {device_id} deleted"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
