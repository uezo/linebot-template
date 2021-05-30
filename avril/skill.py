from abc import ABC, abstractmethod


class SkillBase(ABC):
    topic = None

    def __init__(self, bot):
        assert self.topic is not None
        self.bot = bot
        self.db_session = bot.db_session
        self.logger = bot.logger

    @abstractmethod
    def process_request(self, request, user, context):
        pass
