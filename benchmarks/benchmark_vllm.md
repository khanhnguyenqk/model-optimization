# Benchmarking vLLM

This guide provides instructions on how to set up and benchmark the vLLM engine.

## 1. Run vLLM OpenAI Compatible Server (Optional)

If you want to benchmark the vLLM server endpoint, you can run it using Docker:

```bash
# Make sure you have your model weights (e.g., Mistral-7B-v0_1) in a local 'models' directory
docker run --runtime=nvidia --gpus all \
    -v $(pwd)/models:/models \
    -p 8000:8000 \
    --ipc=host \
    vllm/vllm-openai:latest \
    --model /models/Mistral-7B-v0_1
```

This command starts the server, making the model available at `http://localhost:8000`.

## 2. Install vLLM from Source

To run local benchmarks using vLLM's provided scripts, you need to install it from the source repository:

```bash
# Clone the vLLM repository
git clone https://github.com/vllm-project/vllm.git

# Navigate into the cloned directory
cd vllm

# Install vLLM core library
pip install vllm 
```

## 3. Run the Benchmark

vLLM includes benchmark scripts within its repository. A common script for benchmarking serving throughput is `benchmark_serving.py`.

Navigate to the benchmarks directory (if necessary) and run the script. You might need to adjust parameters based on your specific model and hardware.

**Important**: The `benchmark_serving.py` script with the `--dataset-name sharegpt` option requires a JSON file containing the prompts. You need to create this file *before* running the benchmark script.

```bash
# Ensure you are in the vllm directory (e.g., ~/projects/vllm)

# Now, run the benchmark script
python benchmarks/benchmark_serving.py \
    --backend vllm \
    --model /models/Mistral-7B-v0_1 \
    --tokenizer /home/ubuntu/projects/model-optimization/models/Mistral-7B-v0_1 \
    --dataset-name random \
    --num-prompts 100 \
    --request-rate 10 \
    --max-concurrency 10 \
    --host 127.0.0.1 \
    --port 8000 \
    --random-input-len 512 \
    --random-range-ratio 0.2
```

Refer to the vLLM documentation and the specific benchmark script's help (`python benchmarks/benchmark_serving.py --help`) for detailed usage and available options.