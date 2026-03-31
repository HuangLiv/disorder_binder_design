#!/bin/bash

# ============ Step 1: Threading（生成初始氨基酸口袋) ============
mkdir -p 1_threading
cd 1_threading

python /data/hc/proteindesign/disorder_binder_design/threading/make_jobs.py ../peptide.fasta ../templates.list | sort -R > all_jobs

# 本地运行 threading jobs（替代 SLURM）
xargs -a all_jobs -I {} -P 72 bash -c "{}"

# 合并所有 silent 文件（选取能量小于-60进行下一步计算，减小计算量）
cat *.silent > threading.silent
cat *.sc > threading.sc
awk '$3 < -60 {print $NF}' threading.sc | wc -l
awk '$3 < -60 {print $NF}' threading.sc > good_tags.txt
wc -l good_tags.txt

cat good_tags_60.txt | silentslice threading.silent > threading_filtered_60.silent

# 查看有多少个结构
silentls threading_filtered_60.silent | wc -l

cd ..

# ============ Step 2: MPNN 序列设计 ============
mkdir -p 2_mpnn
cd 2_mpnn
export ROSETTA_DB_PATH="/data/hc/proteindesign/rosetta/main/database"

在第一次运行时设置--num_seq_per_target 1，在第二次运行时设置--num_seq_per_target 5。
python /data/hc/proteindesign/disorder_binder_design/mpnn_git_repo/design_scripts/killer_mpnn_interface_design.py \
  -silent /data/hc/proteindesign/disorder_binder_design/flexible_binder/1_threading/threading_filtered_60.silent \
  --num_seq_per_target 1 \
  --max_out 5 \
  --sampling_temp 0.1 \
  --out_folder /data/hc/proteindesign/disorder_binder_design/flexible_binder/2_mpnn \
  --out_name /data/hc/proteindesign/disorder_binder_design/flexible_binder/2_mpnn/mpnn_out 
cd ..

# ============ Step 3: 从 MPNN 输出的 silent 提取 FASTA ============
mkdir -p 3_af3_local

# 提取序列为 FASTA 格式（这是关键一步！）
silentsequence 2_mpnn/mpnn_out.silent | \
  awk '{print ">"$3"\n"$1":"$2}' > 3_af3_local/af3_input.fasta


silentsequence 2_mpnn/mpnn_out.silent | \
awk -v pep="GFTFRNPDDVVREFFGGRDPF" '{print ">"$3"\n"$1":"pep}' \
> 3_af3_local/af3_input.fasta


cd 3_af3_local
  
/data/hc/proteindesign/alphafast/scripts/run_alphafast.sh \
    --input_dir /data/hc/proteindesign/disorder_binder_design/flexible_binder/3_af3_local/af3_json \
    --output_dir /data/hc/proteindesign/disorder_binder_design/flexible_binder/3_af3_local/af3_outputs \
    --db_dir /data/hc/proteindesign/af3_database \
    --weights_dir /data/hc/proteindesign/af3_database/af3_model_parameter \
    --num_gpus 4 \
    --gpu_devices 0,1,2,3 \
    --batch_size 16
  

# ============ Step 5: AF3 结果过滤(过滤条件在对应.py文件中设置) ============
mkdir -p af3_filtering

python /data/hc/proteindesign/disorder_binder_design/scripts/af3_filtering.py

python /data/hc/proteindesign/disorder_binder_design/scripts/af3_fasta_filtering.py

#聚类分析(可选)
mmseqs easy-cluster \
    af3_filtered_design_sequences.fasta \
    mmseqs_clustering \
    mmseqs_tmp \
    --min-seq-id 0.4 \
    -s 5.7
    
# ============ Step 6: mpnn优化 ============
cd af3_outputs

silentfrompdbs *.pdb > af3_out.silent

cd ../../..

mkdir -p 4_mpnn
cd 4_mpnn

python /data/hc/proteindesign/disorder_binder_design/mpnn_git_repo/design_scripts/killer_mpnn_interface_design.py \
  -silent /data/hc/proteindesign/disorder_binder_design/flexible_binder/3_af3_local/3_af3_filtering/collected_top_model_pdb/af3_out.silent \
  --num_seq_per_target 5 \
  --max_out 5 \
  --sampling_temp 0.1 \
  --out_folder /data/hc/proteindesign/disorder_binder_design/flexible_binder/4_mpnn \
  --out_name /data/hc/proteindesign/disorder_binder_design/flexible_binder/4_mpnn/mpnn_out 


# ============ Step 5: AF3 预测及结果过滤 ============
mkdir -p 5_af3_local

silentsequence 4_mpnn/mpnn_out.silent | \
awk -v pep="GFTFRNPDDVVREFFGGRDPF" '{print ">"$3"\n"$1":"pep}' \
> 5_af3_local/af3_input.fasta

or 

silentsequence 4_mpnn/mpnn_out.silent | \
  awk '{print ">"$3"\n"$1":"$2}' > 5_af3_local/af3_input.fasta

python /data/hc/proteindesign/disorder_binder_design/scripts/fasta_to_af3_json_seed5.py

/data/hc/proteindesign/alphafast/scripts/run_alphafast.sh \
    --input_dir /data/hc/proteindesign/disorder_binder_design/flexible_binder/5_af3_local/af3_json \
    --output_dir /data/hc/proteindesign/disorder_binder_design/flexible_binder/5_af3_local/af3_outputs \
    --db_dir /data/hc/proteindesign/af3_database \
    --weights_dir /data/hc/proteindesign/af3_database/af3_model_parameter \
    --num_gpus 4 \
    --gpu_devices 0,1,2,3 \
    --batch_size 16

cd 5_af3_local

mkdir -p af3_filtering

python /data/hc/proteindesign/disorder_binder_design/scripts/af3_filtering.py

python /data/hc/proteindesign/disorder_binder_design/scripts/af3_fasta_filtering.py

#============迭代循环至满足条件的binder数量大于70个======================
#============也可根据自身需求调整过滤标准及数量================