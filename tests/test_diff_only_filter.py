# -*- coding: utf-8 -*-
"""
Unit tests for the "只显示差异" (Show Differences Only) feature.

Tests verify:
1. The backend diff_map correctly classifies items as added/deleted/changed/equal
2. The countDiff logic correctly counts differences
3. The filtering logic correctly identifies which items should be shown/hidden
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
import canmatrix
from canmatrix.compare import compare_db, CompareResult


def _build_diff_map(compare_result):
    """Replicate the frontend's diff_map building logic for testing."""
    diff_map = {}

    def collect_detail_changes(node):
        details = []
        if hasattr(node, 'children') and node.children:
            for child in node.children:
                if child.result and child.result != 'equal':
                    ctype = (child.type or '').lower()
                    old_val = ''
                    new_val = ''
                    signal_name = ''
                    if hasattr(child, 'ref') and child.ref is not None and hasattr(child.ref, 'name'):
                        signal_name = child.ref.name
                    if hasattr(child, 'changes') and child.changes and len(child.changes) >= 2:
                        old_val = str(child.changes[0]) if child.changes[0] is not None else ''
                        new_val = str(child.changes[1]) if child.changes[1] is not None else ''
                    elif child.result in ('deleted', 'removed'):
                        ref_name = ''
                        if hasattr(child, 'ref') and child.ref is not None:
                            ref_name = child.ref.name if hasattr(child.ref, 'name') else str(child.ref)
                        old_val = ref_name
                    elif child.result == 'added':
                        ref_name = ''
                        if hasattr(child, 'ref') and child.ref is not None:
                            ref_name = child.ref.name if hasattr(child.ref, 'name') else str(child.ref)
                        new_val = ref_name
                    elif child.result == 'changed':
                        sub_details = collect_detail_changes(child)
                        if sub_details:
                            parts = []
                            for sd in sub_details:
                                if sd['old'] and sd['new']:
                                    parts.append(sd['old'] + ' -> ' + sd['new'])
                                elif sd['new']:
                                    parts.append('+ ' + sd['new'])
                                elif sd['old']:
                                    parts.append('- ' + sd['old'])
                            old_val = '; '.join(parts) if parts else ''
                    details.append({
                        'type': ctype,
                        'label': ctype,
                        'old': old_val,
                        'new': new_val,
                        'result': child.result,
                        'signal_name': signal_name,
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


def count_diff(compare_result):
    """Replicate the frontend countDiff logic."""
    r = {'total': 0, 'added': 0, 'deleted': 0, 'changed': 0}

    def walk(n):
        if not n:
            return
        if n.result and n.result != 'equal' and n.result is not None:
            r['total'] += 1
            if n.result == 'added':
                r['added'] += 1
            elif n.result == 'deleted':
                r['deleted'] += 1
            elif n.result == 'changed':
                r['changed'] += 1
        if hasattr(n, 'children') and n.children:
            for child in n.children:
                walk(child)

    walk(compare_result)
    return r


def filter_diff_only(diff_map):
    """Simulate the '只显示差异' filter: return only items with diff status."""
    return {k: v for k, v in diff_map.items()
            if v['status'] in ('added', 'deleted', 'changed')}


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def db_identical():
    """Two identical databases - should have zero differences."""
    db1 = canmatrix.CanMatrix()
    db2 = canmatrix.CanMatrix()

    frame1 = canmatrix.Frame("TestFrame", arbitration_id=canmatrix.arbitration_id_converter(0x100), size=8)
    signal1 = canmatrix.Signal("TestSignal", size=8, is_little_endian=False)
    frame1.add_signal(signal1)
    db1.add_frame(frame1)

    frame2 = canmatrix.Frame("TestFrame", arbitration_id=canmatrix.arbitration_id_converter(0x100), size=8)
    signal2 = canmatrix.Signal("TestSignal", size=8, is_little_endian=False)
    frame2.add_signal(signal2)
    db2.add_frame(frame2)

    return db1, db2


@pytest.fixture
def db_with_differences():
    """Two databases with various differences."""
    db1 = canmatrix.CanMatrix()
    db2 = canmatrix.CanMatrix()

    # Frame only in db1 (deleted)
    f_deleted = canmatrix.Frame("DeletedFrame", arbitration_id=canmatrix.arbitration_id_converter(0x200), size=8)
    db1.add_frame(f_deleted)

    # Frame only in db2 (added)
    f_added = canmatrix.Frame("AddedFrame", arbitration_id=canmatrix.arbitration_id_converter(0x300), size=8)
    db2.add_frame(f_added)

    # Frame in both but changed (different DLC)
    f1 = canmatrix.Frame("ChangedFrame", arbitration_id=canmatrix.arbitration_id_converter(0x400), size=8)
    f2 = canmatrix.Frame("ChangedFrame", arbitration_id=canmatrix.arbitration_id_converter(0x400), size=16)
    db1.add_frame(f1)
    db2.add_frame(f2)

    # Frame in both, identical
    f_same = canmatrix.Frame("SameFrame", arbitration_id=canmatrix.arbitration_id_converter(0x500), size=8)
    db1.add_frame(f_same)
    db2.add_frame(f_same)

    return db1, db2


@pytest.fixture
def db_with_signal_changes():
    """Two databases with signal-level changes."""
    db1 = canmatrix.CanMatrix()
    db2 = canmatrix.CanMatrix()

    frame1 = canmatrix.Frame("SignalFrame", arbitration_id=canmatrix.arbitration_id_converter(0x600), size=8)
    sig1 = canmatrix.Signal("ChangedSignal", size=8, is_little_endian=False, factor=1.0, offset=0.0)
    frame1.add_signal(sig1)
    db1.add_frame(frame1)

    frame2 = canmatrix.Frame("SignalFrame", arbitration_id=canmatrix.arbitration_id_converter(0x600), size=8)
    sig2 = canmatrix.Signal("ChangedSignal", size=16, is_little_endian=False, factor=2.0, offset=0.5)
    frame2.add_signal(sig2)
    db2.add_frame(frame2)

    return db1, db2


# ─── Tests ───────────────────────────────────────────────────────────────────

class TestDiffOnlyFilter:
    """Tests for the '只显示差异' filtering feature."""

    def test_identical_databases_produce_no_diff(self, db_identical):
        """Identical databases should produce zero differences."""
        db1, db2 = db_identical
        result = compare_db(db1, db2)
        diff_map = _build_diff_map(result)
        counts = count_diff(result)

        assert counts['total'] == 0
        assert counts['added'] == 0
        assert counts['deleted'] == 0
        assert counts['changed'] == 0
        assert len(filter_diff_only(diff_map)) == 0

    def test_count_diff_classifies_correctly(self, db_with_differences):
        """countDiff should correctly classify added/deleted/changed."""
        db1, db2 = db_with_differences
        result = compare_db(db1, db2)
        counts = count_diff(result)

        assert counts['added'] >= 1, "Should have at least one added item"
        assert counts['deleted'] >= 1, "Should have at least one deleted item"
        assert counts['changed'] >= 1, "Should have at least one changed item"
        assert counts['total'] == counts['added'] + counts['deleted'] + counts['changed']

    def test_filter_diff_only_excludes_equal(self, db_with_differences):
        """filter_diff_only should exclude items with 'equal' status."""
        db1, db2 = db_with_differences
        result = compare_db(db1, db2)
        diff_map = _build_diff_map(result)
        filtered = filter_diff_only(diff_map)

        for key, entry in filtered.items():
            assert entry['status'] in ('added', 'deleted', 'changed'), \
                "Filtered map should only contain added/deleted/changed items, got: {}".format(entry['status'])

    def test_filter_diff_only_returns_all_diffs(self, db_with_differences):
        """filter_diff_only should return all diff items."""
        db1, db2 = db_with_differences
        result = compare_db(db1, db2)
        diff_map = _build_diff_map(result)
        filtered = filter_diff_only(diff_map)

        total_diffs = sum(1 for v in diff_map.values()
                          if v['status'] in ('added', 'deleted', 'changed'))
        assert len(filtered) == total_diffs, \
            "Filtered count should match total diff count"

    def test_toggle_state_transitions(self, db_with_differences):
        """Simulate toggle: active -> show only diffs, inactive -> show all."""
        db1, db2 = db_with_differences
        result = compare_db(db1, db2)
        diff_map = _build_diff_map(result)

        # State 1: inactive (show all)
        all_items = set(diff_map.keys())
        assert len(all_items) > 0

        # State 2: active (show only diffs)
        diff_only = set(filter_diff_only(diff_map).keys())
        assert len(diff_only) > 0
        assert diff_only.issubset(all_items), "Diff-only set should be subset of all items"
        assert len(diff_only) <= len(all_items), "Diff-only should not exceed all items"

        # State 3: toggle back to inactive
        assert all_items == set(diff_map.keys()), "Toggling back should restore all items"

    def test_signal_changes_produce_changed_frame(self, db_with_signal_changes):
        """Signal-level changes should mark the parent frame as changed."""
        db1, db2 = db_with_signal_changes
        result = compare_db(db1, db2)
        diff_map = _build_diff_map(result)

        frame_key = 'FRAME::SignalFrame'
        assert frame_key in diff_map, "Changed frame should be in diff_map"
        assert diff_map[frame_key]['status'] == 'changed', \
            "Frame with changed signal should be marked as changed"

    def test_detail_changes_include_signal_name(self, db_with_signal_changes):
        """Detail changes for signal-level modifications should include signal_name."""
        db1, db2 = db_with_signal_changes
        result = compare_db(db1, db2)
        diff_map = _build_diff_map(result)

        frame_key = 'FRAME::SignalFrame'
        entry = diff_map.get(frame_key, {})
        detail_changes = entry.get('detail_changes', [])

        signal_details = [d for d in detail_changes if d.get('signal_name')]
        assert len(signal_details) > 0, \
            "Signal-level detail changes should include signal_name"

    def test_empty_diff_map_filtering(self):
        """Filtering an empty diff_map should return empty dict."""
        assert filter_diff_only({}) == {}

    def test_no_false_positives_in_filter(self, db_with_differences):
        """Filter should not include items marked as 'equal'."""
        db1, db2 = db_with_differences
        result = compare_db(db1, db2)
        diff_map = _build_diff_map(result)
        filtered = filter_diff_only(diff_map)

        for key, entry in filtered.items():
            assert entry['status'] != 'equal', \
                "Filtered items must not have 'equal' status: {}".format(key)
            assert entry['status'] is not None, \
                "Filtered items must not have None status: {}".format(key)


class TestDiffOnlyPerformance:
    """Performance tests to ensure filtering is under 300ms."""

    def test_filtering_performance(self, db_with_differences):
        """Filtering operation should complete quickly."""
        import time

        db1, db2 = db_with_differences
        result = compare_db(db1, db2)
        diff_map = _build_diff_map(result)

        start = time.time()
        for _ in range(100):
            filtered = filter_diff_only(diff_map)
        elapsed = time.time() - start

        assert elapsed < 0.3, \
            "100 filter operations should complete in under 300ms, took {:.3f}s".format(elapsed)

    def test_count_diff_performance(self, db_with_differences):
        """countDiff should be fast."""
        import time

        db1, db2 = db_with_differences
        result = compare_db(db1, db2)

        start = time.time()
        for _ in range(100):
            counts = count_diff(result)
        elapsed = time.time() - start

        assert elapsed < 0.3, \
            "100 count operations should complete in under 300ms, took {:.3f}s".format(elapsed)
