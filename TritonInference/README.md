
- First, convert the sequence classification model to ONNX using `convert_onnx.py`.
- Run `prepare_model_files.sh` to prepare the model repo directories.
- Serve the model using `serve_classifier.sh`.
- Run `classifyclient.py` for inference.