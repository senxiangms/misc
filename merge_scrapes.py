from ast import parse
import json
import os
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--input_dir", type=str, required=True)
parser.add_argument("--file_prefix", type=str, required=True)
parser.add_argument("--output_file", type=str, required=True)
args = parser.parse_args()

index_set = set()
all_data = []
# read all files in /Users/sxiang/prt/misc/data/freshness_accuracy_results_*_*.json
for file in os.listdir(args.input_dir):
    if file.startswith(args.file_prefix) and file.endswith(".json"):
        with open(os.path.join("/Users/sxiang/prt/misc/data/", file), "r") as f: 
            data = json.load(f)
        for item in data:
            if item["index"] in index_set:
                print(f"Duplicate index: {item['index']}")
                continue
            index_set.add(item["index"])
            all_data.append(item)

# sort by index
all_data.sort(key=lambda x: x["index"])
# write to file
with open(args.output_file, "w") as f:
    json.dump(all_data, f, indent=4)

print(f"Merged {len(all_data)} entries into {args.output_file}")