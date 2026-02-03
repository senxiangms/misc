# read from/Users/sxiang/prt/misc/data/freshness_accuracy_results_*_*.json
import json
import os

index_set = set()
all_data = []
# read all files in /Users/sxiang/prt/misc/data/freshness_accuracy_results_*_*.json
for file in os.listdir("/Users/sxiang/prt/misc/data/"):
    if file.startswith("freshness_accuracy_results_") and file.endswith(".json"):
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
# write to file /Users/sxiang/prt/misc/data/freshness_accuracy_results_dedup.json
with open("/Users/sxiang/prt/misc/data/freshness_accuracy_results_dedup_merged.json", "w") as f:
    json.dump(all_data, f, indent=4)

print("Done")