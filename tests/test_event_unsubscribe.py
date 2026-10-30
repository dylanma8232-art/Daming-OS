import unittest
import weakref
import gc
from daming_os.events import EventBus, Event

class TestEvent(Event):
    pass

class TestEventBus(unittest.TestCase):
    def test_unsubscribe_regular_function(self):
        bus = EventBus()
        calls = []

        def callback(event):
            calls.append(event)

        bus.subscribe(TestEvent, callback)
        bus.publish(TestEvent())
        self.assertEqual(len(calls), 1)

        bus.unsubscribe(TestEvent, callback)
        bus.publish(TestEvent())
        self.assertEqual(len(calls), 1)
        self.assertEqual(len(bus._subscribers[TestEvent]), 0)

    def test_unsubscribe_weak_method(self):
        bus = EventBus()
        calls = []

        class Subscriber:
            def callback(self, event):
                calls.append(event)

        subscriber = Subscriber()
        bus.subscribe(TestEvent, subscriber.callback)
        bus.publish(TestEvent())
        self.assertEqual(len(calls), 1)

        bus.unsubscribe(TestEvent, subscriber.callback)
        bus.publish(TestEvent())
        self.assertEqual(len(calls), 1)
        self.assertEqual(len(bus._subscribers[TestEvent]), 0)

    def test_unsubscribe_cleans_up_garbage_collected_references(self):
        bus = EventBus()
        calls = []

        class Subscriber:
            def callback(self, event):
                calls.append(event)

        def callback2(event):
            calls.append(event)

        subscriber = Subscriber()
        bus.subscribe(TestEvent, subscriber.callback)
        bus.subscribe(TestEvent, callback2)

        self.assertEqual(len(bus._subscribers[TestEvent]), 2)

        # Now delete the subscriber to let it be garbage collected
        del subscriber
        gc.collect()

        # When we unsubscribe callback2, the garbage collected weak reference should also be cleaned up
        bus.unsubscribe(TestEvent, callback2)

        # Only 0 subscribers should remain, as callback2 was explicitly unsubscribed
        # and the subscriber was garbage collected.
        self.assertEqual(len(bus._subscribers[TestEvent]), 0)

    def test_unsubscribe_from_empty_event_type(self):
        bus = EventBus()

        def callback(event):
            pass

        # Unsubscribe from an event type that has never been subscribed to
        bus.unsubscribe(TestEvent, callback)

        self.assertIn(TestEvent, bus._subscribers)
        self.assertEqual(len(bus._subscribers[TestEvent]), 0)

    def test_unsubscribe_non_existent_callback(self):
        bus = EventBus()
        calls = []

        def callback1(event):
            calls.append(event)

        def callback2(event):
            pass

        bus.subscribe(TestEvent, callback1)
        self.assertEqual(len(bus._subscribers[TestEvent]), 1)

        # Unsubscribe a callback that was never subscribed
        bus.unsubscribe(TestEvent, callback2)

        # The list of subscribers should remain unchanged
        self.assertEqual(len(bus._subscribers[TestEvent]), 1)

        # Calling publish should still work
        bus.publish(TestEvent())
        self.assertEqual(len(calls), 1)

if __name__ == '__main__':
    unittest.main()
