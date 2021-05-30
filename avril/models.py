from datetime import datetime
import json
from uuid import uuid4
from sqlalchemy import INT, NVARCHAR, Column, DateTime
from sqlalchemy.ext.declarative import declarative_base


# base class of models. every models extend this class
Base = declarative_base()


def create_all(engine):
    Base.metadata.create_all(bind=engine)


def get_uuid():
    return str(uuid4())


class State(Base):
    __tablename__ = "states"
    id = Column("id", NVARCHAR(255), default=get_uuid, primary_key=True)
    updated_at = Column("updated_at", DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)
    topic = Column("topic", NVARCHAR(255))
    serialized_data = Column("data", NVARCHAR(), nullable=False)
    __data = None

    @property
    def data(self):
        if self.__data is None:
            if not self.serialized_data:
                self.serialized_data = json.dumps({})
            self.__data = json.loads(self.serialized_data)
        return self.__data

    @data.setter
    def data(self, value):
        self.serialized_data = json.dumps(value)
        self.__data = value

    def serialize_data(self):
        self.serialized_data = json.dumps(self.data)

    def to_dict(self):
        return {
            "id": self.id,
            "updated_at": int(
                self.updated_at.timestamp()
                if self.updated_at is not None
                else datetime.utcnow().timestamp()
            ),
            "topic": self.topic,
            "data": self.data
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    def clear(self):
        self.topic = None
        self.data = {}


class User(Base):
    __tablename__ = "users"
    id = Column("id", NVARCHAR(255), primary_key=True)
    updated_at = Column("updated_at", DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)
    display_name = Column("display_name", NVARCHAR(255))
    language = Column("language", NVARCHAR(255))
    picture_url = Column("picture_url", NVARCHAR(255))
    status_message = Column("status_message", NVARCHAR(255))
    serialized_data = Column("data", NVARCHAR(), nullable=False)
    __data = None

    @property
    def data(self):
        if self.__data is None:
            if not self.serialized_data:
                self.serialized_data = json.dumps({})
            self.__data = json.loads(self.serialized_data)
        return self.__data

    @data.setter
    def data(self, value):
        self.serialized_data = json.dumps(value)
        self.__data = value

    def serialize_data(self):
        self.serialized_data = json.dumps(self.data)

    def to_dict(self):
        return {
            "id": self.id,
            "updated_at": int(
                self.updated_at.timestamp()
                if self.updated_at is not None
                else datetime.utcnow().timestamp()
            ),
            "display_name": self.display_name,
            "language": self.language,
            "picture_url": self.picture_url,
            "status_message": self.status_message,
            "data": self.data
        }

    def to_json(self):
        return json.dumps(self.to_dict())


class Request:
    def __init__(self, event=None, source_id=None, source_type=None,
                 timestamp=None, intent=None, entities=None):
        self.event = event
        self.source_id = source_id
        self.source_type = source_type
        self.timestamp = timestamp or datetime.utcnow()
        self.intent = intent
        self.entities = entities if entities is not None else {}

    @classmethod
    def from_event(cls, event):
        return cls(
            event=event,
            source_id=event.get("source_id"),
            source_type=event.get("source_type"),
            timestamp=event.get("timestamp"),
            intent=event.get("intent"),
            entities=event.get("entities")
        )

    def to_dict(self):
        return {
            "event": self.event,
            "source_id": self.source_id,
            "source_type": self.source_type,
            "timestamp": int(self.timestamp.timestamp()),
            "intent": self.intent,
            "entities": self.entities
        }

    def to_json(self):
        return json.dumps(self.to_dict())


class Response:
    def __init__(self, messages=None, end_session=True):
        if not messages:
            messages = []
        elif not isinstance(messages, (list, tuple)):
            messages = [messages]
        self.messages = messages
        self.end_session = end_session

    def to_dict(self):
        return {
            "messages": self.messages,
            "end_session": self.end_session
        }

    def to_json(self):
        return json.dumps(self.to_dict())


class MessageLog(Base):
    __tablename__ = "messagelogs"
    id = Column("id", NVARCHAR(255), default=get_uuid, primary_key=True)
    updated_at = Column("updated_at", DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow, index=True)
    source_id = Column("source_id", NVARCHAR(255), index=True)
    response_time = Column("response_time", INT, index=True)
    __request = Column("request", NVARCHAR())
    __response = Column("response", NVARCHAR())
    intent = Column("intent", NVARCHAR(255))
    __entities = Column("entities", NVARCHAR())
    __state_on_start = Column("state_on_start", NVARCHAR())
    __state_on_end = Column("state_on_end", NVARCHAR())
    __user_on_start = Column("user_on_start", NVARCHAR())
    __user_on_end = Column("user_on_end", NVARCHAR())
    error = Column("error", NVARCHAR())

    @property
    def request(self):
        if not self.__request:
            return None
        return json.loads(self.__request)

    @request.setter
    def request(self, value):
        self.__request = value.to_json()
        self.source_id = value.source_id

    @property
    def response(self):
        if not self.__response:
            return None
        return json.loads(self.__response)

    @response.setter
    def response(self, value):
        self.__response = value.to_json()

    @property
    def entities(self):
        return self.__entities

    @entities.setter
    def entities(self, value):
        self.__entities = json.dumps(value)

    @property
    def state_on_start(self):
        return self.__state_on_start

    @state_on_start.setter
    def state_on_start(self, value):
        self.__state_on_start = value.to_json()

    @property
    def state_on_end(self):
        return self.__state_on_end

    @state_on_end.setter
    def state_on_end(self, value):
        self.__state_on_end = value.to_json()

    @property
    def user_on_start(self):
        return self.__user_on_start

    @user_on_start.setter
    def user_on_start(self, value):
        self.__user_on_start = value.to_json()

    @property
    def user_on_start_as_dict(self):
        if not self.__user_on_start:
            return None
        return json.loads(self.__user_on_start)

    @property
    def user_on_end(self):
        return self.__user_on_end

    @user_on_end.setter
    def user_on_end(self, value):
        self.__user_on_end = value.to_json()
