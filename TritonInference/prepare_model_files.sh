#!/bin/bash
src_dir = <your model.onnx and model.onnx.data files>
mkdir -p model_repository
cd model_repository
mkdir -p sentiment_bert
cp <your pbconfig.txt filepath>/config.pbtxt .
cd sentiment_bert
mkdir -p 1
cd 1
cp $src_dir/model.onnx .
cp $src_dir/model.onnx.data .

