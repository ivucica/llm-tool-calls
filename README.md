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

## Examples how to run

Set up:

```bash
python3 -m venv env
. env/bin/activate
python3 -m pip install -r requirements.txt
```

Run with ollama:

```bash
# possibly needed: 'ollama serve' before:
ollama run llama3.2:latest
```

then in another tab:

```bash
OPENAI_API=http://127.0.0.1:11434/v1 OPENAI_MODEL=llama3.2:latest python3 python-use-example.py
```

Or, run LM Studio and install `mlx-community/llama-3.2-3b-instruct` from the GUI, then:

```bash
OPENAI_API=http://127.0.0.1:5001/v1 python3 python-use-example.py
```

If you `mkdir cache`, then fetched articles will be stored locally.

Another model that seems to work reasonably reliably is
`lmstudio-community/mistral-nemo-instruct-2407`.

## Running Tests

To run the existing tests in `python_use_example_test.py`, follow these steps:

1. Ensure you have the necessary dependencies installed. You can do this by running:
    ```bash
    python3 -m venv env
    . env/bin/activate
    python3 -m pip install -r requirements.txt
    ```

2. Run the tests using `pytest`. You can do this by executing the following command in your terminal:
    ```bash
    pytest python_use_example_test.py
    ```

The `pytest` command will discover and run all the tests defined in `python_use_example_test.py`. The test results will be displayed in the terminal.

## GitHub Actions

The repository includes a GitHub Actions workflow file `python-app.yml` to automate the testing process. The workflow is triggered on every push and pull request to the `main` branch. It sets up Python 3.8, installs dependencies, and runs `pytest` on `python_use_example_test.py`.

You can view the results of the GitHub Actions workflow by navigating to the "Actions" tab of your GitHub repository. The workflow will show the status of each test run, including any errors or failures.

## Example test prompts

*   > compare pikachu and bulbasaur after looking them up and put it in a markdown table. tell me about what franchise they come from, and tell me history of companies that made that franchise
*   > how long passed between birthday of Nikola Tesla and start of WW1?

