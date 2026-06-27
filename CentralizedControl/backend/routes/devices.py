from flask import Blueprint, request, jsonify
from datetime import datetime
from utils.converters import convert_device_fields
from middleware.permissions import require_action_permission


def create_devices_routes(db, token_required):
    devices_bp = Blueprint('devices', __name__, url_prefix='/api/devices')

    # ========== WebSocket相关API端点 ==========
    
    @devices_bp.route('/ws/register', methods=['POST'])
    def ws_device_register():
        """WebSocket设备注册"""
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        device_id = data.get('deviceId')
        organization_id = data.get('organizationId')
        device_name = data.get('deviceName')
        ip_address = data.get('ipAddress')
        mac_address = data.get('macAddress')
        
        if not device_id or not organization_id:
            return jsonify({'error': 'deviceId and organizationId are required'}), 400
        
        now = datetime.now().isoformat()
        
        # 检查设备是否已存在
        existing_device = db.devices.get_by_id(device_id)
        
        if existing_device:
            # 更新设备状态为在线
            db.devices.update(
                device_id,
                status='online',
                last_seen=now,
                last_heartbeat=now,
                offline_reason=None,
                exit_time=None
            )
        else:
            # 创建新设备
            db.devices.create(
                name=device_name or f'Device-{device_id[:8]}',
                ip_address=ip_address or '127.0.0.1',
                organization_id=organization_id,
                mac_address=mac_address,
                status='online',
                last_seen=now,
                last_heartbeat=now
            )
        
        return jsonify({
            'message': 'Device registered successfully',
            'deviceId': device_id,
            'status': 'online',
            'timestamp': now
        })
    
    @devices_bp.route('/ws/heartbeat', methods=['POST'])
    def ws_device_heartbeat():
        """WebSocket设备心跳"""
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        device_id = data.get('deviceId')
        
        if not device_id:
            return jsonify({'error': 'deviceId is required'}), 400
        
        now = datetime.now().isoformat()
        
        # 更新心跳数据
        heartbeat_data = {
            'status': 'online',
            'cpu_usage': data.get('cpuUsage', 0),
            'memory_usage': data.get('memoryUsage', 0),
            'disk_usage': data.get('diskUsage', 0),
            'last_heartbeat': now,
            'last_seen': now,
            'offline_reason': None,
            'exit_time': None
        }
        
        if db.devices.update(device_id, **heartbeat_data):
            # 检查是否有配置更新（简化实现）
            device = db.devices.get_by_id(device_id)
            config_updated = False
            
            if device and device.get('organization_id'):
                # 可以实现配置版本检查逻辑
                config_updated = False
            
            return jsonify({
                'message': 'Heartbeat received',
                'deviceId': device_id,
                'timestamp': now,
                'configUpdated': config_updated
            })
        else:
            return jsonify({'error': 'Device not found'}), 404
    
    @devices_bp.route('/ws/offline', methods=['POST'])
    def ws_device_offline():
        """WebSocket设备离线通知"""
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400
        
        device_id = data.get('deviceId')
        reason = data.get('reason', 'unknown')
        
        if not device_id:
            return jsonify({'error': 'deviceId is required'}), 400
        
        now = datetime.now().isoformat()
        
        offline_data = {
            'status': 'offline',
            'offline_reason': reason,
            'exit_time': now
        }
        
        if db.devices.update(device_id, **offline_data):
            return jsonify({
                'message': 'Device offline notification received',
                'deviceId': device_id,
                'reason': reason,
                'timestamp': now
            })
        else:
            return jsonify({'error': 'Device not found'}), 404

    # ========== HTTP API端点 ==========

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

    @devices_bp.route('/<path:device_id>/software', methods=['GET'])
    @token_required
    @require_action_permission(db, 'device', 'viewSoftware')
    def get_device_software(user, device_id):
        device = db.devices.get_by_id(device_id)
        if not device:
            return jsonify({'error': 'Device not found'}), 404

        include_system = request.args.get('includeSystem', 'true').lower() == 'true'
        search_query = request.args.get('search', '').strip()

        if search_query:
            software_list = db.device_software.search_software(device_id, search_query)
        else:
            software_list = db.device_software.get_software_by_device(device_id, include_system)

        result = []
        for sw in software_list:
            result.append({
                'id': sw['id'],
                'name': sw['name'],
                'publisher': sw['publisher'],
                'version': sw['version'],
                'installDate': sw['install_date'],
                'installLocation': sw['install_location'],
                'estimatedSize': sw['estimated_size'],
                'uninstallString': sw['uninstall_string'],
                'isSystemSoftware': bool(sw['is_system_software']),
                'lastUpdated': sw['last_updated']
            })

        return jsonify({
            'deviceId': device_id,
            'totalCount': len(result),
            'software': result
        })

    @devices_bp.route('/<path:device_id>/software', methods=['POST'])
    def upload_device_software(device_id):
        device = db.devices.get_by_id(device_id)
        if not device:
            return jsonify({'error': 'Device not found'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        software_list = data.get('software', [])
        if not isinstance(software_list, list):
            return jsonify({'error': 'Software must be a list'}), 400

        try:
            db.device_software.upsert_software_list(device_id, software_list)
            return jsonify({
                'message': 'Software list updated successfully',
                'deviceId': device_id,
                'count': len(software_list)
            })
        except Exception as e:
            return jsonify({'error': f'Failed to update software list: {str(e)}'}), 500

    # ========== 设备课表配置 API ==========

    @devices_bp.route('/<path:device_id>/schedule-config', methods=['GET'])
    def get_device_schedule_config(device_id):
        """获取设备的课表配置（优先设备专属，回退到组织默认）"""
        device = db.devices.get_by_id(device_id)
        if not device:
            return jsonify({'error': 'Device not found'}), 404

        schedule = db.devices.get_schedule_config(device_id)
        if schedule:
            return jsonify(schedule)
        return jsonify({
            'weeklyCycleCount': 4,
            'termStartDate': None,
            'weeklies': [],
            '_source': 'default'
        })

    @devices_bp.route('/<path:device_id>/schedule-config', methods=['PUT'])
    @token_required
    def update_device_schedule_config(user, device_id):
        """设置设备专属课表配置并推送到该设备"""
        if user['role'] not in ['super_admin', 'admin']:
            return jsonify({'error': '权限不足，无法更新设备课表'}), 403

        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        device = db.devices.get_by_id(device_id)
        if not device:
            return jsonify({'error': 'Device not found'}), 404

        db.devices.save_schedule_config(device_id, data)

        # 通过WebSocket推送课表到该设备
        try:
            import websocket_service
            if websocket_service.ws_service:
                websocket_service.ws_service.push_schedule_to_device(device_id, data)
        except Exception as e:
            print(f"[Schedule] 推送课表到设备失败: {e}")

        db.activity_logs.create(
            account_id=user['id'],
            account_username=user['username'],
            action_type='update',
            action_category='schedule',
            description=f'用户 {user["username"]} 更新了设备 {device.get("name", device_id)} 的课表配置',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )

        return jsonify({'message': '设备课表配置已保存并推送', 'success': True})

    @devices_bp.route('/<path:device_id>/schedule-config', methods=['DELETE'])
    @token_required
    def delete_device_schedule_config(user, device_id):
        """删除设备专属课表配置（恢复使用组织默认）"""
        if user['role'] not in ['super_admin', 'admin']:
            return jsonify({'error': '权限不足'}), 403

        device = db.devices.get_by_id(device_id)
        if not device:
            return jsonify({'error': 'Device not found'}), 404

        db.devices.delete_schedule_config(device_id)

        # 推送组织默认课表到设备
        try:
            if device.get('organization_id'):
                org_schedule = db.organizations.get_schedule_config(device['organization_id'])
                if org_schedule:
                    import websocket_service
                    if websocket_service.ws_service:
                        websocket_service.ws_service.push_schedule_to_device(device_id, org_schedule)
        except Exception as e:
            print(f"[Schedule] 推送回退课表失败: {e}")

        return jsonify({'message': '设备课表配置已删除，恢复使用组织默认', 'success': True})

    return devices_bp
