from flask import Flask
from flask_cors import CORS
from database import Database
from config import Config
from middleware.auth import token_required
from middleware.heartbeat import HeartbeatChecker
from middleware.permissions import require_action_permission
from routes.auth import create_auth_routes
from routes.accounts import create_accounts_routes
from routes.organizations import create_organizations_routes
from routes.devices import create_devices_routes
from routes.permissions import create_permissions_routes
from routes.activity_logs import create_activity_log_routes
from websocket_service import WebSocketService
import os
import time

config = Config()
db = Database(config.db_path)

app = Flask(__name__)
CORS(app)

server_start_time = time.time()

auth_middleware = token_required(db)

auth_routes = create_auth_routes(db, config, auth_middleware)
accounts_routes = create_accounts_routes(db, auth_middleware)
organizations_routes = create_organizations_routes(db, auth_middleware)
devices_routes = create_devices_routes(db, auth_middleware)
permissions_routes = create_permissions_routes(db, auth_middleware)
activity_logs_routes = create_activity_log_routes(db, auth_middleware, require_action_permission)

app.register_blueprint(auth_routes)
app.register_blueprint(accounts_routes)
app.register_blueprint(organizations_routes)
app.register_blueprint(devices_routes)
app.register_blueprint(permissions_routes)
app.register_blueprint(activity_logs_routes)

# HTTP心跳检查器已禁用（现在使用WebSocket实时心跳）
# heartbeat_checker = HeartbeatChecker(
#     db,
#     timeout=config.heartbeat_timeout,
#     check_interval=10
# )
# heartbeat_checker.start()

# WebSocket服务（主要实时通信，包含心跳检测）
ws_service = WebSocketService(app, db, config)


@app.route('/api/health', methods=['GET'])
def health_check():
    return {'status': 'ok', 'message': 'Server is running', 'websocket': 'enabled'}


@app.route('/api/uptime', methods=['GET'])
def get_uptime():
    elapsed = time.time() - server_start_time
    days = int(elapsed // 86400)
    hours = int((elapsed % 86400) // 3600)
    minutes = int((elapsed % 3600) // 60)
    seconds = int(elapsed % 60)
    uptime_str = f"{days}天{hours}小时{minutes}分钟{seconds}秒"
    return {'uptime': uptime_str}


# WebSocket推送API接口（供其他路由调用）
def push_config_to_device(device_id, config):
    """推送配置到设备"""
    return ws_service.push_config_to_device(device_id, config)

def push_config_to_organization(organization_id, config):
    """推送配置到组织"""
    ws_service.push_config_to_organization(organization_id, config)

def push_activity_log(log_data):
    """推送活动日志"""
    ws_service.push_activity_log(log_data)

def push_notification(message, room=None):
    """推送通知"""
    ws_service.push_notification(message, room)


if __name__ == '__main__':
    print(f"[Server] Starting HTTP+WebSocket on http://0.0.0.0:{config.backend_port}")
    print(f"[WebSocket] Real-time communication enabled")
    # 使用SocketIO运行，支持WebSocket
    ws_service.get_socketio().run(app, debug=True, host='0.0.0.0', port=config.backend_port)
