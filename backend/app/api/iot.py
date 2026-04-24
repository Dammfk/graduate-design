from __future__ import annotations

import base64
import binascii
import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import TelemetryData
from app.services import AlarmService, ControlService, TelemetryService

router = APIRouter(prefix="/api/v1/iot", tags=["iot"])

PAYLOAD_KEYS = {
    "payload",
    "data",
    "message",
    "msg",
    "content",
    "value",
    "body",
    "rawData",
    "raw_data",
    "serviceData",
    "service_data",
    "APPdata",
    "appData",
    "app_data",
}

DEVICE_ID_KEYS = {
    "device_id",
    "deviceId",
    "deviceID",
    "imei",
    "endpoint",
    "endpointName",
    "endpoint_name",
    "nodeId",
}


async def _read_ctwing_request(request: Request) -> Any:
    content_type = request.headers.get("content-type", "")
    raw_body = await request.body()

    if "application/json" in content_type:
        try:
            return json.loads(raw_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid JSON body: {exc}",
            ) from exc

    if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
        form = await request.form()
        return dict(form)

    if not raw_body:
        return {}

    try:
        return json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return raw_body.decode("utf-8", errors="ignore")


def _find_first_value(value: Any, keys: set[str]) -> Any:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in keys:
                return item
        for item in value.values():
            found = _find_first_value(item, keys)
            if found is not None:
                return found
    elif isinstance(value, list):
        for item in value:
            found = _find_first_value(item, keys)
            if found is not None:
                return found
    return None


def _maybe_decode_text(value: str) -> str:
    text = value.strip()
    if not text:
        return text

    try:
        decoded = base64.b64decode(text, validate=True)
        decoded_text = decoded.decode("utf-8")
        if decoded_text.strip():
            return decoded_text.strip()
    except (binascii.Error, UnicodeDecodeError, ValueError):
        pass

    if len(text) % 2 == 0 and all(ch in "0123456789abcdefABCDEF" for ch in text):
        try:
            decoded_text = bytes.fromhex(text).decode("utf-8")
            if decoded_text.strip():
                return decoded_text.strip()
        except (UnicodeDecodeError, ValueError):
            pass

    return text


def _parse_payload(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict):
        app_data = _find_first_value(payload, {"APPdata", "appData", "app_data"})
        if app_data is not None:
            parsed = _parse_payload(app_data)
            if parsed:
                return parsed
        return payload

    if isinstance(payload, list):
        for item in payload:
            parsed = _parse_payload(item)
            if parsed:
                return parsed
        return {}

    if isinstance(payload, bytes):
        payload = payload.decode("utf-8", errors="ignore")

    if not isinstance(payload, str):
        return {}

    decoded_text = _maybe_decode_text(payload)
    try:
        parsed = json.loads(decoded_text)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {"raw_payload": decoded_text}


def _extract_payload(wrapper: Any) -> dict[str, Any]:
    if isinstance(wrapper, dict):
        direct_payload = _find_first_value(wrapper, PAYLOAD_KEYS)
        if direct_payload is not None:
            parsed = _parse_payload(direct_payload)
            if parsed:
                return parsed

        if any(key in wrapper for key in {"temperature", "humidity", "event"}):
            return wrapper

    return _parse_payload(wrapper)


def _extract_device_id(wrapper: Any, payload: dict[str, Any]) -> str:
    device_id = payload.get("device_id") or payload.get("deviceId")
    if not device_id:
        device_id = _find_first_value(wrapper, DEVICE_ID_KEYS)
    if not device_id:
        device_id = "DEVICE_001"
    return str(device_id)


def _to_float_or_none(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _build_telemetry(wrapper: Any, payload: dict[str, Any]) -> TelemetryData | None:
    temperature = _to_float_or_none(payload.get("temperature") or payload.get("T"))
    humidity = _to_float_or_none(payload.get("humidity") or payload.get("H"))
    co2 = _to_float_or_none(payload.get("co2_concentration") or payload.get("co2") or payload.get("CO2"))
    ammonia = _to_float_or_none(payload.get("ammonia_concentration") or payload.get("ammonia") or payload.get("NH3"))

    if temperature is None and humidity is None and co2 is None and ammonia is None:
        return None

    return TelemetryData(
        device_id=_extract_device_id(wrapper, payload),
        temperature=temperature,
        humidity=humidity,
        co2_concentration=co2,
        ammonia_concentration=ammonia,
        timestamp=datetime.utcnow(),
    )


@router.post("/ctwing/uplink")
async def receive_ctwing_uplink(
    request: Request,
    db: Session = Depends(get_db),
):
    wrapper = await _read_ctwing_request(request)
    payload = _extract_payload(wrapper)
    telemetry = _build_telemetry(wrapper, payload)

    if telemetry is None:
        return {
            "status": "ignored",
            "message": "CTWing message received, but no telemetry fields were found",
            "payload": payload,
        }

    try:
        environment_data = await TelemetryService.save_environment_data(
            db, telemetry.device_id, telemetry
        )
        alarms = await AlarmService.check_and_create_alarms(db, environment_data)
        commands = await ControlService.generate_control_commands(db, environment_data)

        return {
            "status": "success",
            "message": "CTWing uplink telemetry received and processed",
            "data": {
                "data_id": environment_data.id,
                "device_id": telemetry.device_id,
                "alarms_created": len(alarms),
                "commands_generated": len(commands),
                "timestamp": TelemetryService._to_display_iso(environment_data.recorded_at),
            },
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process CTWing uplink: {exc}",
        ) from exc
