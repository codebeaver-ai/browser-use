import pytest
import tempfile

from browser_use.agent.message_manager.views import MessageHistory, MessageMetadata
from browser_use.agent.views import AgentHistoryList, AgentOutput
from browser_use.browser.views import BrowserStateHistory, TabInfo
from browser_use.controller.registry.views import ActionRegistry, RegisteredAction
from browser_use.controller.views import ScrollAction
from langchain_core.messages import HumanMessage
from pathlib import Path
from pydantic import BaseModel, ValidationError
from typing import Callable
from unittest.mock import Mock

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

class TestBrowserStateHistory:
    def test_to_dict_method(self):
        """
        Test that the to_dict method of BrowserStateHistory correctly converts the object to a dictionary.
        This test covers the conversion of tabs, screenshot, interacted_element, url, and title.
        """
        # Create mock DOMHistoryElement
        mock_element = Mock()
        mock_element.to_dict.return_value = {"mock": "element"}

        # Create test data
        tabs = [TabInfo(page_id=1, url="https://example.com", title="Example")]
        interacted_element = [mock_element, None]

        # Create BrowserStateHistory instance
        browser_state_history = BrowserStateHistory(
            url="https://example.com",
            title="Example Page",
            tabs=tabs,
            interacted_element=interacted_element,
            screenshot="screenshot.png"
        )

        # Call to_dict method
        result = browser_state_history.to_dict()

        # Assert the result
        assert result == {
            'tabs': [{'page_id': 1, 'url': 'https://example.com', 'title': 'Example'}],
            'screenshot': 'screenshot.png',
            'interacted_element': [{"mock": "element"}, None],
            'url': 'https://example.com',
            'title': 'Example Page'
        }

        # Verify that the to_dict method of the mock element was called
        mock_element.to_dict.assert_called_once()

class TestActionRegistry:
    def test_get_prompt_description(self):
        """
        Test that the get_prompt_description method of ActionRegistry
        correctly concatenates the prompt descriptions of all registered actions.
        """
        # Create a dummy parameter model
        class DummyParams(BaseModel):
            param1: str
            param2: int

        # Create dummy function
        def dummy_func():
            pass

        # Create ActionRegistry instance
        registry = ActionRegistry()

        # Add two actions
        action1 = RegisteredAction(
            name="action1",
            description="First action",
            function=dummy_func,
            param_model=DummyParams
        )
        action2 = RegisteredAction(
            name="action2",
            description="Second action",
            function=dummy_func,
            param_model=DummyParams
        )
        registry.actions = {"action1": action1, "action2": action2}

        # Get prompt description
        prompt_description = registry.get_prompt_description()

        # Assert the result
        expected_description = (
            "First action: \n{action1: {'param1': {'type': 'string'}, 'param2': {'type': 'integer'}}}\n"
            "Second action: \n{action2: {'param1': {'type': 'string'}, 'param2': {'type': 'integer'}}}"
        )
        assert prompt_description == expected_description

class TestScrollAction:
    def test_scroll_action_validation(self):
        """
        Test that ScrollAction correctly validates the 'amount' field.
        This test covers:
        1. Creation of ScrollAction with valid integer amount
        2. Creation of ScrollAction with no amount (should default to None)
        3. Rejection of ScrollAction with invalid (non-integer) amount
        """
        # Test with valid integer amount
        valid_action = ScrollAction(amount=100)
        assert valid_action.amount == 100

        # Test with no amount (should default to None)
        default_action = ScrollAction()
        assert default_action.amount is None

        # Test with invalid (non-integer) amount
        with pytest.raises(ValidationError):
            ScrollAction(amount="invalid")