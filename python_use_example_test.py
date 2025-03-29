import unittest
from unittest.mock import patch, MagicMock
from io import StringIO
import json
import subprocess
import time
from python_use_example import chat_loop, Conversation, UserMessage, AssistantMessage, ToolMessage, SystemMessage, fetch_wikipedia_content, subtract_dates_return_years, ask, parse_tool_call, handle_nontool_response, fetch_streamed_response, fetch_nonstreamed_response, destrictified_tools, ToolCall, Function
import python_use_example

def start_fake_server():
    server_process = subprocess.Popen(['python3', 'fakeserver.py'])
    time.sleep(1)  # Give the server a second to start
    return server_process

def stop_fake_server(server_process):
    server_process.terminate()
    server_process.wait()

class TestChatLoop(unittest.TestCase):
    """
    Test cases for the chat loop functionality.
    """

    @classmethod
    def setUpClass(cls):
        cls.server_process = start_fake_server()

    def setUp(self):
        super().setUp()

        # Ensure HTTP client _only_ connects to the fake server (but otherwise
        # is operating exactly as intended).
        #
        # This should prevent both connecting to Wikipedia and to non-fake
        # 'LLM' API servers.
        #
        # Add a patch to the urllib.request.urlopen used by both the OpenAI API
        # client and the Wikipedia client. The intention is to allow it to be
        # used as-original, but just prevent connections to the real servers.
        self.enterContext(patch.object(
            python_use_example.urllib.request, 'urlopen',
            side_effect=Exception("Network error")).start())

        # Patch out use of file open, too, so cache files aren't accessed or
        # created.
        self.enterContext(patch.object(
            python_use_example, 'open',
            side_effect=Exception("File access error")).start())

    @classmethod
    def tearDownClass(cls):
        stop_fake_server(cls.server_process)

    def tearDown(self):
        import os
        if os.path.exists('test_conversation.json'):
            os.remove('test_conversation.json')

    def test_client_address_and_port(self):
        """
        Minimal test to verify the client points at the correct address and port.
        """
        response = requests.get('http://127.0.0.1:5000/v1/models')
        self.assertEqual(response.status_code, 200)
        self.assertIn("model1", response.json())

    @patch('builtins.input', side_effect=['Hello', 'quit'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_single_round_chat(self, mock_stdout, mock_input):
        """
        Test a single round of chat interaction.
        Expected output: The output should include the initial assistant message, the user message "Hello", and the assistant's response.
        """
        conversation = Conversation()
        chat_loop(conversation)
        output = mock_stdout.getvalue()
        self.assertIn("Hi! I can access Wikipedia to help answer your questions", output)
        # self.assertIn("You: Hello", output) # TODO: This cannot appear because 'input' is mocked
        self.assertIn("Assistant:", output)

    @patch('builtins.input', side_effect=['Hello', 'How are you?', 'quit'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_multiple_rounds_chat(self, mock_stdout, mock_input):
        """
        Test multiple rounds of chat interaction.
        Expected output: The output should include the initial assistant message, the user messages "Hello" and "How are you?", and the assistant's responses.
        """
        conversation = Conversation()
        chat_loop(conversation)
        output = mock_stdout.getvalue()
        self.assertIn("Hi! I can access Wikipedia to help answer your questions", output)
        #self.assertIn("You: Hello", output)  # TODO: This cannot appear because 'input' is mocked. We have to test the equivalent of what the fake Assistant would say.
        #self.assertIn("You: How are you?", output)  # TODO: This cannot appear because 'input' is mocked. We have to test the equivalent of what the fake Assistant would say.
        self.assertIn("Assistant:", output)

    @patch('builtins.input', side_effect=['/save test_conversation.json', 'quit'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_save_conversation(self, mock_stdout, mock_input):
        """
        Test saving the conversation to a JSON file.
        Expected output: The output should be a saved JSON file 'test_conversation.json' containing the conversation with one system message.
        """
        conversation = Conversation()
        chat_loop(conversation)
        with open('test_conversation.json', 'r') as f:
            saved_conversation = json.load(f)
        self.assertEqual(len(saved_conversation['messages']), 1)
        self.assertEqual(saved_conversation['messages'][0]['role'], 'system')

    @patch('builtins.input', side_effect=['/load test_conversation.json', 'quit'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_load_conversation(self, mock_stdout, mock_input):
        """
        Test loading the conversation from a JSON file.
        Expected output: The output should be a loaded conversation from 'test_conversation.json' with one system message.
        """
        conversation = Conversation()
        system_message = SystemMessage(content="System message")
        conversation.add_message(system_message)
        with open('test_conversation.json', 'w') as f:
            f.write(conversation.to_json())
        chat_loop(conversation)
        self.assertEqual(len(conversation.messages), 1)
        self.assertEqual(conversation.messages[0].role, 'system')

    @patch('builtins.input', side_effect=['/clear', 'quit'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_clear_conversation(self, mock_stdout, mock_input):
        """
        Test clearing the conversation history.
        Expected output: The output should indicate that the conversation history has been cleared.
        """
        conversation = Conversation()
        system_message = SystemMessage(content="System message")
        conversation.add_message(system_message)
        chat_loop(conversation)
        self.assertEqual(len(conversation.messages), 1)
        self.assertEqual(conversation.messages[0].role, 'system')

class TestFetchWikipediaContent(unittest.TestCase):
    """
    Test cases for the fetch_wikipedia_content function.
    """

    @classmethod
    def setUpClass(cls):
        cls.server_process = start_fake_server()

    @classmethod
    def tearDownClass(cls):
        stop_fake_server(cls.server_process)

    def tearDown(self):
        import os
        if os.path.exists('test_conversation.json'):
            os.remove('test_conversation.json')

    @patch('python_use_example.urllib.request.urlopen')
    def test_fetch_wikipedia_content_success(self, mock_urlopen):
        """
        Test fetching Wikipedia content successfully.
        Expected output: The output should be a successful response with the title 'Python (programming language)' and content 'Python is a programming language.'
        """
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "query": {
                "search": [{"title": "Python (programming language)"}],
                "pages": {
                    "12345": {
                        "pageid": 12345,
                        "title": "Python (programming language)",
                        "extract": "Python is a programming language."
                    }
                }
            }
        }).encode('utf-8')
        mock_urlopen.return_value = mock_response

        result = fetch_wikipedia_content("Python")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["title"], "Python (programming language)")
        self.assertEqual(result["content"], "Python is a programming language.")

    @patch('python_use_example.urllib.request.urlopen')
    def test_fetch_wikipedia_content_no_article(self, mock_urlopen):
        """
        Test fetching Wikipedia content when no article is found.
        Expected output: The output should be an error response with the message 'No Wikipedia article found for 'NonExistentArticle'.'
        """
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "query": {
                "search": []
            }
        }).encode('utf-8')
        mock_urlopen.return_value = mock_response

        result = fetch_wikipedia_content("NonExistentArticle")
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["message"], "No Wikipedia article found for 'NonExistentArticle'")

    @patch('python_use_example.urllib.request.urlopen', side_effect=Exception("Network error"))
    def test_fetch_wikipedia_content_network_error(self, mock_urlopen):
        """
        Test fetching Wikipedia content when a network error occurs.
        Expected output: The output should be an error response with the message 'Network error.'
        """
        result = fetch_wikipedia_content("Python")
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["message"], "Network error")

class TestSubtractDatesReturnYears(unittest.TestCase):
    """
    Test cases for the subtract_dates_return_years function.
    """

    @classmethod
    def setUpClass(cls):
        cls.server_process = start_fake_server()

    @classmethod
    def tearDownClass(cls):
        stop_fake_server(cls.server_process)

    def test_subtract_dates_return_years_success(self):
        """
        Test subtracting dates successfully.
        Expected output: The output should be a successful response with the content indicating the difference in years between the dates.
        """
        later_date = {"year": 2023, "month": 8, "day": 15}
        earlier_date = {"year": 2000, "month": 5, "day": 10}
        result = subtract_dates_return_years(later_date, earlier_date)
        self.assertEqual(result["status"], "success")
        self.assertIn("Difference in years between dates", result["content"])

    def test_subtract_dates_return_years_invalid_date(self):
        """
        Test subtracting dates with an invalid date.
        Expected output: The output should be an error response with the message 'Invalid date: one or more keys is null in earlier date.'
        """
        later_date = {"year": 2023, "month": 8, "day": 15}
        earlier_date = {"year": None, "month": 5, "day": 10}
        result = subtract_dates_return_years(later_date, earlier_date)
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["message"], "Invalid date: one or more keys is null in earlier date")

    def test_subtract_dates_return_years_missing_keys(self):
        """
        Test subtracting dates with missing keys.
        Expected output: The output should be an error response with the message 'Invalid date: one or more keys missing in earlier date.'
        """
        later_date = {"year": 2023, "month": 8, "day": 15}
        earlier_date = {"year": 2000, "month": 5}
        result = subtract_dates_return_years(later_date, earlier_date)
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["message"], "Invalid date: one or more keys missing in earlier date")

class TestAskFunction(unittest.TestCase):
    """
    Test cases for the ask function.
    """

    @classmethod
    def setUpClass(cls):
        cls.server_process = start_fake_server()

    @classmethod
    def tearDownClass(cls):
        stop_fake_server(cls.server_process)

    @patch('python_use_example.fetch_streamed_response')
    def test_ask_function_tool_calls(self, mock_fetch_streamed_response):
        """
        Test the ask function with tool calls.
        Expected output: The output should include three messages: the user message, the assistant message, and the tool message.
        """
        mock_response = AssistantMessage(
            role="assistant",
            content="Here is the information you requested.",
            tool_calls=[ToolCall(
                id="1",
                type="tool",
                function=Function(
                    name="fetch_wikipedia_content",
                    arguments=json.dumps({"search_query": "Python"})
                )
            )]
        )
        mock_fetch_streamed_response.return_value = mock_response

        messages = [UserMessage(content="Tell me about Python")]
        tools = [MagicMock()]
        result = ask("test_model", messages, tools)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[1].role, "assistant")
        self.assertEqual(result[2].role, "tool")

class TestParseToolCall(unittest.TestCase):
    """
    Test cases for the parse_tool_call function.
    """

    @classmethod
    def setUpClass(cls):
        cls.server_process = start_fake_server()

    @classmethod
    def tearDownClass(cls):
        stop_fake_server(cls.server_process)

    @patch('python_use_example.fetch_wikipedia_content')
    def test_parse_tool_call_fetch_wikipedia_content(self, mock_fetch_wikipedia_content):
        """
        Test parsing a tool call for fetching Wikipedia content.
        Expected output: The output should include one tool message with the content 'Python is a programming language.'
        """
        mock_fetch_wikipedia_content.return_value = {
            "status": "success",
            "content": "Python is a programming language.",
            "title": "Python (programming language)"
        }
        tool_call = ToolCall(
            id="1",
            type="tool",
            function=Function(
                name="fetch_wikipedia_content",
                arguments=json.dumps({"search_query": "Python"})
            )
        )
        result = parse_tool_call(tool_call)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].role, "tool")
        self.assertIn("Python is a programming language.", result[0].content)

class TestHandleNontoolResponse(unittest.TestCase):
    """
    Test cases for the handle_nontool_response function.
    """

    @classmethod
    def setUpClass(cls):
        cls.server_process = start_fake_server()

    @classmethod
    def tearDownClass(cls):
        stop_fake_server(cls.server_process)

    def test_handle_nontool_response_streamed(self):
        """
        Test handling a non-tool response that was streamed.
        Expected output: The output should include two messages: the user message and the assistant message with the content 'Python is a programming language.'
        """
        messages = [UserMessage(content="Tell me about Python")]
        response = AssistantMessage(
            role="assistant",
            content="Python is a programming language."
        )
        result = handle_nontool_response("test_model", messages, response, was_streamed=True)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[1].role, "assistant")
        self.assertEqual(result[1].content, "Python is a programming language.")

if __name__ == '__main__':
    unittest.main()
