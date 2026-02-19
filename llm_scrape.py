import json
import argparse
from openai.types import batch
import requests
import asyncio
from openai import AsyncOpenAI
import importlib
from datetime import datetime
from zoneinfo import ZoneInfo
import httpx

# API_BASE_URL = "https://api.fireworks.ai/inference/v1/"
API_BASE_URL = "http://127.0.0.1:3003/v1/"
API_KEY="Gd6f9y5rSGIGsvmikACK6GhAKKC56gDdMd6S0bOl4GgSEZi4"
# MODEL_ID="accounts/fireworks/models/gpt-oss-120b"
MODEL_ID="Qwen/Qwen3-1.7B"
client = AsyncOpenAI(
    api_key=API_KEY,
    base_url=API_BASE_URL,
)
http_client = httpx.AsyncClient(timeout=120)

def assemble_headers_and_payload(config, messages, json_schema=None):
    headers = {
        "Authorization": f"Bearer {config['API_KEY']}",
        "Content-Type": "application/json"
    }
    # headers.update(config.get('additional_headers', {}))

    payload = {
        "model": config['model'],
        "messages": messages,
    }
    payload.update(config.get('additional_parameters', {}))
    return headers, payload

async def call_llm(args, system_prompt, prompt):
    # using httpx post request to the api
    config = {
        "API_KEY": API_KEY,
        "model": MODEL_ID,
        "additional_headers": {
            "Content-Type": "application/json",
            "temperature": 0.0,
            "chat_template_kwargs": {"enable_thinking": True}
        }
    }
    headers, payload = assemble_headers_and_payload(
        config, 
        [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}], 
        json_schema=None)
    # print(f"headers: {headers}")
    # print(f"payload: {payload}")
    response = await http_client.post(
        API_BASE_URL + "chat/completions", 
        json=payload, headers=headers)
    response.raise_for_status()
    return response.json()
# print current pacific time
time_context_str = "current LA time: " + datetime.now(ZoneInfo("America/Los_Angeles")).strftime("%Y-%m-%d %H:%M:%S")
print(time_context_str)

chat_history = ""   


scrape_counter = 0
async def main(args, system_prompt, _):
    with open(args.input_file, "r") as f:
        data = json.load(f)
    batch_prompts = []
    batch_size = args.batch_size
    buffered_responses = []
    while len(data) % batch_size != 0:
        data.append({"index": len(data), "text": "dummy, !ignore me! "})
    for item in data:
        index = item["index"]
        if index < args.resume_index:
            print(f"Skipping index {index} because it is less than {args.resume_index}")
            continue
        query = item["text"]
        prompt = query # prompt_template.format(query=query, question=query, time_context_str=time_context_str, chat_history=chat_history)
        batch_prompts.append({ "index": index, "query": query, "prompt":  prompt})

        if len(batch_prompts) == batch_size:
            retry = True
            while retry:
                try:
                    prompts = [prompt_dict["prompt"] for prompt_dict in batch_prompts]
                    results = await asyncio.gather(*(call_llm(args, system_prompt, prompt) for prompt in prompts))
                    retry = False
                except Exception as e:
                    print(f"Error: {e}, retry!")
                
            for prompt_dict, response in zip(batch_prompts, results):
                content = response["choices"][0]["message"]["content"]
                print(f"index: {prompt_dict['index']}, query: {prompt_dict['query']}, Response: {content}")
                buffered_responses.append({"index": prompt_dict["index"], "query": prompt_dict["query"], "response": content})
                
                if len(buffered_responses)  == args.buffered_size:
                    print(f"Saving buffered {len(buffered_responses)} responses to file...")
                    with open(args.output_prefix + f"_{buffered_responses[0]['index']}_{buffered_responses[-1]['index']}.json", "w") as f:
                        json.dump(buffered_responses, f, indent=4)
                    buffered_responses = []
            batch_prompts = []

    if len(buffered_responses) > 0:
        print("Saving buffered responses to file...")
        with open(args.output_prefix + f"_{buffered_responses[0]['index']}_{buffered_responses[-1]['index']}.json", "w") as f:
            json.dump(buffered_responses, f, indent=4)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_file", type=str, required=True)
    parser.add_argument("--output_prefix", type=str, required=True)
    parser.add_argument("--qcolumn", type=str, required=False, default="query")
    parser.add_argument("--prompt_module", type=str, required=True)
    parser.add_argument("--prompt_var", type=str, required=True)
    parser.add_argument("--max_tokens", type=int, required=False, default=200)
    parser.add_argument("--resume_index", type=int, required=False, default=0)
    parser.add_argument("--batch_size", type=int, required=False, default=4)
    parser.add_argument("--buffered_size", type=int, required=False, default=1000)
    args = parser.parse_args()
    prompt_module = importlib.import_module(args.prompt_module)
    system_prompt = getattr(prompt_module, args.prompt_var)
    print(f"Prompt template: {system_prompt}")
    print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    input("Press Enter to continue...")
    asyncio.run(main(args, system_prompt, None))

    # python3 llm_scrape.py --input_file ./data/guardrail_test_set.json --output_prefix guardrail1000_eval_ --prompt_module gr_prompt --prompt_var custom_guardrail_prompt 