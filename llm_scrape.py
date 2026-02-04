import json
import argparse
from openai.types import batch
import requests
import asyncio
from openai import AsyncOpenAI
import importlib
from datetime import datetime
# API_BASE_URL = "https://api.fireworks.ai/inference/v1/"
API_BASE_URL = "http://172.20.62.34:3000/v1/"
API_KEY="Gd6f9y5rSGIGsvmikACK6GhAKKC56gDdMd6S0bOl4GgSEZi4"
# MODEL_ID="accounts/fireworks/models/gpt-oss-120b"
MODEL_ID="Qwen/Qwen3-4B-Instruct-2507"
client = AsyncOpenAI(
    api_key=API_KEY,
    base_url=API_BASE_URL,
)

async def call_llm(args, prompt):
    return await client.chat.completions.create(
        model=MODEL_ID,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=args.max_tokens,
    )

scrape_counter = 0
async def main(args, prompt_template):
    with open(args.input_file, "r") as f:
        data = json.load(f)
    batch_prompts = []
    batch_size = 4
    buffered_responses = []
    while len(data) % batch_size != 0:
        data.append({"index": len(data), "query": "dummy, ignore me! "})
    for item in data:
        index = item["index"]
        if index < args.resume_index:
            print(f"Skipping index {index} because it is less than {args.resume_index}")
            continue
        query = item["query"]
        prompt = prompt_template.format(query=query, question=query)
        batch_prompts.append({ "index": index, "query": query, "prompt":  prompt})

        if len(batch_prompts) == batch_size:
            retry = True
            while retry:
                try:
                    prompts = [prompt_dict["prompt"] for prompt_dict in batch_prompts]
                    results = await asyncio.gather(*(call_llm(args, prompt) for prompt in prompts))
                    retry = False
                except Exception as e:
                    print(f"Error: {e}, retry!")
                
            for prompt_dict, response in zip(batch_prompts, results):
                print(f"index: {prompt_dict['index']}, query: {prompt_dict['query']}, Response: {response.choices[0].message.content}")
                buffered_responses.append({"index": prompt_dict["index"], "query": prompt_dict["query"], "response": response.choices[0].message.content})
                
                if len(buffered_responses)  == 1000:
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
    parser.add_argument("--max_tokens", type=int, required=False, default=20)
    parser.add_argument("--resume_index", type=int, required=False, default=0)
    args = parser.parse_args()
    prompt_module = importlib.import_module(args.prompt_module)
    prompt_template = getattr(prompt_module, args.prompt_var)
    asyncio.run(main(args, prompt_template))