# -*- coding: utf-8 -*-
"""Quick test: verify mojibake fix and phys2raw None bug"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from canmatrix.convert import fix_mojibake_gbk, apply_mojibake_fix_to_db
import canmatrix

# Test 1: fix_mojibake_gbk works on garbled text
garbled = '\xcd\xa8\xd0\xc5\xd0\xad\xd2\xe9\xb0\xe6\xb1\xbe'
fixed = fix_mojibake_gbk(garbled)
results = []
results.append(f"fix_mojibake_gbk('{garbled[:20]}') = '{fixed}'")
results.append(f"  Fixed is Chinese: {any('\\u4e00' <= c <= '\\u9fff' for c in fixed)}")

# Test 2: phys2raw with None initial_value
sig = canmatrix.Signal("test", 
    start_bit=0, size=8, is_little_endian=True, is_signed=False,
    factor=1, offset=0, min=0, max=255,
    initial_value=None)
try:
    val = sig.phys2raw(None)
    results.append(f"phys2raw(None) with None initial_value: {val}")
except Exception as e:
    results.append(f"phys2raw(None) ERROR: {e}")

# Test 3: Empty signal
sig2 = canmatrix.Signal("test2",
    start_bit=0, size=8, is_little_endian=True, is_signed=False,
    factor=1, offset=0, min=None, max=None,
    initial_value=None)
try:
    val2 = sig2.phys2raw(None)
    results.append(f"phys2raw(None) with None all: {val2}")
except Exception as e:
    results.append(f"phys2raw(None) ERROR: {e}")

for r in results:
    print(r)
