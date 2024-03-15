set -x

function _lock_parallelism {
    parallelism_limit=$1
    while true; do
        current_parallelism=`jobs | grep Running | wc -l`
        if [ "$current_parallelism" -ge "$parallelism_limit" ]; then
            echo "Current parallelism is ${current_parallelism}, which is equal or larger than limit ${parallelism_limit}; sleep;"
            sleep 20s
        else
            echo "Current parallelism is ${current_parallelism}, which is less than than limit ${parallelism_limit};"
            break
        fi
    done
} 


# starlink test
port=31000
trace_dir="pensieve/data/starlink_scaled_mahimahi/"
trace_files=`ls ${trace_dir}`




for method in default gpt35 gpt4; do
    for trial in 0; do
        for epoch in 4000; do
            summary_dir="pensieve/tests/starlink/${method}-trial-${trial}-epoch-${epoch}"
            model_path="pensieve/data/mahimahi_new_best_models/all_starlink_eval_models/${method}-starlink/trial-${trial}/models/nn_model_ep_${epoch}.ckpt"
            for trace_file in ${trace_files} ; do
                mahimahi_link_file=${trace_dir}${trace_file}
                bash run_single_test.sh ${port} ${mahimahi_link_file} ${summary_dir} ${trace_file} ${model_path} &> /tmp/log-${method}-trial-${trial}-epoch-${epoch}-trace-${trace_file} &
                _lock_parallelism 15
                port=$((${port} + 5))
            done
        done
    done
done


wait