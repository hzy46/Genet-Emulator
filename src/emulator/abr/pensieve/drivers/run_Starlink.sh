#!/bin/bash

# Run experiments
mkdir -p ./pensieve/tests/Starlink

for i in {0..4}; do
    # copy the models to the right place
    cp ./pensieve/data/mahimahi_new_best_models/all_starlink_eval_models/gpt35-starlink/trial-$i/models/nn_model_ep_4000.ckpt.* ./pensieve/data/mahimahi_new_best_models/gpt_eval_models/gpt35-starlink/
    cp ./pensieve/data/mahimahi_new_best_models/all_starlink_eval_models/gpt4-starlink/trial-$i/models/nn_model_ep_4000.ckpt.* ./pensieve/data/mahimahi_new_best_models/gpt_eval_models/gpt4-starlink/
    cp ./pensieve/data/mahimahi_new_best_models/all_starlink_eval_models/default-starlink/trial-$i/models/nn_model_ep_4000.ckpt.* ./pensieve/data/mahimahi_new_best_models/gpt_eval_models/default-starlink/

    # run the experiments
    bash ./pensieve/drivers/run_mahimahi_emulation_GPT35_Starlink.sh
    bash ./pensieve/drivers/run_mahimahi_emulation_GPT4_Starlink.sh
    bash ./pensieve/drivers/run_mahimahi_emulation_Default_Starlink.sh 

    # copy the results to the right place
    cp -r ./pensieve/tests/GPT35_60_40_Starlink ./pensieve/tests/Starlink/GPT35_60_40_Starlink_Run_$i
    cp -r ./pensieve/tests/GPT4_60_40_Starlink ./pensieve/tests/Starlink/GPT4_60_40_Starlink_Run_$i
    cp -r ./pensieve/tests/Default_60_40_Starlink ./pensieve/tests/Starlink/Default_60_40_Starlink_Run_$i
done
