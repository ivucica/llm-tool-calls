"""
LM Studio Tool Use Demo: Wikipedia Querying Chatbot
Demonstrates how an LM Studio model can query Wikipedia
"""

# Standard library imports
import itertools
import json
import shutil
import sys
import threading
import time
import urllib.parse
import urllib.request

# Third-party imports
from openai import OpenAI

# Initialize LM Studio client
import os
base_url = os.getenv("OPENAI_API", default="http://0.0.0.0:5001/v1")
client = OpenAI(base_url=base_url, api_key="lm-studio")
MODEL = os.getenv("OPENAI_MODEL", default="mlx-community/llama-3.2-3b-instruct")


def fetch_wikipedia_content(search_query: str) -> dict:
    """Fetches wikipedia content for a given search_query"""
    try:
        # Search for most relevant article
        search_url = "https://en.wikipedia.org/w/api.php"
        search_params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": search_query,
            "srlimit": 1,
        }

        url = f"{search_url}?{urllib.parse.urlencode(search_params)}"
        with urllib.request.urlopen(url) as response:
            search_data = json.loads(response.read().decode())

        if not search_data["query"]["search"]:
            return {
                "status": "error",
                "message": f"No Wikipedia article found for '{search_query}'",
            }

        # Get the normalized title from search results
        normalized_title = search_data["query"]["search"][0]["title"]

        # Now fetch the actual content with the normalized title
        content_params = {
            "action": "query",
            "format": "json",
            "titles": normalized_title,
            "prop": "extracts",
            "exintro": "true",
            "explaintext": "true",
            "redirects": 1,
        }

        url = f"{search_url}?{urllib.parse.urlencode(content_params)}"
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())

        pages = data["query"]["pages"]
        page_id = list(pages.keys())[0]

        if page_id == "-1":
            return {
                "status": "error",
                "message": f"No Wikipedia article found for '{search_query}'",
            }

        content = pages[page_id]["extract"].strip()
        return {
            "status": "success",
            "content": content,
            "title": pages[page_id]["title"],
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


# Define tool for LM Studio
WIKI_TOOL = {
    "type": "function",
    "function": {
        "name": "fetch_wikipedia_content",
        "description": (
            "Search Wikipedia and fetch the introduction of the most relevant article. "
            "Always use this if the user is asking for something that is likely on wikipedia. "
            "If the user has a typo in their search query, correct it before searching."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "search_query": {
                    "type": "string",
                    "description": "Search query for finding the Wikipedia article",
                },
            },
            "required": ["search_query"],
        },
    },
}


import copy
WIKI_TOOL_2 = copy.deepcopy(WIKI_TOOL)
WIKI_TOOL_2['function']['name'] = 'fetch_real_authoritative_text'
WIKI_TOOL_2['function']['description'] = "Search an authoritative book and fetch the introduction of the most relevant article Always use this if the user is asking for some fact, especially dates, rather than assume wikipedia is correct or your memory is correct. If the user has a typo in the search query, correct it before searching. For biographies, prefer searching for that individual person's article (using their full name)."
WIKI_TOOL_2['function']['parameters']['properties']['search_query']['description'] = 'Search query for finding the authoritative text on the subject'


DATE_SUBTRACT_TOOL = {
  "type": "function",
  "function": {
    "name": "subtract_dates_return_years",
    "description": (
      "Process input dates as timestamps, subtract timestamps, and return how many"
      " years passed in-between, rounded down. Useful to compute age."
      " If the dates are fetched from a different source, do not provide the inputs"
      " until you received them from a different function call."
    ),
    "parameters": {
      "type": "object",
      "properties": {
        "later_date": {
          "type": "object",
          "description": "Year, month and date for the later (newer) of the two input dates. Must be a valid date.",
          "properties": {
             "year": { "type": "number" },
             "month": { "type": "number" },
             "day": { "type": "number" },
          },
          "required": ["year", "month", "day"]

        },
        "earlier_date": {
          "type": "object",
          "description": "Year, month and date for the earlier (older) of the two input dates. Must be a valid date.",
          "properties": {
             "year": { "type": "number" },
             "month": { "type": "number" },
             "day": { "type": "number" },
          },
          "required": ["year", "month", "day"]
        },
      },
      "required": ["later_date", "earlier_date"]
    }
  }
}

import datetime
import ast # alternative to json that handles singlequotes as well

def subtract_dates_return_years(later_date, earlier_date) -> dict:
    """
    Calculate the difference in years between two dates.

    Args:
      later_date (dict): A dictionary containing 'year', 'month', and 'day' for a later date.
      earlier_date (dict): A dictionary containing 'year', 'month', and 'day' for an earlier date.
    Returns:
      dict: A dictionary with the status of the operation and the difference in years, or an error message if dates are invalid.
    """
    if isinstance(later_date, str): 
      try: later_date = json.loads(later_date)
      except: later_date = ast.literal_eval(later_date)  # https://stackoverflow.com/a/21154138 ; any security vuln?
    if isinstance(earlier_date, str):
      try: earlier_date = json.loads(earlier_date)
      except: earlier_date = ast.literal_eval(earlier_date)

    try:
        later = datetime.date(
            later_date['year'],
            later_date['month'],
            later_date['day']
        )
        earlier = datetime.date(
            earlier_date['year'],
            earlier_date['month'],
            earlier_date['day']
        )
    except KeyError as e:
        return {
            "status": "error",
            "message": f"Invalid date: missing key {e} in one or both dates"
        }
    except ValueError as e:
        return {
            "status": "error",
            "message": f"Failed to create date object: invalid value for year, month, or day"
        }

    difference = (later - earlier).days
    years_diff = difference // 365

    return {
        "status": "success",
        "content": f"Difference in years between dates {earlier} and {later} is {years_diff}.",
        "title": f"Difference in years between {later} and {earlier}"
    }




# Class for displaying the state of model processing
class Spinner:
    def __init__(self, message="Processing..."):
        self.spinner = itertools.cycle(["-", "/", "|", "\\"])
        self.busy = False
        self.delay = 0.1
        self.message = message
        self.thread = None

    def write(self, text):
        sys.stdout.write(text)
        sys.stdout.flush()

    def _spin(self):
        while self.busy:
            self.write(f"\r{self.message} {next(self.spinner)}")
            time.sleep(self.delay)
        self.write("\r\033[K")  # Clear the line

    def __enter__(self):
        self.busy = True
        self.thread = threading.Thread(target=self._spin)
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.busy = False
        time.sleep(self.delay)
        if self.thread:
            self.thread.join()
        self.write("\r")  # Move cursor to beginning of line


def chat_loop():
    """
    Main chat loop that processes user input and handles tool calls.
    """
    messages = [
        {
            "role": "system",
            "content": (
                "You are an assistant that can retrieve Wikipedia articles. "
                "When asked about a topic, you can retrieve Wikipedia articles "
                "and cite information from them."

                " You also have a helper utility to help you compute difference"
                " between two dates in years; you prefer to use that to do"
                " date subtraction."

                " If you are asked about a fact, you do prefer to look it up in"
                " wikipedia rather than assuming you know the value already. For"
                " events you believe did not happen, you simply check wikipedia."
                " You avoid overthinking and repetitiveness in thinking."

                " You have little faith in your own knowledge. You do not overthink:"
                " you just look up facts using fetch_wikipedia_content and a"
                " TOOL_REQUEST whenever possible. You keep your thinking stage short"
                " and sweet, and just plan on how to get the data most efficiently."
                " Your memory is faulty so you avoid refering to it."

#                " It is forbidden to you to invoke tools with assumptions about"
#                " values that you must derive by calling other tools; for example,"
#                " if you must fetch two dates from wikipedia, you must not execute"
#                " subtract in the same response. However, you must call all three"
#                " because you are fully aware that not calling Wikipedia means"
#                " some facts would be inaccurate (and you want accurate values)"
#                " and you are also aware that you don't know how to compute"
#                " date differences and must rely on the tool. Therefore, you are"
#                " required to make wikipedia requests in one call, and only then"
#                " later call date subtraction."
            ),
        }
    ]

    print(
        "Assistant: "
        "Hi! I can access Wikipedia to help answer your questions about history, "
        "science, people, places, or concepts - or we can just chat about "
        "anything else!"
    )
    print("(Type 'quit' to exit)")

    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() == "quit":
            break

        messages.append({"role": "user", "content": user_input})
        try:
            with Spinner("Thinking..."):
                response = client.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    tools=[WIKI_TOOL, WIKI_TOOL_2, DATE_SUBTRACT_TOOL],
                )

            if response.choices[0].message.tool_calls:
                # Handle all tool calls
                tool_calls = response.choices[0].message.tool_calls

                # Add all tool calls to messages
                messages.append(
                    {
                        "role": "assistant",
                        "tool_calls": [
                            {
                                "id": tool_call.id,
                                "type": tool_call.type,
                                "function": tool_call.function,
                            }
                            for tool_call in tool_calls
                        ],
                    }
                )

                # Process each tool call and add results
                for tool_call in tool_calls:
                  try:
                    args = json.loads(tool_call.function.arguments)
                    result = None

                    print(f"Requested a call to {tool_call.function.name} / {tool_call.function}")

                    if tool_call.function.name == 'fetch_wikipedia_content' or tool_call.function.name == 'fetch_real_authoritative_text':
                      print(f" Fetching from wikipedia: {args["search_query"]}")
                      result = fetch_wikipedia_content(args["search_query"])

                      # Print the Wikipedia content in a formatted way
                      terminal_width = shutil.get_terminal_size().columns
                      print("\n" + "=" * terminal_width)
                      if result["status"] == "success":
                          print(f"\nWikipedia article: {result['title']}")
                          print("-" * terminal_width)
                          print(result["content"])
                      else:
                          print(
                              f"\nError fetching Wikipedia content: {result['message']}"
                          )
                      print("=" * terminal_width + "\n")

                      if result is None: print(f"??? None in {result}")

                    elif tool_call.function.name == 'subtract_dates_return_years':
                      print(f" Subtracting dates: {args["later_date"]} - {args["earlier_date"]}")

                      result = subtract_dates_return_years(args['later_date'], args['earlier_date'])
                      if result["status"] == "success":
                          print(f"\nSubtracted dates gave the value:")
                          print(result["content"])
                      else:
                          print(
                              f"\nError fetching Wikipedia content: {result['message']}"
                          )

                      if result is None: print(f"??? None in {result}")

                    if result is None:
                      print(f" Returned result {result} is none, filling response with an error.")
                      result = {
                        'status': 'error',
                        'message': f'Sorry, assistant, but the tool you requested {tool_call.function} does not exist.'
                      }

                    messages.append(
                        {
                            "role": "tool",
                            "content": json.dumps(result),
                            "tool_call_id": tool_call.id,
                        }
                    )
                  except Exception as e:
                    resp = {"role": "tool", "content": json.dumps({'status': 'error', 'message': str(e)}), "tool_call_id": tool_call.id}
                    print(resp)
                    messages.append(e)

                # Stream the post-tool-call response
                print("\nAssistant:", end=" ", flush=True)
                stream_response = client.chat.completions.create(
                    model=MODEL, messages=messages, stream=True
                )
                collected_content = ""
                for chunk in stream_response:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        print(content, end="", flush=True)
                        collected_content += content
                print()  # New line after streaming completes
                messages.append(
                    {
                        "role": "assistant",
                        "content": collected_content,
                    }
                )
            else:
                # Handle regular response
                print("\nAssistant:", response.choices[0].message.content)
                messages.append(
                    {
                        "role": "assistant",
                        "content": response.choices[0].message.content,
                    }
                )

        except Exception as e:
            global base_url
            print(
                f"\nError chatting with the LM Studio server!\n\n"
                f"Please ensure:\n"
                f"1. LM Studio server is running at {base_url} (hostname:port)\n"
                f"2. Model '{MODEL}' is downloaded\n"
                f"3. Model '{MODEL}' is loaded, or that just-in-time model loading is enabled\n\n"
                f"Error details: {str(e)}\n"
                "See https://lmstudio.ai/docs/basics/server for more information"
            )
            exit(1)


if __name__ == "__main__":
    chat_loop()


