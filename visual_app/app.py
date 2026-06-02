#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DbcTool 可视化转换工具 - Flask Web 应用
"""

import os
import io
import tempfile
import logging
from datetime import datetime

from flask import Flask, render_template, request, send_file, jsonify, flash
from werkzeug.utils import secure_filename

# 添加项目路径
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import canmatrix
import canmatrix.formats
import canmatrix.convert
import canmatrix.compare
import canmatrix.log


def _detect_file_encoding(filepath, max_bytes=65536):
    """Auto-detect file encoding. Tries gb2312 → utf-8 → iso-8859-1.
    
    GBK/GB2312 is tried first as the default for Chinese automotive DBC files.
    Reads up to max_bytes to test decoding. Returns the first encoding
    that successfully decodes the entire test chunk without errors.
    """
    with open(filepath, 'rb') as f:
        data = f.read(max_bytes)
    for enc in ('gb2312', 'utf-8', 'iso-8859-1'):
        try:
            data.decode(enc)
            return enc
        except (UnicodeDecodeError, UnicodeEncodeError):
            continue
    return 'iso-8859-1'

def _resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller."""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

template_dir = _resource_path('templates')
app = Flask(__name__, template_folder=template_dir)
app.secret_key = 'dbctool_viz_secret_key'

# ─── 配置 ───────────────────────────────────────────────────
UPLOAD_FOLDER = tempfile.mkdtemp(prefix='dbctool_upload_')
OUTPUT_FOLDER = tempfile.mkdtemp(prefix='dbctool_output_')
ALLOWED_EXTENSIONS = {'dbc', 'dbf', 'kcd', 'arxml', 'xml', 'xls', 'xlsx',
                      'json', 'yaml', 'yml', 'sym', 'ldf', 'odx'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

# ─── 格式信息 ────────────────────────────────────────────────

def get_import_formats():
    """获取支持的导入格式列表"""
    formats = []
    for fmt, features in canmatrix.formats.supportedFormats.items():
        if 'load' in features:
            ext = canmatrix.formats.extensionMapping.get(fmt, fmt)
            formats.append({'key': fmt, 'ext': ext, 'label': f'.{ext} ({fmt.upper()})'})
    return formats

def get_export_formats():
    """获取支持的导出格式列表"""
    formats = []
    for fmt, features in canmatrix.formats.supportedFormats.items():
        if 'dump' in features:
            ext = canmatrix.formats.extensionMapping.get(fmt, fmt)
            formats.append({'key': fmt, 'ext': ext, 'label': f'.{ext} ({fmt.upper()})'})
    return formats

# ─── 路由 ────────────────────────────────────────────────────

@app.route('/')
def index():
    """主页"""
    return render_template(
        'index.html',
        import_formats=get_import_formats(),
        export_formats=get_export_formats(),
    )

@app.route('/api/formats')
def api_formats():
    """返回格式信息"""
    return jsonify({
        'import': get_import_formats(),
        'export': get_export_formats(),
    })

@app.route('/api/convert', methods=['POST'])
def api_convert():
    """执行格式转换"""
    logger = None
    try:
        logger = logging.getLogger(__name__)

        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '请选择要转换的文件'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': '未选择文件'}), 400

        input_format = request.form.get('input_format', '').strip()
        output_format = request.form.get('output_format', '').strip()

        original_name = secure_filename(file.filename)

        if not output_format:
            name_lower = original_name.lower()
            if name_lower.endswith('.dbc'):
                output_format = 'xlsx'
            elif name_lower.endswith('.xls') or name_lower.endswith('.xlsx'):
                output_format = 'dbc'

        if not output_format:
            return jsonify({'success': False, 'error': '请选择输出格式'}), 400

        output_ext = canmatrix.formats.extensionMapping.get(output_format, output_format)
        input_path = os.path.join(UPLOAD_FOLDER, original_name)
        try:
            file.save(input_path)
        except Exception as save_error:
            return jsonify({'success': False, 'error': f'文件保存失败: {str(save_error)}'}), 500

        base_name = os.path.splitext(original_name)[0]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_name = f"{base_name}_{timestamp}.{output_ext}"
        output_path = os.path.join(OUTPUT_FOLDER, output_name)

        convert_options = {}

        if input_format:
            convert_options['import_type'] = input_format

        convert_options['force_output'] = output_format

        dbc_import_encoding = request.form.get('dbc_import_encoding', 'auto')
        dbc_export_encoding = request.form.get('dbc_export_encoding', '')
        if not dbc_import_encoding:
            dbc_import_encoding = 'gb2312'

        file_ext = os.path.splitext(original_name)[1].lower().lstrip('.')
        text_based_formats = {'dbc', 'dbf', 'sym'}
        is_text_input = input_format in text_based_formats if input_format else file_ext in text_based_formats

        user_set_export_encoding = bool(dbc_export_encoding)

        if dbc_import_encoding == 'auto' and is_text_input:
            detected = _detect_file_encoding(input_path)
            if detected == 'iso-8859-1':
                dbc_import_encoding = 'gb2312'
            else:
                dbc_import_encoding = detected
                if dbc_import_encoding == 'gb2312' and not user_set_export_encoding:
                    dbc_export_encoding = 'gb2312'
                    user_set_export_encoding = True

        if dbc_import_encoding == 'auto':
            dbc_import_encoding = 'gb2312'

        convert_options['dbcImportEncoding'] = dbc_import_encoding
        if user_set_export_encoding:
            convert_options['dbcExportEncoding'] = dbc_export_encoding

        dbc_import_comment = request.form.get('dbc_import_comment_encoding', dbc_import_encoding)
        if dbc_import_comment == 'auto':
            dbc_import_comment = dbc_import_encoding
        dbc_export_comment = request.form.get('dbc_export_comment_encoding', dbc_export_encoding)
        if dbc_export_comment == 'auto':
            dbc_export_comment = dbc_export_encoding
        convert_options['dbcImportCommentEncoding'] = dbc_import_comment
        convert_options['dbcExportCommentEncoding'] = dbc_export_comment
        if 'dbc_unique_signal' in request.form:
            convert_options['dbcUniqueSignalNames'] = request.form['dbc_unique_signal'] == 'true'

        if request.form.get('fix_mojibake') == 'true':
            convert_options['fixMojibake'] = True

        if request.form.get('arxml_version'):
            convert_options['arVersion'] = request.form['arxml_version']

        if request.form.get('xls_motorola_format'):
            convert_options['xlsMotorolaBitFormat'] = request.form['xls_motorola_format']

        if 'json_canard' in request.form:
            convert_options['jsonExportCanard'] = request.form['json_canard'] == 'true'

        if 'delete_zero_signals' in request.form:
            convert_options['deleteZeroSignals'] = True

        if 'recalc_dlc' in request.form and request.form['recalc_dlc']:
            convert_options['recalcDLC'] = request.form['recalc_dlc']

        if 'ignore_pdu_container' in request.form:
            convert_options['ignorePduContainer'] = True

        if 'delete_obsolete_defines' in request.form:
            convert_options['deleteObsoleteDefines'] = True

        if 'delete_obsolete_ecus' in request.form:
            convert_options['deleteObsoleteEcus'] = True

        if request.form.get('additional_signal_attrs'):
            convert_options['additionalSignalAttributes'] = request.form['additional_signal_attrs']
        if request.form.get('additional_frame_attrs'):
            convert_options['additionalFrameAttributes'] = request.form['additional_frame_attrs']

        logger.info(f"导入文件: {input_path}")
        dbs = canmatrix.formats.loadp(input_path, **{k: v for k, v in convert_options.items()
                                                      if k in ['import_type', 'dbcImportEncoding',
                                                               'dbcImportCommentEncoding', 'arxmlIgnoreClusterInfo',
                                                               'arxmlFlexray', 'arxmlEthernet']})

        if dbs is None or len(dbs) == 0:
            return jsonify({'success': False, 'error': '无法解析输入文件，请检查格式'}), 400

        total_frames = 0
        total_signals = 0
        for name, db in dbs.items():
            db = _apply_filters(db, request.form)
            total_frames += len(db.frames)
            for frame in db.frames:
                total_signals += len(frame.signals)

        canmatrix.convert.convert(input_path, output_path, **convert_options)

        if not os.path.exists(output_path):
            dir_name = os.path.dirname(output_path)
            found_files = [f for f in os.listdir(dir_name)
                          if f.startswith(base_name) and f.endswith(f'.{output_ext}')]
            if found_files:
                import zipfile
                zip_path = os.path.join(OUTPUT_FOLDER, f"{base_name}_{timestamp}.zip")
                with zipfile.ZipFile(zip_path, 'w') as zf:
                    for fn in found_files:
                        zf.write(os.path.join(dir_name, fn), fn)
                output_path = zip_path
                output_name = f"{base_name}_{timestamp}.zip"
            else:
                return jsonify({'success': False, 'error': '导出失败，未生成输出文件'}), 500

        return jsonify({
            'success': True,
            'download_url': f'/download/{os.path.basename(output_path)}',
            'output_name': output_name,
            'stats': {
                'total_frames': total_frames,
                'total_signals': total_signals,
                'input_format': input_format or 'auto-detected',
                'output_format': output_format,
            }
        })

    except Exception as e:
        if logger:
            logger.exception("转换失败: %s", str(e))
        else:
            import traceback
            traceback.print_exc()
        return jsonify({'success': False, 'error': f'转换失败: {str(e)}'}), 500

@app.route('/download/<filename>')
def download_file(filename):
    """下载转换后的文件"""
    filepath = os.path.join(OUTPUT_FOLDER, filename)
    if not os.path.exists(filepath):
        return "文件不存在", 404
    return send_file(filepath, as_attachment=True, download_name=filename)

@app.route('/api/compare', methods=['POST'])
def api_compare():
    """对比两个DBC文件"""
    if 'file1' not in request.files or 'file2' not in request.files:
        return jsonify({'success': False, 'error': '请上传两个DBC文件'}), 400

    file1 = request.files['file1']
    file2 = request.files['file2']

    if file1.filename == '' or file2.filename == '':
        return jsonify({'success': False, 'error': '请选择两个文件'}), 400

    name1 = secure_filename(file1.filename)
    name2 = secure_filename(file2.filename)
    path1 = os.path.join(UPLOAD_FOLDER, f"compare1_{name1}")
    path2 = os.path.join(UPLOAD_FOLDER, f"compare2_{name2}")
    file1.save(path1)
    file2.save(path2)

    try:
        db1 = canmatrix.formats.loadp_flat(path1)
        db2 = canmatrix.formats.loadp_flat(path2)

        if db1 is None:
            return jsonify({'success': False, 'error': f'无法解析文件: {name1}'}), 400
        if db2 is None:
            return jsonify({'success': False, 'error': f'无法解析文件: {name2}'}), 400

        ignore = {}
        if request.form.get('check_comments') != 'true':
            ignore['comment'] = '*'
        if request.form.get('check_attributes') != 'true':
            ignore['ATTRIBUTE'] = '*'
        if request.form.get('ignore_valuetables') == 'true':
            ignore['VALUETABLES'] = True
        if request.form.get('ignore_defines') == 'true':
            ignore['DEFINE'] = '*'

        result = canmatrix.compare.compare_db(db1, db2, ignore)
        comparison_data = _serialize_compare_result(result)
        diff_map = _build_diff_map(result)

        tree1 = _serialize_db_tree(db1)
        tree2 = _serialize_db_tree(db2)

        stats = {
            'db1_name': name1,
            'db2_name': name2,
            'db1_frames': len(db1.frames),
            'db2_frames': len(db2.frames),
            'db1_signals': sum(len(f.signals) for f in db1.frames),
            'db2_signals': sum(len(f.signals) for f in db2.frames),
            'db1_ecus': len(db1.ecus),
            'db2_ecus': len(db2.ecus),
        }

        return jsonify({
            'success': True,
            'comparison': comparison_data,
            'diff_map': diff_map,
            'tree1': tree1,
            'tree2': tree2,
            'stats': stats,
        })

    except Exception as e:
        logging.exception("对比失败")
        return jsonify({'success': False, 'error': f'对比失败: {str(e)}'}), 500

def _serialize_compare_result(result):
    """将 CompareResult 树序列化为 JSON 兼容的字典"""
    if result is None:
        return None
    node = {
        'result': result.result,
        'type': result.type,
        'ref_name': result.ref.name if hasattr(result.ref, 'name') else str(result.ref) if result.ref else '',
        'ref_comment': result.ref.comment if hasattr(result.ref, 'comment') and result.ref.comment else '',
        'ref_id': result.ref.arbitration_id.id if hasattr(result.ref, 'arbitration_id') else '',
    }
    if result.changes:
        node['changes'] = [str(c) if c is not None else '' for c in result.changes]
    if result.children:
        node['children'] = [_serialize_compare_result(c) for c in result.children]
    return node


def _serialize_db_tree(db):
    """将完整的 CanMatrix 数据库序列化为树形结构 JSON"""
    tree = {
        'name': 'CAN Database',
        'type': 'db',
        'children': [],
    }

    ecus_node = {'name': 'ECU Nodes', 'type': 'category', 'children': [], 'count': len(db.ecus)}
    for ecu in sorted(db.ecus, key=lambda e: (e.name or '').lower()):
        ecu_node = {
            'name': ecu.name,
            'type': 'ecu',
            'comment': ecu.comment or '',
            'attributes': {k: str(v) for k, v in ecu.attributes.items()} if ecu.attributes else {},
        }
        ecus_node['children'].append(ecu_node)
    tree['children'].append(ecus_node)

    sorted_frames = sorted(db.frames, key=lambda f: (f.name or '').lower())
    frames_node = {'name': 'Messages / Frames', 'type': 'category', 'children': [], 'count': len(db.frames)}
    for frame in sorted_frames:
        can_id = frame.arbitration_id.id if hasattr(frame, 'arbitration_id') else 0
        is_extended = frame.arbitration_id.extended if hasattr(frame, 'arbitration_id') else False
        frame_node = {
            'name': frame.name,
            'type': 'frame',
            'can_id': can_id,
            'can_id_hex': '0x{:X}'.format(can_id) if can_id else '',
            'extended': is_extended,
            'dlc': frame.size,
            'cycle_time': getattr(frame, 'cycle_time', 0),
            'is_fd': getattr(frame, 'is_fd', False),
            'transmitters': list(frame.transmitters) if hasattr(frame, 'transmitters') else [],
            'receivers': list(frame.receivers) if hasattr(frame, 'receivers') else [],
            'comment': frame.comment or '',
            'children': [],
        }

        for signal in sorted(frame.signals, key=lambda s: (s.name or '').lower()):
            signal_node = {
                'name': signal.name,
                'type': 'signal',
                'start_bit': signal.start_bit,
                'size': signal.size,
                'is_little_endian': signal.is_little_endian,
                'is_signed': signal.is_signed,
                'factor': str(signal.factor) if signal.factor is not None else '',
                'offset': str(signal.offset) if signal.offset is not None else '',
                'min': str(signal.min) if signal.min else '',
                'max': str(signal.max) if signal.max else '',
                'unit': signal.unit or '',
                'multiplex': str(signal.multiplex) if signal.multiplex else '',
                'receivers': list(signal.receivers) if signal.receivers else [],
                'comment': signal.comment or '',
            }
            frame_node['children'].append(signal_node)

        if hasattr(frame, 'signalGroups') and frame.signalGroups:
            sg_node = {'name': 'Signal Groups', 'type': 'signalgroup_category', 'children': []}
            for sg in frame.signalGroups:
                sg_item = {
                    'name': sg.name,
                    'type': 'signalgroup',
                    'id': sg.id,
                    'signals': [s.name for s in sg.signals] if sg.signals else [],
                }
                sg_node['children'].append(sg_item)
            frame_node['children'].append(sg_node)

        frames_node['children'].append(frame_node)
    tree['children'].append(frames_node)

    if db.value_tables:
        vt_node = {'name': 'Value Tables', 'type': 'category', 'children': [], 'count': len(db.value_tables)}
        for vt_name in sorted(db.value_tables.keys(), key=lambda v: v.lower()):
            vt_data = db.value_tables[vt_name]
            vt_item = {
                'name': vt_name,
                'type': 'valuetable',
                'values': {str(k): str(v) for k, v in vt_data.items()},
            }
            vt_node['children'].append(vt_item)
        tree['children'].append(vt_node)

    defines_children = []
    if db.global_defines:
        gd_node = {'name': 'Global Defines', 'type': 'category', 'children': [], 'count': len(db.global_defines)}
        for dname, dval in db.global_defines.items():
            gd_node['children'].append({
                'name': dname, 'type': 'define',
                'definition': getattr(dval, 'definition', str(dval)),
                'default': str(getattr(dval, 'defaultValue', ''))})
        defines_children.append(gd_node)
    if db.ecu_defines:
        ed_node = {'name': 'ECU Defines', 'type': 'category', 'children': [], 'count': len(db.ecu_defines)}
        for dname, dval in db.ecu_defines.items():
            ed_node['children'].append({
                'name': dname, 'type': 'define',
                'definition': getattr(dval, 'definition', str(dval)),
                'default': str(getattr(dval, 'defaultValue', ''))})
        defines_children.append(ed_node)
    if db.frame_defines:
        fd_node = {'name': 'Frame Defines', 'type': 'category', 'children': [], 'count': len(db.frame_defines)}
        for dname, dval in db.frame_defines.items():
            fd_node['children'].append({
                'name': dname, 'type': 'define',
                'definition': getattr(dval, 'definition', str(dval)),
                'default': str(getattr(dval, 'defaultValue', ''))})
        defines_children.append(fd_node)
    if db.signal_defines:
        sd_node = {'name': 'Signal Defines', 'type': 'category', 'children': [], 'count': len(db.signal_defines)}
        for dname, dval in db.signal_defines.items():
            sd_node['children'].append({
                'name': dname, 'type': 'define',
                'definition': getattr(dval, 'definition', str(dval)),
                'default': str(getattr(dval, 'defaultValue', ''))})
        defines_children.append(sd_node)
    if defines_children:
        defs_node = {'name': 'Defines', 'type': 'category', 'children': defines_children}
        tree['children'].append(defs_node)

    return tree


_FIELD_LABELS = {
    'startbit': '起始位 (Startbit)',
    'signalsize': '信号长度 (Size)',
    'signalsign': '符号 (Signed)',
    'is_little_endian': '字节序 (Little Endian)',
    'is_signed': '符号 (Signed)',
    'offset': '偏移量 (Offset)',
    'factor': '缩放因子 (Factor)',
    'min': '最小值 (Min)',
    'max': '最大值 (Max)',
    'unit': '单位 (Unit)',
    'comment': '注释 (Comment)',
    'receivers': '接收节点 (Receivers)',
    'cycle_time': '周期时间 (Cycle Time)',
    'signature': '校验签名',
    'framename': '帧名称 (Frame Name)',
    'signalname': '信号名称 (Signal Name)',
    'dlc': 'DLC (数据长度)',
    'multiplex': '复用类型',
    'values': '信号值表 (Values)',
    'valuetable': '信号值表 (ValueTable)',
    'signal': '信号列表变更',
    'frame': '帧列表变更',
    'ecus': 'ECU 变更',
}


def _build_diff_map(compare_result):
    """从 CompareResult 构建差异映射, 收集详细子变更信息"""
    diff_map = {}

    def collect_detail_changes(node):
        details = []
        if hasattr(node, 'children') and node.children:
            for child in node.children:
                if child.result and child.result != 'equal':
                    ctype = (child.type or '').lower()
                    label = _FIELD_LABELS.get(ctype, child.type or 'unknown')
                    old_val = ''
                    new_val = ''
                    if hasattr(child, 'changes') and child.changes and len(child.changes) >= 2:
                        old_val = str(child.changes[0]) if child.changes[0] is not None else ''
                        new_val = str(child.changes[1]) if child.changes[1] is not None else ''
                    details.append({
                        'type': ctype,
                        'label': label,
                        'old': old_val,
                        'new': new_val,
                    })
        return details

    def walk(node, parent_details=None):
        if node is None:
            return
        node_type = (node.type or '').upper()
        node_name = ''
        if hasattr(node, 'ref') and node.ref is not None:
            node_name = node.ref.name if hasattr(node.ref, 'name') else str(node.ref)
        key = '{}::{}'.format(node_type, node_name)

        if node.result and node.result != 'equal':
            entry = {'status': node.result}

            direct_changes = []
            if hasattr(node, 'changes') and node.changes:
                direct_changes = [str(c) if c is not None else '' for c in node.changes]
            entry['changes'] = direct_changes

            detail_changes = collect_detail_changes(node)
            if not detail_changes and parent_details:
                detail_changes = parent_details
            entry['detail_changes'] = detail_changes

            diff_map[key] = entry

        details_for_children = collect_detail_changes(node)
        if hasattr(node, 'children'):
            for child in node.children:
                walk(child, details_for_children)

    walk(compare_result)
    return diff_map

def _apply_filters(db, form):
    """应用过滤选项"""
    import canmatrix

    # 删除指定 ECU
    if form.get('delete_ecu'):
        for ecu_name in form['delete_ecu'].split(','):
            ecu_name = ecu_name.strip()
            if ecu_name:
                db.del_ecu(ecu_name)

    # 删除指定 Frame
    if form.get('delete_frame'):
        for frame_name in form['delete_frame'].split(','):
            frame_name = frame_name.strip()
            if frame_name:
                db.del_frame(frame_name)

    # 删除零长度信号
    if 'delete_zero_signals' in form:
        db.delete_zero_signals()

    # 重新计算 DLC
    if form.get('recalc_dlc'):
        db.recalc_dlc(form['recalc_dlc'])

    # 删除过时定义
    if 'delete_obsolete_defines' in form:
        db.delete_obsolete_defines()

    # 删除过时 ECU
    if 'delete_obsolete_ecus' in form:
        db.delete_obsolete_ecus()

    return db

# ─── 启动 ────────────────────────────────────────────────────

def main():
    import webbrowser
    host = '127.0.0.1'
    port = 5091
    print(f"\n{'='*60}")
    print(f"  DbcTool 可视化转换工具")
    print(f"  访问地址: http://{host}:{port}")
    print(f"  按 Ctrl+C 停止服务")
    print(f"{'='*60}\n")

    # 自动打开浏览器 (可选)
    try:
        webbrowser.open(f'http://{host}:{port}')
    except Exception:
        pass

    app.run(host=host, port=port, debug=False)

if __name__ == '__main__':
    main()
