import os
import json
import csv

good_models = []

# 正确的目录遍历方式
for design_dir in os.listdir("af3_outputs"):
    design_path = os.path.join("af3_outputs", design_dir)
    
    # 检查是否是目录
    if not os.path.isdir(design_path):
        continue
    
    print(f"检查设计文件夹: {design_dir}")
    
    # 查找 ranking_scores.csv
    csv_file = os.path.join(design_path, f"{design_dir}_ranking_scores.csv")
    
    if not os.path.exists(csv_file):
        print(f"  ✗ 未找到: {csv_file}")
        continue
    
    print(f"  ✓ 找到: {csv_file}")
    
    # 读取 CSV 文件
    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                seed = row['seed']
                sample = row['sample']
                ranking_score = float(row['ranking_score'])
                
                # 查找对应的 JSON 文件
                json_file = os.path.join(design_path, f"{design_dir}_summary_confidences.json")
                
                iptm = 0.0
                ptm = 0.0
                
                if os.path.exists(json_file):
                    try:
                        with open(json_file, 'r') as jf:
                            json_data = json.load(jf)
                            iptm = json_data.get('iptm', 0.0)
                            ptm = json_data.get('ptm', 0.0)
                    except Exception as e:
                        print(f"    ⚠ JSON 读取错误: {e}")
                
                # 过滤条件（初始严格）
                if ranking_score > 0.8 and iptm > 0.83:
                    model_name = f"seed-{seed}_sample-{sample}"
                    good_models.append({
                        'design': design_dir,
                        'model': model_name,
                        'ranking_score': ranking_score,
                        'iptm': iptm,
                        'ptm': ptm
                    })
                    print(f"    ✓ 保留: {model_name} (ranking_score={ranking_score:.4f}, iptm={iptm:.4f})")
    
    except Exception as e:
        print(f"  ✗ CSV 读取错误: {e}")

# 按 ranking_score 排序
good_models.sort(key=lambda x: x['ranking_score'], reverse=True)

# 写入文件
with open("af3_filtered_models.txt", 'w') as f:
    for m in good_models:
        f.write(f"{m['design']}/seed-{m['model'].split('-')[1]}\n")

print(f"\n{'='*60}")
print(f"✓ 过滤完成！")
print(f"✓ 符合条件的模型数: {len(good_models)}")
print(f"✓ 过滤条件: ranking_score > 0.8 AND iptm > 0.83")
print(f"{'='*60}")

if len(good_models) == 0:
    print("\n⚠ 没有模型满足条件！")
    print("降低阈值重新尝试...")
    
    # 重新尝试较宽松的条件
    good_models = []
    
    for design_dir in os.listdir("af3_outputs"):
        design_path = os.path.join("af3_outputs", design_dir)
        if not os.path.isdir(design_path):
            continue
        
        csv_file = os.path.join(design_path, f"{design_dir}_ranking_scores.csv")
        if not os.path.exists(csv_file):
            continue
        
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                seed = row['seed']
                sample = row['sample']
                ranking_score = float(row['ranking_score'])
                
                json_file = os.path.join(design_path, f"{design_dir}_summary_confidences.json")
                iptm = 0.0
                ptm = 0.0
                
                if os.path.exists(json_file):
                    try:
                        with open(json_file, 'r') as jf:
                            json_data = json.load(jf)
                            iptm = json_data.get('iptm', 0.0)
                            ptm = json_data.get('ptm', 0.0)
                    except:
                        pass
                
                # 宽松条件：ranking_score > 0.75 OR iptm > 0.80
                if ranking_score > 0.75 or iptm > 0.80:
                    model_name = f"seed-{seed}_sample-{sample}"
                    good_models.append({
                        'design': design_dir,
                        'model': model_name,
                        'ranking_score': ranking_score,
                        'iptm': iptm,
                        'ptm': ptm
                    })
    
    good_models.sort(key=lambda x: x['ranking_score'], reverse=True)
    
    with open("af3_filtered_models.txt", 'w') as f:
        for m in good_models:
            f.write(f"{m['design']}/seed-{m['model'].split('-')[1]}\n")
    
    print(f"✓ 使用宽松条件：ranking_score > 0.75 OR iptm > 0.80")
    print(f"✓ 符合条件的模型数: {len(good_models)}")

print(f"\n前 20 个最好的模型:")
for i, m in enumerate(good_models[:20]):
    print(f"  {i+1:2d}. {m['design']}/{m['model']:20s} | ranking_score: {m['ranking_score']:.4f} | iptm: {m['iptm']:.4f}")
