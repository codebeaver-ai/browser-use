import pytest
import tempfile

from browser_use.agent.message_manager.views import MessageHistory, MessageMetadata
from browser_use.agent.views import ActionResult, AgentHistory, AgentHistoryList, AgentOutput
from browser_use.browser.views import BrowserStateHistory
from browser_use.controller.registry.views import ActionRegistry, RegisteredAction
from browser_use.controller.views import NoParamsAction
from browser_use.dom.history_tree_processor.service import DOMHistoryElement
from browser_use.dom.views import DOMElementNode, DOMTextNode
from browser_use.telemetry.views import AgentRunTelemetryEvent, BaseTelemetryEvent
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

class TestNoParamsAction:
    """Tests for the NoParamsAction model."""

    def test_no_params_action_ignores_all_inputs(self):
        """
        Test that NoParamsAction ignores all inputs and always results in an empty model.
        This test covers the model_validator and the extra configuration.
        """
        # Test with various types of input
        inputs = [
            {},
            {"some_field": "value"},
            {"a": 1, "b": 2, "c": 3},
            {"complex": {"nested": "structure"}},
        ]

        for input_data in inputs:
            action = NoParamsAction(**input_data)

            # Check that the resulting model is always empty
            assert action.model_dump() == {}

            # Check that no attributes were added to the model
            assert not hasattr(action, "some_field")
            assert not hasattr(action, "a")
            assert not hasattr(action, "complex")

        # Test that extra fields are allowed without raising an error
        NoParamsAction(extra_field="This should not raise an error")

class TestDOMElementNode:
    def test_get_file_upload_element(self):
        """
        Test the get_file_upload_element method of DOMElementNode.
        This test covers:
        1. Finding a file input element within a nested structure.
        2. Returning None when no file input element is present.
        """
        # Create a mock DOM structure with a file input
        file_input = DOMElementNode(
            is_visible=True,
            parent=None,
            tag_name='input',
            xpath='/html/body/div/input',
            attributes={'type': 'file'},
            children=[]
        )
        div = DOMElementNode(
            is_visible=True,
            parent=None,
            tag_name='div',
            xpath='/html/body/div',
            attributes={},
            children=[file_input]
        )
        body = DOMElementNode(
            is_visible=True,
            parent=None,
            tag_name='body',
            xpath='/html/body',
            attributes={},
            children=[div]
        )

        # Test finding the file input element
        result = body.get_file_upload_element()
        assert result == file_input

        # Test with no file input element
        div_without_file_input = DOMElementNode(
            is_visible=True,
            parent=None,
            tag_name='div',
            xpath='/html/body/div',
            attributes={},
            children=[DOMTextNode(is_visible=True, parent=None, text="Some text")]
        )
        body_without_file_input = DOMElementNode(
            is_visible=True,
            parent=None,
            tag_name='body',
            xpath='/html/body',
            attributes={},
            children=[div_without_file_input]
        )

        # Test not finding a file input element
        result = body_without_file_input.get_file_upload_element()
        assert result is None

class TestTelemetryEvents:
    def test_base_telemetry_event_properties(self):
        """
        Test that BaseTelemetryEvent's properties method correctly excludes 'name'
        and that subclasses implement the name property correctly.
        """
        # Create an instance of AgentRunTelemetryEvent
        event = AgentRunTelemetryEvent(
            agent_id="test_agent",
            use_vision=True,
            task="test_task",
            model_name="test_model",
            chat_model_library="test_library",
            version="1.0",
            source="test_source"
        )

        # Check that the name property is correctly implemented
        assert event.name == "agent_run"

        # Check that the properties method returns a dictionary without 'name'
        properties = event.properties
        assert "name" not in properties
        assert properties == {
            "agent_id": "test_agent",
            "use_vision": True,
            "task": "test_task",
            "model_name": "test_model",
            "chat_model_library": "test_library",
            "version": "1.0",
            "source": "test_source"
        }

        # Test that we can't instantiate BaseTelemetryEvent directly
        with pytest.raises(TypeError):
            BaseTelemetryEvent()