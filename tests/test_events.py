import unittest
import sys
import os
import gc

# Add the project directory to sys.path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from daming_os.events import EventBus, Event

class DummyEvent(Event):
    pass

class SubscriberObject:
    def method_callback(self, event):
        pass

def function_callback(event):
    pass

def another_function_callback(event):
    pass

class TestEventBusUnsubscribe(unittest.TestCase):
    def setUp(self):
        self.bus = EventBus()

    def test_unsubscribe_function(self):
        # Functions are stored as strong references
        self.bus.subscribe(DummyEvent, function_callback)
        self.assertEqual(len(self.bus._subscribers[DummyEvent]), 1)

        self.bus.unsubscribe(DummyEvent, function_callback)
        self.assertEqual(len(self.bus._subscribers[DummyEvent]), 0)

    def test_unsubscribe_method(self):
        # Bound methods are stored as weak references
        subscriber = SubscriberObject()
        self.bus.subscribe(DummyEvent, subscriber.method_callback)
        self.assertEqual(len(self.bus._subscribers[DummyEvent]), 1)

        self.bus.unsubscribe(DummyEvent, subscriber.method_callback)
        self.assertEqual(len(self.bus._subscribers[DummyEvent]), 0)

    def test_unsubscribe_cleans_up_dead_weakrefs(self):
        subscriber = SubscriberObject()
        self.bus.subscribe(DummyEvent, subscriber.method_callback)
        self.bus.subscribe(DummyEvent, function_callback)
        self.assertEqual(len(self.bus._subscribers[DummyEvent]), 2)

        # Delete subscriber to make it garbage collected
        del subscriber
        gc.collect()

        # Unsubscribing a different callback should also clean up dead weakrefs
        self.bus.unsubscribe(DummyEvent, function_callback)

        # After unsubscribe, both the explicitly unsubscribed function
        # and the dead weakref should be gone
        self.assertEqual(len(self.bus._subscribers[DummyEvent]), 0)

    def test_unsubscribe_empty(self):
        # Unsubscribing from an event with no subscribers should not raise an error
        try:
            self.bus.unsubscribe(DummyEvent, function_callback)
            # Verify the list is initialized to empty list or doesn't throw
            self.assertEqual(self.bus._subscribers.get(DummyEvent, []), [])
        except Exception as e:
            self.fail(f"unsubscribe raised an exception unexpectedly: {e}")

    def test_unsubscribe_unrelated(self):
        # Unsubscribing a callback that wasn't subscribed should not affect others
        self.bus.subscribe(DummyEvent, function_callback)
        self.assertEqual(len(self.bus._subscribers[DummyEvent]), 1)

        self.bus.unsubscribe(DummyEvent, another_function_callback)
        self.assertEqual(len(self.bus._subscribers[DummyEvent]), 1)
        self.assertIs(self.bus._subscribers[DummyEvent][0], function_callback)

if __name__ == "__main__":
    unittest.main()
