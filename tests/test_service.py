import os
import pytest
import sys

from browser_use.agent.message_manager.service import MessageManager
from browser_use.agent.service import Agent
from browser_use.agent.views import ActionResult, AgentOutput
from browser_use.browser.browser import Browser
from browser_use.browser.context import BrowserContext
from browser_use.browser.views import BrowserState
from browser_use.controller.registry.service import Registry
from browser_use.controller.registry.views import ActionModel
from browser_use.controller.service import Controller
from browser_use.dom.service import DomService
from browser_use.dom.views import DOMElementNode, DOMTextNode
from datetime import datetime
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from pydantic import BaseModel
from unittest.mock import AsyncMock, MagicMock, Mock, patch

# run with python -m pytest tests/test_service.py

# run test with:
# python -m pytest tests/test_service.py
class TestAgent:
	@pytest.fixture
	def mock_controller(self):
		controller = Mock(spec=Controller)
		registry = Mock(spec=Registry)
		registry.registry = MagicMock()
		registry.registry.actions = {'test_action': MagicMock(param_model=MagicMock())}  # type: ignore
		controller.registry = registry
		return controller

	@pytest.fixture
	def mock_llm(self):
		return Mock(spec=BaseChatModel)

	@pytest.fixture
	def mock_browser(self):
		return Mock(spec=Browser)

	@pytest.fixture
	def mock_browser_context(self):
		return Mock(spec=BrowserContext)

	def test_convert_initial_actions(self, mock_controller, mock_llm, mock_browser, mock_browser_context):  # type: ignore
		"""
		Test that the _convert_initial_actions method correctly converts
		dictionary-based actions to ActionModel instances.

		This test ensures that:
		1. The method processes the initial actions correctly.
		2. The correct param_model is called with the right parameters.
		3. The ActionModel is created with the validated parameters.
		4. The method returns a list of ActionModel instances.
		"""
		# Arrange
		agent = Agent(
			task='Test task', llm=mock_llm, controller=mock_controller, browser=mock_browser, browser_context=mock_browser_context
		)
		initial_actions = [{'test_action': {'param1': 'value1', 'param2': 'value2'}}]

		# Mock the ActionModel
		mock_action_model = MagicMock(spec=ActionModel)
		mock_action_model_instance = MagicMock()
		mock_action_model.return_value = mock_action_model_instance
		agent.ActionModel = mock_action_model  # type: ignore

		# Act
		result = agent._convert_initial_actions(initial_actions)

		# Assert
		assert len(result) == 1
		mock_controller.registry.registry.actions['test_action'].param_model.assert_called_once_with(  # type: ignore
			param1='value1', param2='value2'
		)
		mock_action_model.assert_called_once()
		assert isinstance(result[0], MagicMock)
		assert result[0] == mock_action_model_instance

		# Check that the ActionModel was called with the correct parameters
		call_args = mock_action_model.call_args[1]
		assert 'test_action' in call_args
		assert call_args['test_action'] == mock_controller.registry.registry.actions['test_action'].param_model.return_value  # type: ignore

	@pytest.mark.asyncio
	async def test_step_error_handling(self):
		"""
		Test the error handling in the step method of the Agent class.
		This test simulates a failure in the get_next_action method and
		checks if the error is properly handled and recorded.
		"""
		# Mock the LLM
		mock_llm = MagicMock(spec=BaseChatModel)

		# Mock the MessageManager
		with patch('browser_use.agent.service.MessageManager') as mock_message_manager:
			# Create an Agent instance with mocked dependencies
			agent = Agent(task='Test task', llm=mock_llm)

			# Mock the get_next_action method to raise an exception
			agent.get_next_action = AsyncMock(side_effect=ValueError('Test error'))

			# Mock the browser_context
			agent.browser_context = AsyncMock()
			agent.browser_context.get_state = AsyncMock(
				return_value=BrowserState(
					url='https://example.com',
					title='Example',
					element_tree=MagicMock(),  # Mocked element tree
					tabs=[],
					selector_map={},
					screenshot='',
				)
			)

			# Mock the controller
			agent.controller = AsyncMock()

			# Call the step method
			await agent.step()

			# Assert that the error was handled and recorded
			assert agent.consecutive_failures == 1
			assert len(agent._last_result) == 1
			assert isinstance(agent._last_result[0], ActionResult)
			assert 'Test error' in agent._last_result[0].error
			assert agent._last_result[0].include_in_memory == True

class TestRegistry:
    @pytest.fixture
    def registry_with_excludes(self):
        return Registry(exclude_actions=['excluded_action'])

    def test_action_decorator_with_excluded_action(self, registry_with_excludes):
        """
        Test that the action decorator does not register an action
        if it's in the exclude_actions list.
        """
        # Define a function to be decorated
        def excluded_action():
            pass

        # Apply the action decorator
        decorated_func = registry_with_excludes.action(description="This should be excluded")(excluded_action)

        # Assert that the decorated function is the same as the original
        assert decorated_func == excluded_action

        # Assert that the action was not added to the registry
        assert 'excluded_action' not in registry_with_excludes.registry.actions

        # Define another function that should be included
        def included_action():
            pass

        # Apply the action decorator to an included action
        registry_with_excludes.action(description="This should be included")(included_action)

        # Assert that the included action was added to the registry
        assert 'included_action' in registry_with_excludes.registry.actions

    @pytest.mark.asyncio
    async def test_execute_action_with_and_without_browser_context(self):
        """
        Test that the execute_action method correctly handles actions with and without a browser context.
        This test ensures that:
        1. An action requiring a browser context is executed correctly.
        2. An action not requiring a browser context is executed correctly.
        3. The browser context is passed to the action function when required.
        4. The action function receives the correct parameters.
        5. The method raises an error when a browser context is required but not provided.
        """
        registry = Registry()

        # Define a mock action model
        class TestActionModel(BaseModel):
            param1: str

        # Define mock action functions
        async def test_action_with_browser(param1: str, browser):
            return f"Action executed with {param1} and browser"

        async def test_action_without_browser(param1: str):
            return f"Action executed with {param1}"

        # Register the actions
        registry.registry.actions['test_action_with_browser'] = MagicMock(
            requires_browser=True,
            function=AsyncMock(side_effect=test_action_with_browser),
            param_model=TestActionModel,
            description="Test action with browser"
        )

        registry.registry.actions['test_action_without_browser'] = MagicMock(
            requires_browser=False,
            function=AsyncMock(side_effect=test_action_without_browser),
            param_model=TestActionModel,
            description="Test action without browser"
        )

        # Mock BrowserContext
        mock_browser = MagicMock()

        # Execute the action with a browser context
        result_with_browser = await registry.execute_action('test_action_with_browser', {'param1': 'test_value'}, browser=mock_browser)
        assert result_with_browser == "Action executed with test_value and browser"

        # Execute the action without a browser context
        result_without_browser = await registry.execute_action('test_action_without_browser', {'param1': 'test_value'})
        assert result_without_browser == "Action executed with test_value"

        # Test error when browser is required but not provided
        with pytest.raises(RuntimeError, match="Action test_action_with_browser requires browser but none provided"):
            await registry.execute_action('test_action_with_browser', {'param1': 'test_value'})

        # Verify that the action functions were called with correct parameters
        registry.registry.actions['test_action_with_browser'].function.assert_called_once_with(param1='test_value', browser=mock_browser)
        registry.registry.actions['test_action_without_browser'].function.assert_called_once_with(param1='test_value')

class DummySystemPrompt:
    """
    Dummy system prompt class to satisfy MessageManager's constructor requirements.
    """
    def __init__(self, action_descriptions: str, current_date: datetime, max_actions_per_step: int):
        self.action_descriptions = action_descriptions
        self.current_date = current_date
        self.max_actions_per_step = max_actions_per_step

    def get_system_message(self) -> SystemMessage:
        return SystemMessage(content="Dummy system prompt")

class TestMessageManager:
    """
    Tests for MessageManager functionality not covered by existing tests.
    This includes merging successive human messages.
    """

    @pytest.fixture
    def dummy_message_manager(self):
        # A dummy LLM object (not used in merge method)
        dummy_llm = object()
        # Instantiate MessageManager with minimal required parameters using DummySystemPrompt.
        mm = MessageManager(
            llm=dummy_llm,
            task="Dummy task",
            action_descriptions="Dummy actions",
            system_prompt_class=DummySystemPrompt,
            max_input_tokens=1000,
            estimated_characters_per_token=3,
            image_tokens=800,
            include_attributes=[]
        )
        return mm

    def test_merge_successive_human_messages(self, dummy_message_manager):
        """
        Test that merge_successive_human_messages correctly merges successive HumanMessage messages
        while preserving non-human messages.
        """
        # Create a list of messages with successive HumanMessage objects and a non-human message in between
        messages = [
            HumanMessage(content="Hello, "),
            HumanMessage(content="world! "),
            SystemMessage(content="System message."),
            HumanMessage(content="Another message."),
            HumanMessage(content=" And another.")
        ]
        # Call the merge function
        merged = dummy_message_manager.merge_successive_human_messages(messages)

        # Expectation:
        # - The first two HumanMessages get merged into one.
        # - The SystemMessage remains unchanged.
        # - The last two HumanMessages merge into one.
        assert len(merged) == 3, "Expected three messages after merging successive HumanMessages."
        # Verify the merged content of the first pair.
        assert isinstance(merged[0], HumanMessage)
        assert merged[0].content == "Hello, world! "
        # Verify the SystemMessage remains unchanged.
        assert isinstance(merged[1], SystemMessage)
        assert merged[1].content == "System message."
        # Verify the merged content of the last two HumanMessages.
        assert isinstance(merged[2], HumanMessage)
        assert merged[2].content == "Another message. And another."

class TestDomService:
    """
    Tests for DomService functionality not covered by existing tests.
    This test verifies that a ValueError is raised by get_clickable_elements
    when _build_dom_tree returns a DOMTextNode instead of a DOMElementNode.
    """

    @pytest.mark.asyncio
    async def test_build_dom_tree_failure_with_text_node(self):
        """
        Test that DomService.get_clickable_elements raises a ValueError when the parsed node is not a DOMElementNode.
        This is simulated by having page.evaluate return a dictionary representing a TEXT_NODE.
        """
        # Create a dummy page with an async evaluate method that returns a TEXT_NODE dict.
        mock_page = MagicMock()
        mock_page.evaluate = AsyncMock(return_value={
            'type': 'TEXT_NODE',
            'text': 'Sample text',
            'isVisible': True
        })

        dom_service = DomService(page=mock_page)

        # Expect a ValueError because _parse_node returns a DOMTextNode, not a DOMElementNode.
        with pytest.raises(ValueError, match='Failed to parse HTML to dictionary'):
            await dom_service.get_clickable_elements()