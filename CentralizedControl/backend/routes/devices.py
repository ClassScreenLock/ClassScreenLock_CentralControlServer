from flask import Blueprint, request, jsonify
from datetime import datetime
from utils.converters import convert_device_fields
from middleware.permissions import require_action_permission


def create_devices_routes(db, token_required):
    devices_bp = Blueprint('devices', __name__, url_prefix='/api/devices')

    @devices_bp.route('', methods=['GET'])
    @token_required
    def get_devices(user):
        devices = db.devices.get_all()
        return jsonify([convert_device_fields(device) for device in devices])

    @devices_bp.route('/<path:device_id>', methods=['GET'])
    @token_required
    @require_action_permission(db, 'device', 'viewDetail')
    def get_device(user, device_id):
        device = db.devices.get_by_id(device_id)
        if not device:
            return jsonify({'error': 'Device not found'}), 404

        return jsonify(convert_device_fields(device))

    @devices_bp.route('', methods=['POST'])
    @token_required
    def create_device(user):
        if user['role'] not in ['super_admin', 'admin']:
            return jsonify({'error': '权限不足，无法创建设备'}), 403

        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        name = data.get('name')
        ip_address = data.get('ipAddress') or data.get('ip_address')
        organization_id = data.get('organizationId') or data.get('organization_id')

        if not name or not ip_address:
            return jsonify({'error': 'Name and IP address are required'}), 400

        device_id = db.devices.create(
            name=name,
            ip_address=ip_address,
            organization_id=organization_id,
            mac_address=data.get('macAddress') or data.get('mac_address'),
            os_version=data.get('osVersion') or data.get('os_version'),
            app_version=data.get('appVersion') or data.get('app_version'),
            dotnet_version=data.get('dotnetVersion') or data.get('dotnet_version'),
            contact_phone=data.get('contactPhone') or data.get('contact_phone'),
            class_name=data.get('className') or data.get('class_name'),
            person_in_charge=data.get('personInCharge') or data.get('person_in_charge')
        )
        
        db.activity_logs.create(
            account_id=user['id'],
            account_username=user['username'],
            action_type='create',
            action_category='device',
            description=f'用户 {user["username"]} 创建设备 {name} ({ip_address})',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        device = db.devices.get_by_id(device_id)
        return jsonify(convert_device_fields(device)), 201

    @devices_bp.route('/<path:device_id>', methods=['PUT'])
    @token_required
    def update_device(user, device_id):
        if user['role'] not in ['super_admin', 'admin']:
            return jsonify({'error': '权限不足，无法更新设备'}), 403

        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        old_device = db.devices.get_by_id(device_id)
        
        if not db.devices.update(device_id, **data):
            return jsonify({'error': 'Device not found or no changes made'}), 404

        device = db.devices.get_by_id(device_id)
        
        db.activity_logs.create(
            account_id=user['id'],
            account_username=user['username'],
            action_type='update',
            action_category='device',
            description=f'用户 {user["username"]} 更新设备 {device.get("name", device_id)}',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        return jsonify(convert_device_fields(device))

    @devices_bp.route('/<path:device_id>', methods=['DELETE'])
    @token_required
    @require_action_permission(db, 'device', 'delete')
    def delete_device(user, device_id):
        if user['role'] not in ['super_admin', 'admin']:
            return jsonify({'error': '权限不足，无法删除设备'}), 403

        device = db.devices.get_by_id(device_id)
        if not device:
            return jsonify({'error': 'Device not found'}), 404

        device_name = device.get('name', device_id)
        
        db.devices.delete(device_id)
        
        db.activity_logs.create(
            account_id=user['id'],
            account_username=user['username'],
            action_type='delete',
            action_category='device',
            description=f'用户 {user["username"]} 删除设备 {device_name}',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )

        return jsonify({'message': 'Device deleted successfully'})

    @devices_bp.route('/<path:device_id>/heartbeat', methods=['POST'])
    def device_heartbeat(device_id):
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        now = datetime.now().isoformat()

        heartbeat_data = {
            'status': data.get('status', 'online'),
            'cpu_usage': data.get('cpuUsage', 0),
            'memory_usage': data.get('memoryUsage', 0),
            'disk_usage': data.get('diskUsage', 0),
            'last_heartbeat': now,
            'last_seen': now
        }

        if data.get('status') == 'offline':
            heartbeat_data['offline_reason'] = data.get('reason', 'unknown')
            heartbeat_data['exit_time'] = now
        else:
            heartbeat_data['offline_reason'] = None
            heartbeat_data['exit_time'] = None

        if db.devices.update(device_id, **heartbeat_data):
            return jsonify({'message': 'Heartbeat received', 'device_id': device_id})
        else:
            return jsonify({'error': 'Device not found'}), 404

    @devices_bp.route('/<path:device_id>/logout', methods=['POST'])
    def device_logout(device_id):
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        logout_data = {
            'status': 'logged_out',
            'exit_time': datetime.now().isoformat(),
            'offline_reason': data.get('exitReason', 'user_logout')
        }

        if db.devices.update(device_id, **logout_data):
            return jsonify({'message': 'Device logged out', 'device_id': device_id})
        else:
            return jsonify({'error': 'Device not found'}), 404

    @devices_bp.route('/<path:device_id>/network-rules', methods=['GET'])
    def get_device_network_rules(device_id):
        device = db.devices.get_by_id(device_id)
        if not device:
            return jsonify({'error': 'Device not found'}), 404

        org_id = device.get('organization_id')
        if not org_id:
            return jsonify({'domainRules': []})

        config = db.organizations.get_config(org_id)
        if config and config.get('network_config'):
            network_config = config['network_config']
            return jsonify({
                'enabled': network_config.get('enabled', True),
                'mode': network_config.get('mode', 'blacklist'),
                'domainRules': network_config.get('domainRules', [])
            })

        return jsonify({
            'enabled': True,
            'mode': 'blacklist',
            'domainRules': []
        })

    return devices_bp
