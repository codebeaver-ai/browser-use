import pytest

from browser_use.utils import singleton

class TestSingleton:
    """Test class for the singleton decorator."""

    def test_singleton_decorator(self):
        """
        Test that the singleton decorator creates only one instance of a class.
        """
        @singleton
        class TestClass:
            def __init__(self):
                self.value = 0

            def increment(self):
                self.value += 1

        # Create two instances of TestClass
        instance1 = TestClass()
        instance2 = TestClass()

        # Check that both instances are the same object
        assert instance1 is instance2

        # Modify the value using one instance
        instance1.increment()

        # Check that the change is reflected in both instances
        assert instance1.value == 1
        assert instance2.value == 1

        # Create a third instance and verify it's still the same object
        instance3 = TestClass()
        assert instance1 is instance3
        assert instance3.value == 1