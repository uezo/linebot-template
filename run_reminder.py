import os
from configparser import ConfigParser
from flask import Flask, request
from linebot import LineBotApi, WebhookParser
from database import Database
from avril.models import create_all
from avril.controllers import conversation_history_bp
from examples.reminder import ReminderBot
from examples.reminder.workers.notifier import start_notifier_thread

# load config
config = ConfigParser()
config.read(os.getenv("AVRIL_CONFIG_PATH", "./config.ini"))

# create db
db = Database(config["DATABASE"]["connection_string"])

# create and configure app
app = Flask(__name__)
app.bot = ReminderBot(
    line_api=LineBotApi(config["LINE_API"]["channel_access_token"]),
    line_parser=WebhookParser(config["LINE_API"]["channel_secret"]),
    db_session_maker=db.session, logger=app.logger)
app.register_blueprint(conversation_history_bp)


@app.route("/bot/webhook_handler", methods=["POST"])
def handle_webhook():
    # put webhook request data to queue
    app.bot.enqueue_webhook(
        request.data.decode("utf-8"),
        request.headers.get("X-Line-Signature")
    )

    # return immediately
    return "ok"


if __name__ == "__main__":
    # create tables
    create_all(db.engine)

    # run push notification worker
    start_notifier_thread(app.bot)

    # start app
    app.run(host="0.0.0.0", port=12345)
