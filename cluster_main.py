#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集群管理插件 - 主模块
支持多服务器集群管理、面板分组、拖拽排序
支持 arm 和 amd 架构
安装后不主动运行服务
"""

import os
import sys
import json
import time
import subprocess
import sqlite3
import platform
import hashlib
import urllib.request
import urllib.error
import ssl
from datetime import datetime

# 插件根目录
PLUGIN_PATH = os.path.dirname(os.path.abspath(__file__))
PLUGIN_NAME = 'cluster'
PANEL_PATH = '/www/server/mdserver-web'

# 添加面板路径
sys.path.insert(0, PANEL_PATH + '/class')

# 数据库路径
DB_PATH = os.path.join(PLUGIN_PATH, 'data', 'cluster.db')


def get_arch():
    """获取系统架构"""
    machine = platform.machine()
    if machine in ('x86_64', 'AMD64'):
        return 'amd64'
    elif machine in ('aarch64', 'arm64', 'aarch64_be'):
        return 'arm64'
    elif machine.startswith('arm'):
        return 'arm'
    return machine


ARCH = get_arch()


class ClusterDB:
    """集群数据库管理 - SQLite"""
    
    def __init__(self):
        self.db_path = DB_PATH
        self._init_db()
    
    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_db(self):
        """初始化数据库表"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = self._get_conn()
        cursor = conn.cursor()
        
        # 面板分组表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS panel_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                sort_order INTEGER DEFAULT 0,
                color TEXT DEFAULT '#1E9FFF',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime'))
            )
        ''')
        
        # 面板节点表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS panel_nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER DEFAULT 0,
                name TEXT NOT NULL,
                host TEXT NOT NULL,
                port INTEGER DEFAULT 7200,
                api_key TEXT DEFAULT '',
                api_secret TEXT DEFAULT '',
                protocol TEXT DEFAULT 'http',
                status INTEGER DEFAULT 0,
                arch TEXT DEFAULT 'amd64',
                os_info TEXT DEFAULT '',
                panel_version TEXT DEFAULT '',
                cpu_usage REAL DEFAULT 0,
                memory_usage REAL DEFAULT 0,
                disk_usage REAL DEFAULT 0,
                uptime TEXT DEFAULT '',
                last_check TEXT DEFAULT '',
                sort_order INTEGER DEFAULT 0,
                notes TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime'))
            )
        ''')
        
        # 服务管理表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS panel_services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_id INTEGER NOT NULL,
                service_name TEXT NOT NULL,
                service_status TEXT DEFAULT 'stopped',
                auto_start INTEGER DEFAULT 0,
                config_path TEXT DEFAULT '',
                port INTEGER DEFAULT 0,
                version TEXT DEFAULT '',
                last_action TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime'))
            )
        ''')
        
        # 数据库配置表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS db_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_id INTEGER DEFAULT 0,
                db_type TEXT NOT NULL DEFAULT 'mysql',
                db_host TEXT DEFAULT '127.0.0.1',
                db_port INTEGER DEFAULT 3306,
                db_name TEXT DEFAULT '',
                db_user TEXT DEFAULT '',
                db_password TEXT DEFAULT '',
                db_prefix TEXT DEFAULT 'mw_',
                status INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime'))
            )
        ''')
        
        # 子面板设置表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sub_panel_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_id INTEGER NOT NULL,
                config_key TEXT NOT NULL,
                config_value TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now','localtime')),
                updated_at TEXT DEFAULT (datetime('now','localtime'))
            )
        ''')
        
        # 操作日志表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS operation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                node_id INTEGER DEFAULT 0,
                action TEXT NOT NULL,
                result TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now','localtime'))
            )
        ''')
        
        # 初始化默认分组
        cursor.execute("SELECT COUNT(*) as cnt FROM panel_groups")
        if cursor.fetchone()['cnt'] == 0:
            cursor.execute(
                "INSERT INTO panel_groups (name, description, sort_order, color) VALUES (?, ?, ?, ?)",
                ('默认分组', '默认服务器分组', 0, '#1E9FFF')
            )
        
        conn.commit()
        conn.close()
    
    # ========== 分组 CRUD ==========
    
    def get_groups(self):
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM panel_groups ORDER BY sort_order ASC").fetchall()
        conn.close()
        return [dict(r) for r in rows]
    
    def add_group(self, name, description='', color='#1E9FFF'):
        conn = self._get_conn()
        cursor = conn.execute("SELECT MAX(sort_order) as max_sort FROM panel_groups")
        max_sort = cursor.fetchone()['max_sort'] or 0
        conn.execute(
            "INSERT INTO panel_groups (name, description, sort_order, color) VALUES (?, ?, ?, ?)",
            (name, description, max_sort + 1, color)
        )
        conn.commit()
        conn.close()
        return True
    
    def update_group(self, group_id, **kwargs):
        conn = self._get_conn()
        sets = ', '.join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [group_id]
        conn.execute(
            f"UPDATE panel_groups SET {sets}, updated_at = datetime('now','localtime') WHERE id = ?",
            values
        )
        conn.commit()
        conn.close()
        return True
    
    def delete_group(self, group_id):
        conn = self._get_conn()
        conn.execute("UPDATE panel_nodes SET group_id = 0 WHERE group_id = ?", (group_id,))
        conn.execute("DELETE FROM panel_groups WHERE id = ?", (group_id,))
        conn.commit()
        conn.close()
        return True
    
    def reorder_groups(self, group_ids):
        conn = self._get_conn()
        for i, gid in enumerate(group_ids):
            conn.execute("UPDATE panel_groups SET sort_order = ? WHERE id = ?", (i, gid))
        conn.commit()
        conn.close()
        return True
    
    # ========== 节点 CRUD ==========
    
    def get_nodes(self, group_id=None):
        conn = self._get_conn()
        if group_id is not None:
            rows = conn.execute(
                "SELECT n.*, g.name as group_name FROM panel_nodes n "
                "LEFT JOIN panel_groups g ON n.group_id = g.id "
                "WHERE n.group_id = ? ORDER BY n.sort_order ASC",
                (group_id,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT n.*, g.name as group_name FROM panel_nodes n "
                "LEFT JOIN panel_groups g ON n.group_id = g.id "
                "ORDER BY n.sort_order ASC"
            ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    
    def add_node(self, **kwargs):
        conn = self._get_conn()
        fields = ['name', 'host', 'port', 'api_key', 'api_secret', 'protocol',
                  'group_id', 'arch', 'notes']
        values = [kwargs.get(f, '') for f in fields]
        placeholders = ', '.join(['?' for _ in fields])
        conn.execute(
            f"INSERT INTO panel_nodes ({', '.join(fields)}) VALUES ({placeholders})",
            values
        )
        conn.commit()
        conn.close()
        return True
    
    def update_node(self, node_id, **kwargs):
        conn = self._get_conn()
        sets = ', '.join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [node_id]
        conn.execute(
            f"UPDATE panel_nodes SET {sets}, updated_at = datetime('now','localtime') WHERE id = ?",
            values
        )
        conn.commit()
        conn.close()
        return True
    
    def delete_node(self, node_id):
        conn = self._get_conn()
        conn.execute("DELETE FROM panel_services WHERE node_id = ?", (node_id,))
        conn.execute("DELETE FROM db_configs WHERE node_id = ?", (node_id,))
        conn.execute("DELETE FROM sub_panel_configs WHERE node_id = ?", (node_id,))
        conn.execute("DELETE FROM panel_nodes WHERE id = ?", (node_id,))
        conn.commit()
        conn.close()
        return True
    
    def reorder_nodes(self, node_ids):
        conn = self._get_conn()
        for i, nid in enumerate(node_ids):
            conn.execute("UPDATE panel_nodes SET sort_order = ? WHERE id = ?", (i, nid))
        conn.commit()
        conn.close()
        return True
    
    def move_node_to_group(self, node_id, group_id):
        conn = self._get_conn()
        conn.execute(
            "UPDATE panel_nodes SET group_id = ?, updated_at = datetime('now','localtime') WHERE id = ?",
            (group_id, node_id)
        )
        conn.commit()
        conn.close()
        return True
    
    # ========== 服务 CRUD ==========
    
    def get_services(self, node_id):
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM panel_services WHERE node_id = ? ORDER BY service_name ASC",
            (node_id,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    
    def add_service(self, node_id, service_name, **kwargs):
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO panel_services (node_id, service_name, auto_start, config_path, port, version) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (node_id, service_name,
             kwargs.get('auto_start', 0),
             kwargs.get('config_path', ''),
             kwargs.get('port', 0),
             kwargs.get('version', ''))
        )
        conn.commit()
        conn.close()
        return True
    
    def update_service_status(self, service_id, status):
        conn = self._get_conn()
        conn.execute(
            "UPDATE panel_services SET service_status = ?, last_action = ?, "
            "updated_at = datetime('now','localtime') WHERE id = ?",
            (status, status, service_id)
        )
        conn.commit()
        conn.close()
        return True
    
    def update_service_auto_start(self, service_id, auto_start):
        conn = self._get_conn()
        conn.execute(
            "UPDATE panel_services SET auto_start = ?, updated_at = datetime('now','localtime') WHERE id = ?",
            (auto_start, service_id)
        )
        conn.commit()
        conn.close()
        return True
    
    def delete_service(self, service_id):
        conn = self._get_conn()
        conn.execute("DELETE FROM panel_services WHERE id = ?", (service_id,))
        conn.commit()
        conn.close()
        return True
    
    # ========== 数据库配置 ==========
    
    def get_db_configs(self, node_id=None):
        conn = self._get_conn()
        if node_id:
            rows = conn.execute("SELECT * FROM db_configs WHERE node_id = ?", (node_id,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM db_configs").fetchall()
        conn.close()
        return [dict(r) for r in rows]
    
    def save_db_config(self, **kwargs):
        conn = self._get_conn()
        node_id = kwargs.get('node_id', 0)
        db_type = kwargs.get('db_type', 'mysql')
        
        existing = conn.execute(
            "SELECT id FROM db_configs WHERE node_id = ? AND db_type = ?",
            (node_id, db_type)
        ).fetchone()
        
        if existing:
            sets = ', '.join([f"{k} = ?" for k in kwargs.keys()])
            values = list(kwargs.values()) + [existing['id']]
            conn.execute(
                f"UPDATE db_configs SET {sets}, updated_at = datetime('now','localtime') WHERE id = ?",
                values
            )
        else:
            fields = list(kwargs.keys())
            values = list(kwargs.values())
            placeholders = ', '.join(['?' for _ in fields])
            conn.execute(
                f"INSERT INTO db_configs ({', '.join(fields)}) VALUES ({placeholders})",
                values
            )
        conn.commit()
        conn.close()
        return True
    
    # ========== 子面板配置 ==========
    
    def get_sub_panel_configs(self, node_id):
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM sub_panel_configs WHERE node_id = ?", (node_id,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    
    def save_sub_panel_config(self, node_id, config_key, config_value):
        conn = self._get_conn()
        existing = conn.execute(
            "SELECT id FROM sub_panel_configs WHERE node_id = ? AND config_key = ?",
            (node_id, config_key)
        ).fetchone()
        
        if existing:
            conn.execute(
                "UPDATE sub_panel_configs SET config_value = ?, "
                "updated_at = datetime('now','localtime') WHERE id = ?",
                (config_value, existing['id'])
            )
        else:
            conn.execute(
                "INSERT INTO sub_panel_configs (node_id, config_key, config_value) VALUES (?, ?, ?)",
                (node_id, config_key, config_value)
            )
        conn.commit()
        conn.close()
        return True
    
    # ========== 日志 ==========
    
    def add_log(self, node_id, action, result=''):
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO operation_logs (node_id, action, result) VALUES (?, ?, ?)",
            (node_id, action, result)
        )
        conn.commit()
        conn.close()
    
    def get_logs(self, limit=100):
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT l.*, n.name as node_name FROM operation_logs l "
            "LEFT JOIN panel_nodes n ON l.node_id = n.id "
            "ORDER BY l.created_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]


class ClusterAPI:
    """集群API通信 - 与远程面板通信"""
    
    def __init__(self, host, port=7200, api_key='', api_secret='', protocol='http'):
        self.host = host
        self.port = port
        self.api_key = api_key
        self.api_secret = api_secret
        self.protocol = protocol
        self.base_url = f"{protocol}://{host}:{port}"
    
    def _make_sign(self, request_data):
        """生成API签名"""
        if not self.api_key or not self.api_secret:
            return {}
        now = int(time.time())
        token = hashlib.md5(
            (str(now) + hashlib.md5(
                (self.api_key + self.api_secret).encode()
            ).hexdigest()).encode()
        ).hexdigest()
        data = {
            'request_time': now,
            'request_token': token
        }
        data.update(request_data)
        return data
    
    def _request(self, uri, data=None, timeout=10):
        """发送API请求"""
        try:
            url = f"{self.base_url}{uri}"
            request_data = self._make_sign(data or {})
            
            if request_data:
                post_data = urllib.parse.urlencode(request_data).encode('utf-8')
                req = urllib.request.Request(url, data=post_data)
            else:
                req = urllib.request.Request(url)
            
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            response = urllib.request.urlopen(req, timeout=timeout, context=ctx)
            result = json.loads(response.read().decode('utf-8'))
            return result
        except Exception as e:
            return {'status': False, 'msg': str(e)}
    
    def test_connection(self):
        return self._request('/system?action=GetSystemTotal')
    
    def get_service_status(self, service_name):
        return self._request('/system?action=GetServiceStatus', {'name': service_name})
    
    def service_action(self, service_name, action):
        return self._request('/system?action=ServiceAdmin', {
            'name': service_name,
            'type': action
        })


class ClusterManager:
    """集群管理器 - 业务逻辑层"""
    
    def __init__(self):
        self.db = ClusterDB()
    
    def get_arch(self):
        return ARCH
    
    def get_all_groups(self):
        return self.db.get_groups()
    
    def get_all_nodes(self):
        return self.db.get_nodes()
    
    def get_nodes_by_group(self, group_id):
        return self.db.get_nodes(group_id)
    
    def add_group(self, name, description='', color='#1E9FFF'):
        return self.db.add_group(name, description, color)
    
    def update_group(self, group_id, **kwargs):
        return self.db.update_group(group_id, **kwargs)
    
    def delete_group(self, group_id):
        return self.db.delete_group(group_id)
    
    def reorder_groups(self, group_ids):
        return self.db.reorder_groups(group_ids)
    
    def add_node(self, **kwargs):
        return self.db.add_node(**kwargs)
    
    def update_node(self, node_id, **kwargs):
        return self.db.update_node(node_id, **kwargs)
    
    def delete_node(self, node_id):
        return self.db.delete_node(node_id)
    
    def reorder_nodes(self, node_ids):
        return self.db.reorder_nodes(node_ids)
    
    def move_node_to_group(self, node_id, group_id):
        return self.db.move_node_to_group(node_id, group_id)
    
    def test_node_connection(self, node_id):
        nodes = self.db.get_nodes()
        node = next((n for n in nodes if n['id'] == node_id), None)
        if not node:
            return {'status': False, 'msg': '节点不存在'}
        
        api = ClusterAPI(node['host'], node['port'],
                         node['api_key'], node['api_secret'],
                         node['protocol'])
        result = api.test_connection()
        
        if result.get('status'):
            self.db.update_node(node_id, status=1,
                                last_check=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            if 'data' in result:
                info = result['data']
                self.db.update_node(node_id,
                    os_info=str(info.get('system', '')),
                    panel_version=str(info.get('version', '')),
                    cpu_usage=float(info.get('cpu', 0)),
                    memory_usage=float(info.get('mem', 0)),
                    disk_usage=float(info.get('disk', 0)),
                    uptime=str(info.get('uptime', ''))
                )
        else:
            self.db.update_node(node_id, status=0,
                                last_check=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        self.db.add_log(node_id, f'连接测试: {result.get("status")}', str(result))
        return result
    
    def service_action(self, node_id, service_name, action):
        nodes = self.db.get_nodes()
        node = next((n for n in nodes if n['id'] == node_id), None)
        if not node:
            return {'status': False, 'msg': '节点不存在'}
        
        api = ClusterAPI(node['host'], node['port'],
                         node['api_key'], node['api_secret'],
                         node['protocol'])
        result = api.service_action(service_name, action)
        
        services = self.db.get_services(node_id)
        for svc in services:
            if svc['service_name'] == service_name:
                if action in ('start', 'restart', 'reload'):
                    self.db.update_service_status(svc['id'], 'running')
                elif action == 'stop':
                    self.db.update_service_status(svc['id'], 'stopped')
        
        self.db.add_log(node_id, f'服务操作: {service_name} {action}', str(result))
        return result
    
    def get_node_services(self, node_id):
        nodes = self.db.get_nodes()
        node = next((n for n in nodes if n['id'] == node_id), None)
        services = self.db.get_services(node_id)
        
        if node and node['status'] == 1:
            try:
                api = ClusterAPI(node['host'], node['port'],
                                 node['api_key'], node['api_secret'],
                                 node['protocol'])
                for svc in services:
                    result = api.get_service_status(svc['service_name'])
                    if result.get('status'):
                        real_status = result.get('data', {}).get('status', 'unknown')
                        self.db.update_service_status(svc['id'], real_status)
                        svc['service_status'] = real_status
            except Exception:
                pass
        
        return services
    
    def get_db_configs(self, node_id=None):
        return self.db.get_db_configs(node_id)
    
    def save_db_config(self, **kwargs):
        return self.db.save_db_config(**kwargs)
    
    def get_sub_panel_configs(self, node_id):
        return self.db.get_sub_panel_configs(node_id)
    
    def save_sub_panel_config(self, node_id, config_key, config_value):
        return self.db.save_sub_panel_config(node_id, config_key, config_value)
    
    def get_logs(self, limit=100):
        return self.db.get_logs(limit)
    
    def get_common_services(self):
        return [
            {'name': 'nginx', 'display': 'Nginx', 'port': 80,
             'config_path': '/www/server/nginx/conf/nginx.conf'},
            {'name': 'apache', 'display': 'Apache', 'port': 80,
             'config_path': '/www/server/apache/conf/httpd.conf'},
            {'name': 'mysql', 'display': 'MySQL', 'port': 3306,
             'config_path': '/etc/my.cnf'},
            {'name': 'mariadb', 'display': 'MariaDB', 'port': 3306,
             'config_path': '/etc/my.cnf'},
            {'name': 'postgresql', 'display': 'PostgreSQL', 'port': 5432,
             'config_path': '/www/server/pgsql/data/postgresql.conf'},
            {'name': 'php', 'display': 'PHP-FPM', 'port': 9000,
             'config_path': '/www/server/php/etc/php-fpm.conf'},
            {'name': 'redis', 'display': 'Redis', 'port': 6379,
             'config_path': '/www/server/redis/redis.conf'},
            {'name': 'memcached', 'display': 'Memcached', 'port': 11211,
             'config_path': ''},
            {'name': 'pure-ftpd', 'display': 'Pure-Ftpd', 'port': 21,
             'config_path': '/www/server/pure-ftpd/etc/pure-ftpd.conf'},
            {'name': 'openresty', 'display': 'OpenResty', 'port': 80,
             'config_path': '/www/server/openresty/nginx/conf/nginx.conf'},
            {'name': 'mongodb', 'display': 'MongoDB', 'port': 27017,
             'config_path': '/www/server/mongodb/config.conf'},
        ]
