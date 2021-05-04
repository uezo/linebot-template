# linebot-template

A template to build LINE Bot extremely fast🚀

# What's this? 🤔

This is a tiny LINE Bot project template with these features below:

- Multi-skills and Multi-turns support (Context based routing)
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

Click timestamp to see detail information that must be useful to debug your bot.

(image)


# Building your chatbot

Before start building you may want to know the architecture of this template, don't you? Okay, see the diagram below.

![linebot-template Architecture Overview](https://uezo.blob.core.windows.net/github/linebot-template/linebot-template-architecture.png)

In short, just implementing `YourBot.extract_intent` and `YourSkill(s).process_request` are needed to create your chatbot. Any other common features are ready as out of the box.

## Echo bot

This is the simplest example for the bot that has only EchoSkill.

```python
from botframework import SkillBase
from botframework.channels.line import LineBotBase

class EchoSkill(SkillBase):
    # configure topic name of this skill
    topic = "Echo"

    def process_request(self, request, user, context):
        # return what user said
        return request.event.message.text

class EchoBot(LineBotBase):
    # register skills that will be used in this bot
    skills = [EchoSkill]

    def extract_intent(self, request, user, context):
        # trigger EchoSkill everytime
        return EchoSkill.topic
```

## Multi-turn echo bot

If you want to continue topic and keep context next turn, set `end_session=False` to the response from your skill. This is the example of multi-turn echo, that shows current input and last input.

```python
from botframework import SkillBase
from botframework.channels.line import LineBotBase, LineResponse

class MultiTurnEchoSkill(SkillBase):
    topic = "MultiTurnEcho"

    def process_request(self, request, user, context):
        current_text = request.event.message.text
        last_text = context.data.get("last_text")
        context.data["last_text"] = current_text

        message = f"Current input: {current_text}"
        if last_text:
            message += f"\nLast input: {last_text}"

        return LineResponse(
            messages=message,
            end_session=False   # 👈 Add param not to clear context after this turn
        )

class MultiTurnEchoBot(LineBotBase):
    skills = [MultiTurnEchoSkill]

    def extract_intent(self, request, user, context):
        if not context.topic:   # 👈 Add condition not to trigger topic newly when the context is alive
            return MultiTurnEchoSkill.topic
```


## Multi-skill bot

📝🤔

## Multi-turn and Multi-skill bot

📝🤔


# Lifecycle of context

Context is always cleared every turn by default but is kept as long as `end_session=False` is set to Response in your skill.

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
    def context_on_start(self):
        super().context_on_start()

    # override not to set serialized value
    @context_on_start.setter
    def context_on_start(self, value):
        self.__context_on_start = None

class MyBot(LineBotBase):
    # Use custom message log class
    message_log_class = MyMessageLog
        : (省略)
```


# Testing

📝🤔

