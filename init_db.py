#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数据库初始化脚本"""

import os
import sys

PLUGIN_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PLUGIN_PATH)

from cluster_main import ClusterDB

if __name__ == '__main__':
    print("初始化集群管理数据库...")
    db = ClusterDB()
    print("数据库初始化完成！")
    print(f"数据库路径: {db.db_path}")
