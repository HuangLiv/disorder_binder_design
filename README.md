# disorder_binder_design
requirement： Alphafold3(alphafast:https://github.com/RomeroLab/alphafast.git), Kejia_peptide_IDR_binders(https://github.com/drhicks/Kejia_peptide_binders.git), 
pyrosetta, 
ProteinMPNN(https://github.com/dauparas/ProteinMPNN.git), 
rosetta(option,https://github.com/RosettaCommons/rosetta.git).

1. git clone https://github.com/drhicks/Kejia_peptide_binders.git
2. cd Kejia_peptide_binders
3.Make sure silent_tools is in your PATH
4.export REPO=path/to/Kejia_peptide_binders
5.export PATH=${REPO}/silent_tools:${REPO}/job_creation:${PATH}

# ============ Step 1: Threading ============
mkdir -p scripts

cd scripts

git clone https://github.com/HuangLiv/disorder_binder_design.git

cd ..

mkdir -p flexible_binder

cd flexible_binder

mkdir -p 1_threading

cd 1_threading

echo -e ">name\n（your peptide）" > peptide.fasta

python path/to/Kejia_binder_design/threading/make_jobs.py ../peptide.fasta ../templates.list | sort -R > all_jobs

# local threading jobs
xargs -a all_jobs -I {} -P 72 bash -c "{}"

# Combine all silent files (select those with energy less than -60 for further calculation to reduce computational load)

cat *.silent > threading.silent

cat *.sc > threading.sc

awk '$3 < -60 {print $NF}' threading.sc | wc -l

awk '$3 < -60 {print $NF}' threading.sc > good_tags.txt

wc -l good_tags.txt

cat good_tags_60.txt | silentslice threading.silent > threading_filtered_60.silent

# Check how many structures there are

silentls threading_filtered_60.silent | wc -l

cd ..

# ============ Step 2: MPNN sequence design ============

mkdir -p 2_mpnn

cd 2_mpnn

export ROSETTA_DB_PATH="/data/hc/proteindesign/rosetta/main/database"

##Set --num_seq_per_target to 1 during the first run, and set it to 5 during the second run.

python /path/to/Kejia_binder_design/mpnn_git_repo/design_scripts/killer_mpnn_interface_design.py \
  -silent /path/to/Kejia_binder_design/flexible_binder/1_threading/threading_filtered_60.silent \
  --num_seq_per_target 1 \
  --max_out 5 \
  --sampling_temp 0.1 \
  --out_folder /path/to/Kejia_binder_design/flexible_binder/2_mpnn \
  --out_name /path/to/kejia_binder_design/flexible_binder/2_mpnn/mpnn_out 

cd ..

# ============ Step 3: Extract FASTA from the silent output of MPNN ============
mkdir -p 3_af3_local

# The extraction sequence is in FASTA format (this is a crucial step!)

silentsequence 2_mpnn/mpnn_out.silent | \
  awk '{print ">"$3"\n"$1":"$2}' > 3_af3_local/af3_input.fasta

or

silentsequence 2_mpnn/mpnn_out.silent | \
awk -v pep="your peptide" '{print ">"$3"\n"$1":"pep}' \
> 3_af3_local/af3_input.fasta


cd 3_af3_local
  
/path/to/alphafast/scripts/run_alphafast.sh \
    --input_dir /path/to/Kejia_binder_design/flexible_binder/3_af3_local/af3_json \
    --output_dir /path/to/Kejia_binder_design/flexible_binder/3_af3_local/af3_outputs \
    --db_dir /path/to/af3_database \
    --weights_dir /path/to/af3_database/af3_model_parameter \
    --num_gpus 4 \
    --gpu_devices 0,1,2,3 \
    --batch_size 16
  

# ============ Step 5: AF3 result filtering (filtering conditions are set in the corresponding .py file) ============
mkdir -p af3_filtering

python /path/to/Kejia_binder_design/scripts/af3_filtering.py

python //path/to/Kejia_binder_design/scripts/af3_fasta_filtering.py

#cluster analysis(option)
mmseqs easy-cluster \
    af3_filtered_design_sequences.fasta \
    mmseqs_clustering \
    mmseqs_tmp \
    --min-seq-id 0.4 \
    -s 5.7
    
# ============ Step 6: mpnn optimize ============
cd af3_outputs

silentfrompdbs *.pdb > af3_out.silent

cd ../../..

mkdir -p 4_mpnn

cd 4_mpnn

python /path/to/Kejia_binder_design/mpnn_git_repo/design_scripts/killer_mpnn_interface_design.py \
  -silent /path/to/Kejia_binder_design/flexible_binder/3_af3_local/3_af3_filtering/collected_top_model_pdb/af3_out.silent \
  --num_seq_per_target 5 \
  --max_out 5 \
  --sampling_temp 0.1 \
  --out_folder /path/to/Kejia_binder_design/flexible_binder/4_mpnn \
  --out_name /path/to/Kejia_binder_design/flexible_binder/4_mpnn/mpnn_out 


# ============ Step 5: AF3 prediction and result filtering ============
mkdir -p 5_af3_local

silentsequence 4_mpnn/mpnn_out.silent | \
awk -v pep="your peptide" '{print ">"$3"\n"$1":"pep}' \
> 5_af3_local/af3_input.fasta

or 

silentsequence 4_mpnn/mpnn_out.silent | \
  awk '{print ">"$3"\n"$1":"$2}' > 5_af3_local/af3_input.fasta

python /path/to/Kejia_binder_design/scripts/fasta_to_af3_json_seed5.py

/path/to/alphafast/scripts/run_alphafast.sh \
    --input_dir /path/to/Kejia_binder_design/flexible_binder/5_af3_local/af3_json \
    --output_dir /path/to/Kejia_binder_design/flexible_binder/5_af3_local/af3_outputs \
    --db_dir /path/to/af3_database \
    --weights_dir /path/to/af3_database/af3_model_parameter \
    --num_gpus 4 \
    --gpu_devices 0,1,2,3 \
    --batch_size 16

cd 5_af3_local

mkdir -p af3_filtering

python /path/to/Kejia_binder_design/scripts/af3_filtering.py

python /path/to/Kejia_binder_design/scripts/af3_fasta_filtering.py

#=====The iteration loop continues until the number of binders satisfying the condition exceeds 70==============
#============You can also adjust the filtering criteria and quantity according to your own needs================
