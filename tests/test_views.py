import pytest
import tempfile

from browser_use.agent.message_manager.views import MessageHistory, MessageMetadata
from browser_use.agent.views import ActionResult, AgentHistory, AgentHistoryList, AgentOutput
from browser_use.browser.views import BrowserStateHistory
from browser_use.controller.registry.views import ActionRegistry, RegisteredAction
from browser_use.dom.history_tree_processor.service import DOMHistoryElement
from langchain_core.messages import HumanMessage
from pathlib import Path
from pydantic import BaseModel

class TestAgentHistoryList:
    def test_save_and_load_from_file(self):
        """
        Test that AgentHistoryList can be saved to a file and loaded back correctly,
        including custom AgentOutput models and proper handling of interacted_element.
        """
        # Create a sample AgentHistoryList
        history_list = AgentHistoryList(history=[
            AgentHistory(
                model_output=None,
                result=[ActionResult(is_done=True, extracted_content="Test content")],
                state=BrowserStateHistory(
                    url="https://example.com",
                    screenshot="test.png",
                    title="Test Page",
                    tabs=[],
                    interacted_element=[]  # Empty list instead of None
                )
            )
        ])

        # Create a temporary directory and file path
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test_history.json"

            # Save the history to file
            history_list.save_to_file(file_path)

            # Load the history from file
            loaded_history = AgentHistoryList.load_from_file(file_path, AgentOutput)

            # Assert that the loaded history matches the original
            assert len(loaded_history.history) == len(history_list.history)
            assert loaded_history.history[0].result[0].is_done == history_list.history[0].result[0].is_done
            assert loaded_history.history[0].result[0].extracted_content == history_list.history[0].result[0].extracted_content
            assert loaded_history.history[0].state.url == history_list.history[0].state.url
            assert loaded_history.history[0].state.screenshot == history_list.history[0].state.screenshot
            assert loaded_history.history[0].state.title == history_list.history[0].state.title
            assert loaded_history.history[0].state.tabs == history_list.history[0].state.tabs
            assert loaded_history.history[0].state.interacted_element == history_list.history[0].state.interacted_element

class TestActionRegistry:
    def test_register_action_and_get_prompt_description(self):
        """
        Test registering an action in the ActionRegistry and getting the prompt description.
        This test covers the creation of RegisteredAction, adding it to ActionRegistry,
        and generating a prompt description for all registered actions.
        """
        # Create a sample parameter model
        class SampleParams(BaseModel):
            param1: str
            param2: int

        # Create a sample function
        def sample_function(param1: str, param2: int):
            pass

        # Create an ActionRegistry instance
        registry = ActionRegistry()

        # Register an action
        action = RegisteredAction(
            name="sample_action",
            description="A sample action for testing",
            function=sample_function,
            param_model=SampleParams,
            requires_browser=True
        )
        registry.actions["sample_action"] = action

        # Get the prompt description
        prompt_description = registry.get_prompt_description()

        # Assert that the prompt description contains the expected information
        assert "A sample action for testing" in prompt_description
        assert "sample_action" in prompt_description
        assert "param1" in prompt_description
        assert "param2" in prompt_description
        assert "string" in prompt_description.lower()
        assert "integer" in prompt_description.lower()