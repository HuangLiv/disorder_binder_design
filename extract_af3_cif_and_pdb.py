#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import shutil
import sys

# ========= 改成你的实际路径 =========
models_txt = "af3_filtered_models.txt"
af3_outputs_dir = "af3_outputs"

collected_cif_dir = "/af3_filtering/collected_top_model_cif"
collected_pdb_dir = "/af3_filtering/collected_top_model_pdb"

convert_to_pdb = True
# ====================================


def normalize_model_name(name: str) -> str:
    """
    af3_filtered_models.txt 里可能是:
      xxx_dldesign_0/seed-1_sample
    统一变成:
      xxx_dldesign_0
    """
    name = name.strip()
    if not name:
        return ""
    if "/" in name:
        name = name.split("/")[0]
    return name


def read_unique_models(txt_file: Path):
    seen = set()
    models = []
    with open(txt_file, "r", encoding="utf-8") as f:
        for line in f:
            model = normalize_model_name(line)
            if model and model not in seen:
                seen.add(model)
                models.append(model)
    return models


def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)


def convert_cif_to_pdb_with_gemmi(cif_path: Path, pdb_path: Path):
    import gemmi
    st = gemmi.read_structure(str(cif_path))
    st.write_pdb(str(pdb_path))


def find_top_model_cif(model_dir: Path, model_name: str):
    """
    只在 model_dir 顶层找，不递归进入 seed-1_sample-* 子目录
    优先找:
      {model_name}_model.cif
    如果没有，再找顶层唯一的 *_model.cif
    """
    exact_cif = model_dir / f"{model_name}_model.cif"
    if exact_cif.exists():
        return exact_cif

    top_level_candidates = sorted(model_dir.glob("*_model.cif"))
    if len(top_level_candidates) == 1:
        return top_level_candidates[0]

    return None


def main():
    models_file = Path(models_txt)
    outputs_dir = Path(af3_outputs_dir)
    cif_out = Path(collected_cif_dir)
    pdb_out = Path(collected_pdb_dir)

    if not models_file.exists():
        print(f"[ERROR] 找不到 models 文件: {models_file}")
        sys.exit(1)

    if not outputs_dir.exists():
        print(f"[ERROR] 找不到 AF3 outputs 目录: {outputs_dir}")
        sys.exit(1)

    ensure_dir(cif_out)
    if convert_to_pdb:
        ensure_dir(pdb_out)

    models = read_unique_models(models_file)
    print(f"[INFO] models 去重后数量: {len(models)}")

    found_dirs = 0
    copied_cif = 0
    converted_pdb = 0

    missing_dirs = []
    missing_cif = []
    failed_pdb = []

    missing_dir_log = cif_out / "missing_model_dirs.txt"
    missing_cif_log = cif_out / "missing_top_model_cif.txt"
    copied_log = cif_out / "copied_top_model_cif_records.tsv"
    failed_pdb_log = cif_out / "failed_pdb_conversion.txt"

    with open(copied_log, "w", encoding="utf-8") as flog:
        flog.write("model\toriginal_cif\tcopied_cif\n")

        for model in models:
            model_dir = outputs_dir / model

            if not model_dir.exists() or not model_dir.is_dir():
                missing_dirs.append(model)
                continue

            found_dirs += 1

            cif_file = find_top_model_cif(model_dir, model)
            if cif_file is None:
                missing_cif.append(model)
                continue

            dest_cif = cif_out / f"{model}_model.cif"
            shutil.copy2(cif_file, dest_cif)
            copied_cif += 1
            flog.write(f"{model}\t{cif_file}\t{dest_cif}\n")

            if convert_to_pdb:
                dest_pdb = pdb_out / f"{model}_model.pdb"
                try:
                    convert_cif_to_pdb_with_gemmi(dest_cif, dest_pdb)
                    converted_pdb += 1
                except Exception as e:
                    failed_pdb.append((str(dest_cif), str(e)))

    with open(missing_dir_log, "w", encoding="utf-8") as f:
        for x in missing_dirs:
            f.write(x + "\n")

    with open(missing_cif_log, "w", encoding="utf-8") as f:
        for x in missing_cif:
            f.write(x + "\n")

    with open(failed_pdb_log, "w", encoding="utf-8") as f:
        if not failed_pdb:
            f.write("No failed pdb conversion.\n")
        else:
            for cif_file, err in failed_pdb:
                f.write(f"{cif_file}\t{err}\n")

    print("\n[INFO] 完成")
    print(f"[INFO] 去重后 model 数量        : {len(models)}")
    print(f"[INFO] 找到对应文件夹数量      : {found_dirs}")
    print(f"[INFO] 缺失文件夹数量         : {len(missing_dirs)}")
    print(f"[INFO] 缺失顶层 model.cif 数量: {len(missing_cif)}")
    print(f"[INFO] 成功复制 cif 数量      : {copied_cif}")
    if convert_to_pdb:
        print(f"[INFO] 成功转换 pdb 数量      : {converted_pdb}")
    print(f"[INFO] CIF 输出目录           : {cif_out}")
    if convert_to_pdb:
        print(f"[INFO] PDB 输出目录           : {pdb_out}")
    print(f"[INFO] 缺失目录记录           : {missing_dir_log}")
    print(f"[INFO] 缺失 cif 记录          : {missing_cif_log}")
    print(f"[INFO] cif 拷贝记录           : {copied_log}")
    if convert_to_pdb:
        print(f"[INFO] pdb 转换失败记录       : {failed_pdb_log}")


if __name__ == "__main__":
    main()