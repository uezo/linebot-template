from datetime import datetime
from uuid import uuid4
import json
from avril.models import Context, User, Request, Response, MessageLog


class TestContext:
    def test_init(self):
        context_id = str(uuid4())

        context = Context(id=context_id)
        assert context.id == context_id
        assert context.updated_at is None

        context_serialized_data_none = Context(id=context_id)
        assert context_serialized_data_none.serialized_data is None
        assert context_serialized_data_none.data == {}

        context_serialized_data_str = Context(id=context_id)
        assert context_serialized_data_str.serialized_data is None
        context_serialized_data_str.serialized_data = '{"key1": "val1"}'
        assert context_serialized_data_str.data == {"key1": "val1"}

        context_data_dict = Context(id=context_id)
        assert context_data_dict.serialized_data is None
        context_data_dict.data = {"key1": "val1"}
        assert context_data_dict.serialized_data == '{"key1": "val1"}'
        assert context_data_dict.data == {"key1": "val1"}

    def test_to_dict(self):
        context_id = str(uuid4())

        context_data_to_dict = Context(id=context_id)
        context_data_to_dict.topic = "test_topic"
        context_data_to_dict.data = {"key1": "val1"}
        d = context_data_to_dict.to_dict()
        assert d["id"] == context_id
        assert d["updated_at"] is not None
        assert d["topic"] == "test_topic"
        assert d["data"] == {"key1": "val1"}

    def test_to_json(self):
        context_id = str(uuid4())

        context_data_to_json = Context(id=context_id)
        context_data_to_json.topic = "test_topic"
        context_data_to_json.data = {"key1": "val1"}
        d = json.loads(context_data_to_json.to_json())
        assert d["id"] == context_id
        assert d["updated_at"] is not None
        assert d["topic"] == "test_topic"
        assert d["data"] == {"key1": "val1"}


class TestUser:
    def test_init(self):
        user_id = str(uuid4())

        user = User(id=user_id)
        assert user.id == user_id
        assert user.updated_at is None

        user_serialized_data_none = User(id=user_id)
        assert user_serialized_data_none.serialized_data is None
        assert user_serialized_data_none.data == {}

        user_serialized_data_str = User(id=user_id)
        assert user_serialized_data_str.serialized_data is None
        user_serialized_data_str.serialized_data = '{"key1": "val1"}'
        assert user_serialized_data_str.data == {"key1": "val1"}

        user_data_dict = User(id=user_id)
        assert user_data_dict.serialized_data is None
        user_data_dict.data = {"key1": "val1"}
        assert user_data_dict.serialized_data == '{"key1": "val1"}'
        assert user_data_dict.data == {"key1": "val1"}

    def test_to_dict(self):
        user_id = str(uuid4())

        user = User(id=user_id)
        user.display_name = "うえぞう"
        user.language = "ja"
        user.picture_url = "https://imgurl/"
        user.status_message = "status message"
        user.data = {"key1": "val1"}
        d = user.to_dict()
        assert d["id"] == user_id
        assert d["updated_at"] is not None
        assert d["display_name"] == user.display_name
        assert d["language"] == user.language
        assert d["picture_url"] == user.picture_url
        assert d["status_message"] == user.status_message
        assert d["data"] == {"key1": "val1"}

    def test_to_json(self):
        user_id = str(uuid4())

        user = User(id=user_id)
        user.display_name = "うえぞう"
        user.language = "ja"
        user.picture_url = "https://imgurl/"
        user.status_message = "status message"
        user.data = {"key1": "val1"}
        d = json.loads(user.to_json())
        assert d["id"] == user_id
        assert d["updated_at"] is not None
        assert d["display_name"] == user.display_name
        assert d["language"] == user.language
        assert d["picture_url"] == user.picture_url
        assert d["status_message"] == user.status_message
        assert d["data"] == {"key1": "val1"}


class TestRequest:
    def test_init(self):
        request = Request()
        assert request.event is None
        assert request.source_id is None
        assert request.source_type is None
        assert isinstance(request.timestamp, datetime)
        assert request.intent is None
        assert request.entities == {}

    def test_init_with_args(self):
        request = Request(
            event={"key1": "value1"},
            source_id="user_id",
            source_type="user",
            timestamp=datetime(2021, 1, 23, 4, 56, 7),
            intent="weather",
            entities={"location": "tokyo"}
        )
        assert request.event == {"key1": "value1"}
        assert request.source_id == "user_id"
        assert request.source_type == "user"
        assert request.timestamp.year == 2021
        assert request.timestamp.month == 1
        assert request.timestamp.day == 23
        assert request.timestamp.hour == 4
        assert request.timestamp.minute == 56
        assert request.timestamp.second == 7
        assert request.intent == "weather"
        assert request.entities == {"location": "tokyo"}

    def test_from_event(self):
        event = {
            "source_id": "user_id",
            "source_type": "user",
            "timestamp": datetime(2021, 1, 23, 4, 56, 7),
            "intent": "weather",
            "entities": {"location": "tokyo"}
        }
        request = Request.from_event(event)
        assert isinstance(request, Request)
        assert request.event == event
        assert request.source_id == event["source_id"]
        assert request.source_type == event["source_type"]
        assert request.timestamp == event["timestamp"]
        assert request.intent == event["intent"]
        assert request.entities == event["entities"]

    def test_to_dict(self):
        request = Request(
            event={"key1": "value1"},
            source_id="user_id",
            source_type="user",
            timestamp=datetime(2021, 1, 23, 4, 56, 7),
            intent="weather",
            entities={"location": "tokyo"}
        )
        d = request.to_dict()
        assert isinstance(d, dict)
        assert d["event"] == request.event
        assert d["source_id"] == request.source_id
        assert d["source_type"] == request.source_type
        assert d["timestamp"] == int(request.timestamp.timestamp())
        assert d["intent"] == request.intent
        assert d["entities"] == request.entities

    def test_to_json(self):
        request = Request(
            event={"key1": "value1"},
            source_id="user_id",
            source_type="user",
            timestamp=datetime(2021, 1, 23, 4, 56, 7),
            intent="weather",
            entities={"location": "tokyo"}
        )
        d = json.loads(request.to_json())
        assert isinstance(d, dict)
        assert d["event"] == request.event
        assert d["source_id"] == request.source_id
        assert d["source_type"] == request.source_type
        assert d["timestamp"] == int(request.timestamp.timestamp())
        assert d["intent"] == request.intent
        assert d["entities"] == request.entities


class TestResponse:
    def test_init(self):
        response = Response()
        assert response.messages == []
        assert response.end_session is True

    def test_init_with_args(self):
        response = Response(
            messages=["message_1", "message_2"],
            end_session=False
        )
        assert response.messages == ["message_1", "message_2"]
        assert response.end_session is False

        response_not_message_list = Response(
            messages="message",
            end_session=True
        )
        assert response_not_message_list.messages == ["message"]
        assert response_not_message_list.end_session is True

    def test_to_dict(self):
        response = Response(
            messages=["message_1", "message_2"],
            end_session=False
        )
        d = response.to_dict()
        assert isinstance(d, dict)
        assert d["messages"] == response.messages
        assert d["end_session"] == response.end_session

    def test_to_json(self):
        response = Response(
            messages=["message_1", "message_2"],
            end_session=False
        )
        d = json.loads(response.to_json())
        assert d["messages"] == response.messages
        assert d["end_session"] == response.end_session


class TestMessageLog:
    def test_init(self):
        message_log = MessageLog()
        assert message_log.id is None
        assert message_log.updated_at is None
        assert message_log.response_time is None
        assert message_log.error is None

        # properties
        assert message_log.request is None
        assert message_log.response is None
        assert message_log.context_on_start is None
        assert message_log.context_on_end is None
        assert message_log.user_on_start is None
        assert message_log.user_on_end is None

    def test_getter_setters(self):
        message_log = MessageLog()

        request = Request(
            event={"key1": "value1"},
            source_id="user_id",
            source_type="user",
            timestamp=datetime(2021, 1, 23, 4, 56, 7),
            intent="weather",
            entities={"location": "tokyo"}
        )
        message_log.request = request
        assert message_log.request["event"] == request.event
        assert message_log.source_id == request.source_id

        message_log.intent = request.intent
        message_log.entities = request.entities
        assert message_log.intent == request.intent
        assert message_log.entities == json.dumps(request.entities)

        response = Response(
            messages=["message_1", "message_2"],
            end_session=False
        )
        message_log.response = response
        assert message_log.response["messages"] == response.messages
        assert message_log.response["end_session"] == response.end_session

        # create context
        context = Context(
            id=str(uuid4()),
            data={"key1": "value1", "key2": "value2"}
        )
        message_log.context_on_start = context
        assert isinstance(message_log.context_on_start, str)
        d = json.loads(message_log.context_on_start)
        assert d["id"] == context.id
        assert d["data"] == context.data

        # update context and set on_end
        context.data["key1"] = "value1 update"
        context.data["key3"] = "value3"
        message_log.context_on_end = context

        # confirm on_start is not updated and on_end is updated
        d_start = json.loads(message_log.context_on_start)
        assert d_start["id"] == context.id
        assert d_start["data"] == {"key1": "value1", "key2": "value2"}
        d_end = json.loads(message_log.context_on_end)
        assert d_end["id"] == context.id
        assert d_end["data"] == {
            "key1": "value1 update", "key2": "value2", "key3": "value3"
        }

        # create user
        user = User(
            id=str(uuid4()),
            data={"key1": "value1", "key2": "value2"}
        )
        message_log.user_on_start = user
        assert isinstance(message_log.user_on_start, str)
        d = json.loads(message_log.user_on_start)
        assert d["id"] == user.id
        assert d["data"] == user.data

        # update context and set on_end
        user.data["key1"] = "value1 update"
        user.data["key3"] = "value3"
        message_log.user_on_end = user

        # confirm on_start is not updated and on_end is updated
        d_start = json.loads(message_log.user_on_start)
        assert d_start["id"] == user.id
        assert d_start["data"] == {"key1": "value1", "key2": "value2"}
        d_end = json.loads(message_log.user_on_end)
        assert d_end["id"] == user.id
        assert d_end["data"] == {
            "key1": "value1 update", "key2": "value2", "key3": "value3"
        }

        assert isinstance(message_log.user_on_start_as_dict, dict)
        assert message_log.user_on_start_as_dict ==\
            json.loads(message_log.user_on_start)
        assert MessageLog().user_on_start_as_dict is None
