from configparser import ConfigParser
from time import sleep
from uuid import uuid4
import json
import pytest
from sqlalchemy import desc
from botframework import BotBase, SkillBase
from botframework.models import (
    Context, MessageLog, Request, Response, create_all
)
from database import Database

# load config
config = ConfigParser()
config.read("tests/tests.ini")

# initialize database
db = Database(config["DATABASE"]["connection_string"])
create_all(db.engine)

# existing user info
existing_user_id = config["LINE_API"]["existing_user_id"]
existing_user_name = config["LINE_API"]["existing_user_name"]


@pytest.fixture
def bot():
    return BotForTest(
        db_session_maker=Database(
            config["DATABASE"]["connection_string"]).session,
        context_timeout=5
    )


class ResponseTypeSkill(SkillBase):
    topic = "ResponseType"

    def process_request(self, request, user, context):
        req = request.event["text"]

        if "text" in req:
            return "text"

        elif "list" in req:
            return ["text1", "text2"]


class MultiTurnSkill(SkillBase):
    topic = "MultiTurn"

    def process_request(self, request, user, context):
        req = request.event["text"]

        if request.intent == self.topic:
            context.data["count"] = 1
            user.data["myid"] = user.id
            return Response(
                messages="first turn",
                end_session=False
            )

        elif "end" in req:
            return "end"

        elif "err" in req:
            raise Exception("error occured in process_request")

        elif not context.data.get("count") is None:
            context.data["count"] += 1
            # raise Exception("count=" + str(context.data["count"]))
            return Response(
                messages=f"turn {context.data['count']}",
                end_session=False
            )


class ErrorCaseSkill(SkillBase):
    topic = "ErrorCase"

    def process_request(self, request, user, context):
        req = request.event["text"]

        if "skill" in req:
            raise Exception("Error in skill")

        elif "invalid_context" in req:
            context.data["context_status"] = "invalid"
            context.serialize_data = None
            return Response(
                messages="context invalidated",
                end_session=False
            )

        else:
            context.data["context_status"] = "valid"
            return Response(
                messages="No errors",
                end_session=False
            )


class BotForTest(BotBase):
    skills = [ResponseTypeSkill, MultiTurnSkill, ErrorCaseSkill]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.response_buffer = []

    def process_response(self, request, user, context, response):
        self.response_buffer.append(response)

    def extract_intent(self, request, user, context):
        req = request.event["text"]

        if req.startswith("multi_turn"):
            return MultiTurnSkill.topic, {}

        if req.startswith("response"):
            return ResponseTypeSkill.topic, {}

        if req.startswith("error"):
            return ErrorCaseSkill.topic, {}


class TestBotBase:
    def get_context(self, bot, source_id):
        db = bot.db_session()
        try:
            return bot.get_context(db, Request(source_id=source_id))
        finally:
            db.close()

    def get_last_messagelog(self, bot, source_id):
        db = bot.db_session()
        try:
            return db.query(MessageLog).\
                filter(MessageLog.source_id == source_id).\
                order_by(desc(MessageLog.updated_at)).first()
        finally:
            db.close()

    def test_get_context_separated_by_users(self, bot):
        db = bot.db_session()

        try:
            # set user ids
            user_1 = str(uuid4())
            user_2 = str(uuid4())

            # get and update each contexts
            context_1 = bot.get_context(db, Request(source_id=user_1))
            assert context_1.data == {}
            context_1.data["data"] = "for user 1"
            context_1.serialize_data()

            context_2 = bot.get_context(db, Request(source_id=user_2))
            assert context_2.data == {}
            context_2.data["data"] = "for user 2"
            context_2.serialize_data()
            db.commit()

            # wait for 2 seconds (within timeout)
            sleep(2)
            context_1 = bot.get_context(db, Request(source_id=user_1))
            assert context_1.data["data"] == "for user 1"
            context_2 = bot.get_context(db, Request(source_id=user_2))
            assert context_2.data["data"] == "for user 2"

        finally:
            db.close()

    def test_get_context_timeout(self, bot):
        db = bot.db_session()

        try:
            # set user ids
            user_1 = str(uuid4())

            # get context of user1
            context = bot.get_context(db, Request(source_id=user_1))
            assert context.data == {}

            # update context
            new_data = str(uuid4())
            context.topic = "timeout_test"
            context.data["uuid"] = new_data
            context.serialize_data()
            db.commit()

            # wait for 2 seconds (within timeout), data is alive
            sleep(2)
            context = bot.get_context(db, Request(source_id=user_1))
            assert context.topic == "timeout_test"
            assert context.data["uuid"] == new_data

            # wait for 7 seconds (over timeout), data is cleared
            sleep(7)
            context = bot.get_context(db, Request(source_id=user_1))
            assert context.topic is None
            assert context.data == {}

        finally:
            db.close()

    def test_get_user_new(self, bot):
        db = bot.db_session()

        try:
            # get new user
            user_1 = str(uuid4())
            user = bot.get_user(db, Request(source_id=user_1))

            assert user.id == user_1
            assert user.updated_at is not None
            assert user.data == {}

        finally:
            db.close()

    def test_get_user_existing(self, bot):
        db = bot.db_session()

        try:
            # get existing user
            user = bot.get_user(db, Request(source_id=existing_user_id))

            # update data
            new_data = str(uuid4())
            user.data["uuid"] = new_data
            user.serialize_data()
            db.commit()

            # check the data is updated
            user = bot.get_user(db, Request(source_id=existing_user_id))
            assert user.data["uuid"] == new_data

        finally:
            db.close()

    def test_register_skill(self):
        class BotWithNoSkills(BotBase):
            def extract_intent(**kwargs):
                pass

            def process_response(**kwargs):
                pass

        # add skill to bot.skills
        noskill_bot = BotWithNoSkills()
        noskill_bot.register_skill(ResponseTypeSkill)
        assert noskill_bot.skills == [ResponseTypeSkill]

        # confirm that skill is available in bot
        skill = noskill_bot.route(
            Request(intent=ResponseTypeSkill.topic),
            None, Context()
        )
        assert isinstance(skill, ResponseTypeSkill)

    def test_process_events(self, bot):
        # single text response
        bot.process_events([{
            "text": "response text",
            "source_id": existing_user_id
        }])
        assert len(bot.response_buffer[0].messages) == 1
        assert bot.response_buffer[0].messages[0] == "text"

        # multiple text responses
        bot.response_buffer.clear()
        bot.process_events([{
            "text": "response list",
            "source_id": existing_user_id
        }])
        assert len(bot.response_buffer[0].messages) == 2
        assert bot.response_buffer[0].messages[0] == "text1"
        assert bot.response_buffer[0].messages[1] == "text2"

        # no response
        bot.response_buffer.clear()
        bot.process_events([{
            "text": "response nothing",
            "source_id": existing_user_id
        }])
        assert len(bot.response_buffer[0].messages) == 0

    def test_process_events_error(self, bot):
        user_id = str(uuid4())

        # no skill
        bot.response_buffer.clear()
        bot.process_events([{
            "text": "no skill",
            "source_id": user_id
        }])
        assert len(bot.response_buffer) == 0

        # no error occures
        bot.response_buffer.clear()
        bot.process_events([{
            "text": "error noerror",
            "source_id": user_id
        }])
        assert len(bot.response_buffer) == 1
        assert bot.response_buffer[0].messages[0] == "No errors"
        context = self.get_context(bot, user_id)
        assert context.topic == ErrorCaseSkill.topic
        assert context.data["context_status"] == "valid"
        message_log = self.get_last_messagelog(bot, user_id)
        assert message_log.error is None

        # error in skill
        bot.response_buffer.clear()
        bot.process_events([{
            "text": "error skill",
            "source_id": user_id
        }])
        assert len(bot.response_buffer) == 0
        context = self.get_context(bot, user_id)
        assert context.topic is None
        assert context.data == {}
        message_log = self.get_last_messagelog(bot, user_id)
        assert json.loads(message_log.error)["message"] == "Error in skill"

        # no error occures (again)
        bot.response_buffer.clear()
        bot.process_events([{
            "text": "error noerror",
            "source_id": user_id
        }])
        assert len(bot.response_buffer) == 1
        assert bot.response_buffer[0].messages[0] == "No errors"
        context = self.get_context(bot, user_id)
        assert context.topic == ErrorCaseSkill.topic
        assert context.data["context_status"] == "valid"
        message_log = self.get_last_messagelog(bot, user_id)
        assert message_log.error is None

        # error in process_response
        bot.process_response = None     # make process_response not callable
        bot.response_buffer.clear()
        bot.process_events([{
            "text": "error process_response",
            "source_id": user_id
        }])
        assert len(bot.response_buffer) == 0
        context = self.get_context(bot, user_id)
        assert context.topic is None
        assert context.data == {}
        message_log = self.get_last_messagelog(bot, user_id)
        assert json.loads(message_log.error)["message"] ==\
            "'NoneType' object is not callable"

    def test_process_events_multiturn(self, bot):
        # start topic
        bot.process_events([{
            "text": "multi_turn",
            "source_id": existing_user_id
        }])
        assert bot.response_buffer[-1].messages[0] == "first turn"

        # continue topic
        bot.process_events([{
            "text": "continue",
            "source_id": existing_user_id
        }])
        assert bot.response_buffer[-1].messages[0] == "turn 2"

        # continue topic (again)
        bot.process_events([{
            "text": "continue",
            "source_id": existing_user_id
        }])
        assert bot.response_buffer[-1].messages[0] == "turn 3"

        # end topic
        bot.process_events([{
            "text": "end",
            "source_id": existing_user_id
        }])
        assert bot.response_buffer[-1].messages[0] == "end"

        # try to continue topic (no topic)
        bot.process_events([{
            "text": "continue",
            "source_id": existing_user_id
        }])
        assert len(bot.response_buffer) == 4

        # start topic again
        bot.process_events([{
            "text": "multi_turn",
            "source_id": existing_user_id
        }])
        assert bot.response_buffer[-1].messages[0] == "first turn"

        # continue topic
        bot.process_events([{
            "text": "continue",
            "source_id": existing_user_id
        }])
        assert bot.response_buffer[-1].messages[0] == "turn 2"

        # continue topic (again)
        bot.process_events([{
            "text": "continue",
            "source_id": existing_user_id
        }])
        assert bot.response_buffer[-1].messages[0] == "turn 3"

        # error
        bot.process_events([{
            "text": "err",
            "source_id": existing_user_id
        }])
        assert len(bot.response_buffer) == 7

        # try to continue topic (no topic)
        bot.process_events([{
            "text": "continue",
            "source_id": existing_user_id
        }])
        assert len(bot.response_buffer) == 7

    def test_process_events_messagelog(self, bot):
        user_id = str(uuid4())
        messages = [
            "multi_turn",
            "continue 1",
            "continue 2",
            "end",
            "multi_turn",
            "continue 3",
            "err",
        ]

        bot.process_events(
            [
                {
                    "text": m,
                    "source_id": user_id
                } for m in messages
            ]
        )

        db = bot.db_session()
        try:
            message_logs = db.query(MessageLog).\
                filter(MessageLog.source_id == user_id).\
                order_by(MessageLog.updated_at).all()

            for i, ml in enumerate(message_logs):
                assert ml.request["event"]["text"] == messages[i]
                context_on_start = json.loads(ml.context_on_start)["data"]
                context_on_end = json.loads(ml.context_on_end)["data"]
                user_on_start = json.loads(ml.user_on_start)["data"]
                user_on_end = json.loads(ml.user_on_end)["data"]

                if i == 0:
                    assert context_on_start == {}
                    assert context_on_end == {"count": 1}
                    assert user_on_start == {}
                    assert user_on_end == {"myid": user_id}

                elif i == 1:
                    assert context_on_start == {"count": 1}
                    assert context_on_end == {"count": 2}
                    assert user_on_start == {"myid": user_id}
                    assert user_on_end == {"myid": user_id}

                elif i == 2:
                    assert context_on_start == {"count": 2}
                    assert context_on_end == {"count": 3}
                    assert user_on_start == {"myid": user_id}
                    assert user_on_end == {"myid": user_id}

                elif i == 3:
                    assert context_on_start == {"count": 3}
                    assert context_on_end == {}
                    assert user_on_start == {"myid": user_id}
                    assert user_on_end == {"myid": user_id}

                elif i == 4:
                    assert context_on_start == {}
                    assert context_on_end == {"count": 1}
                    assert user_on_start == {"myid": user_id}
                    assert user_on_end == {"myid": user_id}

                elif i == 5:
                    assert context_on_start == {"count": 1}
                    assert context_on_end == {"count": 2}
                    assert user_on_start == {"myid": user_id}
                    assert user_on_end == {"myid": user_id}

                elif i == 6:
                    assert context_on_start == {"count": 2}
                    assert context_on_end == {}
                    assert user_on_start == {"myid": user_id}
                    assert user_on_end == {"myid": user_id}
                    assert json.loads(ml.error)["message"] == \
                        "error occured in process_request"

        finally:
            db.close()

    def test_process_events_custom_messagelog(self, bot):
        class MyMessageLog(MessageLog):
            @property
            def context_on_start(self):
                super().context_on_start()

            # override not to set serialized value
            @context_on_start.setter
            def context_on_start(self, value):
                self.__context_on_start = None

        user_id = str(uuid4())
        db = bot.db_session()
        try:
            bot.process_events([{"text": "ml test", "source_id": user_id}])
            message_log = db.query(MessageLog).\
                filter(MessageLog.source_id == user_id).\
                order_by(desc(MessageLog.updated_at)).first()
            # confirm that context_on_start is saved
            assert json.loads(message_log.context_on_start)["id"] == user_id

            # change message log class to mute context_on_start
            bot.message_log_class = MyMessageLog
            bot.process_events([{"text": "ml test", "source_id": user_id}])
            my_message_log = db.query(MessageLog).\
                filter(MessageLog.source_id == user_id).\
                order_by(desc(MessageLog.updated_at)).first()
            # confirm that context_on_start is not saved
            assert my_message_log.context_on_start is None

        finally:
            db.close()
