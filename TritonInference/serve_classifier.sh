#!/bin/bash
docker rm -f triton-server
docker run --name triton-server --gpus 0 --rm -it \
  -v /home:/home \
  -p8000:8000 -p8001:8001 -p8002:8002 \
  -v <your model repo directory>/model_repository:/models \
  nvcr.io/nvidia/tritonserver:25.10-py3 \
  tritonserver --model-repository=/models