# linebot-template

A template to build LINE Bot extremely fast🚀

[🇯🇵日本語版はこちら](https://github.com/uezo/linebot-template/blob/main/README.ja.md)

# What's this? 🤔

This is a tiny LINE Bot project template with these features below:

- Multi-skills and Multi-turns support (State based routing)
- Scalable (Very essential)
- Continuous improvement support (Message logs)

# Quick Start

First of all, download or clone this repository and install dependencies. Run this command on the of project directory.

NOTE: You can change the directory name as you like before installing dependencies.

```bash
$ pip install -r requirements-dev.txt
```

Next, put your ChannelAccessToken and ChannelSecret in `config.ini`. You can also change `[DATABASE] > connection_string` now or later.

```ini
[LINE_API]
channel_access_token = YOUR_CHANNEL_ACCESS_TOKEN
channel_secret = YOUR_CHANNEL_SECRET

[DATABASE]
connection_string = sqlite:///linebot.db
```

Okay everything is done! Run `run.py` to start your bot.

```bash
$ python run.py
```

Don't forget to expose the webhook endpoint to the Internet with Ngrok or something if you runs bot on your PC, and put the given URL to LINE Developers.

```bash
$ ngrok http 12345
```

(conversation image)

I have one more thing to introduce to you. Access http://localhost:12345/admin/messagelog . You can see the conversation histories on your browser. This is a very powerful tool that helps you to monitor your chatbot is working as you expected and to debug with rich information.

(image)

Click timestamp to see detail information that must be useful for debugging.

(image)


# Building your chatbot

Before start building you may want to know the architecture of this template, especially event processing flow don't you? Okay, see the diagram below.

![linebot-template Event Processing Flow Diagram](https://uezo.blob.core.windows.net/github/linebot-template/flow.png)

In short, just implementing `YourBot.extract_intent` and `YourSkill(s).process_request` are needed to create your chatbot. Any other common features are ready as out of the box.

- `extract_intent` takes `Request`, `User` and `State`. You can get `Event` object from LINE API as `request.event`. Return intent as `str` and entities as `dict` if they are extracted.

```python
def extract_intent(self, request, user, state):
    if request.event.messages == "***":
        # intent and entities are extracted
        return "***", {"key1": "val1", "key2", "val2"}
    elif ... :
        # only intent is extracted
        return "***"
```

- `process_request` also takes `Request`, `User` and `State`. Process business logic, compose list of `Message` object to LINE API and return `Response` object with these messages. You can also return:
    - `str`
    - `Message`
    - `list` of `str`
    - `list` of `Message` and `str`

```python
def process_request(self, request, user, state):
    text = do_something()
    message = TextSendMessage(text=text)
    return Response(messages=[message])
    # 👇 also valid
    # return text
    # return message
    # return [text]
    # return [message]
```


## Echo bot

This is the simplest example for the bot that has only EchoSkill.

```python
from avril import SkillBase
from avril.channels.line import LineBotBase

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
```

## Multi-turn echo bot

If you want to continue topic and keep state next turn, set `end_session=False` to the response from your skill. This is the example of multi-turn echo, that shows current input and last input.

```python
from avril import SkillBase
from avril.channels.line import LineBotBase, LineResponse

class MultiTurnEchoSkill(SkillBase):
    topic = "MultiTurnEcho"

    def process_request(self, request, user, state):
        current_text = request.event.message.text
        last_text = state.data.get("last_text")
        state.data["last_text"] = current_text

        message = f"Current input: {current_text}"
        if last_text:
            message += f"\nLast input: {last_text}"

        return LineResponse(
            messages=message,
            end_session=False   # 👈 Add param not to clear state after this turn
        )

class MultiTurnEchoBot(LineBotBase):
    skills = [MultiTurnEchoSkill]

    def extract_intent(self, request, user, state):
        if not state.topic:   # 👈 Add condition not to trigger topic newly when the state is alive
            return MultiTurnEchoSkill.topic
```


## Multi-skill bot

📝🤔

## Multi-turn and Multi-skill bot

📝🤔


# Lifecycle of state

State is always cleared every turn by default but is kept as long as `end_session=False` is set to Response in your skill.

It will be cleared when:

- `end_session=True` is set to Response in your skill (by default, True is set)
- Timed out. 300 seconds after last update by default
- Intent bound to topic(skill) is extracted regardless that the topic is changed or not
- Exception is caught in `BotBase.process_events`


# Mute MessageLog

In case you don't want to save some data in message log for performance or security reasons, you can mute specific columns by using your own MessageLog class.

```python
class MyMessageLog(MessageLog):
    @property
    def state_on_start(self):
        super().state_on_start()

    # override not to set serialized value
    @state_on_start.setter
    def state_on_start(self, value):
        self.__state_on_start = None

class MyBot(LineBotBase):
    # Use custom message log class
    message_log_class = MyMessageLog
        : (省略)
```


# Testing

📝🤔

