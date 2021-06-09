from datetime import datetime
import traceback
import time
from concurrent.futures import ThreadPoolExecutor
import schedule
from linebot.models import TextSendMessage
from ..crud import RemindRepository


class RemindNotifier:
    def __init__(self, bot):
        self.bot = bot
        self.db_session = bot.db_session
        self.logger = bot.logger

    def notify(self):
        now = datetime.utcnow()
        db = self.db_session()
        try:
            items = RemindRepository.get_items_to_notify(db, now)
            for item in items:
                try:
                    self.bot.line_api.push_message(
                        to=item.remind_to,
                        messages=[
                            TextSendMessage(text=f"リマインド：\"{item.remind_text}\"")
                        ]
                    )
                    item.reminded = 1

                except Exception as ex:
                    self.bot.logger.error(f"Failed in sending message: {str(ex)}\n{traceback.format_exc()}")

                finally:
                    db.commit()

        except Exception as iex:
            self.bot.logger.error(f"Failed in getting items: {str(iex)}\n{traceback.format_exc()}")

        finally:
            db.close()


def start_notifier(bot):
    notifier = RemindNotifier(bot)
    schedule.every(1).minutes.do(notifier.notify)
    while True:
        schedule.run_pending()
        time.sleep(1)


def start_notifier_thread(bot):
    executor = ThreadPoolExecutor(
        max_workers=1, thread_name_prefix="NotifierThread")
    executor.submit(start_notifier, bot)
