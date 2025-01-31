from datetime import datetime
import json
import pytest
from browser_use.agent.prompts import SystemPrompt


class TestSystemPrompt:
    def test_system_message_content(self):
        """
        Test that the SystemPrompt generates a system message with expected content and structure.
        """
        # Arrange
        current_date = datetime(2023, 1, 1, 12, 0)
        action_description = "Test action description"
        system_prompt = SystemPrompt(action_description, current_date)

        # Act
        system_message = system_prompt.get_system_message()

        # Assert
        assert isinstance(system_message.content, str)
        assert "You are a precise browser automation agent" in system_message.content
        assert action_description in system_message.content
        assert "2023-01-01 12:00" in system_message.content
        
        # Check for important sections
        assert "RESPONSE FORMAT:" in system_message.content
        assert "ACTIONS:" in system_message.content
        assert "ELEMENT INTERACTION:" in system_message.content
        assert "NAVIGATION & ERROR HANDLING:" in system_message.content
        assert "TASK COMPLETION:" in system_message.content
        assert "VISUAL CONTEXT:" in system_message.content
        
        # Verify JSON structure description
        assert '"current_state": {' in system_message.content
        assert '"evaluation_previous_goal":' in system_message.content
        assert '"memory":' in system_message.content
        assert '"next_goal":' in system_message.content
        assert '"action": [' in system_message.content
