#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集群管理插件 - API接口
面板通过此文件调用插件功能
"""

import os
import sys
import json

PLUGIN_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PLUGIN_PATH)

from cluster_main import ClusterManager, ARCH

manager = ClusterManager()


def return_json(status, msg='', data=None):
    """统一JSON返回"""
    result = {'status': status, 'msg': msg}
    if data is not None:
        result['data'] = data
    return json.dumps(result, ensure_ascii=False)


# ========== 分组 API ==========

def get_groups():
    groups = manager.get_all_groups()
    return return_json(True, 'ok', groups)


def add_group(name='', description='', color='#1E9FFF'):
    if not name:
        return return_json(False, '分组名称不能为空')
    manager.add_group(name, description, color)
    return return_json(True, '添加成功')


def update_group(id=0, name='', description='', color=''):
    if not id:
        return return_json(False, '分组ID不能为空')
    kwargs = {}
    if name:
        kwargs['name'] = name
    if description:
        kwargs['description'] = description
    if color:
        kwargs['color'] = color
    manager.update_group(int(id), **kwargs)
    return return_json(True, '更新成功')


def delete_group(id=0):
    if not id:
        return return_json(False, '分组ID不能为空')
    manager.delete_group(int(id))
    return return_json(True, '删除成功')


def reorder_groups(ids=''):
    if not ids:
        return return_json(False, '排序ID不能为空')
    group_ids = [int(x) for x in ids.split(',')]
    manager.reorder_groups(group_ids)
    return return_json(True, '排序成功')


# ========== 节点 API ==========

def get_nodes(group_id=''):
    if group_id:
        nodes = manager.get_nodes_by_group(int(group_id))
    else:
        nodes = manager.get_all_nodes()
    return return_json(True, 'ok', {'nodes': nodes, 'arch': ARCH})


def add_node(name='', host='', port=7200, api_key='', api_secret='',
             protocol='http', group_id=0, arch='', notes=''):
    if not name or not host or not api_key or not api_secret:
        return return_json(False, '必填字段不能为空')
    
    node_data = {
        'name': name,
        'host': host,
        'port': int(port),
        'api_key': api_key,
        'api_secret': api_secret,
        'protocol': protocol or 'http',
        'group_id': int(group_id),
        'arch': arch or '',
        'notes': notes or ''
    }
    manager.add_node(**node_data)
    return return_json(True, '添加成功')


def update_node(id=0, **kwargs):
    if not id:
        return return_json(False, '节点ID不能为空')
    update_data = {}
    for key in ['name', 'host', 'port', 'api_key', 'api_secret',
                'protocol', 'group_id', 'arch', 'notes']:
        if key in kwargs and kwargs[key]:
            update_data[key] = int(kwargs[key]) if key == 'port' else kwargs[key]
    manager.update_node(int(id), **update_data)
    return return_json(True, '更新成功')


def delete_node(id=0):
    if not id:
        return return_json(False, '节点ID不能为空')
    manager.delete_node(int(id))
    return return_json(True, '删除成功')


def reorder_nodes(ids=''):
    if not ids:
        return return_json(False, '排序ID不能为空')
    node_ids = [int(x) for x in ids.split(',')]
    manager.reorder_nodes(node_ids)
    return return_json(True, '排序成功')


def move_node(node_id=0, group_id=0):
    if not node_id:
        return return_json(False, '节点ID不能为空')
    manager.move_node_to_group(int(node_id), int(group_id))
    return return_json(True, '移动成功')


def test_connection(id=0):
    if not id:
        return return_json(False, '节点ID不能为空')
    result = manager.test_node_connection(int(id))
    return return_json(result.get('status', False),
                       result.get('msg', ''),
                       result.get('data'))


# ========== 服务管理 API ==========

def get_services(node_id=0):
    if not node_id:
        return return_json(False, '节点ID不能为空')
    services = manager.get_node_services(int(node_id))
    return return_json(True, 'ok', {
        'services': services,
        'common_services': manager.get_common_services()
    })


def service_action(node_id=0, service_name='', action=''):
    if not node_id or not service_name or not action:
        return return_json(False, '参数不完整')
    if action not in ['start', 'stop', 'restart', 'reload']:
        return return_json(False, '无效的操作')
    result = manager.service_action(int(node_id), service_name, action)
    return return_json(result.get('status', False), result.get('msg', ''))


def add_service(node_id=0, service_name='', auto_start=0,
                config_path='', port=0, version=''):
    if not node_id or not service_name:
        return return_json(False, '参数不完整')
    manager.db.add_service(int(node_id), service_name,
                           auto_start=int(auto_start),
                           config_path=config_path or '',
                           port=int(port),
                           version=version or '')
    return return_json(True, '添加成功')


def update_service_auto_start(service_id=0, auto_start=0):
    if not service_id:
        return return_json(False, '服务ID不能为空')
    manager.db.update_service_auto_start(int(service_id), int(auto_start))
    return return_json(True, '更新成功')


def delete_service(service_id=0):
    if not service_id:
        return return_json(False, '服务ID不能为空')
    manager.db.delete_service(int(service_id))
    return return_json(True, '删除成功')


# ========== 数据库配置 API ==========

def get_db_configs(node_id=''):
    if node_id:
        configs = manager.get_db_configs(int(node_id))
    else:
        configs = manager.get_db_configs()
    return return_json(True, 'ok', configs)


def save_db_config(node_id=0, db_type='mysql', db_host='127.0.0.1',
                   db_port=3306, db_name='', db_user='', db_password='',
                   db_prefix='mw_', status=1):
    if not node_id or not db_name or not db_user:
        return return_json(False, '必填字段不能为空')
    db_config = {
        'node_id': int(node_id),
        'db_type': db_type,
        'db_host': db_host,
        'db_port': int(db_port),
        'db_name': db_name,
        'db_user': db_user,
        'db_password': db_password,
        'db_prefix': db_prefix,
        'status': int(status)
    }
    manager.save_db_config(**db_config)
    return return_json(True, '保存成功')


# ========== 子面板设置 API ==========

def get_sub_panel_configs(node_id=0):
    if not node_id:
        return return_json(False, '节点ID不能为空')
    configs = manager.get_sub_panel_configs(int(node_id))
    return return_json(True, 'ok', configs)


def save_sub_panel_config(node_id=0, config_key='', config_value=''):
    if not node_id or not config_key:
        return return_json(False, '参数不完整')
    manager.save_sub_panel_config(int(node_id), config_key, config_value)
    return return_json(True, '保存成功')


# ========== 日志 API ==========

def get_logs(limit=100):
    logs = manager.get_logs(int(limit))
    return return_json(True, 'ok', logs)


def get_arch_info():
    return return_json(True, 'ok', {
        'arch': ARCH,
        'platform': sys.platform,
        'python_version': sys.version
    })
