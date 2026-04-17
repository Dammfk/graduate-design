import argparse
import json
import sys
import time
from typing import Any

import requests
import serial


def safe_print(message: str) -> None:
    try:
        print(message)
    except UnicodeEncodeError:
        sys.stdout.buffer.write((message + "\n").encode("utf-8", errors="replace"))
        sys.stdout.buffer.flush()
    except OSError:
        pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="STM32 串口与 FastAPI 之间的桥接程序")
    parser.add_argument("--port", required=True, help="串口号，例如 COM5")
    parser.add_argument("--baudrate", type=int, default=115200, help="串口波特率，默认 115200")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="后端地址")
    parser.add_argument("--poll-interval", type=float, default=2.0, help="轮询命令的间隔秒数")
    parser.add_argument("--read-timeout", type=float, default=0.2, help="串口读取超时秒数")
    parser.add_argument(
        "--device-id",
        action="append",
        default=[],
        help="手动指定要轮询命令的设备 ID，可重复传入多个",
    )
    return parser.parse_args()


class SerialBridge:
    def __init__(
        self,
        port: str,
        baudrate: int,
        base_url: str,
        poll_interval: float,
        read_timeout: float,
        initial_devices: list[str],
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.poll_interval = poll_interval
        self.last_poll_time = time.time() + max(2.0, poll_interval)
        self.session = requests.Session()
        self.serial = serial.Serial(port=port, baudrate=baudrate, timeout=read_timeout)
        self.known_devices: set[str] = {device_id for device_id in initial_devices if device_id}

    def run(self) -> None:
        safe_print(f"[Bridge] 串口已打开: {self.serial.port} @ {self.serial.baudrate}")
        safe_print(f"[Bridge] 后端地址: {self.base_url}")
        if self.known_devices:
            safe_print(f"[Bridge] 初始轮询设备: {', '.join(sorted(self.known_devices))}")

        try:
            while True:
                self._read_from_serial_once()
                self._poll_pending_commands_if_needed()
        except KeyboardInterrupt:
            safe_print("\n[Bridge] 用户中断，准备退出")
        finally:
            self.serial.close()
            self.session.close()
            safe_print("[Bridge] 已关闭")

    def _read_from_serial_once(self) -> None:
        raw = self.serial.readline()
        if not raw:
            return

        line = raw.decode("utf-8", errors="ignore").strip()
        if not line:
            return

        safe_print(f"[串口接收] {line}")

        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            safe_print("[Bridge] 收到非 JSON 内容，已忽略")
            return

        if payload.get("type") == "ack":
            self._handle_ack(payload)
            return

        self._forward_telemetry(payload)

    def _forward_telemetry(self, payload: dict[str, Any]) -> None:
        device_id = payload.get("device_id")
        if not device_id:
            safe_print("[Bridge] 遥测数据缺少 device_id，已忽略")
            return

        self.known_devices.add(str(device_id))

        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/telemetry/",
                json=payload,
                timeout=10,
            )
            response.raise_for_status()
            safe_print(f"[HTTP 上报] telemetry 已上传: {device_id}")
        except requests.RequestException as exc:
            safe_print(f"[Bridge] 上传 telemetry 失败: {exc}")

    def _poll_pending_commands_if_needed(self) -> None:
        now = time.time()
        if now - self.last_poll_time < self.poll_interval:
            return

        self.last_poll_time = now
        self._poll_pending_commands()

    def _poll_pending_commands(self) -> None:
        if not self.known_devices:
            self.known_devices.update(self._collect_known_devices())

        for device_id in sorted(self.known_devices):
            try:
                response = self.session.get(
                    f"{self.base_url}/api/v1/control/devices/{device_id}/commands/pending",
                    timeout=10,
                )
                response.raise_for_status()
                data = response.json().get("data", [])
            except requests.RequestException as exc:
                safe_print(f"[Bridge] 轮询命令失败 {device_id}: {exc}")
                continue

            for command in data:
                self._send_command_to_device(command)

    def _collect_known_devices(self) -> set[str]:
        devices: set[str] = set()
        try:
            response = self.session.get(f"{self.base_url}/api/v1/telemetry/overview", timeout=10)
            response.raise_for_status()
            payload = response.json().get("data", {})
            for item in payload.get("devices", []):
                device_id = item.get("device_id")
                if device_id:
                    devices.add(device_id)
        except requests.RequestException:
            pass
        return devices

    def _send_command_to_device(self, command: dict[str, Any]) -> None:
        command_id = command["id"]
        serial_payload = {
            "command_id": command_id,
            "target": command["target_component"],
            "command": command["command_type"],
        }
        line = json.dumps(serial_payload, ensure_ascii=False, separators=(",", ":")) + "\n"

        try:
            self.serial.write(line.encode("utf-8"))
            self.serial.flush()
            safe_print(f"[串口发送] {line.strip()}")
            self._update_command_status(command_id, "sent")
        except serial.SerialException as exc:
            safe_print(f"[Bridge] 串口发送命令失败: {exc}")

    def _handle_ack(self, payload: dict[str, Any]) -> None:
        command_id = payload.get("command_id")
        status = payload.get("status")
        if not command_id or not status:
            safe_print("[Bridge] ACK 缺少 command_id 或 status，已忽略")
            return

        normalized_status = str(status).lower()
        if normalized_status == "ok":
            normalized_status = "success"
        elif normalized_status == "fail":
            normalized_status = "failed"

        self._update_command_status(int(command_id), normalized_status)
        safe_print(f"[Bridge] 命令回执已更新: command_id={command_id}, status={normalized_status}")

    def _update_command_status(self, command_id: int, status: str) -> None:
        try:
            response = self.session.put(
                f"{self.base_url}/api/v1/control/commands/{command_id}/status",
                json={"status": status},
                timeout=10,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            safe_print(f"[Bridge] 更新命令状态失败 {command_id}: {exc}")


def main() -> None:
    args = parse_args()
    bridge = SerialBridge(
        port=args.port,
        baudrate=args.baudrate,
        base_url=args.base_url,
        poll_interval=args.poll_interval,
        read_timeout=args.read_timeout,
        initial_devices=args.device_id,
    )
    bridge.run()


if __name__ == "__main__":
    main()
