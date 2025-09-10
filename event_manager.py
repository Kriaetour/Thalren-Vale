class EventManager:
    """A simple event manager to handle game events and listeners."""

    def __init__(self):
        self.listeners = {}

    def register_listener(self, event_type, listener_func):
        """
        Registers a function to listen for a specific event type.
        :param event_type: The name of the event (e.g., 'on_kill').
        :param listener_func: The function to call when the event is dispatched.
        """
        if event_type not in self.listeners:
            self.listeners[event_type] = []
        self.listeners[event_type].append(listener_func)
        # print(f"[EventManager] Registered listener for '{event_type}': {listener_func.__name__}") # Optional debug

    def dispatch(self, event_type, **kwargs):
        """
        Dispatches an event, calling all registered listeners.
        If a listener returns a value that is not None, it signifies that
        the event has been "handled", and the dispatch loop will stop and
        return that value.
        :param event_type: The name of the event to dispatch.
        :param kwargs: Keyword arguments to pass to the listener functions.
        """
        if event_type in self.listeners:
            for listener in self.listeners[event_type]:
                result = listener(**kwargs)
                if result is not None:
                    return result
        return None

# A global instance to be used throughout the game
event_manager = EventManager()