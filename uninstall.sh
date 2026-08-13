#!/bin/bash
# 集群管理插件卸载脚本

PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

PLUGIN_DIR="/www/server/mdserver-web/plugins/cluster"

echo "============================================="
echo "  集群管理插件 - 卸载脚本"
echo "============================================="

# 清理数据（保留data目录供用户备份）
if [ -d "${PLUGIN_DIR}/data" ]; then
    echo "数据目录保留在: ${PLUGIN_DIR}/data"
    echo "如需完全删除，请手动执行: rm -rf ${PLUGIN_DIR}"
fi

echo "插件卸载完成"
echo "============================================="