"""Functions to check if the embeddings can be fetched, within a deadline.

This attempts to do this using the standard Python library's http client,
without loading additional dependencies.
"""

import http.client
import json

import argparse
import os



def attempt_embeddings_fetch(text: str, timeout: float, model: str, api_key: str='', api_endpoint: str='http://localhost:5001/v1/embeddings') -> list[float]:
    """
    Attempt to fetch embeddings for the given text within the specified deadline.

    Args:
        text (str): The input text for which embeddings are to be fetched.
        timeout (float): The timeout by which the embeddings must be fetched.
        model (str): The model to use for fetching embeddings.
        api_endpoint (str): The API endpoint to fetch embeddings from. Defaults
            a localhost endpoint on port 5001, for example LM Studio.

    Returns:
        list[float]: The fetched embeddings as a list of floats.
    """

    example_request: str = """
POST /v1/embeddings HTTP/1.1
Content-Type: application/json
Content-Length: 124
Host: a.b.c.d
Connection: close
Accept: application/json
User-Agent: silent-passenger/1.0
Authorization: Bearer 123

{
  "model": "gaianet/text-embedding-nomic-embed-text-v1.5-embedding",
  "input": "There is a walrus in us! 1744022772"
}
    """
    del example_request  # This is just an example request, not used in the code.

    print(f"Attempting to fetch embeddings for text: {text} using model: {model} "
          f"from API endpoint: {api_endpoint} with timeout: {timeout} seconds.")

    conn = None
    warnings: list[str] = []
    resp_str: str = ""
    try:
        schema = api_endpoint.split('://')[0]
        host = api_endpoint.split('://')[1].split('/')[0]
        if not host:
            raise ValueError("Invalid API endpoint provided.")
        conncls = http.client.HTTPConnection
        if schema == "https":
            conncls = http.client.HTTPSConnection
        conn = conncls(host, timeout=timeout)
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'silent-passenger/1.0',
        }
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'

        path = '/' + api_endpoint.split('://')[1].split('/', 1)[1]

        payload = json.dumps({
            'model': model,
            'input': text
        }).encode('utf-8')
        conn.request('POST', path, body=payload, headers=headers)

        print('using host %s and path %s' % (host, path))

        response = conn.getresponse()
        if response.status != 200:
            raise http.client.HTTPException(f"HTTP error: {response.status} {response.reason}")
        data = response.read()
        resp_str = data.decode('utf-8')

        # response structure:
        # { "object": "list", "data": [
        #   { "object": "embedding", "embedding": [ 1, 2, 3 ], "index": 0 }
        # ], "model": "modelname", "usage": { "prompt_tokens": 0, "total_tokens": 0 } }

        # decode json response
        resp = json.loads(resp_str)
        if not isinstance(resp, dict):
            raise ValueError("Invalid response format: response should be a dict / object.")
        if resp.get("object", None) != "list":
            raise ValueError("Invalid response format: response should contain a list-type object, got %s instead." % resp.get("object", None))
        if "data" not in resp.keys():
            raise ValueError("Invalid response format: response should contain a key named 'data'.")
        data = resp["data"]
        if not isinstance(data, list):
            raise ValueError("Invalid response format: 'data' should be a list / array.")
        if len(data) == 0:
            raise ValueError("Invalid response format: 'data' should not be zero-length.")
        if len(data) > 1:
            warnings.append("Got multiple objects inside data, using only the first one (index: %d)" % data[0].get("index", None))
        data0 = data[0]
        if data0.get("object") != "embedding":
            raise ValueError("Invalid response format: 'data0' should contain an embedding-type object, got %s instead." % data.get("object", None))
        if data0.get("index", None):
            warnings.append("Got embedding object with index that is present, but not zero: %d" % data0.get("index", None))
        embedding = data0.get("embedding", [])
        if not isinstance(embedding, list):
            raise ValueError("Invalid response format: 'embedding' should be a list.")
        if len(embedding) == 0:
            raise ValueError("Invalid response format: Empty embedding list received.")
        if not all(isinstance(x, float) for x in embedding):
            raise ValueError(
                "Invalid response format: all elements in 'embedding' should be floats.")

        return embedding
    except http.client.HTTPException as e:
        print(f"Error fetching embeddings: {e}")
        if not warnings:
            # avoid printing resp_str twice
            print(resp_str)
        return []
    except ValueError as e:
        if not warnings:
            # avoid printing resp_str twice
            print(resp_str)
            print(resp)
        raise
    finally:
        if warnings:
            print("Warnings:")
            print(warnings)
            print(resp_str)
        if conn:
            conn.close()


def main(argv: list[str] = []) -> None:
    """Example usage. Allows overriding the API endpoint, text, model, timeout.

    Uses OPENAI_API environment variable to derive the API endpoint by
    appending '/v1/embeddings' to the base URL.

    Usage:
        python embeddings_check.py --text "Hello, world!" --timeout 5.0 --api_endpoint "http://localhost:5001/v1/embeddings"

    Args:
        argv (list[str]): Command line arguments, where the arguments are passed
            as flags --text, --timeout, and --api_endpoint, all optional.

    """
    parser = argparse.ArgumentParser(
        description="Check if embeddings can be fetched within a deadline.")
    parser.add_argument(
        '--text', type=str, default="Hello, world!", help='Text to fetch embeddings for.')
    parser.add_argument(
        '--timeout', type=float, default=5.0, help='Timeout in seconds to fetch embeddings.')
    parser.add_argument(
        '--model', type=str,
        default=os.getenv('OPENAI_MODEL',
                          'gaianet/text-embedding-nomic-embed-text-v1.5-embedding'),
        help='Model to use for fetching embeddings.')
    parser.add_argument(
        '--api_key', type=str,
        default=os.getenv('OPENAI_KEY', ''),
       help='API key to use.')
    parser.add_argument(
        '--api_endpoint', type=str,
        default=os.getenv('OPENAI_API', 'http://localhost:5001/v1') + '/embeddings',
        help='API endpoint to fetch embeddings from.')

    args = parser.parse_args(argv)

    embeddings = attempt_embeddings_fetch(args.text, args.timeout, args.model, args.api_key, args.api_endpoint)
    if embeddings:
        print(f"Fetched embeddings: {embeddings}")
    else:
        print("Failed to fetch embeddings.")


if __name__ == "__main__":
    import sys
    main(sys.argv[1:])
