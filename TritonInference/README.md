
1. first you need to convert sequence classification model into onnx format using convert_onnx.py
2. run bash script prepare_model_files to prepare model repo directories
3. serve the model using run_triton.sh
4. run classifyclient.py to inference