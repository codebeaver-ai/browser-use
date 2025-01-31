import os
import pytest
import sys
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from browser_use.agent.message_manager.service import MessageManager
from browser_use.agent.service import Agent
from browser_use.agent.views import ActionResult, AgentOutput
from browser_use.browser.browser import Browser
from browser_use.browser.context import BrowserContext
from browser_use.browser.views import BrowserState
from browser_use.controller.registry.service import Registry
from browser_use.controller.registry.views import ActionModel
from browser_use.controller.service import Controller
from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import BaseModel
from langchain_core.messages import SystemMessage, HumanMessage
from browser_use.agent.prompts import SystemPrompt

# run with python -m pytest tests/test_service.py

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

    @pytest.mark.parametrize("chat_model_library, expected_method", [
        ("ChatGoogleGenerativeAI", None),
        ("ChatOpenAI", "function_calling"),
        ("AzureChatOpenAI", "function_calling"),
        ("UnknownModel", None)
    ])
    def test_set_tool_calling_method(self, chat_model_library, expected_method):
        """
        Test that set_tool_calling_method correctly determines the tool calling method
        based on the chat model library being used.
        
        This test covers:
        1. ChatGoogleGenerativeAI should return None
        2. ChatOpenAI should return "function_calling"
        3. AzureChatOpenAI should return "function_calling"
        4. Unknown models should return None
        """
        # Mock the LLM
        mock_llm = MagicMock()
        
        # Create an Agent instance with the mocked LLM
        agent = Agent(task="Test task", llm=mock_llm)
        
        # Mock the _set_model_names method to set the chat_model_library
        with patch.object(Agent, '_set_model_names') as mock_set_model_names:
            mock_set_model_names.side_effect = lambda: setattr(agent, 'chat_model_library', chat_model_library)
            
            # Call _set_model_names to set the chat_model_library
            agent._set_model_names()
            
            # Now call set_tool_calling_method
            result = agent.set_tool_calling_method("auto")
            
            assert result == expected_method

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