from flask import Blueprint, request, jsonify
from utils.converters import format_activity_log


def create_activity_log_routes(db, token_required, require_action_permission):
    activity_log_bp = Blueprint('activity_logs', __name__, url_prefix='/api/activity-logs')

    @activity_log_bp.route('', methods=['GET'])
    @token_required
    @require_action_permission(db, 'systemLogs', 'view')
    def get_activity_logs(user):
        page = request.args.get('page')
        page_size = request.args.get('pageSize')
        limit = request.args.get('limit')
        category = request.args.get('category')
        action_type = request.args.get('actionType')
        keyword = request.args.get('keyword')
        
        if page is not None and page_size is not None:
            page = int(page)
            page_size = int(page_size)
            offset = (page - 1) * page_size
            
            logs, total = db.activity_logs.get_filtered_with_keyword(category, action_type, keyword, page_size, offset)
            
            return jsonify({
                'logs': [format_activity_log(log) for log in logs],
                'total': total,
                'page': page,
                'pageSize': page_size
            })
        else:
            limit = int(limit) if limit else 50
            if category:
                logs = db.activity_logs.get_by_category(category, limit)
            else:
                logs = db.activity_logs.get_recent(limit)
            
            return jsonify([format_activity_log(log) for log in logs])

    @activity_log_bp.route('/<int:log_id>', methods=['DELETE'])
    @token_required
    @require_action_permission(db, 'systemLogs', 'deleteSingle')
    def delete_activity_log(user, log_id):
        db.activity_logs.delete(log_id)
        return jsonify({'message': 'Log deleted successfully'})

    @activity_log_bp.route('/batch', methods=['DELETE'])
    @token_required
    @require_action_permission(db, 'systemLogs', 'batchDelete')
    def batch_delete_activity_logs(user):
        data = request.get_json()
        log_ids = data.get('ids', [])
        if not log_ids:
            return jsonify({'error': 'No log IDs provided'}), 400
        
        db.activity_logs.batch_delete(log_ids)
        return jsonify({'message': f'{len(log_ids)} logs deleted successfully'})

    @activity_log_bp.route('/clear', methods=['DELETE'])
    @token_required
    @require_action_permission(db, 'systemLogs', 'clearAll')
    def clear_all_activity_logs(user):
        db.activity_logs.clear_all()
        return jsonify({'message': 'All logs cleared successfully'})

    @activity_log_bp.route('/my', methods=['GET'])
    @token_required
    @require_action_permission(db, 'systemLogs', 'view')
    def get_my_activity_logs(user):
        limit = request.args.get('limit', 50, type=int)
        logs = db.activity_logs.get_by_account(user['id'], limit)
        return jsonify([format_activity_log(log) for log in logs])

    return activity_log_bp
