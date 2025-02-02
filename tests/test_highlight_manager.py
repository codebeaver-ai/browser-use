import pytest

from PIL import Image
from browser_use.browser.manager.highlight_manager import HighlightManager

class FakeDOMHistoryElement:
    """
    A fake DOMHistoryElement to simulate an element with highlight_index and position.
    """
    def __init__(self, highlight_index, position):
        self.highlight_index = highlight_index
        self.position = position

class FakePosition:
    """
    A simple fake position class with left, top, width, and height attributes.
    """
    def __init__(self, left, top, width, height):
        self.left = left
        self.top = top
        self.width = width
        self.height = height

class TestHighlightManager:
    """
    Test suite for the HighlightManager class.
    """

    def test_highlight_no_position_raises_valueerror(self):
        """
        Test that highlighting an element with no position raises a ValueError.
        """
        hm = HighlightManager()
        # Create a dummy element with position set to None
        fake_element = FakeDOMHistoryElement(highlight_index=1, position=None)
        dummy_image = Image.new("RGBA", (100, 100))

        with pytest.raises(ValueError, match="Position is required to highlight an element"):
            hm.highlight_element([fake_element], dummy_image)