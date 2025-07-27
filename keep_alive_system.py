import requests
import time
import threading
from datetime import datetime


class KeepAliveSystem:
    """簡化版保持服務喚醒的系統"""

    def __init__(self, service_url, ping_interval=840):  # 14分鐘ping一次
        self.service_url = service_url.rstrip('/')
        self.ping_interval = ping_interval  # 秒
        self.is_running = False
        self.ping_thread = None

    def ping_service(self):
        """Ping 服務以保持喚醒"""
        try:
            response = requests.get(f"{self.service_url}/", timeout=30)
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if response.status_code == 200:
                print(f"✅ [{current_time}] Keep-alive ping successful")
                return True
            else:
                print(f"⚠️ [{current_time}] Keep-alive ping failed with status {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"❌ [{current_time}] Keep-alive ping error: {e}")
            return False

    def start(self):
        """啟動保持喚醒服務"""
        if self.is_running:
            print("Keep-alive service is already running")
            return

        self.is_running = True

        def ping_loop():
            print(f"🚀 Keep-alive service started, pinging every {self.ping_interval // 60} minutes")

            while self.is_running:
                try:
                    # 等待指定時間
                    for _ in range(self.ping_interval):
                        if not self.is_running:
                            break
                        time.sleep(1)

                    if self.is_running:
                        self.ping_service()

                except Exception as e:
                    print(f"❌ Keep-alive loop error: {e}")
                    time.sleep(60)  # 出錯後等待1分鐘再重試

        self.ping_thread = threading.Thread(target=ping_loop, daemon=True)
        self.ping_thread.start()

    def stop(self):
        """停止保持喚醒服務"""
        self.is_running = False
        print("🛑 Keep-alive service stopped")


# 全域保持喚醒服務實例
keep_alive_service = None


def initialize_keep_alive(service_url):
    """初始化保持喚醒服務"""
    global keep_alive_service

    if keep_alive_service is None:
        keep_alive_service = KeepAliveSystem(service_url)
        keep_alive_service.start()

    return keep_alive_service