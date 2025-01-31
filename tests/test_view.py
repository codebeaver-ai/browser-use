import pytest

from browser_use.dom.history_tree_processor.view import CoordinateSet, Coordinates, DOMHistoryElement, ViewportInfo

class TestDOMHistoryElement:
    def test_to_dict_method(self):
        """
        Test the to_dict method of DOMHistoryElement.
        This test covers the scenario where all optional fields are provided.
        """
        # Create a sample DOMHistoryElement with all fields populated
        element = DOMHistoryElement(
            tag_name="div",
            xpath="/html/body/div[1]",
            highlight_index=1,
            entire_parent_branch_path=["html", "body", "div"],
            attributes={"class": "container", "id": "main"},
            shadow_root=False,
            css_selector="div.container#main",
            page_coordinates=CoordinateSet(
                top_left=Coordinates(x=0, y=0),
                top_right=Coordinates(x=100, y=0),
                bottom_left=Coordinates(x=0, y=100),
                bottom_right=Coordinates(x=100, y=100),
                center=Coordinates(x=50, y=50),
                width=100,
                height=100
            ),
            viewport_coordinates=CoordinateSet(
                top_left=Coordinates(x=10, y=10),
                top_right=Coordinates(x=90, y=10),
                bottom_left=Coordinates(x=10, y=90),
                bottom_right=Coordinates(x=90, y=90),
                center=Coordinates(x=50, y=50),
                width=80,
                height=80
            ),
            viewport_info=ViewportInfo(
                scroll_x=0,
                scroll_y=0,
                width=1024,
                height=768
            )
        )

        # Call the to_dict method
        result = element.to_dict()

        # Assert that the result is a dictionary
        assert isinstance(result, dict)

        # Assert that all expected keys are present in the result
        expected_keys = [
            'tag_name', 'xpath', 'highlight_index', 'entire_parent_branch_path',
            'attributes', 'shadow_root', 'css_selector', 'page_coordinates',
            'viewport_coordinates', 'viewport_info'
        ]
        for key in expected_keys:
            assert key in result

        # Assert that the values are correct
        assert result['tag_name'] == "div"
        assert result['xpath'] == "/html/body/div[1]"
        assert result['highlight_index'] == 1
        assert result['entire_parent_branch_path'] == ["html", "body", "div"]
        assert result['attributes'] == {"class": "container", "id": "main"}
        assert result['shadow_root'] is False
        assert result['css_selector'] == "div.container#main"

        # Check that nested structures are correctly converted to dictionaries
        assert isinstance(result['page_coordinates'], dict)
        assert isinstance(result['viewport_coordinates'], dict)
        assert isinstance(result['viewport_info'], dict)

        # Check a few nested values
        assert result['page_coordinates']['width'] == 100
        assert result['viewport_coordinates']['height'] == 80
        assert result['viewport_info']['width'] == 1024