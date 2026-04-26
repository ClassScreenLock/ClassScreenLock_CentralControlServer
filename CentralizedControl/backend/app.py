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

heartbeat_checker = HeartbeatChecker(
    db,
    timeout=config.heartbeat_timeout,
    check_interval=10
)
heartbeat_checker.start()


@app.route('/api/health', methods=['GET'])
def health_check():
    return {'status': 'ok', 'message': 'Server is running'}


@app.route('/api/uptime', methods=['GET'])
def get_uptime():
    elapsed = time.time() - server_start_time
    days = int(elapsed // 86400)
    hours = int((elapsed % 86400) // 3600)
    minutes = int((elapsed % 3600) // 60)
    seconds = int(elapsed % 60)
    uptime_str = f"{days}天{hours}小时{minutes}分钟{seconds}秒"
    return {'uptime': uptime_str}


if __name__ == '__main__':
    print(f"[Server] Starting on http://0.0.0.0:{config.backend_port}")
    app.run(debug=True, host='0.0.0.0', port=config.backend_port)
