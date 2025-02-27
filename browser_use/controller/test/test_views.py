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

class TestActions:
    """Test cases for all Pydantic Action models."""

    def test_search_google_action_valid(self):
        """Test valid instantiation of SearchGoogleAction."""
        model = SearchGoogleAction(query="python")
        assert model.query == "python"

    def test_go_to_url_action_valid(self):
        """Test valid instantiation of GoToUrlAction."""
        model = GoToUrlAction(url="http://example.com")
        assert model.url == "http://example.com"

    def test_click_element_action_valid(self):
        """Test valid instantiation of ClickElementAction including optional parameter."""
        model = ClickElementAction(index=1, xpath="//div")
        assert model.index == 1
        assert model.xpath == "//div"
        model2 = ClickElementAction(index=2)
        assert model2.xpath is None

    def test_input_text_action_valid(self):
        """Test valid instantiation of InputTextAction including optional parameter."""
        model = InputTextAction(index=0, text="hello", xpath="//input")
        assert model.index == 0
        assert model.text == "hello"
        assert model.xpath == "//input"
        model2 = InputTextAction(index=1, text="world")
        assert model2.xpath is None

    def test_done_action_valid(self):
        """Test valid instantiation of DoneAction."""
        model = DoneAction(text="done", success=True)
        assert model.text == "done"
        assert model.success is True

    def test_switch_tab_action_valid(self):
        """Test valid instantiation of SwitchTabAction."""
        model = SwitchTabAction(page_id=2)
        assert model.page_id == 2

    def test_open_tab_action_valid(self):
        """Test valid instantiation of OpenTabAction."""
        model = OpenTabAction(url="http://example.com")
        assert model.url == "http://example.com"

    def test_scroll_action_valid(self):
        """Test valid instantiation of ScrollAction with specified amount and without."""
        model = ScrollAction(amount=100)
        assert model.amount == 100
        model2 = ScrollAction()
        assert model2.amount is None

    def test_send_keys_action_valid(self):
        """Test valid instantiation of SendKeysAction."""
        model = SendKeysAction(keys="Enter")
        assert model.keys == "Enter"

    def test_extract_page_content_action_valid(self):
        """Test valid instantiation of ExtractPageContentAction."""
        model = ExtractPageContentAction(value="content")
        assert model.value == "content"

    def test_no_params_action_ignore_inputs(self):
        """Test that NoParamsAction ignores all inputs and returns an empty dict."""
        model = NoParamsAction(field="value", another=123)
        assert model.dict() == {}

    def test_search_google_action_missing_field(self):
        """Test that SearchGoogleAction raises error when 'query' is missing."""
        with pytest.raises(ValidationError):
            SearchGoogleAction()

    def test_done_action_missing_field(self):
        """Test that DoneAction raises error when a required field is missing."""
        with pytest.raises(ValidationError):
            DoneAction(success=True)
    def test_search_google_action_invalid_type(self):
        """Test that SearchGoogleAction fails validation when query is not a string."""
        with pytest.raises(ValidationError):
            SearchGoogleAction(query=123)

    def test_click_element_action_invalid_index(self):
        """Test that ClickElementAction fails validation when index is not an integer."""
        with pytest.raises(ValidationError):
            ClickElementAction(index="one", xpath="//div")

    def test_input_text_action_missing_required_fields(self):
        """Test that InputTextAction raises error when required fields are missing (text field missing)."""
        with pytest.raises(ValidationError):
            InputTextAction(index=0)

    def test_scroll_action_invalid_type(self):
        """Test that ScrollAction fails validation when amount cannot be coerced to an integer."""
        with pytest.raises(ValidationError):
            ScrollAction(amount="not-a-number")

    def test_done_action_extra_field_ignored(self):
        """Test that DoneAction ignores extra fields and they do not appear in the output."""
        model = DoneAction(text="done", success=True, extra="value")
        # Extra field 'extra' should be ignored in the model dict output.
        assert "extra" not in model.dict()

    def test_extract_page_content_action_extra_field_ignored(self):
        """Test that ExtractPageContentAction ignores extra fields."""
        model = ExtractPageContentAction(value="content", extra="ignored")
        assert "extra" not in model.dict()
    def test_no_params_action_without_inputs(self):
        """Test that NoParamsAction returns an empty dict when no inputs are provided."""
        model = NoParamsAction()
        assert model.dict() == {}

    def test_scroll_action_float_coercible(self):
        """Test that ScrollAction coerces a float representing an integer to an int."""
        model = ScrollAction(amount=100.0)
        assert model.amount == 100

    def test_scroll_action_float_not_coercible(self):
        """Test that ScrollAction fails validation when a float with a fractional part is provided."""
        with pytest.raises(ValidationError):
            ScrollAction(amount=100.5)

    def test_search_google_action_extra_fields(self):
        """Test that SearchGoogleAction ignores extra fields."""
        model = SearchGoogleAction(query="python", extra1="notallowed", extra2=123)
        # Extra fields should be ignored in the model's dict output.
        assert model.dict() == {"query": "python"}

    def test_input_text_action_extra_field(self):
        """Test that InputTextAction ignores extra fields beyond those defined."""
        model = InputTextAction(index=0, text="hello", xpath="//input", extra_field="ignored")
        assert "extra_field" not in model.dict()

    def test_click_element_action_extra_field(self):
        """Test that ClickElementAction ignores extra fields beyond the defined ones."""
        model = ClickElementAction(index=1, xpath="//div", extra_param="ignored")
        assert "extra_param" not in model.dict()
    def test_go_to_url_action_invalid_type(self):
        """Test that GoToUrlAction fails validation when url is not a string."""
        with pytest.raises(ValidationError):
            GoToUrlAction(url=123)

    def test_send_keys_action_invalid_type(self):
        """Test that SendKeysAction fails validation when keys is not a string."""
        with pytest.raises(ValidationError):
            SendKeysAction(keys=123)

    def test_switch_tab_action_invalid_type(self):
        """Test that SwitchTabAction properly converts a string representing an integer to an int."""
        model = SwitchTabAction(page_id="2")
        assert model.page_id == 2

    def test_open_tab_action_invalid_type(self):
        """Test that OpenTabAction fails validation when url is not a string."""
        with pytest.raises(ValidationError):
            OpenTabAction(url=456)

    def test_extract_page_content_action_invalid_type(self):
        """Test that ExtractPageContentAction fails validation when value is not a string."""
        with pytest.raises(ValidationError):
            ExtractPageContentAction(value=789)

    def test_done_action_invalid_type(self):
        """Test that DoneAction fails validation when fields have invalid types."""
        with pytest.raises(ValidationError):
            DoneAction(text=100, success="yes")

    def test_input_text_action_invalid_text_type(self):
        """Test that InputTextAction fails validation when text is not a string."""
        with pytest.raises(ValidationError):
            InputTextAction(index=0, text=100, xpath="//input")

    def test_click_element_action_invalid_xpath_type(self):
        """Test that ClickElementAction fails validation when xpath is neither a string nor None."""
        with pytest.raises(ValidationError):
            ClickElementAction(index=0, xpath=["not", "a", "string"])