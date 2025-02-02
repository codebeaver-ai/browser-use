import pytest

from browser_use.dom.history_tree_processor import view

class TestDOMHistoryElement:
    """
    Test cases for the DOMHistoryElement and related classes.
    Ensures that the to_dict() method returns the correct fields and that
    the Position dataclass is mutable.
    """

    def test_to_dict_excludes_position(self):
        """
        Test that the to_dict() method of DOMHistoryElement returns a dictionary
        that does not include the 'position' field, even if the position is provided.
        """
        element = view.DOMHistoryElement(
            tag_name="div",
            xpath="/html/body/div",
            highlight_index=1,
            entire_parent_branch_path=["html", "body"],
            attributes={"class": "container"},
            shadow_root=False,
            position=view.Position(top=10, left=20, width=100, height=200)
        )
        result = element.to_dict()
        # Check that all expected fields are present and correct.
        assert result["tag_name"] == "div"
        assert result["xpath"] == "/html/body/div"
        assert result["highlight_index"] == 1
        assert result["entire_parent_branch_path"] == ["html", "body"]
        assert result["attributes"] == {"class": "container"}
        assert result["shadow_root"] is False
        # Ensure that the 'position' field is not part of the dictionary.
        assert "position" not in result

    def test_position_mutability(self):
        """
        Test that the Position dataclass is mutable, meaning that its fields can be
        modified after initialization.
        """
        pos = view.Position(top=0, left=0, width=50, height=50)
        # Modify the position values.
        pos.top = 15
        pos.left = 25
        pos.width = 75
        pos.height = 85
        # Assert that the modifications are correctly reflected.
        assert pos.top == 15
        assert pos.left == 25
        assert pos.width == 75
        assert pos.height == 85