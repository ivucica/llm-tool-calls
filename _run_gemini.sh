#!/bin/bash
export OPENAI_API_KEY=$(cat _gemini_key.txt)
export OPENAI_API=https://generativelanguage.googleapis.com/v1beta/openai/
export OPENAI_MODEL=models/gemini-2.0-pro-exp-02-05

#curl https://generativelanguage.googleapis.com/v1beta/openai/models \
#  -H "Authorization: Bearer ${OPENAI_API_KEY}"


. env/bin/activate

python3 python_use_example.py
