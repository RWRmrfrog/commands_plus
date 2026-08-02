"""Event listener demonstrating how to respond to player events.

Listeners are separate classes (not the Plugin itself) that hold @event_handler
methods. Register them in on_enable with self.register_events(). This keeps
event handling logic organized and out of the main plugin class.
"""

from endstone.plugin import Plugin


class CommandsPlusListener:
    def __init__(self, plugin: Plugin) -> None:
        # Keep a reference to the plugin so we can use its logger and config.
        self._plugin = plugin