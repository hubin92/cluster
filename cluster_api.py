#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集群管理插件 - API接口
提供面板调用的API接口
"""

import os
import sys
import json

PLUGIN_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PLUGIN_PATH)

from cluster_main import ClusterManager, ARCH

manager = ClusterManager()


def get_args():
    """获取请求参数"""
    import request
    args = {}
    for k in request.form:
        args[k] = request.form[k]
    for k in request.args:
        args[k] = request.args[k]
    return args


def return_json(status, msg='', data=None):
    """返回JSON"""
    result = {'status': status, 'msg': msg}
    if data is not None:
        result['data'] = data
    return json.dumps(result, ensure_ascii=False)


# ========== 分组API ==========

def get_groups():
    """获取所有分组"""
    groups = manager.get_all_groups()
    return return_json(True, 'ok', groups)


def add_group():
    """添加分组"""
    args = get_args()
    name = args.get('name', '')
    if not name:
        return return_json(False, '分组名称不能为空')
    description = args.get('description', '')
    color = args.get('color', '#1E9FFF')
    manager.add_group(name, description, color)
    return return_json(True, '添加成功')


def update_group():
    """更新分组"""
    args = get_args()
    group_id = int(args.get('id', 0))
    if not group_id:
        return return_json(False, '分组ID不能为空')
    kwargs = {}
    for key in ['name', 'description', 'color']:
        if key in args:
            kwargs[key] = args[key]
    manager.update_group(group_id, **kwargs)
    return return_json(True, '更新成功')


def delete_group():
    """删除分组"""
    args = get_args()
    group_id = int(args.get('id', 0))
    if not group_id:
        return return_json(False, '分组ID不能为空')
    manager.delete_group(group_id)
    return return_json(True, '删除成功')


def reorder_groups():
    """重新排序分组"""
    args = get_args()
    ids = args.get('ids', '')
    if not ids:
        return return_json(False, '排序ID不能为空')
    group_ids = [int(x) for x in ids.split(',')]
    manager.reorder_groups(group_ids)
    return return_json(True, '排序成功')


# ========== 节点API ==========

def get_nodes():
    """获取所有节点"""
    args = get_args()
    group_id = args.get('group_id', '')
    if group_id:
        nodes = manager.get_nodes_by_group(int(group_id))
    else:
        nodes = manager.get_all_nodes()
    return return_json(True, 'ok', {'nodes': nodes, 'arch': ARCH})


def add_node():
    """添加节点"""
    args = get_args()
    required = ['name', 'host', 'api_key', 'api_secret']
    for field in required:
        if not args.get(field):
            return return_json(False, f'{field} 不能为空')
    
    node_data = {
        'name': args.get('name'),
        'host': args.get('host'),
        'port': int(args.get('port', 7200)),
        'api_key': args.get('api_key'),
        'api_secret': args.get('api_secret'),
        'protocol': args.get('protocol', 'http'),
        'group_id': int(args.get('group_id', 0)),
        'arch': args.get('arch', ''),
        'notes': args.get('notes', '')
    }
    manager.add_node(**node_data)
    return return_json(True, '添加成功')


def update_node():
    """更新节点"""
    args = get_args()
    node_id = int(args.get('id', 0))
    if not node_id:
        return return_json(False, '节点ID不能为空')
    
    kwargs = {}
    for key in ['name', 'host', 'port', 'api_key', 'api_secret', 'protocol', 'group_id', 'arch', 'notes']:
        if key in args:
            kwargs[key] = args[key] if key != 'port' else int(args[key])
    manager.update_node(node_id, **kwargs)
    return return_json(True, '更新成功')


def delete_node():
    """删除节点"""
    args = get_args()
    node_id = int(args.get('id', 0))
    if not node_id:
        return return_json(False, '节点ID不能为空')
    manager.delete_node(node_id)
    return return_json(True, '删除成功')


def reorder_nodes():
    """重新排序节点"""
    args = get_args()
    ids = args.get('ids', '')
    if not ids:
        return return_json(False, '排序ID不能为空')
    node_ids = [int(x) for x in ids.split(',')]
    manager.reorder_nodes(node_ids)
    return return_json(True, '排序成功')


def move_node():
    """移动节点到分组"""
    args = get_args()
    node_id = int(args.get('node_id', 0))
    group_id = int(args.get('group_id', 0))
    if not node_id:
        return return_json(False, '节点ID不能为空')
    manager.move_node_to_group(node_id, group_id)
    return return_json(True, '移动成功')


def test_connection():
    """测试节点连接"""
    args = get_args()
    node_id = int(args.get('id', 0))
    if not node_id:
        return return_json(False, '节点ID不能为空')
    result = manager.test_node_connection(node_id)
    return return_json(result.get('status', False), result.get('msg', ''), result.get('data'))


# ========== 服务管理API ==========

def get_services():
    """获取节点服务列表"""
    args = get_args()
    node_id = int(args.get('node_id', 0))
    if not node_id:
        return return_json(False, '节点ID不能为空')
    services = manager.get_node_services(node_id)
    return return_json(True, 'ok', {
        'services': services,
        'common_services': manager.get_common_services()
    })


def service_action():
    """执行服务操作"""
    args = get_args()
    node_id = int(args.get('node_id', 0))
    service_name = args.get('service_name', '')
    action = args.get('action', '')  # start/stop/restart/reload
    if not node_id or not service_name or not action:
        return return_json(False, '参数不完整')
    if action not in ['start', 'stop', 'restart', 'reload']:
        return return_json(False, '无效的操作')
    result = manager.service_action(node_id, service_name, action)
    return return_json(result.get('status', False), result.get('msg', ''))


def add_service():
    """添加服务到节点"""
    args = get_args()
    node_id = int(args.get('node_id', 0))
    service_name = args.get('service_name', '')
    if not node_id or not service_name:
        return return_json(False, '参数不完整')
    manager.db.add_service(node_id, service_name,
                           auto_start=args.get('auto_start', 0),
                           config_path=args.get('config_path', ''),
                           port=int(args.get('port', 0)),
                           version=args.get('version', ''))
    return return_json(True, '添加成功')


def update_service_auto_start():
    """更新服务自启动状态"""
    args = get_args()
    service_id = int(args.get('service_id', 0))
    auto_start = int(args.get('auto_start', 0))
    if not service_id:
        return return_json(False, '服务ID不能为空')
    manager.db.update_service_auto_start(service_id, auto_start)
    return return_json(True, '更新成功')


def delete_service():
    """删除服务"""
    args = get_args()
    service_id = int(args.get('service_id', 0))
    if not service_id:
        return return_json(False, '服务ID不能为空')
    manager.db.delete_service(service_id)
    return return_json(True, '删除成功')


# ========== 数据库配置API ==========

def get_db_configs():
    """获取数据库配置"""
    args = get_args()
    node_id = args.get('node_id', '')
    if node_id:
        configs = manager.get_db_configs(int(node_id))
    else:
        configs = manager.get_db_configs()
    return return_json(True, 'ok', configs)


def save_db_config():
    """保存数据库配置"""
    args = get_args()
    required = ['node_id', 'db_type', 'db_host', 'db_name', 'db_user', 'db_password']
    for field in required:
        if not args.get(field):
            return return_json(False, f'{field} 不能为空')
    
    db_config = {
        'node_id': int(args.get('node_id')),
        'db_type': args.get('db_type'),
        'db_host': args.get('db_host'),
        'db_port': int(args.get('db_port', 3306)),
        'db_name': args.get('db_name'),
        'db_user': args.get('db_user'),
        'db_password': args.get('db_password'),
        'db_prefix': args.get('db_prefix', 'mw_'),
        'status': int(args.get('status', 1))
    }
    manager.save_db_config(**db_config)
    return return_json(True, '保存成功')


# ========== 子面板设置API ==========

def get_sub_panel_configs():
    """获取子面板配置"""
    args = get_args()
    node_id = int(args.get('node_id', 0))
    if not node_id:
        return return_json(False, '节点ID不能为空')
    configs = manager.get_sub_panel_configs(node_id)
    return return_json(True, 'ok', configs)


def save_sub_panel_config():
    """保存子面板配置"""
    args = get_args()
    node_id = int(args.get('node_id', 0))
    config_key = args.get('config_key', '')
    config_value = args.get('config_value', '')
    if not node_id or not config_key:
        return return_json(False, '参数不完整')
    manager.save_sub_panel_config(node_id, config_key, config_value)
    return return_json(True, '保存成功')


# ========== 日志API ==========

def get_logs():
    """获取操作日志"""
    args = get_args()
    limit = int(args.get('limit', 100))
    logs = manager.get_logs(limit)
    return return_json(True, 'ok', logs)


def get_arch_info():
    """获取架构信息"""
    return return_json(True, 'ok', {
        'arch': ARCH,
        'platform': sys.platform,
        'python_version': sys.version
    })