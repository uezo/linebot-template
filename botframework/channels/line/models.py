from linebot.models import SourceGroup, SourceRoom, SourceUser, TextSendMessage
from ...models import Request, Response


class LineRequest(Request):
    @classmethod
    def from_event(cls, event):
        if isinstance(event.source, SourceUser):
            source_id = event.source.user_id
            source_type = "user"
        elif isinstance(event.source, SourceRoom):
            source_id = event.source.room_id
            source_type = "room"
        elif isinstance(event.source, SourceGroup):
            source_id = event.source.group_id
            source_type = "group"
        else:
            raise Exception("Unknown source")

        return cls(event=event, source_id=source_id, source_type=source_type)

    def to_dict(self):
        d = super().to_dict()
        d["event"] = self.event.as_json_dict()
        return d


class LineResponse(Response):
    def __init__(self, messages=None, end_session=True):
        super().__init__(messages, end_session)
        self.messages = [
            TextSendMessage(text=m) if isinstance(m, str) else m
            for m in self.messages
        ]

    def to_dict(self):
        d = super().to_dict()
        d["messages"] = [m.as_json_dict() for m in self.messages]
        return d
