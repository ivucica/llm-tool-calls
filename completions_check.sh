#!/bin/bash

OPENAI_MODEL="${OPENAI_MODEL:-mlx-community/llama-3.2-3b-instruct}"
OPENAI_API="${OPENAI_API:-http://localhost:5001/v1}"
OPENAI_KEY="${OPENAI_KEY:-}"

OPENAI_HEADER="${OPENAI_KEY:+-H "Authorization: Bearer ${OPENAI_KEY}"}"

# Format: https://www.llama.com/docs/model-cards-and-prompt-formats/llama3_2/#-prompt-template- (2025-08-29)
# Also: https://github.com/meta-llama/llama-models/blob/57d9b434514159a812a61e38c992c276ef5432dc/models/llama3_2/text_prompt_format.md
TEXT="${TEXT:-There is a walrus in us! $(date +%s)}"
SYSTEM_TEXT="${SYSTEM_TEXT:-You are an expert assistant that replies in one sentence at most.}"
RAW_TEXT="${RAW_TEXT:-<|start_header_id|>system<|end_header_id|>${SYSTEM_TEXT}<|eot_id|><|start_header_id|>user<|end_header_id|>${TEXT}<|eot_id|><|start_header_id|>assistant<|end_header_id|>}"

echo $OPENAI_MODEL
echo $OPENAI_API
if [[ -z $OPENAI_KEY ]] ; then
  echo "no key"
else
  echo "has key"
fi
echo $TEXT

set -v

curl $OPENAI_HEADER -X POST -H "Content-Type: application/json" -d '{
  "model": "'"${OPENAI_MODEL}"'",
  "prompt": "'"${RAW_TEXT}"'"
}' --max-time 15.0 "${OPENAI_API}""/completions"

# This is for the non-chat completions check.
