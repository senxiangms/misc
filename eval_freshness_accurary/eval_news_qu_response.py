import json
import argparse
from news_qu_utils import normalize, entity_type_from_list, SUPPORTED_GEO, SUPPORTED_TOPICS, EntityType
# add response json file as an argument
parser = argparse.ArgumentParser()
parser.add_argument("--response_json_file", type=str, required=True)
args = parser.parse_args()

# load response json file
response_json = None
with open(args.response_json_file, "r") as f:
    response_json = json.load(f)

metrics = {}
metrics["geo_mismatch"] = 0
metrics["topic_mismatch"] = 0
metrics["entity_mismatch"] = 0
metrics["temporal_mismatch"] = 0
empty_entries = 0

for entry in response_json:
    if isinstance(entry ["result"], str):
        try:
            entry["result"] = json.loads(entry["result"])
        except:
            print(f"Error loading result: {entry['index']}: {entry['result']}")
            empty_entries += 1
            continue
    if entry["result"] is None:
        empty_entries += 1
        continue
    geography = entry["result"]["geography"]
    temporal =  entry["result"]["temporal"]
    topical = entry["result"]["topical"]
    entity = entry["result"]["entity"]
    geography = normalize(geography)
    temporal = normalize(temporal)
    topics = normalize(topical)
    entity_type = entity_type_from_list(entity)

    geo_supported = geography in SUPPORTED_GEO
    topic_supported = (isinstance(topics, list) and all(normalize(t) in SUPPORTED_TOPICS for t in topics))

    topic_norm  = "Supported Topic" if topic_supported else "Unsupported Topic"
    geo_norm = "Supported Geo" if geo_supported else "Unsupported Geo"
    entity_norm = "Multiple Entities" if entity_type == EntityType.MULTIPLE else "Single Entity" if entity_type == EntityType.SINGLE else "No Entity"
    temporal_norm = "Current" if temporal == "current" else "None" if temporal == "general" else "Recent Past" 

    geo_truth = entry["geography"]
    topic_truth = entry["topical"]
    temporal_truth = entry["temporal"] if entry["temporal"] is not None else "None"
    entity_truth = entry["entity"]  
    if geo_norm != geo_truth:
        print(f"Geo Mismatch: {entry['index']}: {geo_norm} != {geo_truth}")
        metrics["geo_mismatch"] += 1
    if topic_norm != topic_truth:
        print(f"Topic Mismatch: {entry['index']}: {topic_norm} != {topic_truth}")
        metrics["topic_mismatch"] += 1
    if temporal_norm != temporal_truth:
        print(f"Temporal Mismatch: {entry['index']}: {temporal_norm} != {temporal_truth}")
        metrics["temporal_mismatch"] += 1
    if entity_norm != entity_truth:
        print(f"Entity Mismatch: {entry['index']}: {entity_norm} != {entity_truth}")
        metrics["entity_mismatch"] += 1

print(metrics)
print(f"Empty entries: {empty_entries}")
valid_entries = len(response_json) - empty_entries
print(f"Total valid entries: {valid_entries}")
print(f"Geo Mismatch: {metrics['geo_mismatch'] / (valid_entries)}")
print(f"Topic Mismatch: {metrics['topic_mismatch'] / valid_entries}")
print(f"Temporal Mismatch: {metrics['temporal_mismatch'] / valid_entries}")
print(f"Entity Mismatch: {metrics['entity_mismatch'] / valid_entries}")
