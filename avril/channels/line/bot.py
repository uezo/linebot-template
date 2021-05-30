from ...bot import BotBase
from ...models import HistoryVerbosity
from .models import LineRequest, LineResponse


class LineBotBase(BotBase):
    request_class = LineRequest
    response_class = LineResponse

    def __init__(self, *, line_api, line_parser,
                 db_session_maker=None, logger=None,
                 threads=None, state_timeout=300,
                 history_verbosity=HistoryVerbosity.All):
        super().__init__(
            db_session_maker=db_session_maker, logger=logger,
            threads=threads, state_timeout=state_timeout,
            history_verbosity=history_verbosity
        )
        self.line_api = line_api
        self.line_parser = line_parser

    def get_user(self, db, request, update_profile=True):
        if request.source_type == "user":
            user = super().get_user(db, request)
        else:
            return None

        if update_profile:
            # get user profile from line
            user_profile = self.line_api.get_profile(request.source_id)
            # update user
            user.display_name = user_profile.display_name
            user.language = user_profile.language
            user.picture_url = user_profile.picture_url
            user.status_message = user_profile.status_message

        return user

    def process_response(self, request, user, state, response):
        # send response to user
        if response.messages:
            self.line_api.reply_message(
                request.event.reply_token, response.messages
            )

    def process_webhook(self, data, signature):
        # parse events from webhook request with verifying signature
        events = self.line_parser.parse(data, signature)
        # process events
        self.process_events(events)

    def enqueue_webhook(self, data, signature):
        self.executor.submit(self.process_webhook, data, signature)
