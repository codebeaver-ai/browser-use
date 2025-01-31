from browser_use.agent.message_manager.views import MessageHistory, MessageMetadata
from langchain_core.messages import HumanMessage


class TestMessageHistory:
    def test_remove_message_updates_total_tokens(self):
        """
        Test that removing a message from MessageHistory correctly updates the total_tokens count.
        """
        # Create a MessageHistory instance
        history = MessageHistory()
        
        # Add a message with some tokens
        message = HumanMessage(content="Test message")
        metadata = MessageMetadata(input_tokens=10)
        history.add_message(message, metadata)
        
        # Verify initial state
        assert history.total_tokens == 10
        assert len(history.messages) == 1
        
        # Remove the message
        history.remove_message()
        
        # Verify final state
        assert history.total_tokens == 0
        assert len(history.messages) == 0
