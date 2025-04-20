docker run --runtime nvidia --gpus all \
    -v $(pwd)/models:/models \
    -p 8000:8000 \
    --ipc=host \
    vllm/vllm-openai:latest
    --model /model/Mistral-7B-v0_1