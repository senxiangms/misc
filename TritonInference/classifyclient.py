"""Classify sentiment using Triton-inferred sentiment_bert model."""

import time

import numpy as np
from transformers import AutoTokenizer
import tritonclient.http as httpclient

TRITON_URL = "localhost:8000"
MODEL_NAME = "sentiment_bert"

tokenizer = AutoTokenizer.from_pretrained(
    "nlptown/bert-base-multilingual-uncased-sentiment",
    model_max_length=128,
)


def classify(texts: list[str]) -> list[int]:
    """Return predicted class (0-4) for each text."""
    inputs = tokenizer(
        texts,
        return_tensors="np",
        padding="max_length",
        truncation=True,
        max_length=128,
    )

    client = httpclient.InferenceServerClient(url=TRITON_URL)

    input_ids = httpclient.InferInput("input_ids", inputs["input_ids"].shape, "INT64")
    input_ids.set_data_from_numpy(inputs["input_ids"])

    attention_mask = httpclient.InferInput(
        "attention_mask", inputs["attention_mask"].shape, "INT64"
    )
    attention_mask.set_data_from_numpy(inputs["attention_mask"])

    outputs = httpclient.InferRequestedOutput("logits")

    # log response latency
    import time
    start_time = time.time()
    response = client.infer(
        model_name=MODEL_NAME,
        inputs=[input_ids, attention_mask],
        outputs=[outputs],
        model_version="1",
    )
    end_time = time.time()
    print(f"Response latency: {end_time - start_time} seconds")
    logits = response.as_numpy("logits")

    return np.argmax(logits, axis=1).tolist()


if __name__ == "__main__":
    examples = ["This is great!", "I hate it.", "It's okay."]
    preds = classify(examples)
    for text, pred in zip(examples, preds):
        print(f"{text!r} -> class {pred}")
    