#!/bin/bash
. env/bin/activate

export OPENAI_API=http://127.0.0.1:11434/v1
export OPENAI_MODEL=llama3.2:latest

python3 python_use_example.py
