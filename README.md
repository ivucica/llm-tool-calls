# llm-python-tool

This is a **modification** of the LM Studio's documentation's example for interacting with the
LLM using the OpenAI API and allowing it to make calls to "tools". In this case, tools are
Python functions, and are exposed to the LLM using handcrafted schemas.

This was an attempt to unblock the AI from answering a question completely incorrectly due to
its training on what the current date and current state of the world is (such as the currently
elected political officials), where a particular model was very much locked into believing the
situation from 2023-2024 is the current one.

Additionally, it was an attempt to get the model to not trust its own mathematical prowess and
to instead diff the dates using a specialized tool.

## Remaining problems

The tool, as provided and modified, does not allow a chain of tool calls to be made. Therefore,
a request to fetch some dates (such as birthdays) from Wikipedia followed by using a subtraction
tool has not worked.

