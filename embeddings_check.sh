#!/bin/bash

OPENAI_MODEL="${OPENAI_MODEL:-gaianet/text-embedding-nomic-embed-text-v1.5-embedding}"
OPENAI_API="${OPENAI_API:-http://localhost:5001/v1}"
OPENAI_KEY="${OPENAI_KEY:-}"

OPENAI_HEADER="${OPENAI_KEY:+-H "Authorization: Bearer ${OPENAI_KEY}"}"

TEXT="${TEXT:-There is a walrus in us! $(date +%s)}"

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
  "model": "gaianet/text-embedding-nomic-embed-text-v1.5-embedding",
  "input": "'"${TEXT}"'"
}' --max-time 15.0 "${OPENAI_API}""/embeddings"

