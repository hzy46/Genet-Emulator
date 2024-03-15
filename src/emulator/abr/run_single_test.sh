base_port=15000
video_server_port=$((${base_port} + 1))
abr_server_port=$((${base_port} + 2))

cd pensieve/video_server
python video_server.py --port ${video_server_port} & 
cd ../../

mm-delay 40 mm-loss uplink 0 mm-loss downlink 0 mm-link pensieve/data/12mbps pensieve/data/starlink_scaled_mahimahi/starlink_trace_15.log -- bash -xc "python -m pensieve.virtual_browser.virtual_browser --ip $\\{MAHIMAHI_BASE\\} --port ${video_server_port} --abr RL --video-size-file-dir pensieve/data/video_sizes --summary-dir pensieve/tests/GPT4_60_40_Starlink --trace-file starlink_trace_15.log --actor-path pensieve/data/mahimahi_new_best_models/gpt_eval_models/gpt4-starlink/nn_model_ep_4000.ckpt --abr-server-port=${abr_server_port}"

ps aux | grep ${video_server_port} | grep video_server | awk '{print $2}' | xargs kill
