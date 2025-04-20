#!/bin/bash

# --- Configuration ---
MODEL_PATH="/models/Mistral-7B-v0_1"
TOKENIZER_PATH="/home/ubuntu/projects/model-optimization/models/Mistral-7B-v0_1"
HOST="127.0.0.1"
PORT="8000"
BACKEND="vllm"
DATASET="random"        # Using random dataset to control lengths precisely
NUM_PROMPTS=100         # Number of requests per run
RESULT_DIR="results_prod_sim" # Directory to save JSON results

# --- Realistic Parameter Settings ---

# Define representative request shapes as "INPUT_LEN:OUTPUT_LEN" pairs
# Example: Short Q&A, Medium Summary, Long Context Task
REQUEST_SHAPES=(
  "128:64"
  "512:128"
  "1024:256"
)

# Define concurrency levels (and corresponding QPS) to test
CONCURRENCIES=(1 5 10 20 30) # Adjust as needed

# Define sampling parameters for generation
# Set temperature=0 for greedy decoding (fastest, deterministic)
# Set temperature > 0 and top_p < 1 for probabilistic sampling
TEMPERATURE=0.7
TOP_P=0.95
TOP_K=-1 # -1 typically disables top-k in vLLM/Hugging Face if top_p is used

# --- Script Logic ---
mkdir -p "$RESULT_DIR" # Create results directory if it doesn't exist

echo "Starting benchmark runs with production-like settings..."

# Add sampling parameters to the command arguments if they are active
sampling_args=""
if (( $(echo "$TEMPERATURE > 0" | bc -l) )); then
  sampling_args+=" --temperature $TEMPERATURE"
fi
if (( $(echo "$TOP_P < 1" | bc -l) )); then
  sampling_args+=" --top-p $TOP_P"
fi
# Only add top_k if it's positive, assuming -1 or 0 disables it
if [[ "$TOP_K" -gt 0 ]]; then
    sampling_args+=" --top-k $TOP_K"
fi
echo "Using fixed sampling parameters:$sampling_args"


# Loop through each defined request shape
for shape in "${REQUEST_SHAPES[@]}"; do
  # Parse input and output lengths from the shape string
  IFS=':' read -r input_len output_len <<< "$shape"

  echo "=========================================="
  echo "Testing Request Shape: Input=${input_len}, Output=${output_len}"
  echo "=========================================="

  # Loop through each concurrency level for this shape
  for concurrency in "${CONCURRENCIES[@]}"; do

    # Set request rate equal to concurrency for this run to try and saturate
    request_rate=$concurrency

    echo "--------------------------------------------------"
    echo "Running: Concurrency = $concurrency, Request Rate = $request_rate"
    echo "--------------------------------------------------"

    # Construct a descriptive filename
    # Include sampling info if it varied, but here it's fixed per script run
    output_filename="${RESULT_DIR}/bench_${BACKEND}_in${input_len}_out${output_len}_con${concurrency}_qps${request_rate}.json"

    # Run the benchmark command
    # Note: Added the sampling_args variable
    python benchmarks/benchmark_serving.py \
      --backend "$BACKEND" \
      --model "$MODEL_PATH" \
      --tokenizer "$TOKENIZER_PATH" \
      --dataset-name "$DATASET" \
      --num-prompts "$NUM_PROMPTS" \
      --request-rate "$request_rate" \
      --max-concurrency "$concurrency" \
      --host "$HOST" \
      --port "$PORT" \
      --random-input-len "$input_len" \
      --random-output-len "$output_len" \
      $sampling_args \
      --save-result \
      --result-filename "$output_filename"

    if [ $? -ne 0 ]; then
        echo "ERROR: Benchmark run failed for In=${input_len}, Out=${output_len}, Con=${concurrency}"
        # Optional: decide whether to continue or exit on error
        # exit 1
    fi

    # Optional: Add a small delay between runs if needed
    # sleep 5
  done
done

echo "=========================================="
echo "All benchmark runs completed."
echo "Results saved in '$RESULT_DIR' directory."
echo "=========================================="