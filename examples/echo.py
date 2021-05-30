from avril import SkillBase
from avril.channels.line import LineBotBase, LineResponse


class EchoSkill(SkillBase):
    # configure topic name of this skill
    topic = "Echo"

    def process_request(self, request, user, state):
        # return what user said
        return request.event.message.text


class EchoBot(LineBotBase):
    # register skills that will be used in this bot
    skills = [EchoSkill]

    def extract_intent(self, request, user, state):
        # trigger EchoSkill everytime
        return EchoSkill.topic


class MultiTurnEchoSkill(SkillBase):
    topic = "MultiTurnEcho"

    def process_request(self, request, user, state):
        current_text = request.event.message.text
        last_text = state.data.get("last_text")
        state.data["last_text"] = current_text

        message = f"今回の発話：{current_text}"
        if last_text:
            message += f"\n前回の発話：{last_text}"

        return LineResponse(
            messages=message,
            end_session=False
        )


class MultiTurnEchoBot(LineBotBase):
    skills = [MultiTurnEchoSkill]

    def extract_intent(self, request, user, state):
        if not state.topic:
            return MultiTurnEchoSkill.topic
