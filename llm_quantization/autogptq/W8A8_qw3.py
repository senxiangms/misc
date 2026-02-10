
from transformers import AutoTokenizer
from auto_gptq import AutoGPTQForCausalLM, BaseQuantizeConfig

model_id = "Qwen/Qwen3-4B-Instruct-2507"
output_dir = "./qwen3-4b-instruct-gptq-int8"

tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)

quant_config = BaseQuantizeConfig(
    bits=8,
    group_size=128,
    desc_act=False
)

model = AutoGPTQForCausalLM.from_pretrained(
    model_id,
    quantize_config=quant_config,
    device_map="auto",
    trust_remote_code=True
)

model.quantize(tokenizer)
model.save_quantized(output_dir)
tokenizer.save_pretrained(output_dir)

print("Saved GPTQ INT8 to:", output_dir)
