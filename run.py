from configparser import ConfigParser
from flask import Flask, request
from linebot import LineBotApi, WebhookParser
from database import Database
from botframework.models import create_all
from botframework.controllers import message_log_bp
from examples.echo import EchoBot, MultiTurnEchoBot

# load config
config = ConfigParser()
config.read("./config.ini")

# create db
db = Database(config["DATABASE"]["connection_string"])

# create and configure app
app = Flask(__name__)
app.bot = EchoBot(
    line_api=LineBotApi(config["LINE_API"]["channel_access_token"]),
    line_parser=WebhookParser(config["LINE_API"]["channel_secret"]),
    db_session_maker=db.session, logger=app.logger)
app.register_blueprint(message_log_bp)


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

    # start app
    app.run(host="0.0.0.0", port=12345, debug=True)
