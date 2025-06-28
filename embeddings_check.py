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
    try:
        host = api_endpoint.split('//')[1].split('/')[0]
        if not host:
            raise ValueError("Invalid API endpoint provided.")
        conn = http.client.HTTPConnection(host, timeout=timeout)
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'silent-passenger/1.0',
        }
        if api_key:
            headers['Authorization'] = f'Bearer {api_key}'

        payload = json.dumps({
            'model': model,
            'input': text
        }).encode('utf-8')
        conn.request('POST', '/v1/embeddings', body=payload, headers=headers)

        response = conn.getresponse()
        if response.status != 200:
            raise http.client.HTTPException(f"HTTP error: {response.status} {response.reason}")
        data = response.read()
        embeddings_str = data.decode('utf-8')
        # decode json response
        embeddings = json.loads(embeddings_str).get('embeddings', [])
        if not isinstance(embeddings, list):
            raise ValueError("Invalid response format: 'embeddings' should be a list.")
        if not all(isinstance(x, float) for x in embeddings):
            raise ValueError(
                "Invalid response format: all elements in 'embeddings' should be floats.")
        if len(embeddings) == 0:
            raise ValueError("Empty embeddings list received.")
        return embeddings
    except http.client.HTTPException as e:
        print(f"Error fetching embeddings: {e}")
        return []
    finally:
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
        '--api_endpoint', type=str,
        default=os.getenv('OPENAI_API', 'http://localhost:5001/v1/embeddings'),
       help='API endpoint to fetch embeddings from.')

    args = parser.parse_args(argv)

    embeddings = attempt_embeddings_fetch(args.text, args.timeout, args.model, args.api_endpoint)
    if embeddings:
        print(f"Fetched embeddings: {embeddings}")
    else:
        print("Failed to fetch embeddings.")


if __name__ == "__main__":
    import sys
    main(sys.argv[1:])
