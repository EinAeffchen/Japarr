from discord import NotFound, RequestsWebhookAdapter, Webhook
from japarr.logger import get_module_logger
import japarr
from japarr.config.config import get_config
logger = get_module_logger("Discord")


class DiscordConnector:
    def __init__(self):
        cfg = get_config()
        self.webhook = Webhook.from_url(
            cfg["general"].get("discord_webhook"),
            adapter=RequestsWebhookAdapter(),
        )
        try:
            self.webhook.send("Japarr test message.")
            self.active = True
        except NotFound:
            logger.warning(
                "Webhook is wrong or missing, deactivate logging to discord!"
            )
            self.active = False

    def send(self, message):
        if self.active:
            self.webhook.send(message)
        else:
            logger.info(message)


discord_writer = DiscordConnector()
