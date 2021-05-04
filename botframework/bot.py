from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import json
from logging import getLogger
from time import time
import traceback
from .models import Context, MessageLog, User, Request, Response


class BotBase(ABC):
    skills = []
    request_class = Request
    response_class = Response
    message_log_class = MessageLog

    def __init__(self, *, db_session_maker=None, logger=None,
                 threads=None, context_timeout=300):
        self.db_session = db_session_maker
        self.logger = logger or getLogger(__name__)
        self.executor = ThreadPoolExecutor(
            max_workers=threads, thread_name_prefix="LineEvent"
        )
        self.context_timeout = context_timeout
        self.__skills = {s.topic: s for s in self.skills}
        if len(self.__skills) == 0:
            self.logger.warning("No skills has been registered yet.")

    def register_skill(self, skill):
        self.skills.append(skill)
        self.__skills[skill.topic] = skill

    def get_context(self, db, request):
        # get or create context
        context = db.query(Context).\
            filter(Context.id == request.source_id).first()

        if not context:
            context = Context(id=request.source_id, data={})
            db.add(context)
            db.flush()
        else:
            gap = datetime.utcnow() - context.updated_at
            if gap.total_seconds() > self.context_timeout:
                context.clear()

        return context

    def get_user(self, db, request, update_profile=True):
        # get or create user
        user = db.query(User).\
            filter(User.id == request.source_id).first()

        if not user:
            user = User(id=request.source_id, data={})
            db.add(user)
            db.flush()

        return user

    @abstractmethod
    def extract_intent(self, request, user, context):
        pass

    def route(self, request, user, context):
        if request.intent in self.__skills:
            # set topic to start skill match to intent
            skill = self.__skills[request.intent]
            context.clear()
            context.topic = skill.topic

        if context.topic in self.__skills:
            # start or continue skill match to topic
            return self.__skills[context.topic](self)

    @abstractmethod
    def process_response(self, request, user, context, response):
        pass

    def process_events(self, events):
        try:
            db = self.db_session()
        except Exception as ex:
            self.logger.error(
                "Error in connecting to database: "
                + f"{str(ex)}\n{traceback.format_exc()}"
            )
            return

        for event in events:
            start_time = time()
            message_log = self.message_log_class()
            context = None
            user = None

            try:
                # parse event to request
                request = self.request_class.from_event(event)
                message_log.request = request

                # get context
                context = self.get_context(db, request)
                message_log.context_on_start = context

                # get user
                user = self.get_user(db, request)
                message_log.user_on_start = user

                # extract intent
                intent_entities = self.extract_intent(request, user, context)
                if isinstance(intent_entities, tuple):
                    request.intent, request.entities = intent_entities
                else:
                    request.intent = intent_entities
                    request.entities = {}
                message_log.intent = request.intent
                message_log.entities = request.entities

                # route to skill
                skill = self.route(request, user, context)
                if skill is None:
                    self.logger.info("No skill found")
                    continue

                # execute skill
                response = skill.process_request(request, user, context)
                if not isinstance(response, self.response_class):
                    response = self.response_class(response)
                message_log.response = response

                # process response
                self.process_response(request, user, context, response)

                # clear context
                if response.end_session:
                    context.clear()

            except Exception as ex:
                self.logger.error(
                    "Error in processing event: "
                    + f"{str(ex)}\n{traceback.format_exc()}"
                )
                message_log.error = json.dumps(
                    {"message": str(ex), "trace": traceback.format_exc()}
                )
                if context:
                    # clear context on error
                    context.clear()

            finally:
                try:
                    # serialize context and user to save in database
                    if context is not None:
                        context.serialize_data()
                        message_log.context_on_end = context
                    if user is not None:
                        user.serialize_data()
                        message_log.user_on_end = user

                    # message log
                    message_log.response_time =\
                        int((time() - start_time) * 1000)
                    db.add(message_log)

                    db.commit()

                except Exception as ex:
                    self.logger.error(
                        "Error in storing data: "
                        + f"{str(ex)}\n{traceback.format_exc()}"
                    )

                    db.rollback()

        db.close()

    def enqueue_events(self, events):
        self.executor.submit(self.process_events, events)
