from configparser import ConfigParser
from uuid import uuid4
import pytest
from linebot import LineBotApi
from linebot.exceptions import LineBotApiError
from linebot.models import (MessageEvent, SourceGroup, SourceRoom, SourceUser,
                            TextMessage, TextSendMessage)
from botframework import SkillBase
from botframework.channels.line import LineBotBase, LineRequest, LineResponse
from botframework.models import create_all
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
    # customize line api client
    line_api = LineBotApi(config["LINE_API"]["channel_access_token"])
    line_api.reply_buffer = []
    def reply_message_to_buffer(
            reply_token, messages, notification_disabled=False, timeout=None):
        line_api.reply_buffer.extend(messages)
    line_api.reply_message = reply_message_to_buffer

    # create bot with line api client
    bot = BotForTest(
        line_api=line_api,
        line_parser=None,
        db_session_maker=Database(
            config["DATABASE"]["connection_string"]).session,
        context_timeout=5
    )

    return bot


class EchoSkill(SkillBase):
    topic = "Echo"

    def process_request(self, request, user, context):
        return "You said " + request.event.message.text


class BotForTest(LineBotBase):
    skills = [EchoSkill]

    def extract_intent(self, request, user, context):
        return EchoSkill.topic, {}


class TestLineRequest:
    def test_from_event(self):
        # user
        user_event = MessageEvent(
            message=TextMessage(text="message from user"),
            source=SourceUser("user_id"))
        user_request = LineRequest.from_event(user_event)
        assert user_request.source_id == user_event.source.user_id
        assert user_request.source_type == "user"
        assert user_request.event.message.text == user_event.message.text

        # group
        group_event = MessageEvent(
            message=TextMessage(text="message from group"),
            source=SourceGroup("group_id"))
        group_request = LineRequest.from_event(group_event)
        assert group_request.source_id == group_event.source.group_id
        assert group_request.source_type == "group"
        assert group_request.event.message.text == group_event.message.text

        # room
        room_event = MessageEvent(
            message=TextMessage(text="message from group"),
            source=SourceRoom("room_id"))
        room_request = LineRequest.from_event(room_event)
        assert room_request.source_id == room_event.source.room_id
        assert room_request.source_type == "room"
        assert room_request.event.message.text == room_event.message.text

        # none
        unknown_event = MessageEvent(
            message=TextMessage(text="message from unknown"),
            source=None)
        with pytest.raises(Exception):
            LineRequest.from_event(unknown_event)

    def test_to_dict(self):
        user_event = MessageEvent(
            message=TextMessage(text="message from user"),
            source=SourceUser("user_id"))
        user_request = LineRequest.from_event(user_event)

        d = user_request.to_dict()
        assert isinstance(d["event"], dict)
        assert d["event"]["message"]["text"] == user_event.message.text
        assert d["source_id"] == user_event.source.user_id
        assert d["source_type"] == "user"
        assert isinstance(d["timestamp"], int)
        assert d["intent"] is None
        assert d["entities"] == {}


class TestLineResponse:
    def test_init(self):
        text_1 = "text_1"
        text_2 = "text_2"
        message_1 = TextSendMessage(text="message_1")
        message_2 = TextSendMessage(text="message_2")

        text_response = LineResponse(messages=text_1)
        assert len(text_response.messages) == 1
        assert isinstance(text_response.messages[0], TextSendMessage)
        assert text_response.messages[0].text == text_1
        assert text_response.end_session is True

        text_list_messages = [text_1, text_2]
        text_list_response = LineResponse(messages=text_list_messages)
        assert len(text_list_response.messages) == 2
        for i, m in enumerate(text_list_response.messages):
            assert isinstance(m, TextSendMessage)
            assert m.text == text_list_messages[i]

        message_response = LineResponse(messages=message_1)
        assert len(message_response.messages) == 1
        assert isinstance(message_response.messages[0], TextSendMessage)
        assert message_response.messages[0].text == message_1.text

        message_list_messages = [message_1, message_2]
        message_list_response = LineResponse(messages=message_list_messages)
        assert len(message_list_response.messages) == 2
        for i, m in enumerate(message_list_response.messages):
            assert isinstance(m, TextSendMessage)
            assert m.text == message_list_messages[i].text

        mixed_messages = [text_1, message_1, text_2, message_2]
        mixed_response = LineResponse(messages=mixed_messages)
        assert len(mixed_response.messages) == 4
        for i, m in enumerate(mixed_response.messages):
            assert isinstance(m, TextSendMessage)
            if isinstance(mixed_messages[i], str):
                assert m.text == mixed_messages[i]
            else:
                assert m.text == mixed_messages[i].text

    def test_to_dict(self):
        text_1 = "text_1"
        text_response = LineResponse(messages=text_1)
        d = text_response.to_dict()
        assert isinstance(d["messages"], list)
        for m in d["messages"]:
            assert isinstance(m, dict)
            assert m["text"] == text_1
        assert d["end_session"] is True


class TestLineBotBase:
    def test_get_user(self, bot):
        db = bot.db_session()

        try:
            # get existing user
            user = bot.get_user(
                db,
                LineRequest.from_event(
                    MessageEvent(source=SourceUser(user_id=existing_user_id))
                )
            )

            # property is updated by line profile api
            assert user.display_name == existing_user_name

            # update data
            new_data = str(uuid4())
            user.data["uuid"] = new_data
            user.serialize_data()
            db.commit()

            # check the data is updated
            user = bot.get_user(
                db,
                LineRequest.from_event(
                    MessageEvent(source=SourceUser(user_id=existing_user_id))
                )
            )
            assert user.data["uuid"] == new_data

            # return None when event from group
            group = bot.get_user(
                db,
                LineRequest.from_event(
                    MessageEvent(source=SourceGroup(group_id="group_id"))
                )
            )
            assert group is None

            # error occures when unknown user
            with pytest.raises(LineBotApiError):
                bot.get_user(
                    db,
                    LineRequest.from_event(
                        MessageEvent(
                            source=SourceUser(user_id="unknown_user_id")
                        )
                    )
                )

        finally:
            db.close()

    def test_process_response(self, bot):
        # create LINE MessageEvents manually
        event_1 = MessageEvent(
            message=TextMessage(text="event_1"),
            source=SourceUser(user_id=existing_user_id))
        event_2 = MessageEvent(
            message=TextMessage(text="event_2"),
            source=SourceUser(user_id=existing_user_id))

        # process events and check the responses for them
        bot.process_events([event_1, event_2])
        assert len(bot.line_api.reply_buffer) == 2
        assert bot.line_api.reply_buffer[0].text == "You said event_1"
        assert bot.line_api.reply_buffer[1].text == "You said event_2"
