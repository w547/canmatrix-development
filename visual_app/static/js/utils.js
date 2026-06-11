var DbcTool = DbcTool || {};

DbcTool.escapeHtml = function(s) {
    if (!s) return '';
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
};

DbcTool.getExt = function(name) {
    var i = name.lastIndexOf('.');
    return i >= 0 ? name.slice(i + 1).toLowerCase() : '';
};

DbcTool.fmtFromExt = function(ext) {
    var m = {'dbc': 'dbc', 'dbf': 'dbf', 'arxml': 'arxml', 'xml': 'arxml', 'kcd': 'kcd',
             'xls': 'xls', 'xlsx': 'xlsx', 'json': 'json', 'yaml': 'yaml', 'yml': 'yaml',
             'sym': 'sym', 'ldf': 'ldf', 'odx': 'odx'};
    return m[ext] || '';
};

DbcTool.findFmtKey = function(ext, fmtMap) {
    var k = DbcTool.fmtFromExt(ext);
    if (!k) return '';
    for (var i = 0; i < fmtMap.length; i++) {
        if (fmtMap[i].key === k) return fmtMap[i].key;
    }
    return '';
};

DbcTool.clearAllMsgs = function() {
    ['msg-err', 'msg-ok', 'msg-inf'].forEach(function(id) {
        var e = document.getElementById(id);
        e.classList.remove('show');
        e.textContent = '';
    });
};

DbcTool.msg = function(t, x) {
    DbcTool.clearAllMsgs();
    var e = document.getElementById('msg-' + t);
    e.textContent = x;
    e.classList.add('show');
    setTimeout(function() { e.classList.remove('show'); }, 8000);
};

DbcTool.toggleAdv = function(hdrId, bodyId) {
    var h = document.getElementById(hdrId);
    var b = document.getElementById(bodyId);
    h.classList.toggle('open');
    b.classList.toggle('open');
};

DbcTool.setupUpload = function(zoneId, inpId, handler) {
    var z = document.getElementById(zoneId);
    var inp = document.getElementById(inpId);
    z.addEventListener('click', function() { inp.click(); });
    inp.addEventListener('change', function() { if (inp.files.length) handler(inp.files[0]); });
    z.addEventListener('dragover', function(e) { e.preventDefault(); z.classList.add('drag-over'); });
    z.addEventListener('dragleave', function() { z.classList.remove('drag-over'); });
    z.addEventListener('drop', function(e) {
        e.preventDefault();
        z.classList.remove('drag-over');
        if (e.dataTransfer.files.length) handler(e.dataTransfer.files[0]);
    });
};

DbcTool.formatFileSize = function(size) {
    if (size < 1024) return size + ' B';
    if (size < 1048576) return (size / 1024).toFixed(1) + ' KB';
    return (size / 1048576).toFixed(1) + ' MB';
};

DbcTool.ICONS = {
    'db': '\uD83D\uDCC1',
    'category': '\uD83D\uDCC2',
    'frame': '\uD83D\uDCC4',
    'signal': '\u26A1',
    'ecu': '\uD83D\uDCBB',
    'valuetable': '\uD83D\uDCCB',
    'define': '\u2699',
    'signalgroup': '\uD83D\uDDD2',
    'signalgroup_category': '\uD83D\uDCC1'
};
