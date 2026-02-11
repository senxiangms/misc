import argparse
import json
parser = argparse.ArgumentParser(
    usage="python3 llm_compare.py --truth ./data/seed_data_gpt5_responses.json --treatment ./data/qw3-4b-guardrail_0_999.json --trt_key content_status --trt_val_map safe:0,unsafe:1 --truth_key gpt5_status")
parser.add_argument("--truth", type=str, required=True, help="Truth file containing the ground truth")
parser.add_argument("--treatment", type=str, required=True, help="Treatment file containing the LLM responses")
parser.add_argument("--trt_key", type=str, required=True, help="column key in the treatment file to compare with the truth")
parser.add_argument("--trt_val_map", help="string to int, like 'unsafe:1,safe:0'", type=str, required=True)
parser.add_argument("--truth_key", type=str, required=True, help="column key in the truth file to compare with the treatment")
args = parser.parse_args()

# read the baseline and treatment files
with open(args.truth, "r") as f:
    truth = json.load(f)

truth_dict = {item["index"]: item for item in truth}

with open(args.treatment, "r") as f:
    treatment = json.load(f)

trt_val_map = {item.split(":")[0]: (item.split(":")[1]) for item in args.trt_val_map.split(",")}

empty_responses = 0
invalid_responses = 0
inconsistent_responses = 0
consistent_responses = 0

for item in treatment:
    if item["index"] not in truth_dict:
        print(f"Index {item['index']} not found in truth")
        continue
    ground_truth = truth_dict[item["index"]]
    if "result" in item:
        treatment_result = item["result"]
    else:
        treatment_result = item["response"]
    if treatment_result is None or treatment_result == "":
        empty_responses += 1
        continue
    try:
        if isinstance(treatment_result, str):
            response_json = json.loads(treatment_result)
        else:
            response_json = treatment_result
    except:
        print(f"Index {item['index']} {args.trt_key} is not a valid JSON: {treatment_result}")
        invalid_responses += 1
        continue
    
    if trt_val_map[response_json[args.trt_key]] != str(ground_truth[args.truth_key]):
        #print(f" {trt_val_map[response_json[args.trt_key]]} != {str(ground_truth[args.truth_key])}")
        print(f"Index {item['index']} {args.trt_key} mismatch: {response_json[args.trt_key]}, truth/baseline: {ground_truth[args.truth_key]}")
        inconsistent_responses += 1
        continue
    consistent_responses += 1

print(f"Empty responses: {empty_responses}")
print(f"Invalid responses: {invalid_responses}")
print(f"Inconsistent responses: {inconsistent_responses}")
print(f"Consistent responses: {consistent_responses}")
print(f"Total responses: {empty_responses + invalid_responses + inconsistent_responses + consistent_responses}")
print(f"Accuracy: {consistent_responses / (empty_responses + invalid_responses + inconsistent_responses + consistent_responses)}")