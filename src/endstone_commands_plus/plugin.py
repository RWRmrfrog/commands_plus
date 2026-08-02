"""Example plugin demonstrating commands, configuration, and lifecycle methods."""

from endstone import ColorFormat, Player
from endstone.event import event_handler, ServerListPingEvent
from endstone.command import Command, CommandSender
from endstone.plugin import Plugin
from typing_extensions import override

from .listener import CommandsPlusListener


class CommandsPlus(Plugin):
    # The prefix shown in log messages, e.g. [CommandsPlus] Hello!
    prefix = "CommandsPlus"

    # Must match the major.minor version of the Endstone API you are targeting.
    api_version = "0.11"

    commands = {
        "hat": {
            "description": "Place the item in your hand on your head.",
            "usages": ["/hat"],
            "permissions": ["commands_plus.command.hat"],
        },
        "offhand": {
            "description": "Place the item in your hand in your offhand.",
            "usages": ["/offhand"],
            "permissions": ["commands_plus.command.offhand"],
        },
        "nick": {
            "description": "Change your nickname.",
            "usages": ["/nick", "/nick clear", "/nick <name: string>"],
            "permissions": ["commands_plus.command.nick"],
        },
        "motd": {
            "description": "Reload or display the server MOTD from config.",
            "usages": ["/motd", "/motd reload"],
            "permissions": ["commands_plus.command.motd"],
        }
    }

    # Permissions are declared separately from commands. The "default" field controls
    # who gets the permission automatically: True = everyone, "op" = operators only,
    # False = no one (must be explicitly granted).
    permissions = {
        "commands_plus.command.hat": {
            "description": "Allow users to use the /hat command.",
            "default": True,
        },
        "commands_plus.command.offhand": {
            "description": "Allow users to use the /offhand command.",
            "default": True,
        },
        "commands_plus.command.nick": {
            "description": "Allow users to use the /nick command.",
            "default": True,
        },
        "commands_plus.command.motd": {
            "description": "Allow users to use the /motd command.",
            "default": "op",
        }
    }

    def load_motd_from_config(self) -> None:
        """Load motd string from config.yml into memory."""
        self.reload_config()
        self._motd = self.config.get("motd", "A Minecraft Endstone Server")

    @event_handler
    def on_server_list_ping(self, event: ServerListPingEvent) -> None:
        event.motd = self._motd

    @staticmethod
    def is_blocked_hat_item(item_id: str) -> bool:
        # Normalize (strip "minecraft:" if present)
        name = item_id
        if ':' in name:
            name = name.split(':', 1)[1]

        blocked_suffixes = (
            "_chestplate",
            "_leggings",
            "_boots",
            "_helmet",  # block other helmets from being "hat"-ed too, remove if you want to allow them
        )
        blocked_exact = (
            "elytra",
            "shield",
        )

        if name.endswith(blocked_suffixes):
            return True
        if name in blocked_exact:
            return True
        return False

    @override
    def on_enable(self) -> None:

        # Copies config.toml to the plugin's data folder on first run.
        # On subsequent runs it does nothing, preserving the user's edits.
        self.save_default_config()

        self.load_motd_from_config()
        self.register_events(self)

        self.register_events(CommandsPlusListener(self))

        self.logger.info("CommandsPlus enabled!")

    @override
    def on_disable(self) -> None:
        self.logger.info("CommandsPlus disabled!")

    @override
    def on_command(self, sender: CommandSender, command: Command, args: list[str]) -> bool:
        """Called when a player or the console runs one of this plugin's commands.

        Args:
            sender: Who ran the command (Player, ConsoleCommandSender, etc.).
            command: The command that was executed.
            args: The arguments passed after the command name.

        Returns:
            True if the command was handled successfully.
        """
        match command.name:
            case "hat":
                if isinstance(sender, Player):
                    held_item = sender.inventory.item_in_main_hand
                    helmet_slot = sender.inventory.helmet

                    if held_item is None:
                        sender.send_message(f"{ColorFormat.YELLOW}You're not holding any items!")
                    elif self.is_blocked_hat_item(held_item.type.id):
                        sender.send_message(f"{ColorFormat.YELLOW}You cannot wear this item as a hat!")
                    elif helmet_slot is not None and helmet_slot.type.id != "minecraft:air":
                        sender.send_message(f"{ColorFormat.YELLOW}You currently have something occupying your helmet slot! Please remove the item and try again!")
                    else:
                        sender.inventory.helmet = held_item
                        sender.inventory.clear(sender.inventory.held_item_slot)

            case "offhand":
                if isinstance(sender, Player):
                    held_item = sender.inventory.item_in_main_hand
                    offhand_slot = sender.inventory.item_in_off_hand
            
                    if held_item is None:
                        sender.send_message(f"{ColorFormat.YELLOW}You're not holding any items!")
                    elif offhand_slot is not None and offhand_slot.type.id != "minecraft:air":
                        sender.send_message(f"{ColorFormat.YELLOW}You currently have something occupying your offhand slot! Please remove the item and try again!")
                    else:
                        sender.inventory.item_in_off_hand = held_item
                        sender.inventory.clear(sender.inventory.held_item_slot)

            case "nick":
                if isinstance(sender, Player):
                    if args and args[0].lower() == "clear":
                        sender.name_tag = sender.name
                        sender.send_message(f"{ColorFormat.YELLOW}Nickname cleared")
                    elif args:
                        nick = args[0]
                        sender.name_tag = nick
                        sender.send_message(f"{ColorFormat.YELLOW}Nickname set to: {nick}")
                    else:
                        sender.send_message(f"{ColorFormat.YELLOW}Current Name: {sender.name_tag}")

            case "motd":
                if args and args[0].lower() == "reload":
                    self.load_motd_from_config()
                    sender.send_message(f"{ColorFormat.YELLOW}MOTD reloaded: {self._motd}")
                else:
                    sender.send_message(f"{ColorFormat.YELLOW}Current MOTD: {self._motd}")

        return True
