def format_account(account):
    return {
        'id': account['id'],
        'username': account['username'],
        'role': account['role'],
        'createdAt': account['created_at'],
        'lastLoginAt': account['last_login_at'],
        'isActive': bool(account['is_active'])
    }


def convert_organization_fields(organization):
    if not organization:
        return None

    converted = dict(organization)

    field_mapping = {
        'created_at': 'createdAt',
        'server_url': 'serverUrl'
    }

    for db_field, frontend_field in field_mapping.items():
        if db_field in converted:
            converted[frontend_field] = converted[db_field]
            del converted[db_field]

    return converted


def convert_device_fields(device):
    if not device:
        return None

    converted = dict(device)

    field_mapping = {
        'last_heartbeat': 'lastHeartbeat',
        'last_seen': 'lastSeen',
        'exit_time': 'exitTime',
        'offline_reason': 'offlineReason',
        'contact_phone': 'contactPhone',
        'class_name': 'className',
        'person_in_charge': 'personInCharge',
        'cpu_usage': 'cpuUsage',
        'memory_usage': 'memoryUsage',
        'disk_usage': 'diskUsage',
        'os_version': 'osVersion',
        'app_version': 'appVersion',
        'dotnet_version': 'dotnetVersion',
        'organization_id': 'organizationId',
        'mac_address': 'macAddress',
        'ip_address': 'ipAddress',
        'registered_at': 'registeredAt'
    }

    for db_field, frontend_field in field_mapping.items():
        if db_field in converted:
            converted[frontend_field] = converted[db_field]
            del converted[db_field]

    return converted


def format_activity_log(log):
    return {
        'id': log['id'],
        'accountId': log['account_id'],
        'accountUsername': log['account_username'],
        'actionType': log['action_type'],
        'actionCategory': log['action_category'],
        'description': log['description'],
        'ipAddress': log['ip_address'],
        'userAgent': log['user_agent'],
        'createdAt': log['created_at']
    }
