import threading
import time
from datetime import datetime


class HeartbeatChecker:
    def __init__(self, db, timeout=20, check_interval=10):
        self.db = db
        self.timeout = timeout
        self.check_interval = check_interval
        self._thread = None

    def start(self):
        self._thread = threading.Thread(target=self._check_heartbeat, daemon=True)
        self._thread.start()

    def _check_heartbeat(self):
        while True:
            try:
                devices = self.db.get_all_devices()
                now = datetime.now()

                for device in devices:
                    if device['status'] == 'online':
                        last_heartbeat = device.get('last_heartbeat')
                        if last_heartbeat:
                            try:
                                last_time = datetime.fromisoformat(last_heartbeat)
                                diff = (now - last_time).total_seconds()

                                if diff > self.timeout:
                                    self.db.update_device(
                                        device['id'],
                                        status='offline',
                                        offline_reason='heartbeat_timeout'
                                    )
                                    print(f"[HeartbeatChecker] 设备 {device['name']} 心跳超时，标记为离线")
                            except Exception as e:
                                print(f"[HeartbeatChecker] 解析心跳时间失败: {e}")
                        else:
                            self.db.update_device(
                                device['id'],
                                status='offline',
                                offline_reason='no_heartbeat'
                            )
            except Exception as e:
                print(f"[HeartbeatChecker] 检查心跳失败: {e}")

            time.sleep(self.check_interval)
