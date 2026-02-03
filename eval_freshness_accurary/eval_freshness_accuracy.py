# use fireworks api to evaluate the freshness accuracy
import requests
import json
import time
import os
import sys
import logging
import traceback
import random
import string
import hashlib
import hmac
import base64
import urllib.parse
import argparse
from news_classifier_prompt import custom_data_freshness_prompt
import statistics
# firework api base url   
FIREWORKS_API_BASE_URL = "https://api.fireworks.ai/inference/v1/"
FIREWORKS_API_KEY="Gd6f9y5rSGIGsvmikACK6GhAKKC56gDdMd6S0bOl4GgSEZi4"

additional_parameters = {"top_k": 1, "top_p": 0.1}

import asyncio
from openai import AsyncOpenAI

client = AsyncOpenAI(
    api_key=FIREWORKS_API_KEY,
    base_url=FIREWORKS_API_BASE_URL,
)

async def call_llm(prompt):
    return await client.chat.completions.create(
        model="accounts/fireworks/models/gpt-oss-120b",
        messages=[
            {"role": "system", "content": "You are a helpful assistant. Do not show your reasoning. Only output the final answer."}, 
            {"role": "user", "content": prompt}
        ],
        temperature=0.0,
        max_tokens=1000,
    )

location = "New York"
time = "2026-01-26 12:00:00"
time_and_location_str = f"The current time and location is {time} in {location}"

# read from file /Users/sxiang/prt/PrtInferenceService/tests/news_query_classifier/seed_data_queries.json
def get_prompts():
    with open("/Users/sxiang/prt/PrtInferenceService/tests/news_query_classifier/seed_data_queries.json", "r") as f:
        queries = json.load(f)
        for query in queries:
            yield query

async def main(args):
    all_prompts_generator = get_prompts()
    batch_size = 2
    all_prompts_results = []
    retry = False
    metrics = {"input_tokens": [], "output_tokens": []}
    start_index = 0
    end_index = 0
    while all_prompts_generator: # while not exhausted
        if not retry: 
            batch_prompts = []
            i = 0
            while i < batch_size:
                try:
                    prompt_metadata_dict = next(all_prompts_generator)
                except StopIteration:
                    break
                if prompt_metadata_dict["index"] >= args.resume_index:
                    batch_prompts.append(prompt_metadata_dict)
                    i += 1
                else:
                    print(f"Skipping index {prompt_metadata_dict['index']} because it is less than {args.resume_index}")

        prompts = []
        if batch_prompts:
            for prompt_metadata_dict in batch_prompts:
                query = prompt_metadata_dict["query"]
                custom_data_freshness_prompt_str = custom_data_freshness_prompt.format(time_and_location_str=time_and_location_str, question=query)
                prompts.append(custom_data_freshness_prompt_str)
            try:
                results = await asyncio.gather(*(call_llm(prompt) for prompt in prompts))
            except Exception as e:
                print(f"Error: {e}, retry!")
                results = []
                retry = True
                continue
            retry = False
            for prompt_metadata_dict, result in zip(batch_prompts, results):
                print("--------------------------------")
                print(f"Prompt: {prompt_metadata_dict['query']}, Index: {prompt_metadata_dict['index']}") 
                print(f"Result: {result.choices[0].message.content}")
                prompt_metadata_dict["result"] = result.choices[0].message.content
                all_prompts_results.append(prompt_metadata_dict)
                metrics["input_tokens"].append(result.usage.prompt_tokens)
                metrics["output_tokens"].append(result.usage.completion_tokens)
                end_index = prompt_metadata_dict["index"]
            if end_index - start_index > 10:
                with open(f"{args.output_prefix}_{start_index}_{end_index}.json", "w") as f:
                    json.dump(all_prompts_results, f, indent=4)
                print(f"{start_index}_{end_index} Metrics: {statistics.mean(metrics['input_tokens'])}, {statistics.mean(metrics['output_tokens'])}")
                start_index = end_index
                end_index = 0
                all_prompts_results = []
                
# add arg resume_index to resume from a given index
parser = argparse.ArgumentParser()
parser.add_argument("--resume_index", type=int, default=0)
parser.add_argument("--output_prefix", type=str, default="freshness_accuracy_results")
args = parser.parse_args()
asyncio.run(main(args))
