#!/bin/bash
# 正确打包插件 - 使用英文目录名

PLUGIN_NAME="cluster"
ZIP_FILE="${PLUGIN_NAME}.zip"

echo "============================================="
echo "  打包集群管理插件"
echo "============================================="

# 清理旧文件
rm -rf "${PLUGIN_NAME}" "${ZIP_FILE}"

# 创建英文目录
mkdir -p "${PLUGIN_NAME}/templates"
mkdir -p "${PLUGIN_NAME}/static/css"
mkdir -p "${PLUGIN_NAME}/static/js"
mkdir -p "${PLUGIN_NAME}/data"

# 复制所有文件
cp info.json "${PLUGIN_NAME}/"
cp index.json "${PLUGIN_NAME}/"
cp install.sh "${PLUGIN_NAME}/"
cp uninstall.sh "${PLUGIN_NAME}/"
cp cluster_main.py "${PLUGIN_NAME}/"
cp cluster_api.py "${PLUGIN_NAME}/"
cp init_db.py "${PLUGIN_NAME}/"
cp main.py "${PLUGIN_NAME}/" 2>/dev/null || true
cp templates/index.html "${PLUGIN_NAME}/templates/"
cp templates/cluster.html "${PLUGIN_NAME}/templates/"
cp static/css/cluster.css "${PLUGIN_NAME}/static/css/"
cp static/js/cluster.js "${PLUGIN_NAME}/static/js/"

# 设置权限
chmod +x "${PLUGIN_NAME}/install.sh"
chmod +x "${PLUGIN_NAME}/uninstall.sh"
chmod +x "${PLUGIN_NAME}/"*.py 2>/dev/null || true

# 打包
zip -r "${ZIP_FILE}" "${PLUGIN_NAME}/"

echo ""
echo "============================================="
echo "  打包完成!"
echo "  文件: ${ZIP_FILE}"
echo ""
echo "  ZIP 结构 (英文目录名):"
echo "  └── cluster/           ← 必须英文！"
echo "      ├── info.json"
echo "      ├── index.json"
echo "      ├── install.sh"
echo "      └── ..."
echo ""
echo "  安装路径: /www/server/mdserver-web/plugins/cluster/"
echo "============================================="
