#!/bin/bash
# 集群管理插件安装脚本
# 支持 arm 和 amd 架构

PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

PLUGIN_DIR="/www/server/mdserver-web/plugins/cluster"
PANEL_DIR="/www/server/mdserver-web"

echo "============================================="
echo "  集群管理插件 - 安装脚本"
echo "  支持架构: arm64, amd64"
echo "============================================="

# 检测系统架构
ARCH=$(uname -m)
case $ARCH in
    x86_64|amd64)
        ARCH="amd64"
        echo "检测到架构: amd64"
        ;;
    aarch64|arm64|armv8*)
        ARCH="arm64"
        echo "检测到架构: arm64"
        ;;
    armv7*|armv6*)
        ARCH="arm"
        echo "检测到架构: arm (32位)"
        ;;
    *)
        echo "警告: 未知架构 $ARCH，尝试继续安装"
        ;;
esac

# 确保目录存在
mkdir -p ${PLUGIN_DIR}
mkdir -p ${PLUGIN_DIR}/templates
mkdir -p ${PLUGIN_DIR}/static/css
mkdir -p ${PLUGIN_DIR}/static/js
mkdir -p ${PLUGIN_DIR}/data

echo "架构: ${ARCH} - 插件目录已创建"
echo "插件安装路径: ${PLUGIN_DIR}"

# 设置权限
chown -R www:www ${PLUGIN_DIR} 2>/dev/null || true
chmod -R 755 ${PLUGIN_DIR}
chmod +x ${PLUGIN_DIR}/*.sh 2>/dev/null || true

# 初始化数据库
if [ -f "${PLUGIN_DIR}/init_db.py" ]; then
    echo "正在初始化数据库..."
    cd ${PLUGIN_DIR}
    python3 init_db.py 2>/dev/null || python init_db.py 2>/dev/null || echo "数据库初始化跳过（可能需要手动初始化）"
fi

echo ""
echo "============================================="
echo "  集群管理插件安装完成！"
echo "  插件目录: ${PLUGIN_DIR}"
echo "  请刷新面板页面查看插件"
echo "  注意：安装后不会自动启动服务"
echo "============================================="
