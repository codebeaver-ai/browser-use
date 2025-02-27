import pytest
from pydantic import ValidationError
from browser_use.controller.views import (
    SearchGoogleAction,
    GoToUrlAction,
    ClickElementAction,
    InputTextAction,
    DoneAction,
    SwitchTabAction,
    OpenTabAction,
    ScrollAction,
    SendKeysAction,
    ExtractPageContentAction,
    NoParamsAction
)

class TestActionModels:
    """Test cases for action models defined in views.py."""

    def test_search_google_action(self):
        """Test creating SearchGoogleAction with a query."""
        action = SearchGoogleAction(query="openai")
        assert action.query == "openai"

    def test_go_to_url_action(self):
        """Test creating GoToUrlAction with a URL."""
        action = GoToUrlAction(url="http://example.com")
        assert action.url == "http://example.com"

    def test_click_element_action_with_xpath(self):
        """Test ClickElementAction with both index and xpath provided."""
        action = ClickElementAction(index=1, xpath="//div")
        assert action.index == 1
        assert action.xpath == "//div"

    def test_click_element_action_without_xpath(self):
        """Test ClickElementAction with only index provided."""
        action = ClickElementAction(index=2)
        assert action.index == 2
        assert action.xpath is None

    def test_input_text_action_with_xpath(self):
        """Test InputTextAction with both index, text and xpath."""
        action = InputTextAction(index=1, text="hello", xpath="//input")
        assert action.index == 1
        assert action.text == "hello"
        assert action.xpath == "//input"

    def test_input_text_action_without_xpath(self):
        """Test InputTextAction with only index and text."""
        action = InputTextAction(index=2, text="world")
        assert action.index == 2
        assert action.text == "world"
        assert action.xpath is None

    def test_done_action(self):
        """Test DoneAction with text and success flag."""
        action = DoneAction(text="done", success=True)
        assert action.text == "done"
        assert action.success is True

    def test_switch_tab_action(self):
        """Test SwitchTabAction with page_id."""
        action = SwitchTabAction(page_id=3)
        assert action.page_id == 3

    def test_open_tab_action(self):
        """Test OpenTabAction with url."""
        action = OpenTabAction(url="http://openai.com")
        assert action.url == "http://openai.com"

    def test_scroll_action_default(self):
        """Test ScrollAction without specifying amount (should be None)."""
        action = ScrollAction()
        assert action.amount is None

    def test_scroll_action_with_amount(self):
        """Test ScrollAction with a specified amount."""
        action = ScrollAction(amount=100)
        assert action.amount == 100

    def test_send_keys_action(self):
        """Test SendKeysAction with keys."""
        action = SendKeysAction(keys="CTRL+C")
        assert action.keys == "CTRL+C"

    def test_extract_page_content_action(self):
        """Test ExtractPageContentAction with value."""
        action = ExtractPageContentAction(value="some content")
        assert action.value == "some content"

    def test_no_params_action_discards_input(self):
        """Test NoParamsAction ignores any input provided."""
        data = {"unexpected": "value", "another": 123}
        action = NoParamsAction(**data)
        # The resulting dict representation should be empty.
        assert action.dict() == {}

    def test_no_params_action_allows_extra_fields(self):
        """Test NoParamsAction doesn't raise error with extra fields."""
        data = {"a": 1, "b": 2, "some": "value"}
        action = NoParamsAction(**data)
        # Even though extra fields were allowed, they are ignored by the pre-validator.
        assert action.dict() == {}

    def test_no_params_action_with_empty_input(self):
        """Test NoParamsAction with empty input returns an empty model."""
        action = NoParamsAction()
        assert action.dict() == {}

    def test_validation_error_on_missing_required_field(self):
        """Test that missing required field in a model raises ValidationError."""
        with pytest.raises(ValidationError):
            _ = SearchGoogleAction()  # missing 'query'

    def test_validation_error_on_wrong_type(self):
        """Test that providing the wrong type for a field raises ValidationError."""
        with pytest.raises(ValidationError):
            _ = ClickElementAction(index="not an int")
    def test_extra_fields_not_allowed(self):
        """Test that extra fields are ignored for each model (except NoParamsAction) and not included in the output."""
        models_and_defaults = [
            (SearchGoogleAction, {"query": "test"}),
            (GoToUrlAction, {"url": "http://example.com"}),
            (ClickElementAction, {"index": 0}),
            (InputTextAction, {"index": 0, "text": "test"}),
            (DoneAction, {"text": "done", "success": True}),
            (SwitchTabAction, {"page_id": 0}),
            (OpenTabAction, {"url": "http://example.com"}),
            (ScrollAction, {}),  # amount is optional
            (SendKeysAction, {"keys": "abc"}),
            (ExtractPageContentAction, {"value": "content"}),
        ]
        for model_cls, valid_data in models_and_defaults:
            action = model_cls(**{**valid_data, "unexpected_field": "value"})
            # The extra field "unexpected_field" should be ignored.
            assert "unexpected_field" not in action.dict()
            # The remaining data should match the valid_data.
            assert action.dict(exclude_unset=True) == valid_data
        action = ClickElementAction(index="10", xpath="//div")
        assert action.index == 10
    def test_parse_obj_methods(self):
        """Test that parse_obj method works correctly for all models."""
        models_and_defaults = [
            (SearchGoogleAction, {"query": "test"}),
            (GoToUrlAction, {"url": "http://example.com"}),
            (ClickElementAction, {"index": 5}),
            (InputTextAction, {"index": 2, "text": "sample"}),
            (DoneAction, {"text": "complete", "success": False}),
            (SwitchTabAction, {"page_id": 1}),
            (OpenTabAction, {"url": "http://example.com/tab"}),
            (ScrollAction, {"amount": 50}),
            (SendKeysAction, {"keys": "ALT+F4"}),
            (ExtractPageContentAction, {"value": "extracted"}),
        ]
        for model_cls, valid_data in models_and_defaults:
            # Using parse_obj to create an instance of the model
            instance = model_cls.parse_obj(valid_data)
            # Verify that converting to dict (excluding unset defaults) matches valid_data
            assert instance.dict(exclude_unset=True) == valid_data

        # Specifically for ClickElementAction, ensure type coercion via parse_obj works.
        instance = ClickElementAction.parse_obj({"index": "7", "xpath": "//span"})
        assert instance.index == 7

    def test_no_params_action_large_input(self):
        """Test NoParamsAction with a large input dictionary to ensure all fields are discarded."""
        large_input = {f"key{i}": i for i in range(100)}
        instance = NoParamsAction.parse_obj(large_input)
        # Even with a large input, the resulting dict output should be empty.
        assert instance.dict() == {}
    def test_input_text_action_type_coercion(self):
        """Test that InputTextAction converts index from a string to an int."""
        instance = InputTextAction.parse_obj({"index": "3", "text": "coercion test"})
        assert instance.index == 3
        assert instance.text == "coercion test"

    def test_switch_tab_action_type_coercion(self):
        """Test that SwitchTabAction converts page_id from a string to an int."""
        instance = SwitchTabAction.parse_obj({"page_id": "4"})
        assert instance.page_id == 4

    def test_click_element_action_xpath_conversion(self):
        """Test that ClickElementAction converts xpath to string if possible."""
        instance = ClickElementAction.parse_obj({"index": 10, "xpath": "123"})
        # expecting xpath to be converted to string "123"
        assert instance.xpath == "123"

    def test_done_action_with_success_as_int(self):
        """Test that DoneAction converts an integer success flag to boolean."""
        instance_true = DoneAction.parse_obj({"text": "done check", "success": 1})
        instance_false = DoneAction.parse_obj({"text": "done check", "success": 0})
        assert instance_true.success is True
        assert instance_false.success is False

    def test_scroll_action_invalid_type(self):
        """Test that ScrollAction raises ValidationError when provided with a non-integer amount."""
        with pytest.raises(ValidationError):
            _ = ScrollAction(amount="abc")

    def test_extraneous_fields_with_nested_dict(self):
        """Test that nested extra fields are ignored in the model data."""
        data = {"query": "nested", "extra": {"key": "value"}}
        instance = SearchGoogleAction(**data)
        # Ensure that the extra nested dictionary is not included in the output dict.
        assert "extra" not in instance.dict()

    def test_extract_page_content_action_extra_fields(self):
        """Test that ExtractPageContentAction ignores extra fields and only keeps the value field."""
        data = {"value": "content", "irrelevant": "data", "another_one": 42}
        instance = ExtractPageContentAction(**data)
        # extra keys should not appear in the dict representation
        assert instance.dict(exclude_unset=True) == {"value": "content"}