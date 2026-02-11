
import onnx
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

model_name = "nlptown/bert-base-multilingual-uncased-sentiment"

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)
model.eval()


class LogitsWrapper(torch.nn.Module):
    def __init__(self, base_model):
        super().__init__()
        self.base_model = base_model

    def forward(self, input_ids, attention_mask):
        return self.base_model(
            input_ids=input_ids, attention_mask=attention_mask
        ).logits


export_model = LogitsWrapper(model)

# Dummy input
inputs = tokenizer(
    ["This is great!", "This is great!"],
    return_tensors="pt",
    padding="max_length",
    truncation=True,
    max_length=128,
)

torch.onnx.export(
    export_model,
    (inputs["input_ids"], inputs["attention_mask"]),
    "model.onnx",
    input_names=["input_ids", "attention_mask"],
    output_names=["logits"],
    dynamic_axes={
        "input_ids": {0: "batch_size", 1: "seq_len"},
        "attention_mask": {0: "batch_size", 1: "seq_len"},
        "logits": {0: "batch_size", 1: "num_labels"}
    },
    opset_version=17, # 17 support IR == 10
    do_constant_folding=False
)

model_onnx = onnx.load("model.onnx")
print(model_onnx.graph.output[0].type.tensor_type.shape)
print(model_onnx.graph.input[0].type.tensor_type.shape)
print(model_onnx.graph.input[1].type.tensor_type.shape)

print("ONNX model exported successfully")