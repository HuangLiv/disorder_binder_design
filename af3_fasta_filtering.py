#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path

# ======== 输入输出文件 ========
models_file = "af3_filtered_models.txt"
input_fasta = "af3_input.fasta"
output_fasta = "deduplicated_selected_sequences.fasta"
#missing_file = "missing_models.txt"
# ==============================


def normalize_model_name(name: str) -> str:
    """
    把 models.txt 里的
    xxx_dldesign_0/seed-1_sample
    规范化成
    xxx_dldesign_0
    """
    name = name.strip()
    if not name:
        return ""
    if "/" in name:
        name = name.split("/")[0]
    return name


def read_unique_models(models_path: str):
    """
    读取 models 文件，去重并保留原始顺序
    """
    seen = set()
    unique_models = []

    with open(models_path, "r", encoding="utf-8") as f:
        for line in f:
            model = normalize_model_name(line)
            if not model:
                continue
            if model not in seen:
                seen.add(model)
                unique_models.append(model)

    return unique_models


def read_fasta_as_dict(fasta_path: str):
    """
    读取 fasta，返回:
    {
        header_id: sequence
    }

    默认取 > 后第一段作为 ID
    例如:
    >dao_66_xxx
    SEQUENCE
    """
    fasta_dict = {}
    current_id = None
    seq_lines = []

    with open(fasta_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip()
            if not line:
                continue

            if line.startswith(">"):
                if current_id is not None:
                    fasta_dict[current_id] = "".join(seq_lines)

                header = line[1:].strip()
                current_id = header.split()[0]
                seq_lines = []
            else:
                seq_lines.append(line)

        # 最后一条
        if current_id is not None:
            fasta_dict[current_id] = "".join(seq_lines)

    return fasta_dict


def main():
    if not Path(models_file).exists():
        raise FileNotFoundError(f"找不到 models 文件: {models_file}")
    if not Path(input_fasta).exists():
        raise FileNotFoundError(f"找不到 fasta 文件: {input_fasta}")

    unique_models = read_unique_models(models_file)
    fasta_dict = read_fasta_as_dict(input_fasta)

    found = 0
    missing = []

    with open(output_fasta, "w", encoding="utf-8") as fout:
        for model in unique_models:
            if model in fasta_dict:
                fout.write(f">{model}\n")
                fout.write(f"{fasta_dict[model]}\n")
                found += 1
            else:
                missing.append(model)

    with open(missing_file, "w", encoding="utf-8") as fmiss:
        for model in missing:
            fmiss.write(model + "\n")

    print("完成")
    print(f"models 去重后数量: {len(unique_models)}")
    print(f"成功提取数量: {found}")
    print(f"未匹配数量: {len(missing)}")
    print(f"输出 fasta: {output_fasta}")
    print(f"未匹配列表: {missing_file}")


if __name__ == "__main__":
    main()