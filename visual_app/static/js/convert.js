var DbcTool = DbcTool || {};

DbcTool.Convert = (function() {
    var cvFile = null;
    var fmtMap = [];

    function init(_fmtMap) {
        fmtMap = _fmtMap;
    }

    function fileInCvt(f) {
        cvFile = f;
        var ne = document.getElementById('fnameCvt');
        var z = document.getElementById('zoneCvt');
        var sz = DbcTool.formatFileSize(f.size);
        ne.textContent = '\u2713 ' + f.name + ' (' + sz + ')';
        ne.style.display = 'block';
        z.classList.add('has-file');

        var ext = DbcTool.getExt(f.name);
        var fmtKey = DbcTool.findFmtKey(ext, fmtMap);
        var sel = document.getElementById('inFmtCvt');
        var badge = document.getElementById('autoBadge');

        if (fmtKey) {
            sel.value = fmtKey;
            badge.classList.add('show');
            document.getElementById('fmtHint').textContent = '\u2713 已自动识别为 .' + ext + ' (' + fmtKey.toUpperCase() + ') 格式';
        } else {
            sel.value = '';
            badge.classList.remove('show');
            document.getElementById('fmtHint').textContent = '\u26A0 无法自动识别 "' + f.name + '" 的格式，请手动选择或确认文件扩展名';
        }

        var outSel = document.getElementById('outFmtCvt');
        if (fmtKey === 'dbc') {
            outSel.value = 'xlsx';
        } else if (fmtKey === 'xls' || fmtKey === 'xlsx') {
            outSel.value = 'dbc';
        }

        updBtnCvt();
    }

    function updBtnCvt() {
        var b = document.getElementById('btnGoCvt');
        var o = document.getElementById('outFmtCvt').value;
        b.disabled = !(cvFile && o);
        b.textContent = cvFile && o ? '开始转换' : cvFile ? '请选择输出格式' : '请先导入文件';
    }

    function hideResCvt() {
        document.getElementById('resCardCvt').classList.remove('show');
    }

    function doConvert() {
        if (!cvFile || !document.getElementById('outFmtCvt').value) return;
        hideResCvt();

        var f = new FormData();
        f.append('file', cvFile);
        f.append('output_format', document.getElementById('outFmtCvt').value);

        var inf = document.getElementById('inFmtCvt').value;
        if (inf) f.append('input_format', inf);

        if (document.getElementById('cO0').checked) f.append('delete_zero_signals', '1');
        if (document.getElementById('cO1').checked) f.append('delete_obsolete_defines', '1');
        if (document.getElementById('cO2').checked) f.append('delete_obsolete_ecus', '1');
        if (document.getElementById('cO3').checked) f.append('ignore_pdu_container', '1');

        var dlc = document.getElementById('cDlc').value;
        if (dlc) f.append('recalc_dlc', dlc);

        f.append('arxml_version', document.getElementById('cAr').value);
        f.append('dbc_import_encoding', document.getElementById('cEncI').value);
        f.append('dbc_export_encoding', document.getElementById('cEncO').value);
        f.append('dbc_import_comment_encoding', document.getElementById('cEncI').value);
        f.append('dbc_export_comment_encoding', document.getElementById('cEncO').value);
        f.append('xls_motorola_format', document.getElementById('cMot').value);
        f.append('dbc_unique_signal', document.getElementById('cUniq').checked);
        f.append('json_canard', document.getElementById('cCanard').checked);
        f.append('fix_mojibake', document.getElementById('cMojibake').checked);

        var fa = document.getElementById('cFAttr').value;
        if (fa) f.append('additional_frame_attrs', fa);
        var sa = document.getElementById('cSAttr').value;
        if (sa) f.append('additional_signal_attrs', sa);

        var btn = document.getElementById('btnGoCvt');
        btn.innerHTML = '<span class="spin"></span> 转换中...';
        btn.disabled = true;

        fetch('/api/convert', { method: 'POST', body: f })
            .then(function(r) { return r.json(); })
            .then(function(d) {
                if (d.success) {
                    showResCvt(d);
                } else {
                    DbcTool.msg('err', d.error);
                }
            })
            .catch(function(e) {
                DbcTool.msg('err', '请求失败: ' + e.message);
            })
            .finally(function() {
                btn.innerHTML = '开始转换';
                updBtnCvt();
            });
    }

    function showResCvt(d) {
        document.getElementById('resCardCvt').classList.add('show');
        document.getElementById('statsGridCvt').innerHTML =
            '<div class=stat><div class=stat-val>' + d.stats.total_frames + '</div><div class=stat-lbl>帧数 (Frames)</div></div>' +
            '<div class=stat><div class=stat-val>' + d.stats.total_signals + '</div><div class=stat-lbl>信号数 (Signals)</div></div>' +
            '<div class=stat><div class=stat-val style=font-size:.9rem>' + d.stats.input_format + '</div><div class=stat-lbl>输入格式</div></div>' +
            '<div class=stat><div class=stat-val style=font-size:.9rem>' + d.stats.output_format + '</div><div class=stat-lbl>输出格式</div></div>';
        var btn = document.getElementById('btnDlCvt');
        btn.href = d.download_url;
        btn.download = d.output_name;
        btn.scrollIntoView({ behavior: 'smooth' });

        try {
            localStorage.setItem('dbctool_convert_data', JSON.stringify({
                stats: d.stats,
                download_url: d.download_url,
                output_name: d.output_name,
                timestamp: Date.now()
            }));
        } catch (e) {}
    }

    return {
        init: init,
        fileInCvt: fileInCvt,
        updBtnCvt: updBtnCvt,
        doConvert: doConvert,
        hideResCvt: hideResCvt
    };
})();
