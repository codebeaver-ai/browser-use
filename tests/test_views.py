import pytest
import tempfile

from browser_use.agent.message_manager.views import MessageHistory, MessageMetadata
from browser_use.agent.views import AgentHistoryList, AgentOutput
from langchain_core.messages import HumanMessage
from pathlib import Path

class TestMessageHistory:
    def test_remove_message_updates_total_tokens(self):
        """
        Test that removing a message from MessageHistory correctly updates the total_tokens count.
        """
        # Create a MessageHistory instance
        history = MessageHistory()

        # Add a message with some tokens
        message = HumanMessage(content="Test message")
        metadata = MessageMetadata(input_tokens=10)
        history.add_message(message, metadata)

        # Verify initial state
        assert history.total_tokens == 10
        assert len(history.messages) == 1

        # Remove the message
        history.remove_message()

        # Verify final state
        assert history.total_tokens == 0
        assert len(history.messages) == 0

class TestAgentHistoryList:
    def test_save_and_load_from_file(self):
        """
        Test that AgentHistoryList can be saved to a file and loaded back correctly.
        This test covers the save_to_file and load_from_file methods.
        """
        # Create a sample AgentHistoryList
        history_list = AgentHistoryList(history=[])

        # Create a temporary directory and file path
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test_history.json"

            # Save the history to file
            history_list.save_to_file(file_path)

            # Load the history from file
            loaded_history = AgentHistoryList.load_from_file(file_path, AgentOutput)

            # Assert that the loaded history matches the original
            assert loaded_history.model_dump() == history_list.model_dump()

        # The temporary directory and its contents are automatically cleaned up