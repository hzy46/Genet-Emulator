# Example:
# base_port: 15000
# mahimahi_link_file: pensieve/data/starlink_scaled_mahimahi/starlink_trace_15.log
# summary_dir: pensieve/tests/GPT4_60_40_Starlink
# trace_file: starlink_trace_15.log
# model_path: pensieve/data/mahimahi_new_best_models/gpt_eval_models/gpt4-starlink/nn_model_ep_4000.ckpt
set -x

base_port=$1
mahimahi_link_file=$2
summary_dir=$3
trace_file=$4
model_path=$5

# for tensorflow, force cpu
export CUDA_VISIBLE_DEVICES=""

mkdir -p ${summary_dir}

video_server_port=$((${base_port} + 1))
abr_server_port=$((${base_port} + 2))

ps aux | grep ${video_server_port} | grep video_server | awk '{print $2}' | xargs kill
ps aux | grep ${abr_server_port} | grep virtual_browser | awk '{print $2}' | xargs kill

cd pensieve/video_server
python video_server.py --port ${video_server_port} & 
cd ../../

sleep 3s

mm-delay 40 mm-loss uplink 0 mm-loss downlink 0 mm-link pensieve/data/12mbps ${mahimahi_link_file} -- bash -xc "python -m pensieve.virtual_browser.virtual_browser --ip \${MAHIMAHI_BASE} --port ${video_server_port} --abr RL --video-size-file-dir pensieve/data/video_sizes --summary-dir ${summary_dir} --trace-file ${trace_file} --actor-path ${model_path} --abr-server-port=${abr_server_port}"

ps aux | grep ${video_server_port} | grep video_server | awk '{print $2}' | xargs kill
