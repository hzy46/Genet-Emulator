# set -x

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

# clear
bash clear.sh

while [[ true ]]; do
    # starlink test
    port=31000
    trace_dir="pensieve/data/5G/"
    trace_files=`ls ${trace_dir}`
    exist_task=f
    for method in default gpt35 gpt4; do
        summary_dir="pensieve/tests/5G/${method}-trial-${trial}-epoch-${epoch}"
        model_path="pensieve/data/mahimahi_new_best_models/gpt_eval_models/${method}-5g/nn_model_ep_${epoch}.ckpt"
        for trace_file in ${trace_files} ; do
            mahimahi_link_file=${trace_dir}${trace_file}
            ret_file=${summary_dir}"/log_RL_"${trace_file}
            python check_log_file.py ${ret_file}  # delete if not valid
            if [ -f ${ret_file} ]; then
                continue
            fi
            echo $ret_file
            sleep 5s
            bash run_single_test_4G_5G.sh ${port} ${mahimahi_link_file} ${summary_dir} ${trace_file} ${model_path} &> /tmp/log-5G-${method}-trial-${trial}-epoch-${epoch}-trace-${trace_file} &
            exist_task=t
            _lock_parallelism 100
            port=$((${port} + 5))
        done
    done
    _lock_parallelism 1
    wait
    if [ $exist_task == "f" ]; then
        break
    fi
done

while [[ true ]]; do
    # starlink test
    port=31000
    trace_dir="pensieve/data/4G/"
    trace_files=`ls ${trace_dir}`
    exist_task=f
    for method in default gpt35 gpt4; do
        summary_dir="pensieve/tests/4G/${method}-trial-${trial}-epoch-${epoch}"
        model_path="pensieve/data/mahimahi_new_best_models/gpt_eval_models/${method}-4g/nn_model_ep_${epoch}.ckpt"
        for trace_file in ${trace_files} ; do
            mahimahi_link_file=${trace_dir}${trace_file}
            ret_file=${summary_dir}"/log_RL_"${trace_file}
            python check_log_file.py ${ret_file}  # delete if not valid
            if [ -f ${ret_file} ]; then
                continue
            fi
            echo $ret_file
            sleep 5s
            bash run_single_test_4G_5G.sh ${port} ${mahimahi_link_file} ${summary_dir} ${trace_file} ${model_path} &> /tmp/log-5G-${method}-trial-${trial}-epoch-${epoch}-trace-${trace_file} &
            exist_task=t
            _lock_parallelism 100
            port=$((${port} + 5))
        done
    done
    _lock_parallelism 1
    wait
    if [ $exist_task == "f" ]; then
        break
    fi
done


wait