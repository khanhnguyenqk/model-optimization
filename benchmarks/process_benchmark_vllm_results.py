# process_benchmark_results.py

import argparse
import json
import os
import re
import pandas as pd

def parse_filename(filename):
    """
    Parses the benchmark parameters from the filename.
    Expected format: bench_{BACKEND}_in{INPUT}_out{OUTPUT}_con{CON}_qps{QPS}.json
    Returns a dictionary of parameters or None if format doesn't match.
    """
    # Regex to capture the numeric values associated with keys
    # It allows for non-numeric backend but requires numeric values after in, out, con, qps
    match = re.match(
        r"bench_.*?"  # Match 'bench_' followed by any characters (non-greedy for backend)
        r"_in(\d+)"   # Capture input length
        r"_out(\d+)"  # Capture output length
        r"_con(\d+)"  # Capture concurrency
        r"_qps(\d+)"  # Capture request rate (QPS)
        r"\.json$",   # Must end with .json
        filename
    )
    if match:
        try:
            return {
                "input_len": int(match.group(1)),
                "output_len": int(match.group(2)),
                "concurrency": int(match.group(3)),
                "request_rate": int(match.group(4)),
            }
        except (ValueError, IndexError):
            return None # Should not happen with regex, but good practice
    return None

def process_results(results_dir):
    """
    Processes all benchmark JSON files in the specified directory.

    Args:
        results_dir (str): The path to the directory containing JSON result files.

    Returns:
        pandas.DataFrame: A DataFrame containing the consolidated results.
                         Returns None if the directory is invalid or no valid
                         files are found.
    """
    if not os.path.isdir(results_dir):
        print(f"Error: Directory not found: {results_dir}")
        return None

    all_results = []

    print(f"Scanning directory: {results_dir}")
    found_files = 0
    processed_files = 0

    for filename in os.listdir(results_dir):
        if filename.endswith(".json"):
            found_files += 1
            file_path = os.path.join(results_dir, filename)

            # Parse parameters from filename
            params = parse_filename(filename)
            if not params:
                print(f"  Skipping file with unexpected name format: {filename}")
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Extract key metrics, using .get() for safety
                metrics = {
                    "completed_requests": data.get("completed"),
                    "num_prompts": data.get("num_prompts"), # From config section
                    "request_throughput": data.get("request_throughput"),
                    "output_throughput": data.get("output_throughput"),
                    "total_token_throughput": data.get("total_token_throughput"),
                    "mean_ttft_ms": data.get("mean_ttft_ms"),
                    "p99_ttft_ms": data.get("p99_ttft_ms"),
                    "mean_tpot_ms": data.get("mean_tpot_ms"),
                    "p99_tpot_ms": data.get("p99_tpot_ms"),
                    "mean_e2el_ms": data.get("mean_e2el_ms"), # Extract E2E latency
                    "p99_e2el_ms": data.get("p99_e2el_ms"),   # Extract E2E latency P99
                    "backend": data.get("backend"),
                    "model_id": data.get("model_id"),
                    "temperature": data.get("temperature"), # Included if sampling was used
                    "top_p": data.get("top_p"),             # Included if sampling was used
                    "top_k": data.get("top_k"),             # Included if sampling was used
                }

                # Combine parameters from filename and metrics from file content
                result_row = {**params, **metrics}
                all_results.append(result_row)
                processed_files += 1

            except json.JSONDecodeError:
                print(f"  Skipping corrupted JSON file: {filename}")
            except Exception as e:
                print(f"  Skipping file due to error processing {filename}: {e}")

    print(f"Scan complete. Found {found_files} JSON files, processed {processed_files}.")

    if not all_results:
        print("No valid benchmark result files processed.")
        return None

    # Create DataFrame
    df = pd.DataFrame(all_results)

    # Define a logical column order (added e2el metrics)
    column_order = [
        "input_len", "output_len", "concurrency", "request_rate",
        "request_throughput", "output_throughput", "total_token_throughput",
        "mean_ttft_ms", "p99_ttft_ms",
        "mean_tpot_ms", "p99_tpot_ms",
        "mean_e2el_ms", "p99_e2el_ms", # Added E2E latency columns
        "completed_requests", "num_prompts", # Verification columns
        "backend", "model_id", "temperature", "top_p", "top_k" # Config columns
    ]
    # Reorder columns, keeping only those present in the DataFrame
    # Handle potential missing columns gracefully
    df = df[[col for col in column_order if col in df.columns]]


    # Sort the DataFrame for better readability
    df.sort_values(by=["input_len", "output_len", "concurrency", "request_rate"], inplace=True)

    return df

def main():
    parser = argparse.ArgumentParser(description="Process benchmark results from JSON files into a table.")
    parser.add_argument("results_dir", type=str, help="Directory containing the benchmark JSON files.")
    parser.add_argument("-o", "--output-basename", type=str, default="benchmark_summary",
                        help="Base name for the output CSV and JSON table files (without extension).")
    args = parser.parse_args()

    # Process the results
    results_df = process_results(args.results_dir)

    if results_df is not None and not results_df.empty:
        # Determine output directory (parent of results_dir)
        output_dir = os.path.dirname(os.path.abspath(args.results_dir))
        if not output_dir: # Handle case where results_dir is root or relative in cwd
             output_dir = "."

        # Define output filenames
        csv_filename = os.path.join(output_dir, f"{args.output_basename}.csv")
        json_filename = os.path.join(output_dir, f"{args.output_basename}.json")

        # Save to CSV
        try:
            results_df.to_csv(csv_filename, index=False, encoding='utf-8')
            print(f"Results saved to CSV: {csv_filename}")
        except Exception as e:
            print(f"Error saving CSV file: {e}")

        # Save to JSON (records format)
        try:
            results_df.to_json(json_filename, orient="records", indent=2, default_handler=str)
            print(f"Results saved to JSON: {json_filename}")
        except Exception as e:
            print(f"Error saving JSON file: {e}")

if __name__ == "__main__":
    main()