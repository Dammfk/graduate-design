from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
import urllib.error
import urllib.request

from app.core.config import settings


class CTWingCommandService:
    API_BASE_URL = "https://ag-api.ctwing.cn"
    TIME_PATH = "/echo"
    COMMAND_PATH = "/aep_device_command/command"

    @staticmethod
    def _is_configured() -> bool:
        return all(
            [
                settings.CTWING_APP_KEY,
                settings.CTWING_APP_SECRET,
                settings.CTWING_MASTER_KEY,
                settings.CTWING_PRODUCT_ID,
                settings.CTWING_DEVICE_ID,
            ]
        )

    @staticmethod
    @staticmethod
    def _get_time_offset() -> int:
        request = urllib.request.Request(url=f"{CTWingCommandService.API_BASE_URL}{CTWingCommandService.TIME_PATH}")
        start = int(time.time() * 1000)
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                end = int(time.time() * 1000)
                header_value = response.headers.get("x-ag-timestamp")
                if not header_value:
                    return 0
                return int(int(header_value) - ((end + start) / 2))
        except Exception:
            return 0

    @staticmethod
    def _build_signature(*, timestamp: str, params: list[tuple[str, str]], body: str) -> str:
        lines = [
            f"application:{settings.CTWING_APP_KEY or ''}",
            f"timestamp:{timestamp}",
        ]
        for key, value in params:
            lines.append(f"{key}:{value}")
        if body.strip():
            lines.append(body)
        message = "\n".join(lines) + "\n"
        secret = (settings.CTWING_APP_SECRET or "").encode("utf-8")
        digest = hmac.new(secret, message.encode("utf-8"), hashlib.sha1).digest()
        return base64.b64encode(digest).decode("utf-8")

    @staticmethod
    def dispatch_command(
        *,
        command_id: int,
        device_id: str,
        target_component: str,
        command_type: str,
        reason: str | None = None,
    ) -> dict:
        if not CTWingCommandService._is_configured():
            raise RuntimeError("CTWing command API is not configured")

        if device_id != settings.CTWING_LOCAL_DEVICE_ID:
            raise RuntimeError(f"No CTWing device mapping configured for {device_id}")

        payload = json.dumps(
            {
                "command_id": command_id,
                "target": target_component,
                "command": command_type.upper(),
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
        body_dict = {
            "content": {
                "dataType": 1,
                "payload": payload,
            },
            "deviceId": settings.CTWING_DEVICE_ID,
            "operator": settings.CTWING_OPERATOR,
            "productId": int(settings.CTWING_PRODUCT_ID),
            "ttl": int(settings.CTWING_COMMAND_TTL),
            "level": 1,
        }
        body = json.dumps(body_dict, ensure_ascii=False, separators=(",", ":"))
        params: list[tuple[str, str]] = []
        if settings.CTWING_MASTER_KEY:
            params.append(("MasterKey", settings.CTWING_MASTER_KEY))
        params = sorted(params)
        timestamp = str(int(time.time() * 1000) + CTWingCommandService._get_time_offset())
        signature = CTWingCommandService._build_signature(timestamp=timestamp, params=params, body=body)

        request = urllib.request.Request(
            url=f"{settings.CTWING_API_BASE_URL}{CTWingCommandService.COMMAND_PATH}",
            data=body.encode("utf-8"),
            method="POST",
            headers={
                "Content-Type": "application/json;charset=utf-8",
                "application": settings.CTWING_APP_KEY or "",
                "timestamp": timestamp,
                "signature": signature,
                "version": settings.CTWING_COMMAND_API_VERSION,
                "MasterKey": settings.CTWING_MASTER_KEY or "",
            },
        )

        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                response_text = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"CTWing command API HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"CTWing command API request failed: {exc}") from exc

        try:
            parsed = json.loads(response_text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Invalid CTWing command response: {response_text}") from exc

        code = parsed.get("code")
        if code not in (0, "0", None):
            raise RuntimeError(
                f"CTWing command rejected: code={code}, msg={parsed.get('msg')}, body={response_text}"
            )

        return parsed
