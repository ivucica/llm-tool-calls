import unittest
from unittest.mock import patch, MagicMock
from io import StringIO
import json
from python_use_example import chat_loop, Conversation, UserMessage, AssistantMessage, ToolMessage, SystemMessage

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

if __name__ == '__main__':
    unittest.main()
