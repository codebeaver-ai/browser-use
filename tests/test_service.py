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
from browser_use.dom.history_tree_processor.service import HistoryTreeProcessor
from browser_use.dom.history_tree_processor.view import DOMHistoryElement
from browser_use.dom.service import DomService
from browser_use.dom.views import DOMElementNode
from langchain_core.language_models.chat_models import BaseChatModel
from playwright.async_api import Page
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

class TestHistoryTreeProcessor:
    def test_convert_dom_element_to_history_element(self):
        """
        Test that the convert_dom_element_to_history_element method correctly
        converts a DOMElementNode to a DOMHistoryElement.

        This test ensures that:
        1. The method correctly extracts the tag name, xpath, and highlight index.
        2. The parent branch path contains only the current element's tag name.
        3. The attributes and shadow root are properly transferred.
        """
        # Create a mock parent DOMElementNode
        mock_parent = DOMElementNode(
            tag_name="div",
            xpath="/html/body/div",
            highlight_index=0,
            is_visible=True,
            parent=None,
            attributes={},
            children=[],
            shadow_root=None
        )

        # Create a mock child DOMElementNode
        mock_dom_element = DOMElementNode(
            tag_name="a",
            xpath="/html/body/div/a",
            highlight_index=1,
            is_visible=True,
            parent=mock_parent,
            attributes={"href": "https://example.com"},
            children=[],
            shadow_root=None
        )

        # Convert the mock DOMElementNode to a DOMHistoryElement
        history_element = HistoryTreeProcessor.convert_dom_element_to_history_element(mock_dom_element)

        # Assert that the conversion is correct
        assert isinstance(history_element, DOMHistoryElement)
        assert history_element.tag_name == "a"
        assert history_element.xpath == "/html/body/div/a"
        assert history_element.highlight_index == 1
        assert history_element.entire_parent_branch_path == ["a"]  # Changed expectation
        assert history_element.attributes == {"href": "https://example.com"}
        assert history_element.shadow_root is None

class TestDomService:
    @pytest.fixture
    def mock_page(self):
        return Mock(spec=Page)

    def test_create_selector_map(self, mock_page):
        """
        Test that the _create_selector_map method correctly creates a mapping
        between highlight indices and DOMElementNodes.

        This test ensures that:
        1. The method correctly processes a simple DOM tree.
        2. The resulting selector map contains the correct mappings.
        3. Elements without highlight indices are not included in the map.
        """
        # Create a simple DOM tree
        root = DOMElementNode(
            tag_name="html",
            xpath="/html",
            highlight_index=0,
            is_visible=True,
            parent=None,
            attributes={},
            children=[],
            shadow_root=None
        )
        body = DOMElementNode(
            tag_name="body",
            xpath="/html/body",
            highlight_index=1,
            is_visible=True,
            parent=root,
            attributes={},
            children=[],
            shadow_root=None
        )
        div = DOMElementNode(
            tag_name="div",
            xpath="/html/body/div",
            highlight_index=None,  # This element should not be in the selector map
            is_visible=True,
            parent=body,
            attributes={},
            children=[],
            shadow_root=None
        )
        a = DOMElementNode(
            tag_name="a",
            xpath="/html/body/div/a",
            highlight_index=2,
            is_visible=True,
            parent=div,
            attributes={},
            children=[],
            shadow_root=None
        )

        root.children = [body]
        body.children = [div]
        div.children = [a]

        # Create DomService instance
        dom_service = DomService(mock_page)

        # Call _create_selector_map
        selector_map = dom_service._create_selector_map(root)

        # Assert the correct mappings
        assert len(selector_map) == 3
        assert selector_map[0] == root
        assert selector_map[1] == body
        assert selector_map[2] == a
        assert None not in selector_map  # Ensure the div without highlight_index is not in the map