#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json
from pathlib import Path

input_fasta = "3_af3_local/af3_input.fasta"
output_dir = "3_af3_local/af3_json"

Path(output_dir).mkdir(parents=True, exist_ok=True)

def safe_name(name):
    name = name.strip()
    name = re.sub(r'[<>:"/\\|?*\s]+', "_", name)
    return name

records = []
with open(input_fasta, "r") as f:
    header = None
    seq_lines = []
    for line in f:
        line = line.strip()
        if not line:
            continue
        if line.startswith(">"):
            if header is not None:
                records.append((header, "".join(seq_lines)))
            header = line[1:].strip()
            seq_lines = []
        else:
            seq_lines.append(line)
    if header is not None:
        records.append((header, "".join(seq_lines)))

n_ok = 0
n_skip = 0

for name, seq in records:
    if ":" not in seq:
        print(f"[skip] {name}: 序列里没有 ':'，无法拆分成 A/B 两条链")
        n_skip += 1
        continue

    parts = seq.split(":")
    if len(parts) != 2:
        print(f"[skip] {name}: 序列中 ':' 数量不是 1 个")
        n_skip += 1
        continue

    seqA = parts[0].strip().upper()
    seqB = parts[1].strip().upper()

    if not seqA or not seqB:
        print(f"[skip] {name}: A链或B链为空")
        n_skip += 1
        continue

    data = {
        "name": name,
        "sequences": [
            {
                "protein": {
                    "id": ["A"],
                    "sequence": seqA
                }
            },
            {
                "protein": {
                    "id": ["B"],
                    "sequence": seqB
                }
            }
        ],
        "modelSeeds": [1],
        "dialect": "alphafold3",
        "version": 1
    }

    out_json = Path(output_dir) / f"{safe_name(name)}.json"
    with open(out_json, "w", encoding="utf-8") as out:
        json.dump(data, out, indent=2, ensure_ascii=False)

    print(f"[ok] {out_json}")
    n_ok += 1

print(f"\n完成: 成功 {n_ok} 个, 跳过 {n_skip} 个")