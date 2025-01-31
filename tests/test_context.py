import pytest

from browser_use.browser.browser import Browser
from browser_use.browser.context import BrowserContext, BrowserContextConfig
from unittest.mock import Mock, patch

class TestBrowserContext:
    """Test class for BrowserContext"""

    @pytest.fixture
    def mock_browser(self):
        """Fixture to create a mock Browser object"""
        return Mock(spec=Browser)

    @patch('browser_use.browser.context.uuid.uuid4')
    def test_browser_context_initialization(self, mock_uuid4, mock_browser):
        """
        Test the initialization of BrowserContext with custom configuration.
        This test checks if the BrowserContext is correctly initialized with
        the provided configuration and if the context_id is set properly.
        """
        # Arrange
        mock_uuid4.return_value = "test-uuid"
        custom_config = BrowserContextConfig(
            cookies_file="test_cookies.json",
            minimum_wait_page_load_time=1.0,
            browser_window_size={'width': 1920, 'height': 1080},
            highlight_elements=False,
            viewport_expansion=1000,
            allowed_domains=['example.com']
        )

        # Act
        browser_context = BrowserContext(mock_browser, config=custom_config)

        # Assert
        assert browser_context.context_id == "test-uuid"
        assert browser_context.config == custom_config
        assert browser_context.browser == mock_browser
        assert browser_context.session is None

        # Check specific config values
        assert browser_context.config.cookies_file == "test_cookies.json"
        assert browser_context.config.minimum_wait_page_load_time == 1.0
        assert browser_context.config.browser_window_size == {'width': 1920, 'height': 1080}
        assert browser_context.config.highlight_elements is False
        assert browser_context.config.viewport_expansion == 1000
        assert browser_context.config.allowed_domains == ['example.com']