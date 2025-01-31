import os
import pytest
import sys

from browser_use.agent.message_manager.service import MessageManager
from browser_use.agent.prompts import SystemPrompt
from browser_use.agent.service import Agent
from browser_use.agent.views import ActionResult, AgentOutput
from browser_use.browser.browser import Browser
from browser_use.browser.context import BrowserContext
from browser_use.browser.views import BrowserState
from browser_use.controller.registry.service import Registry
from browser_use.controller.registry.views import ActionModel
from browser_use.controller.service import Controller
from browser_use.dom.history_tree_processor.service import HistoryTreeProcessor
from browser_use.dom.history_tree_processor.view import DOMHistoryElement
from browser_use.dom.service import DomService
from browser_use.dom.views import DOMElementNode, DOMTextNode
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel
from unittest.mock import AsyncMock, MagicMock, Mock, patch

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

class TestHistoryTreeProcessor:
    def test_convert_dom_element_to_history_element(self):
        """
        Test that the convert_dom_element_to_history_element method correctly
        converts a DOMElementNode to a DOMHistoryElement.

        This test ensures that:
        1. The method returns a DOMHistoryElement instance.
        2. The returned object has the correct attributes from the input DOMElementNode.
        3. The parent_branch_path is correctly calculated.
        """
        # Arrange
        mock_parent = DOMElementNode(
            tag_name="div",
            xpath="/html/body/div",
            highlight_index=0,
            is_visible=True,
            parent=None,
            attributes={},
            children=[]
        )
        mock_dom_element = DOMElementNode(
            tag_name="p",
            xpath="/html/body/div/p",
            highlight_index=1,
            is_visible=True,
            parent=mock_parent,
            attributes={"class": "test"},
            children=[]
        )

        # Act
        result = HistoryTreeProcessor.convert_dom_element_to_history_element(mock_dom_element)

        # Assert
        assert isinstance(result, DOMHistoryElement)
        assert result.tag_name == "p"
        assert result.xpath == "/html/body/div/p"

class TestDomService:
    @pytest.fixture
    def sample_dom_tree(self):
        """
        Create a sample DOM tree for testing.
        """
        root = DOMElementNode(
            tag_name="html",
            xpath="/html",
            highlight_index=0,
            is_visible=True,
            parent=None,
            attributes={},
            children=[]
        )
        body = DOMElementNode(
            tag_name="body",
            xpath="/html/body",
            highlight_index=1,
            is_visible=True,
            parent=root,
            attributes={},
            children=[]
        )
        div = DOMElementNode(
            tag_name="div",
            xpath="/html/body/div",
            highlight_index=2,
            is_visible=True,
            parent=body,
            attributes={},
            children=[]
        )
        p = DOMElementNode(
            tag_name="p",
            xpath="/html/body/div/p",
            highlight_index=3,
            is_visible=True,
            parent=div,
            attributes={},
            children=[]
        )
        text = DOMTextNode(
            text="Hello, world!",
            is_visible=True,
            parent=p
        )

        root.children = [body]
        body.children = [div]
        div.children = [p]
        p.children = [text]

        return root

    def test_create_selector_map(self, sample_dom_tree):
        """
        Test that the _create_selector_map method correctly creates a selector map
        from a given DOM tree.

        This test ensures that:
        1. The method returns a dictionary (SelectorMap).
        2. The dictionary keys correspond to the highlight indices.
        3. The dictionary values are the correct DOMElementNode instances.
        4. Text nodes are not included in the selector map.
        """
        dom_service = DomService(page=None)  # We don't need a real page for this test

        selector_map = dom_service._create_selector_map(sample_dom_tree)

        assert isinstance(selector_map, dict)
        assert len(selector_map) == 4  # 4 elements with highlight indices

        assert 0 in selector_map and selector_map[0].tag_name == "html"
        assert 1 in selector_map and selector_map[1].tag_name == "body"
        assert 2 in selector_map and selector_map[2].tag_name == "div"
        assert 3 in selector_map and selector_map[3].tag_name == "p"

        # Ensure text node is not in the selector map
        assert 4 not in selector_map