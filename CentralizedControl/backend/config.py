import os
import json


class Config:
    def __init__(self, config_file=None):
        if config_file is None:
            config_file = os.path.join(os.path.dirname(__file__), 'config.json')
        self.config_file = config_file
        self._config = self._load_config()

    def _load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'backendPort': 5000,
            'serverPort': 5173,
            'systemName': 'ClassScreenLock 集控管理平台'
        }

    def save_config(self, config):
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        self._config = config

    def get(self, key, default=None):
        return self._config.get(key, default)

    def set(self, key, value):
        self._config[key] = value

    @property
    def backend_port(self):
        return self._config.get('backendPort', 5000)

    @property
    def server_port(self):
        return self._config.get('serverPort', 5173)

    @property
    def system_name(self):
        return self._config.get('systemName', 'ClassScreenLock 集控管理平台')

    @property
    def token_expiry_hours(self):
        return self._config.get('tokenExpiryHours', 48)

    @property
    def heartbeat_timeout(self):
        return self._config.get('heartbeatTimeout', 20)

    @property
    def db_path(self):
        return os.path.join(os.path.dirname(__file__), 'classscreenlock.db')
