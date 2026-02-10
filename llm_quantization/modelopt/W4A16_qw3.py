# tested on nvidia-modelopt 0.37.0 + tensorrt_llm 1.2.0rc6.post3
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import json
import modelopt.torch.quantization as mtq
import modelopt.torch.export as mte
from datasets import load_dataset

model_id = "Qwen/Qwen3-4B-Instruct-2507"

tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    torch_dtype=torch.bfloat16,
    device_map="cuda",
    trust_remote_code=True,
)
model.eval()

dataset = load_dataset("wikitext", "wikitext-2-raw-v1", split="train[:1%]")
dataset = dataset.filter(lambda ex: ex["text"] and ex["text"].strip() != "")

def tokenize_fn(example):
    return tokenizer(
        example["text"],
        truncation=True,
        max_length=512,
    )

calib_data = dataset.map(tokenize_fn, remove_columns=dataset.column_names)
from torch.utils.data import DataLoader
from transformers import DataCollatorWithPadding

data_collator = DataCollatorWithPadding(tokenizer=tokenizer, return_tensors="pt")
data_loader = DataLoader(
    calib_data,
    batch_size=4,
    shuffle=True,
    collate_fn=data_collator,
)
def forward_loop(model):
    for batch in data_loader:
        batch = {k: v.to("cuda") for k, v in batch.items()}
        model(**batch)

config = mtq.INT4_AWQ_CFG
# config['quant_cfg']['*input_quantizer'] = {"enable": False}
#{'quant_cfg': {'*weight_quantizer': [{'num_bits': 4, 'block_sizes': {-1: 128, 'type': 'static'}, 'enable': True}, {'num_bits': (4, 3), 'axis': None, 'enable': True}], '*input_quantizer': {'num_bits': (4, 3), 'axis': None, 'enable': True}, 'nn.BatchNorm1d': {'*': {'enable': False}}, 'nn.BatchNorm2d': {'*': {'enable': False}}, 'nn.BatchNorm3d': {'*': {'enable': False}}, 'nn.LeakyReLU': {'*': {'enable': False}}, '*lm_head*': {'enable': False}, '*proj_out.*': {'enable': False}, '*block_sparse_moe.gate*': {'enable': False}, '*router*': {'enable': False}, '*mlp.gate.*': {'enable': False}, '*mlp.shared_expert_gate.*': {'enable': False}, '*output_layer*': {'enable': False}, 'output.*': {'enable': False}, 'default': {'enable': False}}, 'algorithm': 'awq_lite'}
print(config)
model = mtq.quantize(
    model=model,
    config=config, 
    forward_loop=forward_loop)

prompt = "Explain speculative decoding in LLMs."
inputs = tokenizer(prompt, return_tensors="pt").to("cuda")

with torch.no_grad():
    out = model.generate(**inputs, max_new_tokens=50)

print(tokenizer.decode(out[0], skip_special_tokens=True))

tokenizer.save_pretrained("/home/ubuntu/qwen3-4b-instruct-2507-int8-modelopt_bf16")

mte.export_hf_checkpoint(
    model=model,
    dtype=torch.bfloat16,  # or torch.float16
    export_dir="/home/ubuntu/qwen3-4b-instruct-2507-int8-modelopt_bf16",
    save_modelopt_state=False,
)