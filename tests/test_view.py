import pytest

from browser_use.dom.history_tree_processor.view import DOMHistoryElement, Position

class TestDOMHistoryElement:
    def test_to_dict_method(self):
        """
        Test the to_dict() method of DOMHistoryElement to ensure it correctly
        converts the object to a dictionary representation.
        """
        # Create a DOMHistoryElement instance
        dom_element = DOMHistoryElement(
            tag_name="div",
            xpath="/html/body/div[1]",
            highlight_index=1,
            entire_parent_branch_path=["html", "body", "div"],
            attributes={"class": "container", "id": "main"},
            shadow_root=True,
            position=Position(top=10, left=20, width=100, height=50)
        )

        # Call the to_dict() method
        result = dom_element.to_dict()

        # Assert that the result is a dictionary
        assert isinstance(result, dict)

        # Assert that the dictionary contains the expected keys and values
        assert result["tag_name"] == "div"
        assert result["xpath"] == "/html/body/div[1]"
        assert result["highlight_index"] == 1
        assert result["entire_parent_branch_path"] == ["html", "body", "div"]
        assert result["attributes"] == {"class": "container", "id": "main"}
        assert result["shadow_root"] is True

        # Assert that the position is not included in the dictionary
        assert "position" not in result