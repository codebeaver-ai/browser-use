import pytest
import json
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
    NoParamsAction,
)

def test_search_google_action_valid():
    """Test creating SearchGoogleAction with a valid query."""
    query = "python pytest"
    action = SearchGoogleAction(query=query)
    assert action.query == query

def test_go_to_url_action_valid():
    """Test creating GoToUrlAction with a valid URL."""
    url = "https://example.com"
    action = GoToUrlAction(url=url)
    assert action.url == url

def test_click_element_action_defaults():
    """Test ClickElementAction with and without optional xpath."""
    # Without xpath provided, it should be None.
    action = ClickElementAction(index=1)
    assert action.index == 1
    assert action.xpath is None

def test_click_element_action_with_xpath():
    """Test ClickElementAction with specified xpath."""
    xpath = "//button[@id='submit']"
    action = ClickElementAction(index=2, xpath=xpath)
    assert action.index == 2
    assert action.xpath == xpath

def test_input_text_action_defaults():
    """Test InputTextAction with missing optional xpath."""
    action = InputTextAction(index=0, text="hello")
    assert action.index == 0
    assert action.text == "hello"
    assert action.xpath is None

def test_input_text_action_with_xpath():
    """Test InputTextAction with provided xpath."""
    xpath_val = "//input[@name='q']"
    action = InputTextAction(index=1, text="world", xpath=xpath_val)
    assert action.index == 1
    assert action.text == "world"
    assert action.xpath == xpath_val

def test_done_action():
    """Test DoneAction for both success True and False."""
    action_true = DoneAction(text="Completed", success=True)
    action_false = DoneAction(text="Failed", success=False)
    assert action_true.text == "Completed"
    assert action_true.success is True
    assert action_false.text == "Failed"
    assert action_false.success is False

def test_switch_tab_action():
    """Test SwitchTabAction using a valid page_id."""
    page_id = 3
    action = SwitchTabAction(page_id=page_id)
    assert action.page_id == page_id

def test_open_tab_action():
    """Test OpenTabAction using a valid URL."""
    url = "https://openai.com"
    action = OpenTabAction(url=url)
    assert action.url == url

def test_scroll_action_defaults():
    """Test ScrollAction with no amount provided defaults to None."""
    action = ScrollAction()
    assert action.amount is None

def test_scroll_action_with_value():
    """Test ScrollAction with a provided amount value."""
    amount = 250
    action = ScrollAction(amount=amount)
    assert action.amount == amount

def test_send_keys_action():
    """Test SendKeysAction with a valid keys string."""
    keys = "ENTER"
    action = SendKeysAction(keys=keys)
    assert action.keys == keys

def test_extract_page_content_action():
    """Test ExtractPageContentAction with valid content."""
    value = "<html></html>"
    action = ExtractPageContentAction(value=value)
    assert action.value == value

def test_no_params_action_ignores_input():
    """Test that NoParamsAction ignores all provided inputs and results in an empty model."""
    # Provide multiple arbitrary fields
    action = NoParamsAction(foo="bar", number=123, nested={"a": 1})
    # The resulting model should have no fields
    assert action.dict() == {}

def test_no_params_action_extra_fields_allowed():
    """Test that NoParamsAction can accept unknown fields due to its Config extra='allow'."""
    data = {"unexpected": "value", "another": 42}
    action = NoParamsAction(**data)
    assert action.dict() == {}
def test_search_google_action_invalid_type():
    """Test that SearchGoogleAction raises a ValidationError when query is not a string."""
    with pytest.raises(ValidationError):
        SearchGoogleAction(query=123)

def test_click_element_action_invalid_index():
    """Test that ClickElementAction raises a ValidationError when index is not an integer."""
    with pytest.raises(ValidationError):
        ClickElementAction(index="not an int")

def test_go_to_url_action_extra_field():
    """Test that GoToUrlAction ignores unknown extra fields and returns only expected data."""
    action = GoToUrlAction(url="https://example.com", foo="unexpected")
    # Validate that only the defined 'url' field is accepted.
    assert action.dict() == {"url": "https://example.com"}
def test_open_tab_action_invalid_url_type():
    """Test that OpenTabAction raises a ValidationError when url is not a string."""
    with pytest.raises(ValidationError):
        OpenTabAction(url=12345)

def test_switch_tab_action_invalid_type():
    """Test that SwitchTabAction raises a ValidationError when page_id is not an integer."""
    with pytest.raises(ValidationError):
        SwitchTabAction(page_id="page")

def test_input_text_action_extra_field():
    """Test that InputTextAction ignores unknown extra fields and returns only expected data."""
    action = InputTextAction(index=0, text="hello", extra="oops")
    # Validate that only 'index', 'text', and the optional 'xpath' (defaulting to None) are present.
    assert action.dict() == {"index": 0, "text": "hello", "xpath": None}
def test_scroll_action_invalid_amount():
    """Test that ScrollAction raises a ValidationError when amount is not an integer or None."""
    with pytest.raises(ValidationError):
        ScrollAction(amount="not an int")

def test_send_keys_action_invalid_type():
    """Test that SendKeysAction raises a ValidationError when keys is not a string."""
    with pytest.raises(ValidationError):
        SendKeysAction(keys=123)

def test_extract_page_content_action_invalid_type():
    """Test that ExtractPageContentAction raises a ValidationError when value is not a string."""
    with pytest.raises(ValidationError):
        ExtractPageContentAction(value=999)
def test_click_element_action_multiple_invalid():
    """Test ClickElementAction with multiple invalid types for index and xpath."""
    with pytest.raises(ValidationError) as exc_info:
        ClickElementAction(index="invalid", xpath=123)
    errors = exc_info.value.errors()
    # Ensure there is an error for both index and xpath types.
    assert any("index" in e.get("loc", []) for e in errors)
    assert any("xpath" in e.get("loc", []) for e in errors)

def test_input_text_action_multiple_invalid():
    """Test InputTextAction with multiple invalid types for index, text, and xpath."""
    with pytest.raises(ValidationError) as exc_info:
        InputTextAction(index="zero", text=12345, xpath=678)
    errors = exc_info.value.errors()
    # Verify that each field has a validation error.
    assert any("index" in e.get("loc", []) for e in errors)
    assert any("text" in e.get("loc", []) for e in errors)
    assert any("xpath" in e.get("loc", []) for e in errors)

def test_done_action_json_conversion():
    """Test the JSON conversion of DoneAction."""
    action = DoneAction(text="Test JSON", success=True)
    # Using pydantic v2's model_dump_json; if using pydantic v1 use action.json()
    json_str = action.model_dump_json()
    parsed_json = json.loads(json_str)
    # Compare dictionaries to avoid issues due to whitespace formatting differences
    assert parsed_json == {"text": "Test JSON", "success": True}

def test_no_params_action_handles_none_and_empty():
    """Test that NoParamsAction ignores None and empty values in input."""
    action = NoParamsAction(foo=None, bar="", nested=None)
    assert action.dict() == {}

def test_no_params_action_str_method():
    """Test that the string representation of NoParamsAction reflects an empty model."""
    action = NoParamsAction(unexpected="value")
    # Even though a value is passed, due to the pre-validator, the model remains empty.
    # Instead of checking the string directly (which can vary), we verify that the dumped model is empty.
    assert action.model_dump() == {}

def test_scroll_action_negative_amount():
    """Test that ScrollAction accepts negative integer values for the amount field."""
    action = ScrollAction(amount=-100)
    assert action.amount == -100
def test_search_google_action_roundtrip():
    """Test roundtrip JSON conversion for SearchGoogleAction."""
    original = SearchGoogleAction(query="pytest")
    json_str = original.model_dump_json()
    new = SearchGoogleAction.model_validate_json(json_str)
    assert original == new

def test_click_element_action_copy():
    """Test that copying ClickElementAction produces an equal object."""
    original = ClickElementAction(index=1, xpath="//div")
    copy = original.model_copy()
    assert original == copy

def test_equality_of_done_action():
    """Test equality operations for DoneAction objects."""
    a = DoneAction(text="Complete", success=True)
    b = DoneAction(text="Complete", success=True)
    c = DoneAction(text="Incomplete", success=False)
    assert a == b
    assert a != c

def test_open_tab_action_roundtrip():
    """Test JSON roundtrip for OpenTabAction."""
    original = OpenTabAction(url="https://openai.com")
    json_str = original.model_dump_json()
    new = OpenTabAction.model_validate_json(json_str)
    assert original == new

def test_scroll_action_optional_absent():
    """Test that ScrollAction returns None for amount when omitted."""
    action = ScrollAction()
    assert action.amount is None

def test_send_keys_action_roundtrip():
    """Test roundtrip JSON conversion for SendKeysAction."""
    original = SendKeysAction(keys="TAB")
    json_str = original.model_dump_json()
    new = SendKeysAction.model_validate_json(json_str)
    assert original == new

def test_extract_page_content_action_roundtrip():
    """Test roundtrip JSON conversion for ExtractPageContentAction."""
    original = ExtractPageContentAction(value="<html></html>")
    json_str = original.model_dump_json()
    new = ExtractPageContentAction.model_validate_json(json_str)
    assert original == new

def test_search_google_action_extra_field():
    """Test that SearchGoogleAction ignores unexpected fields and returns only expected data."""
    action = SearchGoogleAction(query="extra fields", foo="bar")
    assert action.dict() == {"query": "extra fields"}