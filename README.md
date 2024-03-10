# GENET: Automatic Curriculum Generation for Learning Adaptation in Networking

## Installation

### Operating system information
Ubuntu 18.04. A large VM is preferred, e.g., reproducing Figure 9 CC takes
about 20 minutes on a VM with 96 vCPUs or 1 hour on a VM with 32 vCPUs. We
assume a VM with 32 vCPUs, 64G memory and 32G SSD storage is used for the
instructions below.

### Python Version
The repository is only tested under python3.6.9.

### Install apt packages

```bash
cd Genet
bash install.sh
```

## Emulation

## ABR
Please follow the [README](https://github.com/GenetProject/Genet/tree/main/src/emulator/abr#readme) under ```src/emulator/abr/```


## FAQ
1. CUDA driver error

    If the following cuda driver error message shows up, please ignore for now.
    The final results are not affected by the error message.
    ```bash
     E tensorflow/stream_executor/cuda/cuda_driver.cc:318] failed call to cuInit: UNKNOWN ERROR
    (genet) ubuntu@reproduce-genet:~/Genet/genet-lb-fig-upload$ python rl_test.py --saved_model="results/testing_model/udr_1/model_ep_49600.ckpt"
    2022-06-23 20:46:00.130224: E tensorflow/stream_executor/cuda/cuda_driver.cc:318] failed call to cuInit: UNKNOWN ERROR
    ```
