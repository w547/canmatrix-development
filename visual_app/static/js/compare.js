var DbcTool = DbcTool || {};

DbcTool.Compare = (function() {
    var cmpFile1 = null;
    var cmpFile2 = null;
    var diffMap = null;
    var diffOnlyActive = false;

    var tooltipEl = null;
    var tooltipTimer = null;
    var tooltipHideTimer = null;
    var tooltipVisible = false;
    var tooltipRect = null;
    var tooltipMouseTracker = null;

    var treeData1 = null;
    var treeData2 = null;
    var summaryData = [];
    var summaryFilteredData = [];
    var summaryPage = 1;
    var summaryPageSize = 30;

    var SUMMARY_COLUMNS = [
        { header: '父级', key: 'parent', render: function(item) { return item.parent; } },
        { header: '变更类型', key: 'result', render: function(item) {
            var resultMap = { 'added': '新增', 'deleted': '删除', 'removed': '删除', 'changed': '变更' };
            return resultMap[item.result] || item.result;
        }},
        { header: '子级', key: 'child', render: function(item) { return item.child; } },
        { header: '属性', key: 'label', render: function(item) { return item.label || '-'; } },
        { header: '旧值', key: 'old', render: function(item) { return item.old || '-'; } },
        { header: '新值', key: 'new', render: function(item) { return item.new || '-'; } },
        { header: '变更描述', key: 'description', render: function(item) { return item.description; } }
    ];

    var STORAGE_KEY = 'dbctool_compare_data';
    var STORAGE_FILE1_KEY = 'dbctool_compare_file1';
    var STORAGE_FILE2_KEY = 'dbctool_compare_file2';
    var STORAGE_CONVERT_KEY = 'dbctool_convert_data';

    function init() {
        var isFresh = (window.location.search || '').indexOf('fresh=1') >= 0;
        if (isFresh) {
            clearPersistedData();
            clearConvertPersistedData();
            if (window.history && window.history.replaceState) {
                window.history.replaceState({}, '', window.location.pathname);
            }
        }
        initTooltip();
        if (!isFresh) {
            restorePersistedData();
            restoreConvertPersistedData();
        }
    }

    function _saveCompareData(d) {
        try {
            var toSave = {
                diff_map: d.diff_map,
                tree1: d.tree1,
                tree2: d.tree2,
                stats: d.stats,
                comparison: d.comparison,
                timestamp: Date.now()
            };
            localStorage.setItem(STORAGE_KEY, JSON.stringify(toSave));
        } catch (e) {}
    }

    function restorePersistedData() {
        try {
            var raw = localStorage.getItem(STORAGE_KEY);
            if (!raw) return;
            var d = JSON.parse(raw);
            if (!d.diff_map || !d.tree1 || !d.tree2) return;
            diffMap = d.diff_map;
            showResCmp(d);
            var btn = document.getElementById('btnClearCache');
            if (btn) btn.style.display = 'block';
        } catch (e) {}
    }

    function clearPersistedData() {
        try {
            localStorage.removeItem(STORAGE_KEY);
            localStorage.removeItem(STORAGE_FILE1_KEY);
            localStorage.removeItem(STORAGE_FILE2_KEY);
            localStorage.removeItem(STORAGE_CONVERT_KEY);
        } catch (e) {}
        var btn = document.getElementById('btnClearCache');
        if (btn) btn.style.display = 'none';
        hideResCmp();
        document.getElementById('resCardCvt').classList.remove('show');
    }

    function _saveConvertData(d) {
        try {
            var toSave = {
                stats: d.stats,
                download_url: d.download_url,
                output_name: d.output_name,
                timestamp: Date.now()
            };
            localStorage.setItem(STORAGE_CONVERT_KEY, JSON.stringify(toSave));
        } catch (e) {}
    }

    function restoreConvertPersistedData() {
        try {
            var raw = localStorage.getItem(STORAGE_CONVERT_KEY);
            if (!raw) return;
            var d = JSON.parse(raw);
            if (!d.stats || !d.download_url) return;
            document.getElementById('resCardCvt').classList.add('show');
            document.getElementById('statsGridCvt').innerHTML =
                '<div class=stat><div class=stat-val>' + d.stats.total_frames + '</div><div class=stat-lbl>帧数 (Frames)</div></div>' +
                '<div class=stat><div class=stat-val>' + d.stats.total_signals + '</div><div class=stat-lbl>信号数 (Signals)</div></div>' +
                '<div class=stat><div class=stat-val style=font-size:.9rem>' + DbcTool.escapeHtml(d.stats.input_format) + '</div><div class=stat-lbl>输入格式</div></div>' +
                '<div class=stat><div class=stat-val style=font-size:.9rem>' + DbcTool.escapeHtml(d.stats.output_format) + '</div><div class=stat-lbl>输出格式</div></div>';
            var btn = document.getElementById('btnDlCvt');
            btn.href = d.download_url;
            btn.download = d.output_name;
        } catch (e) {}
    }

    function clearConvertPersistedData() {
        try {
            localStorage.removeItem(STORAGE_CONVERT_KEY);
        } catch (e) {}
        document.getElementById('resCardCvt').classList.remove('show');
    }

    function fileInCmp1(f) {
        cmpFile1 = f;
        var ne = document.getElementById('fnameCmp1');
        var z = document.getElementById('zoneCmp1');
        var sz = DbcTool.formatFileSize(f.size);
        ne.textContent = '\u2713 ' + f.name + ' (' + sz + ')';
        ne.style.display = 'block';
        z.classList.add('has-file');
        updBtnCmp();
    }

    function fileInCmp2(f) {
        cmpFile2 = f;
        var ne = document.getElementById('fnameCmp2');
        var z = document.getElementById('zoneCmp2');
        var sz = DbcTool.formatFileSize(f.size);
        ne.textContent = '\u2713 ' + f.name + ' (' + sz + ')';
        ne.style.display = 'block';
        z.classList.add('has-file');
        updBtnCmp();
    }

    function updBtnCmp() {
        var b = document.getElementById('btnGoCmp');
        b.disabled = !(cmpFile1 && cmpFile2);
        b.textContent = cmpFile1 && cmpFile2 ? '\uD83D\uDD0D 开始比较' : cmpFile1 || cmpFile2 ? '请上传两个文件' : '请先上传两个DBC文件';
    }

    function hideResCmp() {
        document.getElementById('resCardCmp').classList.remove('show');
    }

    function doCompare() {
        if (!cmpFile1 || !cmpFile2) return;
        hideResCmp();

        var f = new FormData();
        f.append('file1', cmpFile1);
        f.append('file2', cmpFile2);
        f.append('check_comments', document.getElementById('pComments').checked);
        f.append('check_attributes', document.getElementById('pAttrs').checked);
        f.append('ignore_valuetables', document.getElementById('pValTabs').checked);
        f.append('ignore_defines', document.getElementById('pDefs').checked);

        var btn = document.getElementById('btnGoCmp');
        btn.innerHTML = '<span class="spin"></span> 比较中...';
        btn.disabled = true;

        fetch('/api/compare', { method: 'POST', body: f })
            .then(function(r) { return r.json(); })
            .then(function(d) {
                if (d.success) {
                    showResCmp(d);
                } else {
                    DbcTool.msg('err', d.error);
                }
            })
            .catch(function(e) {
                DbcTool.msg('err', '请求失败: ' + e.message);
            })
            .finally(function() {
                btn.innerHTML = '\uD83D\uDD0D 开始比较';
                updBtnCmp();
            });
    }

    function countDiff(node) {
        var r = { total: 0, added: 0, deleted: 0, changed: 0 };
        function walk(n) {
            if (!n) return;
            if (n.result && n.result !== 'equal' && n.result !== null) {
                r.total++;
                if (n.result === 'added') r.added++;
                else if (n.result === 'deleted') r.deleted++;
                else if (n.result === 'changed') r.changed++;
            }
            if (n.children) n.children.forEach(walk);
        }
        walk(node);
        return r;
    }

    function showResCmp(d) {
        diffMap = d.diff_map;

        var card = document.getElementById('resCardCmp');
        card.classList.add('show');

        var s = d.stats;
        document.getElementById('statsGridCmp').innerHTML =
            '<div class=stat><div class=stat-val>' + s.db1_frames + ' / ' + s.db2_frames + '</div><div class=stat-lbl>帧数 (基准/对比)</div></div>' +
            '<div class=stat><div class=stat-val>' + s.db1_signals + ' / ' + s.db2_signals + '</div><div class=stat-lbl>信号数 (基准/对比)</div></div>' +
            '<div class=stat><div class=stat-val>' + s.db1_ecus + ' / ' + s.db2_ecus + '</div><div class=stat-lbl>ECU数 (基准/对比)</div></div>' +
            '<div class=stat><div class=stat-val style=font-size:.8rem>' + DbcTool.escapeHtml(s.db1_name) + '</div><div class=stat-lbl>基准文件</div></div>' +
            '<div class=stat><div class=stat-val style=font-size:.8rem>' + DbcTool.escapeHtml(s.db2_name) + '</div><div class=stat-lbl>对比文件</div></div>';

        var summary = document.getElementById('diffSummary');
        var counts = countDiff(d.comparison);
        summary.innerHTML =
            '<div class="diff-stat ds-total">\uD83D\uDCCA 总差异: ' + counts.total + '</div>' +
            '<div class="diff-stat ds-added">+ 新增: ' + counts.added + '</div>' +
            '<div class="diff-stat ds-deleted">- 删除: ' + counts.deleted + '</div>' +
            '<div class="diff-stat ds-changed">~ 变更: ' + counts.changed + '</div>';

        document.getElementById('pNameLeft').textContent = s.db1_name;
        document.getElementById('pNameRight').textContent = s.db2_name;

        renderSideTree('cmpBodyLeft', d.tree1, 'base');
        renderSideTree('cmpBodyRight', d.tree2, 'compare');
        treeData1 = d.tree1;
        treeData2 = d.tree2;
        updateSideStats(d.tree1, d.tree2);
        attachTooltipListeners();

        initDivider();
        initSyncScrollbar();

        var btn = document.getElementById('btnDiffOnly');
        btn.classList.remove('active');
        diffOnlyActive = false;
        document.getElementById('btnSummary').disabled = false;
        document.getElementById('btnExport').disabled = false;

        card.scrollIntoView({ behavior: 'smooth' });

        _saveCompareData(d);

        var btnCache = document.getElementById('btnClearCache');
        if (btnCache) btnCache.style.display = 'block';
    }

    function toggleDiffOnly() {
        diffOnlyActive = !diffOnlyActive;
        var btn = document.getElementById('btnDiffOnly');
        var left = document.getElementById('cmpBodyLeft');
        var right = document.getElementById('cmpBodyRight');

        if (diffOnlyActive) {
            btn.classList.add('active');
            applyDiffOnlyFilter(left);
            applyDiffOnlyFilter(right);
        } else {
            btn.classList.remove('active');
            removeDiffOnlyFilter(left);
            removeDiffOnlyFilter(right);
        }

        updateSyncThumbAfterToggle();
    }

    function applyDiffOnlyFilter(container) {
        var allNodes = container.querySelectorAll('.tnode');
        for (var i = 0; i < allNodes.length; i++) {
            if (allNodes[i].classList.contains('expanded')) {
                allNodes[i].setAttribute('data-was-expanded', '1');
            }
        }
        var topNodes = container.querySelectorAll(':scope > .tnode');
        for (var i = 0; i < topNodes.length; i++) {
            applyDiffOnlyFilterNode(topNodes[i]);
        }
    }

    function applyDiffOnlyFilterNode(tnode) {
        var childrenContainer = tnode.querySelector(':scope > .tn-children');
        var childNodes = childrenContainer ? childrenContainer.querySelectorAll(':scope > .tnode') : [];
        var anyChildVisible = false;
        for (var i = 0; i < childNodes.length; i++) {
            if (applyDiffOnlyFilterNode(childNodes[i])) {
                anyChildVisible = true;
            }
        }
        var selfHasDiff = tnode.classList.contains('tn-diff-added') ||
                          tnode.classList.contains('tn-diff-deleted') ||
                          tnode.classList.contains('tn-diff-changed');
        var isContainer = tnode.classList.contains('tn-db') ||
                          tnode.classList.contains('tn-category') ||
                          tnode.classList.contains('tn-signalgroup_category');

        if (selfHasDiff || anyChildVisible || isContainer) {
            tnode.classList.remove('tn-hidden');
            if ((isContainer || anyChildVisible) && childrenContainer) {
                tnode.classList.add('tn-diff-expanded');
            }
            return true;
        } else {
            tnode.classList.add('tn-hidden');
            return false;
        }
    }

    function removeDiffOnlyFilter(container) {
        var allNodes = container.querySelectorAll('.tnode');
        for (var i = 0; i < allNodes.length; i++) {
            allNodes[i].classList.remove('tn-hidden');
            allNodes[i].classList.remove('tn-diff-expanded');
            if (allNodes[i].getAttribute('data-was-expanded') === '1') {
                allNodes[i].classList.add('expanded');
                var arrow = allNodes[i].querySelector(':scope > .tn-row > .tn-arrow');
                if (arrow) arrow.classList.add('open');
            }
            allNodes[i].removeAttribute('data-was-expanded');
        }
    }

    function updateSyncThumbAfterToggle() {
        var syncBar = document.getElementById('cmpSyncScrollbar');
        if (!syncBar) return;
        var syncThumb = document.getElementById('cmpSyncThumb');
        var body = document.getElementById('cmpBodyRight');
        var maxScroll = body.scrollHeight - body.clientHeight;
        if (maxScroll > 0) {
            syncThumb.style.display = '';
            var trackHeight = syncBar.clientHeight;
            var thumbHeight = Math.max(20, (body.clientHeight / body.scrollHeight) * trackHeight);
            syncThumb.style.height = thumbHeight + 'px';
            var thumbTravel = trackHeight - thumbHeight;
            syncThumb.style.top = (body.scrollTop / maxScroll * thumbTravel) + 'px';
        } else {
            syncThumb.style.display = 'none';
        }
    }

    function renderSideTree(containerId, tree, side) {
        var container = document.getElementById(containerId);
        container.innerHTML = renderTreeNode(tree, side, 0);
    }

    function _computeSubtreeAggregate(node) {
        var agg = { total: 0, added: 0, deleted: 0, changed: 0 };
        function walk(n) {
            if (!n) return;
            var typeMap = {
                'ecu': 'ECU', 'frame': 'FRAME', 'signal': 'SIGNAL', 'valuetable': 'VALUETABLE',
                'define': 'DEFINE', 'signalgroup': 'SIGNALGROUP', 'db': 'DATABASE',
                'category': '', 'signalgroup_category': ''
            };
            var dt = typeMap[n.type] || n.type.toUpperCase();
            var dk = dt + '::' + (n.name || '');
            var entry = diffMap ? diffMap[dk] : null;
            var st = entry ? entry.status : null;
            if (n.type !== 'category' && n.type !== 'signalgroup_category' && n.type !== 'db') {
                if (st === 'added') { agg.total++; agg.added++; }
                else if (st === 'deleted') { agg.total++; agg.deleted++; }
                else if (st === 'changed') { agg.total++; agg.changed++; }
            }
            if (n.children) n.children.forEach(walk);
        }
        walk(node);
        return agg;
    }

    function _collectContainerSubtreeChanges(node, maxDepth, excludeTypes, excludeDetailTypes) {
        var allChanges = [];
        function walk(n, depth) {
            if (!n) return;
            if (maxDepth !== undefined && depth > maxDepth) return;
            if (excludeTypes && excludeTypes.indexOf(n.type) >= 0) return;
            var typeMap = {
                'ecu': 'ECU', 'frame': 'FRAME', 'signal': 'SIGNAL', 'valuetable': 'VALUETABLE',
                'define': 'DEFINE', 'signalgroup': 'SIGNALGROUP', 'db': 'DATABASE',
                'category': '', 'signalgroup_category': ''
            };
            var dt = typeMap[n.type] || n.type.toUpperCase();
            var dk = dt + '::' + (n.name || '');
            var entry = diffMap ? diffMap[dk] : null;
            if (entry) {
                if (entry.status === 'changed' && entry.detail_changes) {
                    for (var i = 0; i < entry.detail_changes.length; i++) {
                        var d = entry.detail_changes[i];
                        if (_isContainerChangeType(d.type, d.label)) continue;
                        if (excludeDetailTypes && excludeDetailTypes.indexOf(d.type) >= 0) continue;
                        allChanges.push(d);
                    }
                } else if (entry.status === 'added') {
                    allChanges.push({
                        type: 'added',
                        label: n.name,
                        result: 'added',
                        nodeType: dt,
                        nodeName: n.name
                    });
                } else if (entry.status === 'deleted') {
                    allChanges.push({
                        type: 'deleted',
                        label: n.name,
                        result: 'deleted',
                        nodeType: dt,
                        nodeName: n.name
                    });
                }
            }
            if (n.children) n.children.forEach(function(c) { walk(c, depth + 1); });
        }
        walk(node, 0);
        return allChanges;
    }

    function renderTreeNode(node, side, depth) {
        if (!node) return '';

        var hasChildren = node.children && node.children.length > 0;
        var nodeType = node.type || '';
        var nodeName = node.name || '';
        var diffClass = '';
        var diffBadge = '';
        var tooltipAttr = '';

        var typeMap = {
            'ecu': 'ECU', 'frame': 'FRAME', 'signal': 'SIGNAL', 'valuetable': 'VALUETABLE',
            'define': 'DEFINE', 'signalgroup': 'SIGNALGROUP', 'db': 'DATABASE',
            'category': '', 'signalgroup_category': ''
        };
        var diffKeyType = typeMap[nodeType] || nodeType.toUpperCase();
        var diffKey = diffKeyType + '::' + nodeName;

        var diffEntry = diffMap ? (diffMap[diffKey] || null) : null;
        var diffStatus = diffEntry ? diffEntry.status : null;

        var isContainer = (nodeType === 'db' || nodeType === 'category' || nodeType === 'signalgroup_category');
        var isDb = (nodeType === 'db');

        if (isContainer && hasChildren && !isDb) {
            var containerAgg = _computeSubtreeAggregate(node);
            if (containerAgg.total > 0) {
                diffClass = ' tn-diff-changed';
                var badgeParts = [];
                if (containerAgg.added > 0) badgeParts.push('<span class="tn-diff-badge added">+ADDED:' + containerAgg.added + '</span>');
                if (containerAgg.deleted > 0) badgeParts.push('<span class="tn-diff-badge deleted">-DELETED:' + containerAgg.deleted + '</span>');
                if (containerAgg.changed > 0) badgeParts.push('<span class="tn-diff-badge changed cht-hover">~CHANGED:' + containerAgg.changed + '</span>');
                diffBadge = badgeParts.join(' ');
                tooltipAttr = ' data-cmp-tooltip="' + side + '" data-cmp-key="' + DbcTool.escapeHtml(diffKey) + '" data-cmp-container="1" data-cmp-type="' + DbcTool.escapeHtml(nodeType) + '" data-cmp-name="' + DbcTool.escapeHtml(nodeName) + '"';
            }
        } else if (!isDb) {
            if (diffStatus === 'added') {
                diffClass = ' tn-diff-added';
                diffBadge = '<span class="tn-diff-badge added">+ADDED</span>';
                if (nodeType === 'frame') {
                    tooltipAttr = ' data-cmp-tooltip="' + side + '" data-cmp-key="' + DbcTool.escapeHtml(diffKey) + '"';
                }
            } else if (diffStatus === 'deleted') {
                diffClass = ' tn-diff-deleted';
                diffBadge = '<span class="tn-diff-badge deleted">-DELETED</span>';
                if (nodeType === 'frame') {
                    tooltipAttr = ' data-cmp-tooltip="' + side + '" data-cmp-key="' + DbcTool.escapeHtml(diffKey) + '"';
                }
            } else if (diffStatus === 'changed') {
                diffClass = ' tn-diff-changed';
                diffBadge = '<span class="tn-diff-badge changed cht-hover">~CHANGED</span>';
                tooltipAttr = ' data-cmp-tooltip="' + side + '" data-cmp-key="' + DbcTool.escapeHtml(diffKey) + '"';
            } else if (nodeType !== 'category' && nodeType !== 'db' && nodeType !== 'signalgroup_category') {
                diffClass = '';
            }
        }

        if (diffStatus === 'deleted' && nodeType === 'frame' && node.can_id_hex) {
            diffBadge += ' <span class="tn-meta">' + DbcTool.escapeHtml(node.can_id_hex) + ' DLC:' + node.dlc + '</span>';
        } else if (diffStatus === 'added' && nodeType === 'frame' && node.can_id_hex) {
            diffBadge += ' <span class="tn-meta">' + DbcTool.escapeHtml(node.can_id_hex) + ' DLC:' + node.dlc + '</span>';
        }

        var icon = DbcTool.ICONS[nodeType] || '\u25CF';
        if (diffStatus === 'added') icon = '+';
        else if (diffStatus === 'deleted') icon = '\u2212';
        else if (diffStatus === 'changed') icon = '~';
        else if (isContainer && containerAgg && containerAgg.total > 0) icon = '~';

        var meta = '';
        if (nodeType === 'frame') {
            meta = '<span class="tn-meta">' + DbcTool.escapeHtml(node.can_id_hex) +
                   (node.extended ? ' Ext' : (node.is_fd ? ' FD' : '')) +
                   ' DLC:' + node.dlc +
                   (node.cycle_time ? ' Cyc:' + node.cycle_time + 'ms' : '') + '</span>';
        } else if (nodeType === 'signal') {
            meta = '<span class="tn-meta">bit:' + node.start_bit + ' sz:' + node.size +
                   ' f:' + node.factor + ' o:' + node.offset +
                   (node.unit ? ' [' + DbcTool.escapeHtml(node.unit) + ']' : '') + '</span>';
        } else if (nodeType === 'ecu') {
            if (node.comment) meta = '<span class="tn-meta">' + DbcTool.escapeHtml(node.comment).substring(0, 40) + '</span>';
        } else if (nodeType === 'category') {
            if (node.count !== undefined) meta = '<span class="tn-meta">(' + node.count + ')</span>';
        } else if (nodeType === 'signalgroup') {
            if (node.signals) meta = '<span class="tn-meta">signals: ' + node.signals.length + '</span>';
        }

        var indentPx = depth * 6;
        var cls = 'tnode tn-' + nodeType + diffClass;
        var html = '<div class="' + cls + '" style="padding-left:' + indentPx + 'px"' + tooltipAttr + '>';
        html += '<div class="tn-row" onclick="DbcTool.Compare.toggleTreeNode(this)">';
        html += '<span class="tn-arrow' + (hasChildren ? '' : ' empty') + '">&#x25B6;</span>';
        html += '<span class="tn-icon">' + icon + '</span>';
        html += '<span class="tn-label"><span class="tn-name">' + DbcTool.escapeHtml(nodeName) + '</span>' + meta + diffBadge + '</span>';
        html += '</div>';

        if (hasChildren) {
            html += '<div class="tn-children">';
            var children = node.children.slice();
            children.sort(function(a, b) {
                var na = (a.name || '').toLowerCase();
                var nb = (b.name || '').toLowerCase();
                if (a.type !== b.type) return 0;
                return na < nb ? -1 : na > nb ? 1 : 0;
            });
            for (var i = 0; i < children.length; i++) {
                html += renderTreeNode(children[i], side, depth + 1);
            }
            html += '</div>';
        }
        html += '</div>';
        return html;
    }

    function toggleTreeNode(rowEl) {
        var node = rowEl.parentElement;
        var arrow = rowEl.querySelector('.tn-arrow');
        if (node.classList.contains('tn-diff-expanded')) {
            node.classList.remove('tn-diff-expanded');
            arrow.classList.remove('open');
            setTimeout(function() {
                updateSyncThumbAfterToggle();
            }, 0);
            return;
        }
        node.classList.toggle('expanded');
        if (node.classList.contains('expanded')) {
            arrow.classList.add('open');
        } else {
            arrow.classList.remove('open');
        }
        setTimeout(function() {
            updateSyncThumbAfterToggle();
        }, 0);
    }

    function updateSideStats(tree1, tree2) {
        function countSideStats(tree) {
            var r = { total: 0, added: 0, deleted: 0, changed: 0, equal: 0 };
            function walk(n) {
                if (!n) return;
                var typeMap = {
                    'ecu': 'ECU', 'frame': 'FRAME', 'signal': 'SIGNAL', 'valuetable': 'VALUETABLE',
                    'define': 'DEFINE', 'signalgroup': 'SIGNALGROUP', 'db': 'DATABASE'
                };
                var dt = typeMap[n.type] || n.type.toUpperCase();
                var dk = dt + '::' + (n.name || '');
                var entry = diffMap ? diffMap[dk] : null;
                var st = entry ? entry.status : null;
                if (n.type !== 'category' && n.type !== 'signalgroup_category' && n.type !== 'db') {
                    r.total++;
                    if (st === 'added') r.added++;
                    else if (st === 'deleted') r.deleted++;
                    else if (st === 'changed') r.changed++;
                    else r.equal++;
                }
                if (n.children) n.children.forEach(walk);
            }
            walk(tree);
            return r;
        }

        var ls = countSideStats(tree1);
        var rs = countSideStats(tree2);

        function barHtml(stats) {
            return '<span class="ss-item"><span class="ss-dot ad"></span>+' + stats.added + '</span>' +
                   '<span class="ss-item"><span class="ss-dot dl"></span>-' + stats.deleted + '</span>' +
                   '<span class="ss-item"><span class="ss-dot ch"></span>~' + stats.changed + '</span>' +
                   '<span class="ss-item">Total: ' + stats.total + ' items</span>';
        }
        document.getElementById('cmpStatsLeft').innerHTML = barHtml(ls);
        document.getElementById('cmpStatsRight').innerHTML = barHtml(rs);
    }

    function initDivider() {
        var div = document.getElementById('cmpDivider');
        if (!div || div._dividerInited) return;
        div._dividerInited = true;
        var split = document.getElementById('cmpSplit');
        var left = document.getElementById('cmpPanelLeft');
        var isDragging = false;
        var startX = 0;
        var startLeft = 0;

        div.addEventListener('mousedown', function(e) {
            isDragging = true;
            startX = e.clientX;
            startLeft = left.getBoundingClientRect().width;
            document.body.style.cursor = 'col-resize';
            document.body.style.userSelect = 'none';
            e.preventDefault();
        });

        document.addEventListener('mousemove', function(e) {
            if (!isDragging) return;
            var dx = e.clientX - startX;
            var total = split.getBoundingClientRect().width - 16;
            var pct = ((startLeft + dx) / total) * 100;
            pct = Math.max(15, Math.min(85, pct));
            split.style.gridTemplateColumns = pct + '% 4px calc(' + (100 - pct) + '% - 16px) 12px';
        });

        document.addEventListener('mouseup', function() {
            if (isDragging) {
                isDragging = false;
                document.body.style.cursor = '';
                document.body.style.userSelect = '';
            }
        });
    }

    function initSyncScrollbar() {
        var leftBody = document.getElementById('cmpBodyLeft');
        var rightBody = document.getElementById('cmpBodyRight');
        var syncBar = document.getElementById('cmpSyncScrollbar');
        var syncThumb = document.getElementById('cmpSyncThumb');
        if (!syncBar || syncBar._syncInited) return;
        syncBar._syncInited = true;
        var isDragging = false;
        var dragStartY = 0;
        var dragStartScroll = 0;

        function updateThumb() {
            var body = rightBody;
            var maxScroll = body.scrollHeight - body.clientHeight;
            if (maxScroll <= 0) {
                syncThumb.style.display = 'none';
                return;
            }
            syncThumb.style.display = '';
            var trackHeight = syncBar.clientHeight;
            var thumbHeight = Math.max(20, (body.clientHeight / body.scrollHeight) * trackHeight);
            syncThumb.style.height = thumbHeight + 'px';
            var thumbTravel = trackHeight - thumbHeight;
            var scrollPct = maxScroll > 0 ? body.scrollTop / maxScroll : 0;
            syncThumb.style.top = (scrollPct * thumbTravel) + 'px';
        }

        function syncScrollBoth(scrollTop) {
            var body = rightBody;
            var maxScroll = body.scrollHeight - body.clientHeight;
            if (maxScroll <= 0) return;
            var clamped = Math.max(0, Math.min(scrollTop, maxScroll));
            leftBody.scrollTop = clamped;
            rightBody.scrollTop = clamped;
        }

        rightBody.addEventListener('scroll', function() {
            if (isDragging) return;
            updateThumb();
        });

        syncThumb.addEventListener('mousedown', function(e) {
            isDragging = true;
            dragStartY = e.clientY;
            dragStartScroll = rightBody.scrollTop;
            syncBar.classList.add('dragging');
            document.body.style.userSelect = 'none';
            e.preventDefault();
            e.stopPropagation();
        });

        document.addEventListener('mousemove', function(e) {
            if (!isDragging) return;
            var body = rightBody;
            var maxScroll = body.scrollHeight - body.clientHeight;
            if (maxScroll <= 0) return;
            var trackHeight = syncBar.clientHeight;
            var thumbHeight = syncThumb.offsetHeight;
            var thumbTravel = trackHeight - thumbHeight;
            if (thumbTravel <= 0) return;
            var dy = e.clientY - dragStartY;
            var scrollDelta = (dy / thumbTravel) * maxScroll;
            var newScroll = dragStartScroll + scrollDelta;
            newScroll = Math.max(0, Math.min(newScroll, maxScroll));
            syncScrollBoth(newScroll);
        });

        document.addEventListener('mouseup', function() {
            if (isDragging) {
                isDragging = false;
                syncBar.classList.remove('dragging');
                document.body.style.userSelect = '';
            }
        });

        var observer = new MutationObserver(function() {
            setTimeout(function() { updateThumb(); }, 0);
        });
        observer.observe(rightBody, { childList: true, subtree: true, characterData: true });

        setTimeout(function() { updateThumb(); }, 100);
    }

    function initTooltip() {
        if (!tooltipEl) {
            tooltipEl = document.createElement('div');
            tooltipEl.className = 'cht-tooltip';
            tooltipEl.id = 'chtTooltip';
            tooltipEl.addEventListener('mouseenter', onTooltipEnter);
            tooltipEl.addEventListener('mouseleave', onTooltipLeave);
            tooltipEl.addEventListener('click', onTooltipClick);
            document.body.appendChild(tooltipEl);
        }
        if (!tooltipMouseTracker) {
            document.addEventListener('mousemove', onGlobalMouseMove, { passive: true });
            tooltipMouseTracker = true;
        }
    }

    function onGlobalMouseMove(e) {
        if (!tooltipVisible || !tooltipRect) return;
        var bufferPx = 30;
        var expandedRect = {
            left: tooltipRect.left - bufferPx,
            right: tooltipRect.right + bufferPx,
            top: tooltipRect.top - bufferPx,
            bottom: tooltipRect.bottom + bufferPx
        };
        if (e.clientX >= expandedRect.left && e.clientX <= expandedRect.right &&
            e.clientY >= expandedRect.top && e.clientY <= expandedRect.bottom) {
            clearTimeout(tooltipHideTimer);
            tooltipHideTimer = null;
            tooltipEl.classList.remove('hiding');
        }
    }

    function attachTooltipListeners() {
        var bodies = [document.getElementById('cmpBodyLeft'), document.getElementById('cmpBodyRight')];
        bodies.forEach(function(body) {
            body.removeEventListener('mouseover', onTooltipOver);
            body.removeEventListener('mouseout', onTooltipOut);
            body.addEventListener('mouseover', onTooltipOver);
            body.addEventListener('mouseout', onTooltipOut);
        });
    }

    function _formatDetailLabel(detail, nodeName) {
        var signalName = detail.signal_name || '';
        var label = detail.label || '';
        var ctype = detail.type || '';
        var result = detail.result || '';
        var oldVal = detail.old || '';
        var newVal = detail.new || '';
        var desc = detail.description || '';

        var resultText = '';
        if (result === 'added') resultText = '新增';
        else if (result === 'deleted' || result === 'removed') resultText = '删除';
        else resultText = '变更';

        if (ctype === 'frame_info') {
            var parts = [];
            if (detail.can_id_hex) parts.push(detail.can_id_hex);
            if (detail.dlc) parts.push('DLC:' + detail.dlc);
            if (detail.extended) parts.push('Ext');
            if (detail.is_fd) parts.push('FD');
            if (detail.cycle_time) parts.push('Cyc:' + detail.cycle_time + 'ms');
            var infoStr = parts.length > 0 ? '（' + parts.join(' ') + '）' : '';
            return '【' + label + '】' + infoStr;
        }

        var isContainerEntry = (ctype === 'added' || ctype === 'deleted');
        if (isContainerEntry) {
            var entryNodeType = (detail.nodeType || '').toUpperCase();
            if (entryNodeType === 'FRAME' || entryNodeType === 'SIGNAL' || entryNodeType === 'ECU') {
                return label;
            }
            var typeLabelMap2 = { 'ECU': 'ECU节点', 'VALUETABLE': '值表', 'DEFINE': '定义', 'SIGNALGROUP': '信号组' };
            var tl = typeLabelMap2[entryNodeType] || entryNodeType;
            return '【' + label + '】' + tl + '【' + resultText + '】';
        }

        var isSignalEntry = (ctype === 'signal');
        var isListChange = (label.indexOf('列表变更') >= 0);

        if (isSignalEntry) {
            var sigName = signalName || oldVal || newVal || nodeName;
            if (result === 'deleted' || result === 'removed') {
                return sigName;
            }
            if (result === 'added') {
                return sigName;
            }
            return '【' + sigName + '信号】【' + resultText + '】（' + nodeName + '），' + oldVal + ' → ' + newVal;
        }

        var subject = signalName || nodeName;
        var attrPart = isListChange ? '' : ('的【' + label + '】');

        if (result === 'deleted' || result === 'removed') {
            var delVal = oldVal ? (oldVal + ' → (已删除)') : '(已删除)';
            return '【' + subject + '】' + attrPart + '【' + resultText + '】（' + nodeName + '），' + delVal;
        }

        if (result === 'added') {
            var addVal = newVal ? ('(新增) → ' + newVal) : '(新增)';
            return '【' + subject + '】' + attrPart + '【' + resultText + '】（' + nodeName + '），' + addVal;
        }

        if (desc) {
            return '【' + subject + '】' + attrPart + '，' + desc;
        }

        return '【' + subject + '】' + attrPart + '，' + oldVal + ' → ' + newVal;
    }

    function _isContainerChangeType(ctype, label) {
        if (ctype === 'frame' || ctype === 'ecus' ||
            ctype === 'attributes' || ctype === 'signalgroup') {
            return true;
        }
        return false;
    }

    function _collectFrameSignalChanges(frameName, side) {
        var tree = side === 'base' ? treeData1 : treeData2;
        var signalChanges = [];
        if (!tree) return signalChanges;

        function findFrame(node) {
            if (!node) return null;
            if (node.type === 'frame' && node.name === frameName) return node;
            if (node.children) {
                for (var i = 0; i < node.children.length; i++) {
                    var found = findFrame(node.children[i]);
                    if (found) return found;
                }
            }
            return null;
        }

        function collectSignals(node) {
            if (!node) return;
            if (node.type === 'signal') {
                var sigKey = 'SIGNAL::' + node.name;
                var sigEntry = diffMap ? diffMap[sigKey] : null;
                if (sigEntry) {
                    if (sigEntry.status === 'changed' && sigEntry.detail_changes) {
                        for (var k = 0; k < sigEntry.detail_changes.length; k++) {
                            var d = sigEntry.detail_changes[k];
                            if (!_isContainerChangeType(d.type, d.label)) {
                                signalChanges.push(d);
                            }
                        }
                    } else if (sigEntry.status === 'added') {
                        signalChanges.push({
                            type: 'signal',
                            label: node.name,
                            result: 'added',
                            signal_name: node.name,
                            nodeName: node.name
                        });
                    } else if (sigEntry.status === 'deleted') {
                        signalChanges.push({
                            type: 'signal',
                            label: node.name,
                            result: 'deleted',
                            signal_name: node.name,
                            nodeName: node.name
                        });
                    }
                }
            }
            if (node.children) {
                for (var j = 0; j < node.children.length; j++) {
                    collectSignals(node.children[j]);
                }
            }
        }

        var frameNode = findFrame(tree);
        if (frameNode) {
            collectSignals(frameNode);
        }
        return signalChanges;
    }

    function _getFrameInfo(frameName, side) {
        var tree = side === 'base' ? treeData1 : treeData2;
        if (!tree) return null;

        function findFrame(node) {
            if (!node) return null;
            if (node.type === 'frame' && node.name === frameName) return node;
            if (node.children) {
                for (var i = 0; i < node.children.length; i++) {
                    var found = findFrame(node.children[i]);
                    if (found) return found;
                }
            }
            return null;
        }

        var frameNode = findFrame(tree);
        if (!frameNode) return null;
        return {
            can_id_hex: frameNode.can_id_hex || '',
            dlc: frameNode.dlc || '',
            cycle_time: frameNode.cycle_time || '',
            extended: frameNode.extended || false,
            is_fd: frameNode.is_fd || false
        };
    }

    var _pendingTooltipEl = null;
    var _pendingTooltipEvent = null;

    function _showTooltipContent(el, e) {
        var key = el.getAttribute('data-cmp-key');
        var isContainer = el.getAttribute('data-cmp-container') === '1';

        var typeMap = {
            'ECU': 'ECU节点', 'FRAME': '帧/消息', 'SIGNAL': '信号', 'VALUETABLE': '值表',
            'DEFINE': '定义', 'SIGNALGROUP': '信号组', 'DATABASE': '数据库',
            'category': '分类', 'signalgroup_category': '信号组分类', 'db': '数据库'
        };
        var typeLabelMap = {
            'category': '分类', 'signalgroup_category': '信号组分类', 'db': '数据库'
        };
        var keyParts = key.split('::');
        var nodeType = keyParts[0] || '';
        var nodeName = keyParts.slice(1).join('::') || '';

        var containerType = '';
        var containerName = nodeName;
        if (isContainer) {
            containerType = el.getAttribute('data-cmp-type') || '';
            nodeType = containerType.toUpperCase();
            if (containerType === 'db') nodeType = 'DATABASE';
            else if (containerType === 'category') nodeType = 'CATEGORY';
            else if (containerType === 'signalgroup_category') nodeType = 'SIGNALGROUP_CATEGORY';
        }

        var nodeTypeLabel = typeMap[nodeType] || typeLabelMap[nodeType] || nodeType;

        var side = el.getAttribute('data-cmp-tooltip');

        var allDetails = [];
        var directChanges = [];

        if (isContainer) {
            var tree = side === 'base' ? treeData1 : treeData2;
            if (tree) {
                containerName = el.getAttribute('data-cmp-name') || nodeName;
                function findNode(n) {
                    if (!n) return null;
                    var expectedType = nodeType === 'DATABASE' ? 'db' :
                                       nodeType === 'CATEGORY' ? 'category' :
                                       nodeType === 'SIGNALGROUP_CATEGORY' ? 'signalgroup_category' :
                                       nodeType.toLowerCase();
                    if (n.name === containerName && n.type === expectedType) return n;
                    if (n.children) {
                        for (var ci = 0; ci < n.children.length; ci++) {
                            var found = findNode(n.children[ci]);
                            if (found) return found;
                        }
                    }
                    return null;
                }
                var containerNode = findNode(tree);
                if (containerNode) {
                    var maxDepth, excludeTypes, excludeDetailTypes;
                    if (containerType === 'category') {
                        var catName = (containerName || '').toLowerCase();
                        if (catName.indexOf('message') >= 0 || catName.indexOf('frame') >= 0) {
                            maxDepth = undefined;
                            excludeTypes = ['signal'];
                            excludeDetailTypes = ['signal'];
                        } else {
                            maxDepth = 1;
                            excludeTypes = ['frame', 'signal', 'signalgroup'];
                            excludeDetailTypes = undefined;
                        }
                    } else if (containerType === 'signalgroup_category') {
                        maxDepth = undefined;
                        excludeTypes = undefined;
                        excludeDetailTypes = undefined;
                    } else {
                        maxDepth = undefined;
                        excludeTypes = undefined;
                        excludeDetailTypes = undefined;
                    }
                    allDetails = _collectContainerSubtreeChanges(containerNode, maxDepth, excludeTypes, excludeDetailTypes);
                }
            }
        } else {
            var entry = diffMap ? (diffMap[key] || null) : null;
            if (!entry) return;
            var isAddedFrame = (entry.status === 'added' && nodeType === 'FRAME');
            var isDeletedFrame = (entry.status === 'deleted' && nodeType === 'FRAME');
            if (entry.status !== 'changed' && !isAddedFrame && !isDeletedFrame) return;
            var detailList = entry.detail_changes || [];
            directChanges = entry.changes || [];

            if (isAddedFrame || isDeletedFrame) {
                var frameInfo = _getFrameInfo(nodeName, side);
                if (frameInfo) {
                    allDetails.push({
                        type: 'frame_info',
                        label: nodeName,
                        result: isAddedFrame ? 'added' : 'deleted',
                        can_id_hex: frameInfo.can_id_hex,
                        dlc: frameInfo.dlc,
                        cycle_time: frameInfo.cycle_time,
                        extended: frameInfo.extended,
                        is_fd: frameInfo.is_fd,
                        nodeName: nodeName
                    });
                }
            } else if (nodeType === 'FRAME') {
                var signalChanges = _collectFrameSignalChanges(nodeName, side);
                for (var sc = 0; sc < signalChanges.length; sc++) {
                    allDetails.push(signalChanges[sc]);
                }
                for (var fi = 0; fi < detailList.length; fi++) {
                    var fd = detailList[fi];
                    if (fd.type === 'signal') continue;
                    if (!_isContainerChangeType(fd.type, fd.label)) {
                        allDetails.push(fd);
                    }
                }
            } else {
                for (var i = 0; i < detailList.length; i++) {
                    if (!_isContainerChangeType(detailList[i].type, detailList[i].label)) {
                        allDetails.push(detailList[i]);
                    }
                }
            }
        }

        var addedItems = [], deletedItems = [], changedItems = [];
        for (var j = 0; j < allDetails.length; j++) {
            var d = allDetails[j];
            if (d.result === 'added') {
                addedItems.push(d);
            } else if (d.result === 'deleted' || d.result === 'removed') {
                deletedItems.push(d);
            } else {
                changedItems.push(d);
            }
        }

        var totalChanges = addedItems.length + deletedItems.length + changedItems.length;
        if (!isContainer && totalChanges === 0 && directChanges.length >= 2) totalChanges = 1;

        var isFrameContext = (!isContainer && nodeType === 'FRAME');
        var isAddedFrame = (!isContainer && nodeType === 'FRAME' && entry && entry.status === 'added');
        var isDeletedFrame = (!isContainer && nodeType === 'FRAME' && entry && entry.status === 'deleted');
        var isMsgCategoryContext = (isContainer && containerType === 'category' &&
            ((containerName || '').toLowerCase().indexOf('message') >= 0 ||
             (containerName || '').toLowerCase().indexOf('frame') >= 0));

        var addedLabel, deletedLabel, changedLabel;
        if (isAddedFrame || isDeletedFrame) {
            addedLabel = '报文信息';
            deletedLabel = '报文信息';
            changedLabel = '修改项';
        } else if (isFrameContext) {
            addedLabel = '新增信号';
            deletedLabel = '删除信号';
            changedLabel = '修改项';
        } else if (isMsgCategoryContext) {
            addedLabel = '新增报文';
            deletedLabel = '删除报文';
            changedLabel = '修改项';
        } else {
            addedLabel = '新增项';
            deletedLabel = '删除项';
            changedLabel = '修改项';
        }

        var now = new Date();
        var timeStr = now.getFullYear() + '-' +
            ('0' + (now.getMonth() + 1)).slice(-2) + '-' +
            ('0' + now.getDate()).slice(-2) + ' ' +
            ('0' + now.getHours()).slice(-2) + ':' +
            ('0' + now.getMinutes()).slice(-2) + ':' +
            ('0' + now.getSeconds()).slice(-2);

        var html = '';
        html += '<div class="cht-hd"><div class="cht-title">&#x26A0; 变更检测 ~ [CHANGED]</div><div class="cht-node">' + DbcTool.escapeHtml(nodeTypeLabel) + ' &raquo; <strong>' + DbcTool.escapeHtml(nodeName) + '</strong></div><div class="cht-time">&#x1F552; 变更时间: ' + timeStr + '</div></div>';
        html += '<div class="cht-bd">';

        if (isContainer) {
            html += '<div class="cht-reason"><strong>判断依据:</strong> 该 ' + nodeTypeLabel + ' 层级下子结构在两个 DBC 文件中存在 <strong>' + totalChanges + '</strong> 项差异。汇总如下：</div>';
        } else {
            html += '<div class="cht-reason"><strong>判断依据:</strong> 该 ' + nodeTypeLabel + ' 在两个 DBC 文件中存在 <strong>' + totalChanges + '</strong> 项差异。系统逐字段对比后发现以下变更：</div>';
        }

        if (allDetails.length > 0) {
            if (addedItems.length > 0) {
                html += '<div class="cht-section"><div class="cht-section-title cht-sec-added" data-cht-toggle="added"><span>&#x2795; ' + addedLabel + ' (' + addedItems.length + ')</span><span class="cht-toggle">&#x25B2;</span></div><div class="cht-section-body">';
                for (var ai = 0; ai < addedItems.length; ai++) {
                    var formattedAdd = _formatDetailLabel(addedItems[ai], nodeName);
                    html += '<div class="cht-item cht-item-added"><span class="cht-ival">' + DbcTool.escapeHtml(formattedAdd) + '</span></div>';
                }
                html += '</div></div>';
            }
            if (deletedItems.length > 0) {
                html += '<div class="cht-section"><div class="cht-section-title cht-sec-deleted" data-cht-toggle="deleted"><span>&#x2796; ' + deletedLabel + ' (' + deletedItems.length + ')</span><span class="cht-toggle">&#x25B2;</span></div><div class="cht-section-body">';
                for (var di = 0; di < deletedItems.length; di++) {
                    var formattedDel = _formatDetailLabel(deletedItems[di], nodeName);
                    html += '<div class="cht-item cht-item-deleted"><span class="cht-ival">' + DbcTool.escapeHtml(formattedDel) + '</span></div>';
                }
                html += '</div></div>';
            }
            if (changedItems.length > 0) {
                html += '<div class="cht-section"><div class="cht-section-title cht-sec-changed" data-cht-toggle="changed"><span>&#x1F504; ' + changedLabel + ' (' + changedItems.length + ')</span><span class="cht-toggle">&#x25B2;</span></div><div class="cht-section-body">';
                for (var ci = 0; ci < changedItems.length; ci++) {
                    var formattedCh = _formatDetailLabel(changedItems[ci], nodeName);
                    html += '<div class="cht-item cht-item-changed"><span class="cht-ival">' + DbcTool.escapeHtml(formattedCh) + '</span></div>';
                }
                html += '</div></div>';
            }
        } else if (!isContainer && directChanges.length >= 2) {
            html += '<div class="cht-vs"><div class="cht-vs-old"><span class="cht-vs-label">[OLD] 基准文件</span>' + DbcTool.escapeHtml(directChanges[0]) + '</div><div class="cht-vs-new"><span class="cht-vs-label">[NEW] 对比文件</span>' + DbcTool.escapeHtml(directChanges[1]) + '</div></div>';
        }
        html += '<div class="cht-rule"><div class="cht-rule-label">&#x1F50D; 判断标准</div><div class="cht-reason" style="border:none;padding:4px 0">系统对两个 DBC 文件中 <strong>相同名称</strong> 的 ' + nodeTypeLabel + ' 进行 <strong>逐字段</strong> 深度比较。当任意字段值不一致时，标记为 <strong style="color:var(--yellow)">CHANGED</strong>。</div></div>';
        html += '</div>';
        html += '<div class="cht-ft">' + nodeTypeLabel + ' &middot; 差异项数: ' + totalChanges + ' &middot; ' + timeStr + '</div>';

        tooltipEl.innerHTML = html;

        var tw = tooltipEl.offsetWidth || 280;
        var th = tooltipEl.offsetHeight || 200;
        var resCard = document.getElementById('resCardCmp');
        var resRect = resCard.getBoundingClientRect();
        var left, top;
        if (side === 'base') {
            left = resRect.left - tw - 10;
            if (left < 10) left = 10;
        } else {
            left = resRect.right + 10;
            if (left + tw > window.innerWidth - 10) left = window.innerWidth - tw - 10;
            if (left < 10) left = 10;
        }
        top = e.clientY - th / 2;
        if (top + th > window.innerHeight - 10) top = window.innerHeight - th - 10;
        if (top < 10) top = 10;
        tooltipEl.style.left = left + 'px';
        tooltipEl.style.top = top + 'px';
        tooltipEl.classList.add('show');
        tooltipEl.classList.remove('hiding');
        tooltipVisible = true;
        tooltipRect = tooltipEl.getBoundingClientRect();
    }

    function onTooltipOver(e) {
        var el = e.target.closest('[data-cmp-tooltip]');
        if (!el) return;

        var frameNode = e.target.closest('.tn-frame');
        if (frameNode && !frameNode.hasAttribute('data-cmp-tooltip')) {
            return;
        }
        if (frameNode && frameNode.hasAttribute('data-cmp-tooltip')) {
            var isChanged = frameNode.classList.contains('tn-diff-changed');
            if (isChanged) {
                var signalNode = e.target.closest('.tn-signal');
                if (signalNode && !signalNode.hasAttribute('data-cmp-tooltip')) {
                    return;
                }
            }
            var isAddedOrDeleted = frameNode.classList.contains('tn-diff-added') || frameNode.classList.contains('tn-diff-deleted');
            if (isAddedOrDeleted) {
                signalNode = e.target.closest('.tn-signal');
                if (signalNode) {
                    return;
                }
            }
        }

        clearTimeout(tooltipHideTimer);
        tooltipHideTimer = null;

        if (tooltipVisible && _pendingTooltipEl === el) {
            return;
        }

        if (tooltipVisible && _pendingTooltipEl && _pendingTooltipEl !== el) {
            clearTimeout(tooltipTimer);
            tooltipEl.classList.remove('hiding');
            tooltipEl.classList.remove('show');
            tooltipVisible = false;
        }

        clearTimeout(tooltipTimer);
        tooltipEl.classList.remove('hiding');

        _pendingTooltipEl = el;
        _pendingTooltipEvent = e;

        tooltipTimer = setTimeout(function() {
            if (_pendingTooltipEl) {
                _showTooltipContent(_pendingTooltipEl, _pendingTooltipEvent);
                _pendingTooltipEl = null;
                _pendingTooltipEvent = null;
                tooltipVisible = true;
                tooltipRect = tooltipEl.getBoundingClientRect();
            }
        }, 250);
    }

    function onTooltipOut(e) {
        var el = e.target.closest('[data-cmp-tooltip]');
        if (!el) return;
        clearTimeout(tooltipTimer);
        _pendingTooltipEl = null;
        _pendingTooltipEvent = null;

        clearTimeout(tooltipHideTimer);
        tooltipHideTimer = setTimeout(function() {
            if (!tooltipVisible) return;
            tooltipEl.classList.add('hiding');
            tooltipHideTimer = setTimeout(function() {
                tooltipEl.classList.remove('show');
                tooltipEl.classList.remove('hiding');
                tooltipVisible = false;
                tooltipRect = null;
            }, 300);
        }, 250);
    }

    function onTooltipEnter() {
        clearTimeout(tooltipTimer);
        clearTimeout(tooltipHideTimer);
        tooltipHideTimer = null;
        tooltipEl.classList.remove('hiding');
        tooltipEl.classList.add('show');
        tooltipVisible = true;
        tooltipRect = tooltipEl.getBoundingClientRect();
    }

    function onTooltipLeave() {
        clearTimeout(tooltipHideTimer);
        tooltipHideTimer = setTimeout(function() {
            if (!tooltipVisible) return;
            tooltipEl.classList.add('hiding');
            tooltipHideTimer = setTimeout(function() {
                tooltipEl.classList.remove('show');
                tooltipEl.classList.remove('hiding');
                tooltipVisible = false;
                tooltipRect = null;
            }, 300);
        }, 200);
    }

    function onTooltipClick(e) {
        var toggle = e.target.closest('.cht-section-title');
        if (!toggle) return;
        var section = toggle.parentElement;
        var body = section.querySelector('.cht-section-body');
        var icon = toggle.querySelector('.cht-toggle');
        if (!body || !icon) return;
        if (body.classList.contains('collapsed')) {
            body.classList.remove('collapsed');
            body.style.maxHeight = '';
            icon.classList.remove('collapsed');
            icon.innerHTML = '&#x25B2;';
        } else {
            body.classList.add('collapsed');
            icon.classList.add('collapsed');
            icon.innerHTML = '&#x25BC;';
        }
    }

    function _buildSummaryData() {
        summaryData = [];
        if (!diffMap) return;

        var parentIdCounter = 0;
        var seenKeys = {};

        function walkTree(node, categoryParent) {
            if (!node) return;

            var currentParent = categoryParent;
            if (node.type === 'category') {
                currentParent = node.name;
            }

            if (node.type !== 'category' && node.type !== 'db' && node.type !== 'signalgroup_category' && node.type !== 'signal') {
                var typeMap = {
                    'ecu': 'ECU', 'frame': 'FRAME',
                    'valuetable': 'VALUETABLE', 'define': 'DEFINE',
                    'signalgroup': 'SIGNALGROUP'
                };
                var diffKeyType = typeMap[node.type] || node.type.toUpperCase();
                var diffKey = diffKeyType + '::' + (node.name || '');
                var entry = diffMap[diffKey] || null;

                if (entry && !seenKeys[diffKey]) {
                    seenKeys[diffKey] = true;
                    if (node.type === 'frame') {
                        _addFrameSummaryEntries(node, entry, currentParent, parentIdCounter++);
                    } else {
                        _addItemSummaryEntry(node, entry, currentParent);
                    }
                }
            }

            if (node.children) {
                for (var i = 0; i < node.children.length; i++) {
                    walkTree(node.children[i], currentParent);
                }
            }
        }

        if (treeData2) walkTree(treeData2, 'CAN Database');

        function walkForDeleted(node, categoryParent) {
            if (!node) return;

            var currentParent = categoryParent;
            if (node.type === 'category') {
                currentParent = node.name;
            }

            if (node.type !== 'category' && node.type !== 'db' && node.type !== 'signalgroup_category' && node.type !== 'signal') {
                var typeMap = {
                    'ecu': 'ECU', 'frame': 'FRAME',
                    'valuetable': 'VALUETABLE', 'define': 'DEFINE',
                    'signalgroup': 'SIGNALGROUP'
                };
                var diffKeyType = typeMap[node.type] || node.type.toUpperCase();
                var diffKey = diffKeyType + '::' + (node.name || '');
                var entry = diffMap[diffKey] || null;

                if (entry && entry.status === 'deleted' && !seenKeys[diffKey]) {
                    seenKeys[diffKey] = true;
                    if (node.type === 'frame') {
                        _addFrameSummaryEntries(node, entry, currentParent, parentIdCounter++);
                    } else {
                        _addItemSummaryEntry(node, entry, currentParent);
                    }
                }
            }

            if (node.children) {
                for (var i = 0; i < node.children.length; i++) {
                    walkForDeleted(node.children[i], currentParent);
                }
            }
        }

        if (treeData1) walkForDeleted(treeData1, 'CAN Database');

        summaryFilteredData = summaryData.slice();
    }

    function _addItemSummaryEntry(node, entry, parent) {
        var nodeName = node.name || '';
        var desc;
        if (entry.status === 'added') {
            desc = '新增' + nodeName;
        } else if (entry.status === 'deleted') {
            desc = '删除' + nodeName;
        } else {
            var detailChanges = entry.detail_changes || [];
            if (detailChanges.length > 0) {
                for (var i = 0; i < detailChanges.length; i++) {
                    var d = detailChanges[i];
                    if (_isContainerChangeType(d.type, d.label)) continue;
                    var dDesc;
                    if (d.result === 'added') {
                        dDesc = '新增' + (d.label || nodeName);
                    } else if (d.result === 'deleted' || d.result === 'removed') {
                        dDesc = '删除' + (d.label || nodeName);
                    } else {
                        dDesc = (d.label || '') + ': ' + (d.old || '') + ' → ' + (d.new || '');
                    }
                    summaryData.push({
                        parent: parent,
                        result: d.result || 'changed',
                        child: nodeName,
                        label: d.label || '',
                        old: d.old || '',
                        new: d.new || '',
                        description: dDesc
                    });
                }
                return;
            }
            if (entry.changes && entry.changes.length >= 2) {
                desc = (entry.changes[0] || '') + ' → ' + (entry.changes[1] || '');
            } else {
                desc = '变更';
            }
        }
        summaryData.push({
            parent: parent,
            result: entry.status,
            child: nodeName,
            label: '',
            old: entry.status === 'added' ? '' : (entry.changes ? entry.changes[0] || '' : ''),
            new: entry.status === 'deleted' ? '' : (entry.changes ? entry.changes[1] || '' : ''),
            description: desc
        });
    }

    function _addFrameSummaryEntries(frameNode, entry, parent, parentId) {
        var frameName = frameNode.name || '';
        var isAdded = entry.status === 'added';
        var isDeleted = entry.status === 'deleted';

        if (isAdded || isDeleted) {
            var desc = (isAdded ? '新增' : '删除') + frameName;
            var parentItem = {
                parent: parent,
                result: isAdded ? 'added' : 'deleted',
                child: frameName,
                label: '',
                old: '',
                new: isAdded ? frameName : '',
                description: desc,
                _isParent: true,
                _parentId: parentId,
                _children: [],
                _expanded: false
            };
            summaryData.push(parentItem);

            var signalTree = isAdded ? treeData2 : treeData1;
            var frameForSignals = _findFrameInTree(frameName, signalTree);
            if (frameForSignals && frameForSignals.children) {
                _collectAllSignalsAsChildren(frameForSignals, isAdded ? 'added' : 'deleted', frameName, parentId, parentItem);
            }
            return;
        }

        var detailChanges = entry.detail_changes || [];
        var frameAttrChanges = [];
        var signalChanges = [];
        var seenSignalAttrKeys = {};
        var changedSignalNames = {};

        for (var i = 0; i < detailChanges.length; i++) {
            var d = detailChanges[i];
            if (d.type === 'signal') {
                var sigName = d.signal_name || d.label || '';
                if (sigName && !changedSignalNames[sigName]) {
                    changedSignalNames[sigName] = d;
                }
            } else if (!_isContainerChangeType(d.type, d.label)) {
                frameAttrChanges.push(d);
            }
        }

        var frameInTree = _findFrameInTree(frameName, treeData1) || _findFrameInTree(frameName, treeData2);
        if (frameInTree) {
            var treeSigChanges = _collectFrameSignalChangesFromNode(frameInTree);
            for (var j = 0; j < treeSigChanges.length; j++) {
                var tsc = treeSigChanges[j];
                var tsKey = (tsc.signal_name || '') + '::' + (tsc.label || '');
                if (!seenSignalAttrKeys[tsKey]) {
                    seenSignalAttrKeys[tsKey] = true;
                    signalChanges.push(tsc);
                    var sn = tsc.signal_name || '';
                    if (sn && changedSignalNames[sn]) {
                        changedSignalNames[sn]._hasDetails = true;
                    }
                }
            }
        }

        var fallbackNames = Object.keys(changedSignalNames);
        for (var fb = 0; fb < fallbackNames.length; fb++) {
            var fbName = fallbackNames[fb];
            var fbEntry = changedSignalNames[fbName];
            if (!fbEntry._hasDetails) {
                signalChanges.push({
                    type: 'signal',
                    label: '',
                    old: fbEntry.old || '',
                    new: fbEntry.new || '',
                    result: fbEntry.result || 'changed',
                    signal_name: fbName
                });
            }
        }

        var hasChildren = signalChanges.length > 0;

        if (frameAttrChanges.length === 0 && !hasChildren) {
            if (entry.changes && entry.changes.length >= 2) {
                summaryData.push({
                    parent: parent,
                    result: 'changed',
                    child: frameName,
                    label: '整体变更',
                    old: entry.changes[0] || '',
                    new: entry.changes[1] || '',
                    description: (entry.changes[0] || '') + ' → ' + (entry.changes[1] || '')
                });
            }
            return;
        }

        for (var k = 0; k < frameAttrChanges.length; k++) {
            var fc = frameAttrChanges[k];
            var fcDesc = fc.label + ': ' + (fc.old || '') + ' → ' + (fc.new || '');
            summaryData.push({
                parent: parent,
                result: 'changed',
                child: frameName,
                label: fc.label,
                old: fc.old || '',
                new: fc.new || '',
                description: fcDesc,
                _isParent: false,
                _parentId: parentId
            });
        }

        if (hasChildren) {
            var parentItem = {
                parent: parent,
                result: 'changed',
                child: frameName,
                label: '',
                old: '',
                new: '',
                description: frameName + '信号变更',
                _isParent: true,
                _parentId: parentId,
                _children: [],
                _expanded: false
            };
            summaryData.push(parentItem);
            _addSignalChildren(signalChanges, frameName, parentId, parentItem);
        }
    }

    function _addSignalChildren(signalChanges, frameName, parentId, parentItem) {
        for (var i = 0; i < signalChanges.length; i++) {
            var sc = signalChanges[i];
            var sigName = sc.signal_name || sc.label || '';
            var sigDesc;
            if (sc.result === 'added') {
                sigDesc = '新增信号' + sigName;
            } else if (sc.result === 'deleted' || sc.result === 'removed') {
                sigDesc = '删除信号' + sigName;
            } else {
                sigDesc = (sc.label || '') + ': ' + (sc.old || '') + ' → ' + (sc.new || '');
            }
            parentItem._children.push({
                parent: frameName,
                result: sc.result || 'changed',
                child: sigName,
                label: sc.label || '',
                old: sc.old || '',
                new: sc.new || '',
                description: sigDesc,
                _isChild: true,
                _parentId: parentId
            });
        }
    }

    function _collectAllSignalsAsChildren(frameNode, status, frameName, parentId, parentItem) {
        function walkSignals(node) {
            if (!node) return;
            if (node.type === 'signal') {
                var sigName = node.name || '';
                var desc = (status === 'added' ? '新增信号' : '删除信号') + sigName;
                parentItem._children.push({
                    parent: frameName,
                    result: status,
                    child: sigName,
                    label: '',
                    old: '',
                    new: status === 'added' ? sigName : '',
                    description: desc,
                    _isChild: true,
                    _parentId: parentId
                });
            }
            if (node.children) {
                for (var i = 0; i < node.children.length; i++) {
                    walkSignals(node.children[i]);
                }
            }
        }
        walkSignals(frameNode);
    }

    function _findFrameInTree(frameName, tree) {
        if (!tree) return null;
        function find(node) {
            if (!node) return null;
            if (node.type === 'frame' && node.name === frameName) return node;
            if (node.children) {
                for (var i = 0; i < node.children.length; i++) {
                    var found = find(node.children[i]);
                    if (found) return found;
                }
            }
            return null;
        }
        return find(tree);
    }

    function _collectFrameSignalChangesFromNode(frameNode) {
        var signalChanges = [];
        if (!frameNode || !frameNode.children) return signalChanges;

        function collect(node) {
            if (!node) return;
            if (node.type === 'signal') {
                var sigKey = 'SIGNAL::' + node.name;
                var sigEntry = diffMap ? diffMap[sigKey] : null;
                if (sigEntry) {
                    if (sigEntry.status === 'changed' && sigEntry.detail_changes) {
                        for (var k = 0; k < sigEntry.detail_changes.length; k++) {
                            var d = sigEntry.detail_changes[k];
                            if (!_isContainerChangeType(d.type, d.label)) {
                                signalChanges.push(d);
                            }
                        }
                    } else if (sigEntry.status === 'added') {
                        signalChanges.push({
                            type: 'signal', label: '', result: 'added',
                            signal_name: node.name, nodeName: node.name
                        });
                    } else if (sigEntry.status === 'deleted') {
                        signalChanges.push({
                            type: 'signal', label: '', result: 'deleted',
                            signal_name: node.name, nodeName: node.name
                        });
                    }
                }
            }
            if (node.children) {
                for (var j = 0; j < node.children.length; j++) {
                    collect(node.children[j]);
                }
            }
        }

        for (var i = 0; i < frameNode.children.length; i++) {
            collect(frameNode.children[i]);
        }
        return signalChanges;
    }

    function openSummary() {
        _buildSummaryData();
        summaryPage = 1;
        _populateNodeFilter();
        _applyFilters();
        var overlay = document.getElementById('summaryOverlay');
        overlay.classList.add('show');
        document.body.style.overflow = 'hidden';
    }

    function closeSummary() {
        var overlay = document.getElementById('summaryOverlay');
        overlay.classList.remove('show');
        document.body.style.overflow = '';
    }

    function _populateNodeFilter() {
        var sel = document.getElementById('summaryNodeFilter');
        var nodes = {};
        for (var i = 0; i < summaryData.length; i++) {
            nodes[summaryData[i].child] = true;
        }
        sel.innerHTML = '<option value="all">全部节点</option>';
        var nodeNames = Object.keys(nodes).sort();
        for (var j = 0; j < nodeNames.length; j++) {
            sel.innerHTML += '<option value="' + DbcTool.escapeHtml(nodeNames[j]) + '">' + DbcTool.escapeHtml(nodeNames[j]) + '</option>';
        }
    }

    function _applyFilters() {
        var searchText = (document.getElementById('summarySearch').value || '').toLowerCase();
        var typeFilter = document.getElementById('summaryFilter').value;
        var nodeFilter = document.getElementById('summaryNodeFilter').value;

        summaryFilteredData = [];
        for (var i = 0; i < summaryData.length; i++) {
            var item = summaryData[i];
            if (typeFilter !== 'all' && item.result !== typeFilter) continue;
            if (nodeFilter !== 'all' && item.child !== nodeFilter) continue;
            if (searchText) {
                var searchTarget = (item.parent + ' ' + item.child + ' ' + item.label + ' ' + item.old + ' ' + item.new + ' ' + item.description).toLowerCase();
                if (searchTarget.indexOf(searchText) < 0) continue;
            }
            summaryFilteredData.push(item);
        }
        summaryPage = 1;
        _renderSummaryTable();
    }

    function filterSummary() {
        _applyFilters();
    }

    function _renderSummaryTable() {
        var body = document.getElementById('summaryBody');
        var pagination = document.getElementById('summaryPagination');
        var countEl = document.getElementById('summaryCount');

        var total = summaryFilteredData.length;
        countEl.textContent = '共 ' + total + ' 条记录';

        if (total === 0) {
            body.innerHTML = '<div class="summary-empty">未找到匹配的变更记录</div>';
            pagination.innerHTML = '';
            return;
        }

        var totalPages = Math.ceil(total / summaryPageSize);
        if (summaryPage > totalPages) summaryPage = totalPages;
        var start = (summaryPage - 1) * summaryPageSize;
        var end = Math.min(start + summaryPageSize, total);
        var pageData = summaryFilteredData.slice(start, end);

        var html = '<table class="summary-table"><thead><tr>';
        for (var ci = 0; ci < SUMMARY_COLUMNS.length; ci++) {
            html += '<th>' + SUMMARY_COLUMNS[ci].header + '</th>';
        }
        html += '</tr></thead><tbody>';

        for (var i = 0; i < pageData.length; i++) {
            var item = pageData[i];
            html += _renderSummaryRow(item, i);
            if (item._isParent && item._expanded && item._children) {
                for (var cc = 0; cc < item._children.length; cc++) {
                    html += _renderSummaryRow(item._children[cc], i, true);
                }
            }
        }
        html += '</tbody></table>';
        body.innerHTML = html;

        var pagHtml = '';
        if (totalPages > 1) {
            pagHtml += '<button class="sp-btn" onclick="DbcTool.Compare.goSummaryPage(1)" ' + (summaryPage === 1 ? 'disabled' : '') + '>首页</button>';
            pagHtml += '<button class="sp-btn" onclick="DbcTool.Compare.goSummaryPage(' + (summaryPage - 1) + ')" ' + (summaryPage === 1 ? 'disabled' : '') + '>上一页</button>';
            var maxShow = 7;
            var pStart = Math.max(1, summaryPage - Math.floor(maxShow / 2));
            var pEnd = Math.min(totalPages, pStart + maxShow - 1);
            if (pEnd - pStart < maxShow - 1) pStart = Math.max(1, pEnd - maxShow + 1);
            for (var p = pStart; p <= pEnd; p++) {
                pagHtml += '<button class="sp-btn' + (p === summaryPage ? ' active' : '') + '" onclick="DbcTool.Compare.goSummaryPage(' + p + ')">' + p + '</button>';
            }
            pagHtml += '<button class="sp-btn" onclick="DbcTool.Compare.goSummaryPage(' + (summaryPage + 1) + ')" ' + (summaryPage === totalPages ? 'disabled' : '') + '>下一页</button>';
            pagHtml += '<button class="sp-btn" onclick="DbcTool.Compare.goSummaryPage(' + totalPages + ')" ' + (summaryPage === totalPages ? 'disabled' : '') + '>末页</button>';
            pagHtml += '<span class="sp-info">第 ' + summaryPage + ' / ' + totalPages + ' 页</span>';
        }
        pagination.innerHTML = pagHtml;
    }

    function _renderSummaryRow(item, idx, isChild) {
        var resultClass = '';
        if (item.result === 'added') { resultClass = 'added'; }
        else if (item.result === 'deleted' || item.result === 'removed') { resultClass = 'deleted'; }
        else { resultClass = 'changed'; }

        var rowClass = isChild ? ' class="s-child-row"' : '';
        if (item._isParent) {
            rowClass = ' class="s-parent-row"';
        }

        var html = '<tr' + rowClass + '>';
        for (var cj = 0; cj < SUMMARY_COLUMNS.length; cj++) {
            var col = SUMMARY_COLUMNS[cj];
            var cellValue = col.render(item, idx);
            if (col.key === 'parent') {
                html += '<td class="s-parent">' + DbcTool.escapeHtml(cellValue) + '</td>';
            } else if (col.key === 'result') {
                html += '<td><span class="s-type ' + resultClass + '">' + DbcTool.escapeHtml(cellValue) + '</span></td>';
            } else if (col.key === 'child') {
                var childHtml = DbcTool.escapeHtml(cellValue);
                if (item._isParent) {
                    var expandIcon = item._expanded ? '▼' : '▶';
                    childHtml = '<span class="s-expand-toggle" data-parent-id="' + item._parentId + '" onclick="DbcTool.Compare.toggleSummaryExpand(event, ' + item._parentId + ')">' + expandIcon + '</span> ' + childHtml;
                }
                if (isChild) {
                    html += '<td class="s-child-name">' + childHtml + '</td>';
                } else {
                    html += '<td><span class="s-node">' + childHtml + '</span></td>';
                }
            } else if (col.key === 'label') {
                html += '<td>' + DbcTool.escapeHtml(cellValue) + '</td>';
            } else if (col.key === 'old') {
                html += '<td class="s-old">' + (cellValue && cellValue !== '-' ? DbcTool.escapeHtml(cellValue) : '<span class="s-empty">-</span>') + '</td>';
            } else if (col.key === 'new') {
                html += '<td class="s-new">' + (cellValue && cellValue !== '-' ? DbcTool.escapeHtml(cellValue) : '<span class="s-empty">-</span>') + '</td>';
            } else if (col.key === 'description') {
                html += '<td class="s-detail">' + DbcTool.escapeHtml(cellValue) + '</td>';
            } else {
                html += '<td>' + DbcTool.escapeHtml(cellValue) + '</td>';
            }
        }
        html += '</tr>';
        return html;
    }

    function toggleSummaryExpand(event, parentId) {
        event.stopPropagation();
        for (var i = 0; i < summaryFilteredData.length; i++) {
            var item = summaryFilteredData[i];
            if (item._isParent && item._parentId === parentId) {
                item._expanded = !item._expanded;
                break;
            }
        }
        _renderSummaryTable();
    }

    function goSummaryPage(page) {
        var totalPages = Math.ceil(summaryFilteredData.length / summaryPageSize);
        if (page < 1 || page > totalPages) return;
        summaryPage = page;
        _renderSummaryTable();
    }

    function expandAllSummary() {
        for (var i = 0; i < summaryFilteredData.length; i++) {
            if (summaryFilteredData[i]._isParent) {
                summaryFilteredData[i]._expanded = true;
            }
        }
        _renderSummaryTable();
    }

    function collapseAllSummary() {
        for (var i = 0; i < summaryFilteredData.length; i++) {
            if (summaryFilteredData[i]._isParent) {
                summaryFilteredData[i]._expanded = false;
            }
        }
        _renderSummaryTable();
    }

    function exportReport() {
        _buildSummaryData();
        _applyFilters();
        if (summaryFilteredData.length === 0) {
            DbcTool.msg('err', '没有可导出的变更数据');
            return;
        }
        _downloadExcel();
        _downloadWord();
    }

    function _downloadExcel() {
        var BOM = '\uFEFF';
        var header = [];
        for (var ci = 0; ci < SUMMARY_COLUMNS.length; ci++) {
            header.push(SUMMARY_COLUMNS[ci].header);
        }
        var csvRows = [header.join('\t')];
        var flatData = _flattenExportData();
        for (var i = 0; i < flatData.length; i++) {
            var item = flatData[i];
            var row = [];
            for (var cj = 0; cj < SUMMARY_COLUMNS.length; cj++) {
                var col = SUMMARY_COLUMNS[cj];
                row.push(col.render(item, i));
            }
            csvRows.push(row.join('\t'));
        }
        var csvContent = BOM + csvRows.join('\n');
        var blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        var url = URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.href = url;
        var now = new Date();
        var ts = now.getFullYear() + ('0' + (now.getMonth() + 1)).slice(-2) + ('0' + now.getDate()).slice(-2) + '_' +
                 ('0' + now.getHours()).slice(-2) + ('0' + now.getMinutes()).slice(-2) + ('0' + now.getSeconds()).slice(-2);
        a.download = 'DBC变更明细_' + ts + '.xls';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    function _downloadWord() {
        var resultColors = { 'added': '#22c55e', 'deleted': '#ef4444', 'removed': '#ef4444', 'changed': '#eab308' };
        var flatData = _flattenExportData();
        var rowsHtml = '';
        for (var i = 0; i < flatData.length; i++) {
            var item = flatData[i];
            var color = resultColors[item.result] || '#94a3b8';
            rowsHtml += '<tr>';
            for (var cj = 0; cj < SUMMARY_COLUMNS.length; cj++) {
                var col = SUMMARY_COLUMNS[cj];
                var cellValue = col.render(item, i);
                if (col.key === 'result') {
                    rowsHtml += '<td style="color:' + color + ';font-weight:bold">' + DbcTool.escapeHtml(cellValue) + '</td>';
                } else {
                    rowsHtml += '<td>' + DbcTool.escapeHtml(cellValue) + '</td>';
                }
            }
            rowsHtml += '</tr>';
        }
        var html = '<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:w="urn:schemas-microsoft-com:office:word" xmlns="http://www.w3.org/TR/REC-html40">';
        html += '<head><meta charset="UTF-8"><title>DBC变更明细报告</title>';
        html += '<style>table{border-collapse:collapse;width:100%}th,td{border:1px solid #ccc;padding:6px 10px;font-size:12px}th{background:#f1f5f9;font-weight:bold;text-align:left}tr:nth-child(even){background:#f8fafc}</style>';
        html += '</head><body>';
        html += '<h2>DBC变更明细报告</h2>';
        html += '<p>生成时间: ' + new Date().toLocaleString('zh-CN') + '</p>';
        html += '<p>总记录数: ' + flatData.length + '</p>';
        html += '<table><thead><tr>';
        for (var hi = 0; hi < SUMMARY_COLUMNS.length; hi++) {
            html += '<th>' + SUMMARY_COLUMNS[hi].header + '</th>';
        }
        html += '</tr></thead><tbody>' + rowsHtml + '</tbody></table>';
        html += '</body></html>';
        var blob = new Blob(['\uFEFF' + html], { type: 'application/msword;charset=utf-8;' });
        var url = URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.href = url;
        var now = new Date();
        var ts = now.getFullYear() + ('0' + (now.getMonth() + 1)).slice(-2) + ('0' + now.getDate()).slice(-2) + '_' +
                 ('0' + now.getHours()).slice(-2) + ('0' + now.getMinutes()).slice(-2) + ('0' + now.getSeconds()).slice(-2);
        a.download = 'DBC变更明细_' + ts + '.doc';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        DbcTool.msg('ok', '变更明细已导出 (Excel + Word)');
    }

    function _flattenExportData() {
        var flat = [];
        for (var i = 0; i < summaryFilteredData.length; i++) {
            var item = summaryFilteredData[i];
            flat.push(item);
            if (item._children && item._children.length > 0) {
                for (var j = 0; j < item._children.length; j++) {
                    flat.push(item._children[j]);
                }
            }
        }
        return flat;
    }

    return {
        init: init,
        fileInCmp1: fileInCmp1,
        fileInCmp2: fileInCmp2,
        updBtnCmp: updBtnCmp,
        doCompare: doCompare,
        hideResCmp: hideResCmp,
        toggleDiffOnly: toggleDiffOnly,
        toggleTreeNode: toggleTreeNode,
        clearPersistedData: clearPersistedData,
        openSummary: openSummary,
        closeSummary: closeSummary,
        filterSummary: filterSummary,
        goSummaryPage: goSummaryPage,
        toggleSummaryExpand: toggleSummaryExpand,
        expandAllSummary: expandAllSummary,
        collapseAllSummary: collapseAllSummary,
        exportReport: exportReport
    };
})();
