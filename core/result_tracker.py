import os
import sys

script_name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
results_filename = f"{script_name}_results.txt"

def load_successful_profiles():
    if not os.path.exists(results_filename):
        return set()
    with open(results_filename, "r", encoding="utf-8") as f:
        return set(line.strip().split(":")[0] for line in f if line.strip().endswith(":1"))

def save_success(profile_number):
    with open(results_filename, "a", encoding="utf-8") as f:
        f.write(f"{profile_number}:1\n")
