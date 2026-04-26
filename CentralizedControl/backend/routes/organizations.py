from flask import Blueprint, request, jsonify
from utils.converters import convert_organization_fields, convert_device_fields
from middleware.permissions import require_action_permission


def create_organizations_routes(db, token_required):
    orgs_bp = Blueprint('organizations', __name__, url_prefix='/api/organizations')

    @orgs_bp.route('', methods=['GET'])
    @token_required
    def get_organizations(user):
        organizations = db.organizations.get_all()
        converted_organizations = [convert_organization_fields(org) for org in organizations]
        return jsonify(converted_organizations)

    @orgs_bp.route('/with-device-counts', methods=['GET'])
    @token_required
    def get_organizations_with_device_counts(user):
        organizations = db.organizations.get_all_with_device_counts()
        converted_organizations = [convert_organization_fields(org) for org in organizations]
        return jsonify(converted_organizations)

    @orgs_bp.route('', methods=['POST'])
    @token_required
    @require_action_permission(db, 'org', 'create')
    def create_organization(user):
        if user['role'] not in ['super_admin', 'admin']:
            return jsonify({'error': '权限不足，无法创建组织'}), 403

        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        name = data.get('name')
        description = data.get('description')

        if not name:
            return jsonify({'error': 'Name is required'}), 400

        org_id = db.organizations.create(name, description)
        
        db.activity_logs.create(
            account_id=user['id'],
            account_username=user['username'],
            action_type='create',
            action_category='organization',
            description=f'用户 {user["username"]} 创建组织 {name}',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        organization = db.organizations.get_by_id(org_id)
        converted_organization = convert_organization_fields(organization)
        return jsonify(converted_organization), 201

    @orgs_bp.route('/<org_id>', methods=['GET'])
    def get_organization(org_id):
        organization = db.organizations.get_by_id(org_id)
        if not organization:
            return jsonify({'error': 'Organization not found'}), 404
        converted_organization = convert_organization_fields(organization)
        return jsonify(converted_organization)

    @orgs_bp.route('/<org_id>', methods=['PUT'])
    @token_required
    @require_action_permission(db, 'org', 'edit')
    def update_organization(user, org_id):
        if user['role'] not in ['super_admin', 'admin']:
            return jsonify({'error': '权限不足，无法更新组织'}), 403

        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        name = data.get('name')
        description = data.get('description')

        old_org = db.organizations.get_by_id(org_id)
        old_name = old_org.get('name') if old_org else org_id
        
        if not db.organizations.update(org_id, name=name, description=description):
            return jsonify({'error': 'Organization not found or no changes made'}), 404

        organization = db.organizations.get_by_id(org_id)
        
        db.activity_logs.create(
            account_id=user['id'],
            account_username=user['username'],
            action_type='update',
            action_category='organization',
            description=f'用户 {user["username"]} 更新组织 {old_name}',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        converted_organization = convert_organization_fields(organization)
        return jsonify(converted_organization)

    @orgs_bp.route('/<org_id>', methods=['DELETE'])
    @token_required
    @require_action_permission(db, 'org', 'delete')
    def delete_organization(user, org_id):
        if user['role'] not in ['super_admin', 'admin']:
            return jsonify({'error': '权限不足，无法删除组织'}), 403

        org = db.organizations.get_by_id(org_id)
        if not org:
            return jsonify({'error': 'Organization not found'}), 404

        org_name = org.get('name', org_id)
        
        db.organizations.delete(org_id)
        
        db.activity_logs.create(
            account_id=user['id'],
            account_username=user['username'],
            action_type='delete',
            action_category='organization',
            description=f'用户 {user["username"]} 删除组织 {org_name}',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )

        return jsonify({'message': 'Organization deleted successfully'})

    @orgs_bp.route('/<org_id>/devices', methods=['GET'])
    @token_required
    def get_organization_devices(user, org_id):
        devices = db.devices.get_by_organization(org_id)
        return jsonify([convert_device_fields(device) for device in devices])

    @orgs_bp.route('/<org_id>/devices', methods=['POST'])
    def add_device_to_organization(org_id):
        organization = db.organizations.get_by_id(org_id)
        if not organization:
            return jsonify({'error': 'Organization not found'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        name = data.get('name')
        ip_address = data.get('ipAddress') or data.get('ip_address')
        mac_address = data.get('macAddress') or data.get('mac_address')
        os_version = data.get('osVersion') or data.get('os_version')
        app_version = data.get('appVersion') or data.get('app_version')
        dotnet_version = data.get('dotnetVersion') or data.get('dotnet_version')
        contact_phone = data.get('contactPhone') or data.get('contact_phone')
        class_name = data.get('className') or data.get('class_name')
        person_in_charge = data.get('personInCharge') or data.get('person_in_charge')
        device_id = data.get('id')

        if not name:
            return jsonify({'error': 'Device name is required'}), 400

        from datetime import datetime
        now = datetime.now().isoformat()

        created_device_id = db.devices.create(
            name=name,
            ip_address=ip_address or '',
            organization_id=org_id,
            device_id=device_id,
            mac_address=mac_address,
            os_version=os_version,
            app_version=app_version,
            dotnet_version=dotnet_version,
            contact_phone=contact_phone,
            class_name=class_name,
            person_in_charge=person_in_charge
        )

        db.devices.update(created_device_id, status='online', last_heartbeat=now, last_seen=now)

        device = db.devices.get_by_id(created_device_id)
        return jsonify(convert_device_fields(device)), 201

    @orgs_bp.route('/<org_id>/security-config', methods=['GET'])
    def get_security_config(org_id):
        config = db.organizations.get_config(org_id)
        if config and config.get('security_config'):
            return jsonify(config['security_config'])
        return jsonify({
            'admin': {
                'adminUsername': 'admin',
                'password': ''
            },
            'accounts': [],
            'security': {
                'isTwoFactorEnabled': False,
                'twoFactorSecret': '',
                'loginVerificationMode': 0
            },
            'permissions': {
                'allowTaskManager': False,
                'allowRegistryEditor': False,
                'allowCommandLine': False,
                'allowFileExplorer': False,
                'allowControlPanel': False,
                'allowSettings': False,
                'allowEdgeBrowser': False,
                'allowScreenshot': False,
                'allowClipboard': False,
                'allowPrint': False,
                'allowUSB': False,
                'allowNetwork': False
            },
            'network': {
                'enabled': True,
                'mode': 'blacklist',
                'domainRules': []
            }
        })

    @orgs_bp.route('/<org_id>/security-config', methods=['PUT'])
    def update_security_config(org_id):
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        organization = db.organizations.get_by_id(org_id)
        if not organization:
            return jsonify({'error': 'Organization not found'}), 404

        existing_config = db.organizations.get_config(org_id)
        security_config = existing_config.get('security_config') if existing_config else None
        network_config = existing_config.get('network_config') if existing_config else None

        if 'security' in data or 'admin' in data or 'permissions' in data or 'accounts' in data:
            security_config = {
                'admin': data.get('admin', {}),
                'accounts': data.get('accounts', []),
                'security': data.get('security', {}),
                'permissions': data.get('permissions', {})
            }

        if 'network' in data or 'enabled' in data or 'mode' in data or 'domainRules' in data:
            network_config = {
                'enabled': data.get('enabled', True),
                'mode': data.get('mode', 'blacklist'),
                'domainRules': data.get('domainRules', [])
            }

        db.organizations.save_config(org_id, security_config, network_config)
        updated_config = db.organizations.get_config(org_id)
        return jsonify(updated_config.get('security_config', {}))

    @orgs_bp.route('/<org_id>/network-config', methods=['GET'])
    def get_network_config(org_id):
        config = db.organizations.get_config(org_id)
        if config and config.get('network_config'):
            return jsonify(config['network_config'])
        return jsonify({
            'enabled': True,
            'mode': 'blacklist',
            'domainRules': []
        })

    @orgs_bp.route('/<org_id>/network-config', methods=['PUT'])
    def update_network_config(org_id):
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        organization = db.organizations.get_by_id(org_id)
        if not organization:
            return jsonify({'error': 'Organization not found'}), 404

        existing_config = db.organizations.get_config(org_id)
        security_config = existing_config.get('security_config') if existing_config else None

        network_config = {
            'enabled': data.get('enabled', True),
            'mode': data.get('mode', 'blacklist'),
            'domainRules': data.get('domainRules', [])
        }

        db.organizations.save_config(org_id, security_config, network_config)
        updated_config = db.organizations.get_config(org_id)
        return jsonify(updated_config.get('network_config', {}))

    return orgs_bp
