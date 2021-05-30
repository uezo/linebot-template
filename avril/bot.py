from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import json
from logging import getLogger
from time import time
import traceback
from .models import State, MessageLog, User, Request, Response


class BotBase(ABC):
    skills = []
    request_class = Request
    response_class = Response
    message_log_class = MessageLog

    def __init__(self, *, db_session_maker=None, logger=None,
                 threads=None, state_timeout=300):
        self.db_session = db_session_maker
        self.logger = logger or getLogger(__name__)
        self.executor = ThreadPoolExecutor(
            max_workers=threads, thread_name_prefix="LineEvent"
        )
        self.state_timeout = state_timeout
        self.__skills = {s.topic: s for s in self.skills}
        if len(self.__skills) == 0:
            self.logger.warning("No skills has been registered yet.")

    def register_skill(self, skill):
        self.skills.append(skill)
        self.__skills[skill.topic] = skill

    def get_state(self, db, request):
        # get or create state
        state = db.query(State).\
            filter(State.id == request.source_id).first()

        if not state:
            state = State(id=request.source_id, data={})
            db.add(state)
            db.flush()
        else:
            gap = datetime.utcnow() - state.updated_at
            if gap.total_seconds() > self.state_timeout:
                state.clear()

        return state

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
    def extract_intent(self, request, user, state):
        pass

    def route(self, request, user, state):
        if request.intent in self.__skills:
            # set topic to start skill match to intent
            skill = self.__skills[request.intent]
            state.clear()
            state.topic = skill.topic

        if state.topic in self.__skills:
            # start or continue skill match to topic
            return self.__skills[state.topic](self)

    @abstractmethod
    def process_response(self, request, user, state, response):
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
            state = None
            user = None

            try:
                # parse event to request
                request = self.request_class.from_event(event)
                message_log.request = request

                # get state
                state = self.get_state(db, request)
                message_log.state_on_start = state

                # get user
                user = self.get_user(db, request)
                message_log.user_on_start = user

                # extract intent
                intent_entities = self.extract_intent(request, user, state)
                if isinstance(intent_entities, tuple):
                    request.intent, request.entities = intent_entities
                else:
                    request.intent = intent_entities
                    request.entities = {}
                message_log.intent = request.intent
                message_log.entities = request.entities

                # route to skill
                skill = self.route(request, user, state)
                if skill is None:
                    self.logger.info("No skill found")
                    continue

                # execute skill
                response = skill.process_request(request, user, state)
                if not isinstance(response, self.response_class):
                    response = self.response_class(response)
                message_log.response = response

                # process response
                self.process_response(request, user, state, response)

                # clear state
                if response.end_session:
                    state.clear()

            except Exception as ex:
                self.logger.error(
                    "Error in processing event: "
                    + f"{str(ex)}\n{traceback.format_exc()}"
                )
                message_log.error = json.dumps(
                    {"message": str(ex), "trace": traceback.format_exc()}
                )
                if state:
                    # clear state on error
                    state.clear()

            finally:
                try:
                    # serialize state and user to save in database
                    if state is not None:
                        state.serialize_data()
                        message_log.state_on_end = state
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
