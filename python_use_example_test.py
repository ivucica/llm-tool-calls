import unittest
from unittest.mock import patch, MagicMock
from io import StringIO
import json
from python_use_example import chat_loop, Conversation, UserMessage, AssistantMessage, ToolMessage, SystemMessage, fetch_wikipedia_content, subtract_dates_return_years, ask, parse_tool_call, handle_nontool_response, fetch_streamed_response, fetch_nonstreamed_response, destrictified_tools

class TestChatLoop(unittest.TestCase):

    @patch('builtins.input', side_effect=['Hello', 'quit'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_single_round_chat(self, mock_stdout, mock_input):
        conversation = Conversation()
        chat_loop(conversation)
        output = mock_stdout.getvalue()
        self.assertIn("Hi! I can access Wikipedia to help answer your questions", output)
        self.assertIn("You: Hello", output)
        self.assertIn("Assistant:", output)

    @patch('builtins.input', side_effect=['Hello', 'How are you?', 'quit'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_multiple_rounds_chat(self, mock_stdout, mock_input):
        conversation = Conversation()
        chat_loop(conversation)
        output = mock_stdout.getvalue()
        self.assertIn("Hi! I can access Wikipedia to help answer your questions", output)
        self.assertIn("You: Hello", output)
        self.assertIn("You: How are you?", output)
        self.assertIn("Assistant:", output)

    @patch('builtins.input', side_effect=['/save test_conversation.json', 'quit'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_save_conversation(self, mock_stdout, mock_input):
        conversation = Conversation()
        chat_loop(conversation)
        with open('test_conversation.json', 'r') as f:
            saved_conversation = json.load(f)
        self.assertEqual(len(saved_conversation['messages']), 1)
        self.assertEqual(saved_conversation['messages'][0]['role'], 'system')

    @patch('builtins.input', side_effect=['/load test_conversation.json', 'quit'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_load_conversation(self, mock_stdout, mock_input):
        conversation = Conversation()
        system_message = SystemMessage(content="System message")
        conversation.add_message(system_message)
        with open('test_conversation.json', 'w') as f:
            f.write(conversation.to_json())
        chat_loop(conversation)
        self.assertEqual(len(conversation.messages), 1)
        self.assertEqual(conversation.messages[0].role, 'system')

class TestFetchWikipediaContent(unittest.TestCase):

    @patch('python_use_example.urllib.request.urlopen')
    def test_fetch_wikipedia_content_success(self, mock_urlopen):
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
        result = fetch_wikipedia_content("Python")
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["message"], "Network error")

class TestSubtractDatesReturnYears(unittest.TestCase):

    def test_subtract_dates_return_years_success(self):
        later_date = {"year": 2023, "month": 8, "day": 15}
        earlier_date = {"year": 2000, "month": 5, "day": 10}
        result = subtract_dates_return_years(later_date, earlier_date)
        self.assertEqual(result["status"], "success")
        self.assertIn("Difference in years between dates", result["content"])

    def test_subtract_dates_return_years_invalid_date(self):
        later_date = {"year": 2023, "month": 8, "day": 15}
        earlier_date = {"year": None, "month": 5, "day": 10}
        result = subtract_dates_return_years(later_date, earlier_date)
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["message"], "Invalid date: one or more keys is null in earlier date")

    def test_subtract_dates_return_years_missing_keys(self):
        later_date = {"year": 2023, "month": 8, "day": 15}
        earlier_date = {"year": 2000, "month": 5}
        result = subtract_dates_return_years(later_date, earlier_date)
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["message"], "Invalid date: one or more keys missing in earlier date")

class TestAskFunction(unittest.TestCase):

    @patch('python_use_example.fetch_streamed_response')
    def test_ask_function_tool_calls(self, mock_fetch_streamed_response):
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

    @patch('python_use_example.fetch_wikipedia_content')
    def test_parse_tool_call_fetch_wikipedia_content(self, mock_fetch_wikipedia_content):
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

    def test_handle_nontool_response_streamed(self):
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
