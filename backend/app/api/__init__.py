from fastapi import APIRouter

from .alarms import router as alarms_router
from .archives import router as archives_router
from .control import router as control_router
from .devices import router as devices_router
from .iot import router as iot_router
from .operations import router as operations_router
from .system import router as system_router
from .telemetry import router as telemetry_router

router = APIRouter()
router.include_router(telemetry_router)
router.include_router(alarms_router)
router.include_router(devices_router)
router.include_router(control_router)
router.include_router(iot_router)
router.include_router(archives_router)
router.include_router(operations_router)
router.include_router(system_router)

__all__ = ["router"]
