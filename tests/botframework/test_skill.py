import pytest
from avril import SkillBase


class DummyBot:
    db_session = "db_session_func"
    logger = "logger_obj"


class HelloSkill(SkillBase):
    topic = "Hello"

    def process_request(self, request, user, state):
        return "Hello"


class NoTopicSkill(SkillBase):
    def process_request(self, request, user, state):
        pass


class TestSkillBase:
    def test_init(self):
        hello_skill = HelloSkill(DummyBot())

        assert hello_skill.db_session == "db_session_func"
        assert hello_skill.logger == "logger_obj"

        with pytest.raises(TypeError):
            _ = SkillBase(None)

        with pytest.raises(AssertionError):
            _ = NoTopicSkill(None)
