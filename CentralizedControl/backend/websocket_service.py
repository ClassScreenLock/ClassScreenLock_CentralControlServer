"""
WebSocket实时通信服务
替代HTTP轮询，实现高敏感度实时推送
"""

import threading
import time
from datetime import datetime
from flask import request
from flask_socketio import SocketIO, emit, join_room, leave_room, rooms


class WebSocketService:
    """WebSocket服务管理器"""
    
    def __init__(self, app, db, config):
        self.app = app
        self.db = db
        self.config = config
        
        # 创建SocketIO实例，支持WebSocket和长轮询fallback
        # 注意：threading 模式不支持真正的 WebSocket，只支持长轮询
        # 使用 eventlet 或 gevent 模式支持 WebSocket
        self.socketio = SocketIO(
            app,
            cors_allowed_origins="*",
            async_mode='threading',  # threading 模式仅支持长轮询
            ping_timeout=120,  # 增加到120秒
            ping_interval=30,  # 每30秒发送ping
            max_http_buffer_size=10 * 1024 * 1024,  # 10MB
            transports=['polling']  # 强制使用长轮询，避免 WebSocket 升级失败
        )
        
        # 设备连接映射: {device_id: sid}
        self.device_connections = {}
        # 前端连接映射: {sid: user_info}
        self.frontend_connections = {}
        # 组织房间映射: {org_id: [sids]}
        self.organization_rooms = {}
        
        # 注册事件处理器
        self._register_handlers()
        
        # 启动后台任务
        self._start_background_tasks()
    
    def _register_handlers(self):
        """注册WebSocket事件处理器"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """客户端连接"""
            print(f"[WebSocket] 客户端连接: {request.sid}, 来自: {request.remote_addr}")
            print(f"[WebSocket] 当前 device_connections({len(self.device_connections)}): {list(self.device_connections.keys())}")
            emit('connected', {'message': 'WebSocket连接成功', 'timestamp': datetime.now().isoformat()})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """客户端断开"""
            sid = request.sid
            print(f"[WebSocket] 客户端断开: {sid}")
            
            # 清理设备连接（不立即标记为离线，等待心跳超时检测）
            # 这样 HTTP 心跳兜底机制可以保持设备在线
            for device_id, device_sid in list(self.device_connections.items()):
                if device_sid == sid:
                    del self.device_connections[device_id]
                    # 不立即标记为离线，由心跳超时检测线程处理
                    # 如果 HTTP 心跳在发送，设备会保持在线
                    print(f"[WebSocket] 设备 {device_id} 连接断开，等待心跳超时检测")
                    break
            
            # 清理前端连接
            if sid in self.frontend_connections:
                user_info = self.frontend_connections[sid]
                del self.frontend_connections[sid]
                # 离开组织房间
                if 'organization_id' in user_info:
                    leave_room(f'org_{user_info["organization_id"]}')
        
        @self.socketio.on('device_register')
        def handle_device_register(*args):
            """设备注册WebSocket连接"""
            # 支持两种格式：对象格式或参数格式
            if len(args) == 1 and isinstance(args[0], dict):
                data = args[0]
                device_id = data.get('deviceId')
                organization_id = data.get('organizationId')
            elif len(args) >= 2:
                # 参数格式: deviceId, organizationId, deviceName, ipAddress, macAddress
                device_id = args[0]
                organization_id = args[1]
            else:
                emit('error', {'message': '无效的注册数据格式'})
                return
            
            if not device_id:
                emit('error', {'message': '缺少设备ID'})
                return
            
            # 注册设备连接
            self.device_connections[device_id] = request.sid

            # 设备始终加入自己的房间（用于点对点推送）
            join_room(f'device_{device_id}')
            # 加入组织房间
            if organization_id:
                join_room(f'org_{organization_id}')
            
            # 更新设备状态为在线
            now = datetime.now().isoformat()
            self.db.devices.update(
                device_id,
                status='online',
                last_seen=now,
                last_heartbeat=now
            )
            
            # 推送设备上线通知到前端
            self._broadcast_device_status(device_id, 'online')
            
            emit('device_registered', {
                'deviceId': device_id,
                'status': 'online',
                'timestamp': now
            })
            
            print(f"[WebSocket] 设备注册成功: {device_id}")
        
        @self.socketio.on('device_heartbeat')
        def handle_device_heartbeat(*args):
            """设备心跳（WebSocket实时心跳）"""
            # 支持两种格式：对象格式或参数格式
            if len(args) == 1 and isinstance(args[0], dict):
                data = args[0]
                device_id = data.get('deviceId')
                cpu_usage = data.get('cpuUsage', 0)
                memory_usage = data.get('memoryUsage', 0)
                disk_usage = data.get('diskUsage', 0)
                device_name = data.get('deviceName')
                ip_address = data.get('ipAddress')
            elif len(args) >= 2:
                # 参数格式: deviceId, deviceName, ipAddress, cpuUsage, memoryUsage, diskUsage
                device_id = args[0]
                device_name = args[1] if len(args) > 1 else None
                ip_address = args[2] if len(args) > 2 else None
                cpu_usage = args[3] if len(args) > 3 else 0
                memory_usage = args[4] if len(args) > 4 else 0
                disk_usage = args[5] if len(args) > 5 else 0
            else:
                return
            
            if not device_id:
                return
            
            # 更新心跳时间
            now = datetime.now().isoformat()
            heartbeat_data = {
                'status': 'online',
                'cpu_usage': cpu_usage,
                'memory_usage': memory_usage,
                'disk_usage': disk_usage,
                'last_heartbeat': now,
                'last_seen': now,
                'device_name': device_name,
                'ip_address': ip_address
            }
            
            self.db.devices.update(device_id, **heartbeat_data)
            
            # 实时推送设备状态到前端
            self._broadcast_device_status(device_id, 'online', heartbeat_data)
            
            # 响应心跳确认
            emit('heartbeat_ack', {
                'timestamp': now,
                'config_updated': self._check_config_update(device_id)
            })
        
        @self.socketio.on('device_offline')
        def handle_device_offline(*args):
            """设备离线通知"""
            # 支持两种格式：对象格式或参数格式
            if len(args) == 1 and isinstance(args[0], dict):
                data = args[0]
                device_id = data.get('deviceId')
                reason = data.get('reason', 'user_logout')
            elif len(args) >= 2:
                device_id = args[0]
                reason = args[1] if len(args) > 1 else 'user_logout'
            else:
                return
            
            if not device_id:
                return
            
            now = datetime.now().isoformat()
            self.db.devices.update(
                device_id,
                status='offline',
                offline_reason=reason,
                exit_time=now
            )
            
            # 推送设备离线通知
            self._broadcast_device_status(device_id, 'offline', reason)
            
            print(f"[WebSocket] 设备离线: {device_id}, 原因: {reason}")
        
        @self.socketio.on('frontend_auth')
        def handle_frontend_auth(data):
            """前端认证连接"""
            token = data.get('token')
            
            if not token:
                emit('error', {'message': '缺少认证令牌'})
                return
            
            # 验证token
            user = self._verify_token(token)
            if not user:
                emit('error', {'message': '认证失败'})
                return
            
            # 注册前端连接
            self.frontend_connections[request.sid] = {
                'user_id': user['id'],
                'username': user['username'],
                'role': user['role'],
                'organization_id': data.get('organizationId')
            }
            
            # 加入全局房间
            join_room('frontend')
            
            # 如果有组织ID，加入组织房间
            org_id = data.get('organizationId')
            if org_id:
                join_room(f'org_{org_id}')
            
            emit('frontend_authenticated', {
                'user': user['username'],
                'role': user['role'],
                'timestamp': datetime.now().isoformat()
            })
            
            print(f"[WebSocket] 前端认证成功: {user['username']}")
        
        @self.socketio.on('subscribe_devices')
        def handle_subscribe_devices(data):
            """订阅设备状态更新"""
            organization_id = data.get('organizationId')
            
            if organization_id:
                join_room(f'org_{organization_id}')
            else:
                join_room('all_devices')
            
            emit('subscribed', {'room': f'org_{organization_id}' if organization_id else 'all_devices'})
        
        @self.socketio.on('subscribe_activity_logs')
        def handle_subscribe_activity_logs(data):
            """订阅活动日志"""
            join_room('activity_logs')
            emit('subscribed', {'room': 'activity_logs'})
        
        @self.socketio.on('request_config_sync')
        def handle_request_config_sync(data):
            """请求配置同步"""
            device_id = data.get('deviceId')
            organization_id = data.get('organizationId')
            
            if not device_id or not organization_id:
                return
            
            # 获取最新配置
            config = self._get_device_config(organization_id)
            
            emit('config_update', {
                'deviceId': device_id,
                'config': config,
                'timestamp': datetime.now().isoformat()
            })

        @self.socketio.on('request_schedule_sync')
        def handle_request_schedule_sync(data):
            """被控端请求课表同步"""
            device_id = data.get('deviceId')
            organization_id = data.get('organizationId')

            if not device_id:
                return

            # 优先获取设备专属课表，回退到组织课表
            schedule = self.db.devices.get_schedule_config(device_id)
            if not schedule and organization_id:
                schedule = self.db.organizations.get_schedule_config(organization_id)

            if schedule:
                emit('schedule_update', {
                    'deviceId': device_id,
                    'schedule': schedule,
                    'timestamp': datetime.now().isoformat()
                })
                print(f"[WebSocket] 课表同步响应已发送到设备 {device_id}")
            else:
                emit('schedule_update', {
                    'deviceId': device_id,
                    'schedule': {
                        'weeklyCycleCount': 4,
                        'termStartDate': None,
                        'weeklies': []
                    },
                    'timestamp': datetime.now().isoformat()
                })
        
        @self.socketio.on('request_device_list')
        def handle_request_device_list(data):
            """请求设备列表"""
            organization_id = data.get('organizationId')

            if organization_id:
                devices = self.db.devices.get_by_organization(organization_id)
            else:
                devices = self.db.devices.get_all()

            emit('device_list', {
                'devices': devices,
                'timestamp': datetime.now().isoformat()
            })

        @self.socketio.on('send_message')
        def handle_send_message(data):
            """集控端向被控设备发送消息（通过WebSocket转发）

            数据格式:
            {
                'deviceId': '<device_id>',
                'message': '<消息内容>',
                'readAloud': True/False,
                'sender': '<发送者用户名，可选>',
                'size': 'small' | 'medium' | 'large' | 'xlarge'（默认 small）,
                'fontSize': 'small' | 'medium' | 'large' | 'xlarge'（默认 medium）,
                'durationMode': 'auto' | 'short' | 'medium' | 'long' | 'custom' | 'persistent'（默认 auto）,
                'customDurationSeconds': <int>（仅 durationMode=custom 时使用，默认 10）,
                'lockWindow': <bool>（默认 false，true 时在通知期间禁止关闭窗口）
            }
            """
            if not isinstance(data, dict):
                emit('message_sent', {'success': False, 'message': '无效的数据格式'})
                return

            device_id = data.get('deviceId')
            message_text = data.get('message')
            read_aloud = bool(data.get('readAloud', False))
            sender = data.get('sender') or ''
            size = (data.get('size') or 'small').lower()
            font_size = (data.get('fontSize') or 'medium').lower()
            duration_mode = (data.get('durationMode') or 'auto').lower()
            custom_duration_seconds = int(data.get('customDurationSeconds') or 10)
            lock_window = bool(data.get('lockWindow', False))

            # 参数校验
            if size not in ('small', 'medium', 'large', 'xlarge'):
                size = 'small'
            if font_size not in ('small', 'medium', 'large', 'xlarge'):
                font_size = 'medium'
            if duration_mode not in ('auto', 'short', 'medium', 'long', 'custom', 'persistent'):
                duration_mode = 'auto'
            custom_duration_seconds = max(5, min(60, custom_duration_seconds))

            if not device_id:
                emit('message_sent', {'success': False, 'message': '缺少设备ID'})
                return

            if not message_text or not str(message_text).strip():
                emit('message_sent', {'success': False, 'message': '消息内容不能为空'})
                return

            # 获取发送者信息（如果未提供 sender，从已认证的前端连接中获取）
            sender_info = sender
            if not sender_info:
                user_info = self.frontend_connections.get(request.sid)
                if user_info:
                    sender_info = user_info.get('username', '')

            ok = self.push_message_to_device(device_id, message_text, read_aloud, sender_info,
                                             size=size, font_size=font_size,
                                             duration_mode=duration_mode,
                                             custom_duration_seconds=custom_duration_seconds,
                                             lock_window=lock_window)

            if not ok:
                print(f"[WebSocket] 消息推送失败：设备 {device_id} 未在WS连接中。"
                      f"当前在线设备({len(self.device_connections)}): "
                      f"{list(self.device_connections.keys())}")

            # 记录活动日志
            try:
                device = self.db.devices.get_by_id(device_id)
                device_name = device.get('name', device_id) if device else device_id
                user_info = self.frontend_connections.get(request.sid)
                if user_info:
                    self.db.activity_logs.create(
                        account_id=user_info.get('user_id'),
                        account_username=user_info.get('username', ''),
                        action_type='send_message',
                        action_category='device',
                        description=f"用户 {user_info.get('username', '')} 向设备 {device_name} 发送消息：{message_text[:100]}",
                        ip_address=request.remote_addr,
                        user_agent=request.headers.get('User-Agent')
                    )
            except Exception as e:
                print(f"[WebSocket] 记录消息日志失败: {e}")

            emit('message_sent', {
                'success': ok,
                'deviceId': device_id,
                'message': '消息已发送' if ok else '设备WebSocket未连接，无法推送消息（设备可能仅通过HTTP心跳在线）',
                'timestamp': datetime.now().isoformat()
            })

        @self.socketio.on('screen_monitor_frame')
        def handle_screen_monitor_frame(*args):
            """被控端推送的屏幕帧（实时画面数据）。

            C# 客户端发送格式（按位置）: [deviceId, timestampMs, format, width, height, base64Data]
            也支持对象格式: {deviceId, timestamp, format, width, height, data}
            """
            try:
                device_id = None
                timestamp_ms = 0
                fmt = 'jpeg'
                width = 0
                height = 0
                data = None

                if len(args) == 1 and isinstance(args[0], dict):
                    payload = args[0]
                    device_id = payload.get('deviceId') or payload.get('device_id')
                    timestamp_ms = int(payload.get('timestamp', 0) or 0)
                    fmt = payload.get('format', 'jpeg') or 'jpeg'
                    width = int(payload.get('width', 0) or 0)
                    height = int(payload.get('height', 0) or 0)
                    data = payload.get('data') or payload.get('base64')
                elif len(args) >= 6:
                    device_id = args[0]
                    timestamp_ms = int(args[1] or 0)
                    fmt = args[2] or 'jpeg'
                    try:
                        width = int(args[3] or 0)
                    except (TypeError, ValueError):
                        width = 0
                    try:
                        height = int(args[4] or 0)
                    except (TypeError, ValueError):
                        height = 0
                    data = args[5]
                else:
                    return

                if not device_id or not data:
                    return

                # 限制单帧大小（base64 解码后最大 ~16MB），超过则丢弃
                if isinstance(data, str) and len(data) > 16 * 1024 * 1024:
                    print(f"[WebSocket] 屏幕帧过大，已丢弃 device={device_id} size={len(data)}")
                    return

                # 增强：补充设备名/IP
                device_name = None
                ip_address = None
                try:
                    dev = self.db.devices.get_by_id(device_id)
                    if dev:
                        device_name = dev.get('name') or dev.get('device_name')
                        ip_address = dev.get('ip_address')
                except Exception:
                    pass

                frame_payload = {
                    'deviceId': device_id,
                    'deviceName': device_name or device_id,
                    'ipAddress': ip_address,
                    'timestamp': timestamp_ms,
                    'format': fmt,
                    'width': width,
                    'height': height,
                    'data': data
                }

                # 转发到所有已认证的前端
                self.socketio.emit('screen_monitor_frame', frame_payload, room='frontend')
                # 每 50 帧打印一次日志（避免刷屏）
                if not hasattr(handle_screen_monitor_frame, '_frame_count'):
                    handle_screen_monitor_frame._frame_count = 0
                handle_screen_monitor_frame._frame_count += 1
                if handle_screen_monitor_frame._frame_count % 50 == 1:
                    print(f"[WebSocket] 已转发 {handle_screen_monitor_frame._frame_count} 帧 | device={device_id} {width}x{height} size={len(str(data)) if data else 0}")
            except Exception as e:
                print(f"[WebSocket] 处理 screen_monitor_frame 失败: {e}")

        @self.socketio.on('screen_monitor_status')
        def handle_screen_monitor_status(*args):
            """被控端推送的屏幕监控状态变化。

            C# 客户端发送格式（按位置）: [deviceId, isStreaming, error]
            或对象格式: {deviceId, isStreaming, error}
            """
            try:
                device_id = None
                is_streaming = False
                error = None

                if len(args) == 1 and isinstance(args[0], dict):
                    payload = args[0]
                    device_id = payload.get('deviceId') or payload.get('device_id')
                    is_streaming = bool(payload.get('isStreaming', False))
                    error = payload.get('error') or None
                elif len(args) >= 2:
                    device_id = args[0]
                    is_streaming = bool(args[1])
                    error = args[2] if len(args) > 2 and args[2] else None
                else:
                    return

                if not device_id:
                    return

                status_payload = {
                    'deviceId': device_id,
                    'isStreaming': is_streaming,
                    'error': error or '',
                    'timestamp': datetime.now().isoformat()
                }

                self.socketio.emit('screen_monitor_status', status_payload, room='frontend')
            except Exception as e:
                print(f"[WebSocket] 处理 screen_monitor_status 失败: {e}")

        @self.socketio.on('screen_monitor_start')
        def handle_screen_monitor_start(*args):
            """集控端 → 指定被控端：发起屏幕监控。

            客户端发送格式（按位置）: [sourceDeviceId, targetDeviceId, fps, jpegQuality, maxWidth, monitorIndex]
            或对象格式: {sourceDeviceId, targetDeviceId, fps, jpegQuality, maxWidth, monitorIndex}
            """
            try:
                source_id = None
                target_id = None
                fps = 10
                jpeg_quality = 60
                max_width = 1280
                monitor_index = 0

                if len(args) == 1 and isinstance(args[0], dict):
                    payload = args[0]
                    source_id = payload.get('sourceDeviceId') or payload.get('sourceId') or payload.get('userId')
                    target_id = payload.get('targetDeviceId') or payload.get('deviceId') or payload.get('targetId')
                    fps = int(payload.get('fps', 10) or 10)
                    jpeg_quality = int(payload.get('jpegQuality', 60) or 60)
                    max_width = int(payload.get('maxWidth', 1280) or 1280)
                    monitor_index = int(payload.get('monitorIndex', 0) or 0)
                elif len(args) >= 6:
                    source_id = args[0]
                    target_id = args[1]
                    try:
                        fps = int(args[2] or 10)
                        jpeg_quality = int(args[3] or 60)
                        max_width = int(args[4] or 1280)
                        monitor_index = int(args[5] or 0)
                    except (TypeError, ValueError):
                        pass
                else:
                    emit('screen_monitor_start_ack', {'success': False, 'message': '无效的请求参数'})
                    return

                if not target_id:
                    emit('screen_monitor_start_ack', {'success': False, 'message': '缺少目标设备ID'})
                    return

                fps = max(1, min(30, fps))
                jpeg_quality = max(1, min(100, jpeg_quality))
                max_width = max(0, min(7680, max_width))
                monitor_index = max(0, monitor_index)

                # 转发到目标设备的房间
                if target_id not in self.device_connections:
                    emit('screen_monitor_start_ack', {
                        'success': False,
                        'deviceId': target_id,
                        'message': '目标设备未连接到WebSocket'
                    })
                    return

                # C# 客户端按位置接收: [fps, jpegQuality, maxWidth, monitorIndex]
                self.socketio.emit('screen_monitor_start', {
                    'fps': fps,
                    'jpegQuality': jpeg_quality,
                    'maxWidth': max_width,
                    'monitorIndex': monitor_index
                }, room=f'device_{target_id}')

                emit('screen_monitor_start_ack', {
                    'success': True,
                    'deviceId': target_id,
                    'fps': fps,
                    'jpegQuality': jpeg_quality,
                    'maxWidth': max_width,
                    'monitorIndex': monitor_index,
                    'timestamp': datetime.now().isoformat()
                })

                print(f"[WebSocket] 集控端 {source_id} 向 {target_id} 发起屏幕监控: "
                      f"fps={fps}, q={jpeg_quality}, w={max_width}, m={monitor_index}")
            except Exception as e:
                print(f"[WebSocket] 处理 screen_monitor_start 失败: {e}")
                emit('screen_monitor_start_ack', {'success': False, 'message': str(e)})

        @self.socketio.on('screen_monitor_stop')
        def handle_screen_monitor_stop(*args):
            """集控端 → 指定被控端：停止屏幕监控。"""
            try:
                source_id = None
                target_id = None

                if len(args) == 1 and isinstance(args[0], dict):
                    payload = args[0]
                    source_id = payload.get('sourceDeviceId') or payload.get('sourceId') or payload.get('userId')
                    target_id = payload.get('targetDeviceId') or payload.get('deviceId') or payload.get('targetId')
                elif len(args) >= 2:
                    source_id = args[0]
                    target_id = args[1]
                else:
                    emit('screen_monitor_stop_ack', {'success': False, 'message': '无效的请求参数'})
                    return

                if not target_id:
                    emit('screen_monitor_stop_ack', {'success': False, 'message': '缺少目标设备ID'})
                    return

                if target_id not in self.device_connections:
                    emit('screen_monitor_stop_ack', {
                        'success': False,
                        'deviceId': target_id,
                        'message': '目标设备未连接到WebSocket'
                    })
                    return

                self.socketio.emit('screen_monitor_stop', {}, room=f'device_{target_id}')

                emit('screen_monitor_stop_ack', {
                    'success': True,
                    'deviceId': target_id,
                    'timestamp': datetime.now().isoformat()
                })

                print(f"[WebSocket] 集控端 {source_id} 通知 {target_id} 停止屏幕监控")
            except Exception as e:
                print(f"[WebSocket] 处理 screen_monitor_stop 失败: {e}")
                emit('screen_monitor_stop_ack', {'success': False, 'message': str(e)})

        @self.socketio.on('screen_monitor_settings')
        def handle_screen_monitor_settings(*args):
            """集控端 → 指定被控端：动态调整参数（不中断流）。"""
            try:
                source_id = None
                target_id = None
                fps = 10
                jpeg_quality = 60
                max_width = 1280

                if len(args) == 1 and isinstance(args[0], dict):
                    payload = args[0]
                    source_id = payload.get('sourceDeviceId') or payload.get('sourceId') or payload.get('userId')
                    target_id = payload.get('targetDeviceId') or payload.get('deviceId') or payload.get('targetId')
                    fps = int(payload.get('fps', 10) or 10)
                    jpeg_quality = int(payload.get('jpegQuality', 60) or 60)
                    max_width = int(payload.get('maxWidth', 1280) or 1280)
                elif len(args) >= 5:
                    source_id = args[0]
                    target_id = args[1]
                    try:
                        fps = int(args[2] or 10)
                        jpeg_quality = int(args[3] or 60)
                        max_width = int(args[4] or 1280)
                    except (TypeError, ValueError):
                        pass
                else:
                    emit('screen_monitor_settings_ack', {'success': False, 'message': '无效的请求参数'})
                    return

                if not target_id:
                    emit('screen_monitor_settings_ack', {'success': False, 'message': '缺少目标设备ID'})
                    return

                fps = max(1, min(30, fps))
                jpeg_quality = max(1, min(100, jpeg_quality))
                max_width = max(0, min(7680, max_width))

                if target_id not in self.device_connections:
                    emit('screen_monitor_settings_ack', {
                        'success': False,
                        'deviceId': target_id,
                        'message': '目标设备未连接到WebSocket'
                    })
                    return

                self.socketio.emit('screen_monitor_settings', {
                    'fps': fps,
                    'jpegQuality': jpeg_quality,
                    'maxWidth': max_width
                }, room=f'device_{target_id}')

                emit('screen_monitor_settings_ack', {
                    'success': True,
                    'deviceId': target_id,
                    'fps': fps,
                    'jpegQuality': jpeg_quality,
                    'maxWidth': max_width,
                    'timestamp': datetime.now().isoformat()
                })

                print(f"[WebSocket] 集控端 {source_id} 向 {target_id} 推送屏幕参数: "
                      f"fps={fps}, q={jpeg_quality}, w={max_width}")
            except Exception as e:
                print(f"[WebSocket] 处理 screen_monitor_settings 失败: {e}")
                emit('screen_monitor_settings_ack', {'success': False, 'message': str(e)})

        @self.socketio.on('screen_monitor_settings_applied')
        def handle_screen_monitor_settings_applied(*args):
            """被控端确认参数已实际生效 → 转发给集控端前端。"""
            try:
                device_id = None
                fps = 10
                jpeg_quality = 60
                max_width = 1280

                if len(args) == 1 and isinstance(args[0], dict):
                    payload = args[0]
                    device_id = payload.get('deviceId') or payload.get('device_id')
                    fps = int(payload.get('fps', 10) or 10)
                    jpeg_quality = int(payload.get('jpegQuality', 60) or 60)
                    max_width = int(payload.get('maxWidth', 1280) or 1280)
                elif len(args) >= 4:
                    device_id = args[0]
                    fps = int(args[1] or 10)
                    jpeg_quality = int(args[2] or 60)
                    max_width = int(args[3] or 1280)

                if not device_id:
                    return

                self.socketio.emit('screen_monitor_settings_applied', {
                    'success': True,
                    'deviceId': device_id,
                    'fps': fps,
                    'jpegQuality': jpeg_quality,
                    'maxWidth': max_width,
                    'timestamp': datetime.now().isoformat()
                }, room='frontend')
            except Exception as e:
                print(f"[WebSocket] 处理 screen_monitor_settings_applied 失败: {e}")

        @self.socketio.on('remote_lock')
        def handle_remote_lock(*args):
            """集控端 → 指定被控端：远程锁屏。"""
            try:
                source_id = None
                target_id = None

                if len(args) == 1 and isinstance(args[0], dict):
                    payload = args[0]
                    source_id = payload.get('sourceDeviceId') or payload.get('sourceId')
                    target_id = payload.get('targetDeviceId') or payload.get('deviceId') or payload.get('targetId')
                elif len(args) >= 2:
                    source_id = args[0]
                    target_id = args[1]

                if not target_id:
                    emit('remote_lock_ack', {'success': False, 'message': '缺少目标设备ID'})
                    return

                if target_id not in self.device_connections:
                    emit('remote_lock_ack', {'success': False, 'deviceId': target_id, 'message': '目标设备未连接'})
                    return

                self.socketio.emit('remote_lock', {}, room=f'device_{target_id}')
                emit('remote_lock_ack', {'success': True, 'deviceId': target_id, 'timestamp': datetime.now().isoformat()})
                print(f"[WebSocket] 集控端 {source_id} 向 {target_id} 发送远程锁屏")
            except Exception as e:
                print(f"[WebSocket] 处理 remote_lock 失败: {e}")
                emit('remote_lock_ack', {'success': False, 'message': str(e)})

        @self.socketio.on('remote_unlock')
        def handle_remote_unlock(*args):
            """集控端 → 指定被控端：远程解锁。"""
            try:
                source_id = None
                target_id = None

                if len(args) == 1 and isinstance(args[0], dict):
                    payload = args[0]
                    source_id = payload.get('sourceDeviceId') or payload.get('sourceId')
                    target_id = payload.get('targetDeviceId') or payload.get('deviceId') or payload.get('targetId')
                elif len(args) >= 2:
                    source_id = args[0]
                    target_id = args[1]

                if not target_id:
                    emit('remote_unlock_ack', {'success': False, 'message': '缺少目标设备ID'})
                    return

                if target_id not in self.device_connections:
                    emit('remote_unlock_ack', {'success': False, 'deviceId': target_id, 'message': '目标设备未连接'})
                    return

                self.socketio.emit('remote_unlock', {}, room=f'device_{target_id}')
                emit('remote_unlock_ack', {'success': True, 'deviceId': target_id, 'timestamp': datetime.now().isoformat()})
                print(f"[WebSocket] 集控端 {source_id} 向 {target_id} 发送远程解锁")
            except Exception as e:
                print(f"[WebSocket] 处理 remote_unlock 失败: {e}")
                emit('remote_unlock_ack', {'success': False, 'message': str(e)})

        @self.socketio.on('push_schedule_to_org')
        def handle_push_schedule_to_org(*args):
            """前端推送课表到组织内所有设备"""
            try:
                if len(args) == 1 and isinstance(args[0], dict):
                    data = args[0]
                    org_id = data.get('organizationId')
                    schedule = data.get('schedule')
                else:
                    return

                if not org_id or not schedule:
                    emit('error', {'message': '缺少组织ID或课表数据'})
                    return

                self.push_schedule_to_organization(org_id, schedule)
                emit('schedule_push_ack', {'success': True, 'organizationId': org_id, 'timestamp': datetime.now().isoformat()})
                print(f"[WebSocket] 前端推送课表到组织 {org_id}")
            except Exception as e:
                print(f"[WebSocket] push_schedule_to_org 失败: {e}")

        @self.socketio.on('push_schedule_to_device')
        def handle_push_schedule_to_device(*args):
            """前端推送课表到单个设备"""
            try:
                if len(args) == 1 and isinstance(args[0], dict):
                    data = args[0]
                    device_id = data.get('deviceId')
                    schedule = data.get('schedule')
                else:
                    return

                if not device_id or not schedule:
                    emit('error', {'message': '缺少设备ID或课表数据'})
                    return

                self.push_schedule_to_device(device_id, schedule)
                emit('schedule_push_ack', {'success': True, 'deviceId': device_id, 'timestamp': datetime.now().isoformat()})
                print(f"[WebSocket] 前端推送课表到设备 {device_id}")
            except Exception as e:
                print(f"[WebSocket] push_schedule_to_device 失败: {e}")

        @self.socketio.on('lock_state')
        def handle_lock_state(*args):
            """被控端推送锁屏状态变化 → 转发给前端。"""
            try:
                device_id = None
                is_locked = False

                if len(args) == 1 and isinstance(args[0], dict):
                    payload = args[0]
                    device_id = payload.get('deviceId') or payload.get('device_id')
                    is_locked = bool(payload.get('isLocked', False))
                elif len(args) >= 2:
                    device_id = args[0]
                    is_locked = bool(args[1])

                if not device_id:
                    return

                self.socketio.emit('lock_state', {
                    'deviceId': device_id,
                    'isLocked': is_locked,
                    'timestamp': datetime.now().isoformat()
                }, room='frontend')
            except Exception as e:
                print(f"[WebSocket] 处理 lock_state 失败: {e}")

    def _verify_token(self, token):
        """验证JWT token"""
        try:
            # 使用数据库的verify_token方法验证
            user = self.db.verify_token(token)
            return user
        except Exception as e:
            print(f"[WebSocket] Token验证失败: {e}")
            return None
    
    def _broadcast_device_status(self, device_id, status, extra_data=None):
        """广播设备状态变化到前端"""
        device = self.db.devices.get_by_id(device_id)
        if not device:
            return
        
        message = {
            'deviceId': device_id,
            'deviceName': device.get('name'),
            'status': status,
            'timestamp': datetime.now().isoformat()
        }
        
        if extra_data:
            message.update(extra_data)
        
        # 推送到所有前端
        self.socketio.emit('device_status_update', message, room='frontend')
        
        # 推送到组织房间
        org_id = device.get('organization_id')
        if org_id:
            self.socketio.emit('device_status_update', message, room=f'org_{org_id}')
    
    def _check_config_update(self, device_id):
        """检查配置是否需要更新"""
        device = self.db.devices.get_by_id(device_id)
        if not device:
            return False
        
        org_id = device.get('organization_id')
        if not org_id:
            return False
        
        # 检查配置版本或更新时间
        # 这里可以实现配置版本检查逻辑
        return False
    
    def _get_device_config(self, organization_id):
        """获取设备配置"""
        config = self.db.organizations.get_config(organization_id)
        return config or {}
    
    def push_config_to_device(self, device_id, config):
        """推送配置到指定设备"""
        if device_id in self.device_connections:
            sid = self.device_connections[device_id]
            self.socketio.emit('config_update', {
                'deviceId': device_id,
                'config': config,
                'timestamp': datetime.now().isoformat()
            }, room=f'device_{device_id}')
            return True
        return False

    def push_message_to_device(self, device_id, message, read_aloud=False, sender=None,
                                size='small', font_size='medium', duration_mode='auto', custom_duration_seconds=10,
                                lock_window=False):
        """向指定设备推送消息（集控端发送给被控设备）

        :param device_id: 设备ID
        :param message: 消息内容
        :param read_aloud: 是否朗读
        :param sender: 发送者用户名（可选）
        :param size: 横幅尺寸 small/medium/large/xlarge（默认 small）
        :param font_size: 文字大小 small/medium/large/xlarge（默认 medium，独立于尺寸）
        :param duration_mode: 持续时间模式 auto/short/medium/long/custom/persistent（默认 auto）
        :param custom_duration_seconds: 自定义持续秒数（仅 duration_mode=custom 时使用，默认 10）
        :param lock_window: 是否在通知时段禁止关闭窗口（默认 false）
        :return: 是否成功推送（设备在线）
        """
        if device_id not in self.device_connections:
            print(f"[WebSocket] push_message_to_device: 设备 {device_id} 不在线")
            return False

        payload = {
            'deviceId': device_id,
            'message': str(message),
            'readAloud': bool(read_aloud),
            'sender': sender or '',
            'size': size or 'small',
            'fontSize': font_size or 'medium',
            'durationMode': duration_mode or 'auto',
            'customDurationSeconds': int(custom_duration_seconds) if custom_duration_seconds else 10,
            'lockWindow': bool(lock_window),
            'timestamp': datetime.now().isoformat()
        }
        room_name = f'device_{device_id}'
        print(f"[WebSocket] push_message_to_device: 向房间 {room_name} 发送 device_message, "
              f"message='{message}', readAloud={read_aloud}, sender='{sender}', "
              f"size={payload['size']}, fontSize={payload['fontSize']}, "
              f"durationMode={payload['durationMode']}, "
              f"customDurationSeconds={payload['customDurationSeconds']}, "
              f"lockWindow={payload['lockWindow']}")
        # 直接发送对象（Socket.IO 客户端会接收到 [event_name, payload] 格式）
        self.socketio.emit('device_message', payload, room=room_name)
        print(f"[WebSocket] push_message_to_device: emit 完成")
        return True
    
    def push_config_to_organization(self, organization_id, config):
        """推送配置到组织内所有设备"""
        self.socketio.emit('config_update', {
            'organizationId': organization_id,
            'config': config,
            'timestamp': datetime.now().isoformat()
        }, room=f'org_{organization_id}')
    
    def push_activity_log(self, log_data):
        """推送活动日志到前端"""
        self.socketio.emit('activity_log', log_data, room='activity_logs')
        self.socketio.emit('activity_log', log_data, room='frontend')
    
    def push_notification(self, message, room=None):
        """推送通知"""
        if room:
            self.socketio.emit('notification', message, room=room)
        else:
            self.socketio.emit('notification', message)

    def push_schedule_to_device(self, device_id, schedule_config):
        """推送课表配置到指定设备"""
        if device_id in self.device_connections:
            self.socketio.emit('schedule_update', {
                'deviceId': device_id,
                'schedule': schedule_config,
                'timestamp': datetime.now().isoformat()
            }, room=f'device_{device_id}')
            print(f"[WebSocket] 课表已推送到设备 {device_id}")
            return True
        print(f"[WebSocket] 推送课表失败：设备 {device_id} 未连接")
        return False

    def push_schedule_to_organization(self, organization_id, schedule_config):
        """推送课表配置到组织内所有设备"""
        self.socketio.emit('schedule_update', {
            'organizationId': organization_id,
            'schedule': schedule_config,
            'timestamp': datetime.now().isoformat()
        }, room=f'org_{organization_id}')
        print(f"[WebSocket] 课表已推送到组织 {organization_id}")
        return True
    
    def _start_background_tasks(self):
        """启动后台任务"""
        # 心跳检查线程（WebSocket超时检测）
        heartbeat_thread = threading.Thread(target=self._heartbeat_checker, daemon=True)
        heartbeat_thread.start()
    
    def _heartbeat_checker(self):
        """WebSocket心跳超时检测"""
        while True:
            try:
                devices = self.db.devices.get_all()
                if not devices:
                    continue
                    
                now = datetime.now()
                
                for device in devices:
                    if not isinstance(device, dict):
                        time.sleep(10)
                        continue
                        
                    if device.get('status') == 'online':
                        last_heartbeat = device.get('last_heartbeat')
                        if last_heartbeat:
                            try:
                                # 处理不同格式的时间字符串
                                if isinstance(last_heartbeat, str):
                                    # 尝试多种格式解析
                                    try:
                                        last_time = datetime.fromisoformat(last_heartbeat.replace('Z', '+00:00'))
                                    except:
                                        # 尝试其他格式
                                        last_time = datetime.strptime(last_heartbeat.split('.')[0], '%Y-%m-%dT%H:%M:%S')
                                    
                                    diff = (now - last_time).total_seconds()
                                    
                                    # WebSocket超时时间更长（60秒）
                                    if diff > 60:
                                        device_id = device.get('id') or device.get('device_id')
                                        device_name = device.get('name') or device.get('device_name') or device_id
                                        self.db.devices.update(
                                            device_id,
                                            status='offline',
                                            offline_reason='ws_timeout'
                                        )
                                        self._broadcast_device_status(device_id, 'offline', 'ws_timeout')
                                        print(f"[WebSocket] 设备 {device_name} WebSocket超时")
                            except Exception as e:
                                print(f"[WebSocket] 解析心跳时间失败: {e}, 原始值: {last_heartbeat}")
            except Exception as e:
                print(f"[WebSocket] 心跳检查失败: {e}")
            
            time.sleep(10)
    
    def get_socketio(self):
        """获取SocketIO实例"""
        return self.socketio


# 模块级实例引用，由 app.py 在创建 WebSocketService 后赋值
ws_service = None  # type: WebSocketService|None
