var currentServiceNodeId = 0;
var draggingNodeId = null;
var draggingGroupId = null;

function allowDrop(ev) {
    ev.preventDefault();
    var card = ev.target.closest('.cluster-group-card');
    if (card) card.classList.add('drag-over');
    var node = ev.target.closest('.cluster-node-card');
    if (node) node.classList.add('drag-over');
}

function dragGroup(ev, groupId) {
    draggingGroupId = groupId;
    ev.dataTransfer.setData("text/plain", "group:" + groupId);
    ev.dataTransfer.effectAllowed = "move";
}

function dragNode(ev, nodeId) {
    draggingNodeId = nodeId;
    ev.dataTransfer.setData("text/plain", "node:" + nodeId);
    ev.dataTransfer.effectAllowed = "move";
}

function dropGroup(ev, targetGroupId) {
    ev.preventDefault();
    var card = ev.target.closest('.cluster-group-card');
    if (card) card.classList.remove('drag-over');
    var data = ev.dataTransfer.getData("text/plain");
    if (data.startsWith("group:")) {
        var sourceGroupId = data.split(":")[1];
        if (sourceGroupId != targetGroupId) reorderGroups();
    }
    draggingGroupId = null;
}

function dropNode(ev, targetGroupId) {
    ev.preventDefault();
    var card = ev.target.closest('.cluster-group-card');
    if (card) card.classList.remove('drag-over');
    var node = ev.target.closest('.cluster-node-card');
    if (node) node.classList.remove('drag-over');
    var data = ev.dataTransfer.getData("text/plain");
    if (data.startsWith("node:")) {
        var nodeId = data.split(":")[1];
        moveNodeToGroup(nodeId, targetGroupId);
    }
    draggingNodeId = null;
}

function dropNodeToNode(ev, targetNodeId) {
    ev.preventDefault();
    var node = ev.target.closest('.cluster-node-card');
    if (node) node.classList.remove('drag-over');
    reorderNodes();
}

document.addEventListener('dragend', function() {
    document.querySelectorAll('.drag-over').forEach(function(el) {
        el.classList.remove('drag-over');
    });
});

function addGroup() {
    layer.prompt({title: '添加分组', formType: 0, placeholder: '请输入分组名称'}, function(name, index) {
        if (!name) { layer.msg('分组名称不能为空'); return; }
        layer.close(index);
        var color = '#' + Math.floor(Math.random()*16777215).toString(16).padStart(6, '0');
        layer.prompt({title: '选择颜色（可选）', formType: 0, value: color}, function(colorVal, idx) {
            layer.close(idx);
            $.post('/cluster/api?action=add_group', {name: name, color: colorVal || color}, function(res) {
                res = typeof res === 'string' ? JSON.parse(res) : res;
                if (res.status) { layer.msg('添加成功', {icon: 1}); setTimeout(function() { location.reload(); }, 800); }
                else layer.msg(res.msg || '添加失败', {icon: 2});
            });
        });
    });
}

function editGroup(id, name, description, color) {
    var html = '<div style="padding:20px;">' +
        '<div class="layui-form-item"><label>名称</label><input type="text" id="editGroupName" class="layui-input" value="' + name + '"></div>' +
        '<div class="layui-form-item"><label>描述</label><input type="text" id="editGroupDesc" class="layui-input" value="' + (description||'') + '"></div>' +
        '<div class="layui-form-item"><label>颜色</label><input type="color" id="editGroupColor" class="layui-input" value="' + (color||'#1E9FFF') + '"></div>' +
        '</div>';
    layer.open({type: 1, title: '编辑分组', area: ['400px', '300px'], content: html, btn: ['保存', '取消'],
        yes: function(index) {
            $.post('/cluster/api?action=update_group', {
                id: id, name: $('#editGroupName').val(), description: $('#editGroupDesc').val(), color: $('#editGroupColor').val()
            }, function(res) {
                res = typeof res === 'string' ? JSON.parse(res) : res;
                if (res.status) { layer.msg('更新成功', {icon: 1}); layer.close(index); setTimeout(function() { location.reload(); }, 800); }
                else layer.msg(res.msg || '更新失败', {icon: 2});
            });
        }
    });
}

function deleteGroup(id) {
    layer.confirm('确定删除该分组吗？节点将移至"未分组"', {btn: ['确定', '取消']}, function(index) {
        $.post('/cluster/api?action=delete_group', {id: id}, function(res) {
            res = typeof res === 'string' ? JSON.parse(res) : res;
            if (res.status) { layer.msg('删除成功', {icon: 1}); setTimeout(function() { location.reload(); }, 800); }
            else layer.msg(res.msg || '删除失败', {icon: 2});
        });
        layer.close(index);
    });
}

function reorderGroups() {
    var groupIds = [];
    document.querySelectorAll('.cluster-group-card[data-group-id]').forEach(function(card) {
        groupIds.push(card.getAttribute('data-group-id'));
    });
    $.post('/cluster/api?action=reorder_groups', {ids: groupIds.join(',')}, function(res) {
        res = typeof res === 'string' ? JSON.parse(res) : res;
        if (!res.status) layer.msg(res.msg || '排序失败', {icon: 2});
    });
}

function reorderNodes() {
    var nodeIds = [];
    document.querySelectorAll('.cluster-node-card[data-node-id]').forEach(function(card) {
        nodeIds.push(card.getAttribute('data-node-id'));
    });
    $.post('/cluster/api?action=reorder_nodes', {ids: nodeIds.join(',')}, function(res) {
        res = typeof res === 'string' ? JSON.parse(res) : res;
        if (!res.status) layer.msg(res.msg || '排序失败', {icon: 2});
    });
}

function moveNodeToGroup(nodeId, groupId) {
    $.post('/cluster/api?action=move_node', {node_id: nodeId, group_id: groupId}, function(res) {
        res = typeof res === 'string' ? JSON.parse(res) : res;
        if (res.status) { layer.msg('移动成功', {icon: 1}); setTimeout(function() { location.reload(); }, 800); }
        else layer.msg(res.msg || '移动失败', {icon: 2});
    });
}

function addNode() { addNodeToGroup(0); }

function addNodeToGroup(groupId) {
    var html = '<div style="padding:20px;">' +
        '<div class="layui-form-item"><label>节点名称</label><input type="text" id="addNodeName" class="layui-input" placeholder="如: 生产服务器1"></div>' +
        '<div class="layui-form-item"><label>主机地址</label><input type="text" id="addNodeHost" class="layui-input" placeholder="如: 192.168.1.100"></div>' +
        '<div class="layui-form-item"><label>端口</label><input type="number" id="addNodePort" class="layui-input" value="7200"></div>' +
        '<div class="layui-form-item"><label>API Key</label><input type="text" id="addNodeApiKey" class="layui-input" placeholder="面板API密钥"></div>' +
        '<div class="layui-form-item"><label>API Secret</label><input type="text" id="addNodeApiSecret" class="layui-input" placeholder="面板API Secret"></div>' +
        '<div class="layui-form-item"><label>协议</label><select id="addNodeProtocol"><option value="http">HTTP</option><option value="https">HTTPS</option></select></div>' +
        '<div class="layui-form-item"><label>架构</label><select id="addNodeArch"><option value="amd64">amd64</option><option value="arm64">arm64</option><option value="arm">arm</option></select></div>' +
        '<input type="hidden" id="addNodeGroupId" value="' + groupId + '"></div>';
    layer.open({type: 1, title: '添加节点', area: ['500px', '480px'], content: html, btn: ['添加', '取消'],
        yes: function(index) {
            var data = {
                name: $('#addNodeName').val(), host: $('#addNodeHost').val(), port: $('#addNodePort').val(),
                api_key: $('#addNodeApiKey').val(), api_secret: $('#addNodeApiSecret').val(),
                protocol: $('#addNodeProtocol').val(), arch: $('#addNodeArch').val(), group_id: $('#addNodeGroupId').val()
            };
            if (!data.name || !data.host || !data.api_key || !data.api_secret) {
                layer.msg('请填写完整信息', {icon: 2}); return;
            }
            $.post('/cluster/api?action=add_node', data, function(res) {
                res = typeof res === 'string' ? JSON.parse(res) : res;
                if (res.status) { layer.msg('添加成功', {icon: 1}); layer.close(index); setTimeout(function() { location.reload(); }, 800); }
                else layer.msg(res.msg || '添加失败', {icon: 2});
            });
        }
    });
}

function editNode(nodeId) {
    $.get('/cluster/api?action=get_nodes', function(res) {
        res = typeof res === 'string' ? JSON.parse(res) : res;
        if (res.status && res.data && res.data.nodes) {
            var node = res.data.nodes.find(function(n) { return n.id == nodeId; });
            if (!node) return;
            var html = '<div style="padding:20px;">' +
                '<div class="layui-form-item"><label>节点名称</label><input type="text" id="editNodeName" class="layui-input" value="' + (node.name||'') + '"></div>' +
                '<div class="layui-form-item"><label>主机地址</label><input type="text" id="editNodeHost" class="layui-input" value="' + (node.host||'') + '"></div>' +
                '<div class="layui-form-item"><label>端口</label><input type="number" id="editNodePort" class="layui-input" value="' + (node.port||7200) + '"></div>' +
                '<div class="layui-form-item"><label>API Key</label><input type="text" id="editNodeApiKey" class="layui-input" value="' + (node.api_key||'') + '"></div>' +
                '<div class="layui-form-item"><label>API Secret</label><input type="text" id="editNodeApiSecret" class="layui-input" value="' + (node.api_secret||'') + '"></div>' +
                '<div class="layui-form-item"><label>备注</label><textarea id="editNodeNotes" class="layui-textarea">' + (node.notes||'') + '</textarea></div></div>';
            layer.open({type: 1, title: '编辑节点', area: ['500px', '450px'], content: html, btn: ['保存', '取消'],
                yes: function(index) {
                    $.post('/cluster/api?action=update_node', {
                        id: nodeId, name: $('#editNodeName').val(), host: $('#editNodeHost').val(),
                        port: $('#editNodePort').val(), api_key: $('#editNodeApiKey').val(),
                        api_secret: $('#editNodeApiSecret').val(), notes: $('#editNodeNotes').val()
                    }, function(res) {
                        res = typeof res === 'string' ? JSON.parse(res) : res;
                        if (res.status) { layer.msg('更新成功', {icon: 1}); layer.close(index); setTimeout(function() { location.reload(); }, 800); }
                        else layer.msg(res.msg || '更新失败', {icon: 2});
                    });
                }
            });
        }
    });
}

function deleteNode(nodeId) {
    layer.confirm('确定删除该节点吗？相关服务和配置也将被删除', {btn: ['确定', '取消']}, function(index) {
        $.post('/cluster/api?action=delete_node', {id: nodeId}, function(res) {
            res = typeof res === 'string' ? JSON.parse(res) : res;
            if (res.status) { layer.msg('删除成功', {icon: 1}); setTimeout(function() { location.reload(); }, 800); }
            else layer.msg(res.msg || '删除失败', {icon: 2});
        });
        layer.close(index);
    });
}

function testNode(nodeId) {
    var loadIndex = layer.load(2, {shade: [0.3, '#000']});
    $.post('/cluster/api?action=test_connection', {id: nodeId}, function(res) {
        layer.close(loadIndex);
        res = typeof res === 'string' ? JSON.parse(res) : res;
        if (res.status) { layer.msg('连接成功！', {icon: 1}); setTimeout(function() { location.reload(); }, 1000); }
        else layer.msg('连接失败: ' + (res.msg || '未知错误'), {icon: 2});
    }).fail(function() { layer.close(loadIndex); layer.msg('请求失败', {icon: 2}); });
}

function refreshAll() { location.reload(); }

function filterNodes(keyword) {
    var cards = document.querySelectorAll('.cluster-node-card');
    keyword = keyword.toLowerCase();
    cards.forEach(function(card) {
        var name = (card.querySelector('.node-name')?.textContent || '').toLowerCase();
        var host = (card.querySelector('.node-host')?.textContent || '').toLowerCase();
        card.style.display = (name.indexOf(keyword) > -1 || host.indexOf(keyword) > -1) ? '' : 'none';
    });
}

function manageServices(nodeId, nodeName) {
    currentServiceNodeId = nodeId;
    location.href = '/cluster/services?node_id=' + nodeId;
}

function loadServices() {
    if (!currentServiceNodeId) return;
    $.get('/cluster/api?action=get_services', {node_id: currentServiceNodeId}, function(res) {
        res = typeof res === 'string' ? JSON.parse(res) : res;
        if (res.status && res.data) {
            renderServiceTable(res.data.services);
            renderAutoStartTable(res.data.services);
            renderCommonServicesSelect(res.data.common_services);
        }
    });
}

function renderServiceTable(services) {
    var tbody = document.getElementById('serviceTableBody');
    if (!tbody) return;
    var html = '';
    services.forEach(function(svc) {
        var cls = svc.service_status === 'running' ? 'status-running' : (svc.service_status === 'stopped' ? 'status-stopped' : 'status-unknown');
        html += '<tr><td><strong>' + svc.service_name + '</strong></td><td><span class="' + cls + '">' + svc.service_status + '</span></td>' +
            '<td>' + (svc.port || '-') + '</td><td>' + (svc.version || '-') + '</td><td>' +
            '<button class="layui-btn layui-btn-xs layui-btn-normal" onclick="doServiceAction(' + svc.id + ',\'' + svc.service_name + '\',\'start\')">启动</button>' +
            '<button class="layui-btn layui-btn-xs layui-btn-danger" onclick="doServiceAction(' + svc.id + ',\'' + svc.service_name + '\',\'stop\')">停止</button>' +
            '<button class="layui-btn layui-btn-xs layui-btn-warm" onclick="doServiceAction(' + svc.id + ',\'' + svc.service_name + '\',\'restart\')">重启</button>' +
            '<button class="layui-btn layui-btn-xs layui-btn-primary" onclick="doServiceAction(' + svc.id + ',\'' + svc.service_name + '\',\'reload\')">重载配置</button>' +
            '<button class="layui-btn layui-btn-xs" onclick="deleteService(' + svc.id + ')">删除</button></td></tr>';
    });
    if (!services.length) html = '<tr><td colspan="5" style="text-align:center;color:#999;">暂无服务，请添加</td></tr>';
    tbody.innerHTML = html;
}

function renderAutoStartTable(services) {
    var tbody = document.getElementById('autoStartTableBody');
    if (!tbody) return;
    var html = '';
    services.forEach(function(svc) {
        html += '<tr><td>' + svc.service_name + '</td><td>' + (svc.auto_start ? '<span style="color:#5FB878;">已开启</span>' : '<span style="color:#FF5722;">已关闭</span>') + '</td><td>' +
            (svc.auto_start ? '<button class="layui-btn layui-btn-xs layui-btn-danger" onclick="toggleAutoStart(' + svc.id + ',0)">关闭自启动</button>' :
            '<button class="layui-btn layui-btn-xs layui-btn-normal" onclick="toggleAutoStart(' + svc.id + ',1)">开启自启动</button>') + '</td></tr>';
    });
    if (!services.length) html = '<tr><td colspan="3" style="text-align:center;color:#999;">暂无服务</td></tr>';
    tbody.innerHTML = html;
}

function renderCommonServicesSelect(commonServices) {
    var select = document.getElementById('newServiceSelect');
    if (!select) return;
    var html = '<option value="">选择要添加的服务...</option>';
    commonServices.forEach(function(svc) {
        html += '<option value="' + svc.name + '" data-port="' + svc.port + '" data-config="' + (svc.config_path||'') + '">' + svc.display + '</option>';
    });
    select.innerHTML = html;
}

function doServiceAction(serviceId, serviceName, action) {
    var names = {start: '启动', stop: '停止', restart: '重启', reload: '重载配置'};
    layer.confirm('确定要' + (names[action] || action) + ' ' + serviceName + ' 吗？', {btn: ['确定', '取消']}, function(index) {
        layer.close(index);
        var loadIndex = layer.load(2);
        $.post('/cluster/api?action=service_action', {node_id: currentServiceNodeId, service_name: serviceName, action: action}, function(res) {
            layer.close(loadIndex);
            res = typeof res === 'string' ? JSON.parse(res) : res;
            if (res.status) { layer.msg('操作成功', {icon: 1}); loadServices(); }
            else layer.msg(res.msg || '操作失败', {icon: 2});
        }).fail(function() { layer.close(loadIndex); layer.msg('请求失败', {icon: 2}); });
    });
}

function toggleAutoStart(serviceId, autoStart) {
    $.post('/cluster/api?action=update_service_auto_start', {service_id: serviceId, auto_start: autoStart}, function(res) {
        res = typeof res === 'string' ? JSON.parse(res) : res;
        if (res.status) { layer.msg('更新成功', {icon: 1}); loadServices(); }
        else layer.msg(res.msg || '更新失败', {icon: 2});
    });
}

function addServiceToNode() {
    var select = document.getElementById('newServiceSelect');
    if (!select || !select.value) { layer.msg('请选择要添加的服务', {icon: 2}); return; }
    var option = select.options[select.selectedIndex];
    $.post('/cluster/api?action=add_service', {
        node_id: currentServiceNodeId, service_name: select.value,
        port: option.getAttribute('data-port') || 0, config_path: option.getAttribute('data-config') || ''
    }, function(res) {
        res = typeof res === 'string' ? JSON.parse(res) : res;
        if (res.status) { layer.msg('添加成功', {icon: 1}); loadServices(); }
        else layer.msg(res.msg || '添加失败', {icon: 2});
    });
}

function deleteService(serviceId) {
    layer.confirm('确定删除该服务吗？', function(index) {
        $.post('/cluster/api?action=delete_service', {service_id: serviceId}, function(res) {
            res = typeof res === 'string' ? JSON.parse(res) : res;
            if (res.status) { layer.msg('删除成功', {icon: 1}); loadServices(); }
            else layer.msg(res.msg || '删除失败', {icon: 2});
        });
        layer.close(index);
    });
}

function saveDbConfig() {
    $.post('/cluster/api?action=save_db_config', {
        node_id: currentServiceNodeId, db_type: $('#dbType').val(), db_host: $('#dbHost').val(),
        db_port: $('#dbPort').val(), db_name: $('#dbName').val(), db_user: $('#dbUser').val(),
        db_password: $('#dbPassword').val(), db_prefix: $('#dbPrefix').val()
    }, function(res) {
        res = typeof res === 'string' ? JSON.parse(res) : res;
        if (res.status) layer.msg('保存成功', {icon: 1});
        else layer.msg(res.msg || '保存失败', {icon: 2});
    });
}

function testDbConnection() { layer.msg('数据库连接测试（需在远程节点实现）', {icon: 0}); }

function saveSubPanelConfig() {
    var configs = {
        panel_name: $('#subPanelName').val(), panel_port: $('#subPanelPort').val(),
        panel_domain: $('#subPanelDomain').val(), panel_ssl: $('#subPanelSSL').is(':checked') ? '1' : '0',
        panel_entrance: $('#subPanelEntrance').val(), panel_max_conn: $('#subPanelMaxConn').val()
    };
    var promises = [];
    for (var key in configs) {
        (function(k, v) {
            promises.push($.post('/cluster/api?action=save_sub_panel_config', {
                node_id: currentServiceNodeId, config_key: k, config_value: v
            }));
        })(key, configs[key]);
    }
    Promise.all(promises).then(function() { layer.msg('保存成功', {icon: 1}); })
        .catch(function() { layer.msg('部分设置保存失败', {icon: 2}); });
}

$(document).ready(function() {
    if (typeof layui !== 'undefined') {
        layui.use(['element', 'form'], function() { layui.form.render(); });
    }
    if (document.getElementById('serviceTableBody')) {
        var params = new URLSearchParams(window.location.search);
        currentServiceNodeId = parseInt(params.get('node_id') || '0');
        loadServices();
    }
});
