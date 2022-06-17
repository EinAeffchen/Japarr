from discord import NotFound, RequestsWebhookAdapter, Webhook, errors
from japarr.logger import get_module_logger
from japarr.config.config import get_config
logger = get_module_logger("Discord")


class DiscordConnector:
    active: bool
    webhook: str

    def __init__(self):
        self.active = True
        cfg = get_config()
        try:
            self.webhook = Webhook.from_url(
                cfg["general"].get("discord_webhook"),
                adapter=RequestsWebhookAdapter(),
            )
        except errors.InvalidArgument:
            logger.warning("No or no valid webhook url set. Running without discord!")
            self.active = False
            return
        try:
            self.webhook.send("Japarr test message.")
            self.active = True
        except NotFound:
            logger.warning(
                "Webhook is wrong or missing, deactivate logging to discord!"
            )
            self.active = False

    def send(self, message):
        """
        bla
        
        docstring
        a = 4"""
        if self.active:
            self.webhook.send(message)
        else:
            logger.info(message)
