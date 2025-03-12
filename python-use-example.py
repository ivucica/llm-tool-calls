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
import typing

# Third-party imports
from openai import OpenAI, pydantic_function_tool
import pydantic

# Initialize LM Studio client
import os
base_url = os.getenv("OPENAI_API", default="http://0.0.0.0:5001/v1")
client = OpenAI(base_url=base_url, api_key="lm-studio")
MODEL = os.getenv("OPENAI_MODEL", default="mlx-community/llama-3.2-3b-instruct")


class WikipediaContentRequest(pydantic.BaseModel):
    """Search Wikipedia and fetch the introduction of the most relevant article.
    
    Always use this if the user is asking for something that is likely on
    wikipedia.

    If the user has a typo in their search query, correct it before searching.

    For biographies, prefer searching for that individual person's article
    (using their full name).
    
    For events, prefer searching for the event name. 

    For other topics, prefer searching for the most common name of the topic in
    a way that would make sense for title of an encyclopedia article.

    Don't combine multiple search queries in one call: instead of 'Nikola Tesla
    WW1', search for 'Nikola Tesla' and 'World War 1' separately as two tool
    calls.

    Don't ask for 'first airing of X', instead ask just for 'X' since the API
    won't correctly handle the former and may return the wrong article. For
    example: 'first showing of The Matrix' should actually be requested with
    query 'The Matrix'.

    If you get an error in a function call, try to fix the arguments and repeat
    the call. Match the arguments strictly: don't assume the tool can handle
    arbitrary input, missing or misformatted parameters, etc.

    Don't make a call using data you do not have; ask for data you need in the
    first round of calls, then make the call you actually want to do in the next
    round. For example: if you try to compute difference between 'birth of Y'
    and 'start of Z', first make a request for an article about 'Y' and article
    about 'Z'; then once you receive the response to those requests, make a
    request for the difference between the dates; and only then send just a
    response without invoking a tool.
    """
    search_query: str = pydantic.Field(
        ...,
        description="Search query for finding the Wikipedia article",
        required=True,
    )


def fetch_wikipedia_content(search_query: str) -> dict:
    """Fetches wikipedia content for a given search_query"""
    # Compute hash of the query and try loading from local cache.
    # If not found, fetch from Wikipedia and store in cache.
    hash_query = hash(search_query)
    cache_file = f"cache/{hash_query}.json"
    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            return json.load(f)

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
        resp = {
            "status": "success",
            "content": content,
            "title": pages[page_id]["title"],
        }
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(resp, f)
        except Exception as e:
            print(f"Error saving cache file: {e}")
        return resp

    except Exception as e:
        return {"status": "error", "message": str(e)}


# Define tool for LM Studio
WIKI_TOOL = pydantic_function_tool(
    WikipediaContentRequest,
    name="fetch_wikipedia_content",
    description=WikipediaContentRequest.__doc__)


import copy
WIKI_TOOL_2 = copy.deepcopy(WIKI_TOOL)
WIKI_TOOL_2['function']['name'] = 'fetch_real_authoritative_text'
WIKI_TOOL_2['function']['description'] = "Search an authoritative book and fetch the introduction of the most relevant article Always use this if the user is asking for some fact, especially dates, rather than assume wikipedia is correct or your memory is correct. If the user has a typo in the search query, correct it before searching. For biographies, prefer searching for that individual person's article (using their full name)."
WIKI_TOOL_2['function']['parameters']['properties']['search_query']['description'] = 'Search query for finding the authoritative text on the subject'


class DateObject(pydantic.BaseModel):
    """
    Year, month and date for one of the input dates. Must be a valid date
    and all fields must be non-null. Optional: what the date represents
    ('birthday of X', 'end of Y', etc.) and where the date came from.
    """
    # Note: these hints end up being "anyOf" instead of just "type": ["string",
    # "null"] as is documented to be expected.
    label: typing.Optional[str] = pydantic.Field(
        ..., description="What the date represents (null or string)."
    )
    origin: typing.Optional[str] = pydantic.Field(
        ..., description="Where the date came from (null or string)."
    )
    year: int = pydantic.Field(..., description="Year (non-null int).")
    month: int = pydantic.Field(..., description="Month (non-null int).")
    day: int = pydantic.Field(..., description="Day (non-null int).")

    class Config:
        extra = pydantic.Extra.forbid  # Additional properties not allowed

class DateSubtractRequest(pydantic.BaseModel):
    """
    Compute difference in years. Process input dates as timestamps, subtract
    timestamps, and return how many years passed, rounded down. Useful to
    compute age. If the dates are fetched from a different source, do not
    provide the inputs until you received them from a different function call.
    """
    later_date: DateObject = pydantic.Field(...,
        description="Later (newer) of the two input dates (must be valid)."
    )
    earlier_date: DateObject = pydantic.Field(...,
        description="Earlier (older) of the two input dates (must be valid)."
    )
    reason: str = pydantic.Field(...,
        description=(
            "Reason for date subtraction, e.g. 'calculate age' or 'compute"
            " difference between first showing of X and birth of Y.")
    )

    class Config:
        extra = pydantic.Extra.forbid

DATE_SUBTRACT_TOOL = pydantic_function_tool(
    DateSubtractRequest,
    name="subtract_dates_return_years",
    description=DateSubtractRequest.__doc__)

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
    if later_date is None or earlier_date is None:
        return {
            "status": "error",
            "message": "Invalid date: one or both dates are None"
        }

    if isinstance(later_date, str): 
        try: later_date = json.loads(later_date)
        except: later_date = ast.literal_eval(later_date)  # https://stackoverflow.com/a/21154138 ; any security vuln?
    if isinstance(earlier_date, str):
        try: earlier_date = json.loads(earlier_date)
        except: earlier_date = ast.literal_eval(earlier_date)

    # If somehow the tool gave us "date" as the child key, extract it up.
    if isinstance(later_date, dict) and 'date' in later_date:
        later_date = later_date['date']
    if isinstance(earlier_date, dict) and 'date' in earlier_date:
        earlier_date = earlier_date['date']

    # Maybe we got YYYY-MM-DD strings instead of dicts. Try splitting by -.
    if isinstance(later_date, str):
        try:
            later_date = later_date.split('-')
            later_date = {
                "year": later_date[0],
                "month": later_date[1],
                "day": later_date[2]
            }
        except Exception as e:
            pass
    if isinstance(earlier_date, str):
        try:
            earlier_date = earlier_date.split('-')
            earlier_date = {
                "year": earlier_date[0],
                "month": earlier_date[1],
                "day": earlier_date[2]
            }
        except Exception as e:
            pass


    if  'year' not in later_date or 'month' not in later_date or 'day' not in later_date:
        return {
            "status": "error",
            "message": "Invalid date: one or more keys missing in later date"
        }
    if 'year' not in earlier_date or 'month' not in earlier_date or 'day' not in earlier_date:
        return {
            "status": "error",
            "message": "Invalid date: one or more keys missing in earlier date"
        }

    if later_date['year'] is None or later_date['month'] is None or later_date['day'] is None:
        return {
            "status": "error",
            "message": "Invalid date: one or more keys is null in later date"
        }
    if earlier_date['year'] is None or earlier_date['month'] is None or earlier_date['day'] is None:
        return {
            "status": "error",
            "message": "Invalid date: one or more keys is null in earlier date"
        }


    try:
        later = datetime.date(
            int(later_date['year']),
            int(later_date['month']),
            int(later_date['day'])
        )
        earlier = datetime.date(
            int(earlier_date['year']),
            int(earlier_date['month']),
            int(earlier_date['day'])
        )
    except KeyError as e:
        return {
            "status": "error",
            "message": f"Invalid date: missing key {e} in one or both dates"
        }
    except ValueError as e:
        return {
            "status": "error",
            "message": f"Failed to create date object: invalid value for year, month, or day: {e}"
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


class Message(pydantic.BaseModel):
    role: str
    content: str

class ToolMessage(Message):
    tool_call_id: str

class ToolCallMessage(Message):
    function: dict
    id: str
    type: str

class UserMessage(Message):
    pass

class SystemMessage(Message):
    pass

class AssistantMessage(Message):
    pass

class ToolResponseError(pydantic.BaseModel):
    status: str = "error"
    message: str

class ToolResponseSuccess(pydantic.BaseModel):
    status: str = "success"
    content: str
    title: str


def parse_tool_call(tool_call: ToolCallMessage) -> list[ToolMessage]:
    """parse_tool_call processes the tool call and returns the response.

    Args:
        tool_call (ToolCallMessage): The tool call to be processed.

    Returns:
        list: A list of messages to be sent back to the model.
    """
    messages = []
    try:
        args = json.loads(tool_call.function.arguments)
        result = None

        print(f"Requested a call to {tool_call.function.name} / {tool_call.function}")
        if tool_call.function.name == 'fetch_wikipedia_content' or tool_call.function.name == 'fetch_real_authoritative_text':
            print(f" Fetching from wikipedia: {args['search_query']}")
            result = fetch_wikipedia_content(args["search_query"])
            if result is None:
                print(f"??? None in {result}")

            # Print the Wikipedia content in a formatted way
            terminal_width = shutil.get_terminal_size().columns

            print("\n" + "=" * terminal_width)
            if result["status"] == "success":
                print(f"\nWikipedia article: {result['title']}")
                print("-" * terminal_width)
                print(result["content"])
            else:
                print(f"\nError fetching Wikipedia content: {result['message']}")
                print("=" * terminal_width + "\n")

        elif tool_call.function.name == 'subtract_dates_return_years':
            if 'later_date' not in args or 'earlier_date' not in args:
                print(f" Subtracting dates: cannot subtract, args was missing dates: {args}")
                result = {
                    'status': 'error',
                    'message': 'Missing required arguments later_date and/or earlier_date'
                }
            else:
                print(f" Subtracting dates: {args['later_date']} - {args['earlier_date']}")

                result = subtract_dates_return_years(args['later_date'], args['earlier_date'])
                if result is None:
                    print(f"??? None in {result}")

                if result["status"] == "success":
                    print("\nSubtracted dates gave the value:")
                    print(result["content"])
                else:
                    print(f"\nError subtracting dates: {result['message']}")

        if result is None:
            print(f" Returned result {result} is none, filling response with an error.")
            result = {
                'status': 'error',
                'message': f'Sorry, assistant, but the tool you requested {tool_call.function} does not exist.'
            }

        messages.append(
            ToolMessage(
                content=json.dumps(result),
                tool_call_id=tool_call.id,
            )
        )
    except KeyError as e:
        print(f"KeyError: {e} -- returning the following response:")
        resp = ToolMessage(
            content=json.dumps({
                'status': 'error',
                'message': f'Missing required arguments: {e}'  # Handled specially so exception is clearer, since KeyError is confusing when turned to string
            }),
            tool_call_id=tool_call.id
        )
        print("===")
        print(resp)
        print("===")
        messages.append(resp)
    except Exception as e:
        print(f"Exception: {e} -- returning the following response:")
        resp = ToolMessage(
            content=json.dumps({
                'status': 'error',
                'message': str(e)
            }),
            tool_call_id=tool_call.id
        )
        print("===")
        print(resp)
        print("===")
        messages.append(resp)
    return messages


def ask(model: str, messages: list[typing.Union[ToolMessage, ToolCallMessage, UserMessage, SystemMessage, AssistantMessage]], tools: list[dict[str, any]], tool_iterations: int = 1) -> list[typing.Union[ToolMessage, ToolCallMessage, UserMessage, SystemMessage, AssistantMessage]]:
    """ask sends the messages to the model and processes the tool calls.

    Args:
        model (str): The model to use for processing.
        messages (list): The messages to send to the model.
        tools (list): The tools to process.
        tool_iterations (int): The number of tool iterations to process.

    Returns:
        list: Updated version of the argument 'messages', with tool responses
            etc attached.
    """
    print(f"Sending a request with {len(messages)} messages in the context, offering {len(tools)} tools...")
    if tool_iterations > 0 and len(tools) > 0:
        with Spinner("Thinking..."):
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=[WIKI_TOOL, WIKI_TOOL_2, DATE_SUBTRACT_TOOL],

                # Tool-enabled calls can also be streaming-enabled. Then the
                # responses in delta.tool_calls are:
                # [{"index": 0, "id": "call_id", "function": {"arguments": "", "name": "function_name"}, "type": "function"}]
                # [{"index": 0, "id": null, "function": {"arguments": "{\"", "name": null}, "type": null}]
                # [{"index": 0, "id": null, "function": {"arguments": "query", "name": null}, "type": null}]
                # [{"index": 0, "id": null, "function": {"arguments": "\":\"", "name": null}, "type": null}]
                # null
                # and we have to aggregate them
            )

        if response.choices[0].message.tool_calls:
            # Handle all tool calls
            tool_calls = response.choices[0].message.tool_calls

            print(f"Tool calls encountered! Reasoning for tool calls: {response.choices[0].message.content}")
            # Add all tool calls to messages
            messages.append(
                {
                    "role": "assistant",
                    "content": response.choices[0].message.content,
                    "tool_calls": [
                        ToolCallMessage(
                            id=tool_call.id,
                            type=tool_call.type,
                            function=tool_call.function,
                        )
                        for tool_call in tool_calls
                    ],
                }
            )

            # Process each tool call and add results
            for tool_call in tool_calls:
                messages += parse_tool_call(tool_call)

            return ask(
                model=MODEL,
                messages=messages,
                tools=tools,
                tool_iterations=tool_iterations - 1,
            )
        else:
            # We were not requested to make any tool calls.
            return handle_nontool_response(
                model=MODEL, messages=messages, response=response)
    else:
        # We were not supposed to make a tool call. Make a request without
        # tools, but with streaming enabled.
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

    return messages


def handle_nontool_response(
        model: str, messages: list[typing.Union[ToolMessage, ToolCallMessage, UserMessage, SystemMessage, AssistantMessage]],
        response: dict[str, any]) -> list[typing.Union[ToolMessage, ToolCallMessage, UserMessage, SystemMessage, AssistantMessage]]:
    """Handle a non-streamed response when we do not expect tool calls."""
    del model

    # Handle regular response
    print("\nAssistant:", response.choices[0].message.content)
    messages.append(
        {
            "role": "assistant",
            "content": response.choices[0].message.content,
        }
    )
    return messages


def chat_loop():
    """
    Main chat loop that processes user input and handles tool calls.
    """
    messages = [
        SystemMessage(
            content=(
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
        )
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

        messages.append(UserMessage(content=user_input))
        try:
            messages += ask(
                model=MODEL,
                messages=messages,
                tools=[WIKI_TOOL, WIKI_TOOL_2, DATE_SUBTRACT_TOOL],
                tool_iterations=4,
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

