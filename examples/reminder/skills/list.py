from datetime import timedelta
from linebot.models import FlexSendMessage
from avril import SkillBase
from ..crud import RemindRepository


class ReminderListSkill(SkillBase):
    topic = "ReminderList"

    def get_item_bubble(self, item_id, remind_at, remind_text):
        return {
            "type": "bubble",
            "size": "micro",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": remind_at.strftime("%m/%d %H:%M"),
                        "color": "#ffffff",
                        "align": "start",
                        "size": "md",
                        "gravity": "center"
                    },
                ],
                "backgroundColor": "#27ACB2",
                "paddingAll": "8px",
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": remind_text,
                        "color": "#333333",
                        "size": "md",
                        "wrap": True
                    }
                ],
                "paddingAll": "8px",
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "0px",
                "contents": [
                    {
                        "type": "button",
                        "style": "link",
                        "height": "sm",
                        "action": {
                            "type": "postback",
                            "label": "削除",
                            "data": f"item_id_to_delete={item_id}"
                        },
                    },
                ],
            },
            "styles": {
                "footer": {
                    "separator": True
                }
            }
        }

    def process_request(self, request, user, state):
        db = self.db_session()
        try:
            items = RemindRepository.get_items(db, user.id)
            if not items:
                return "未通知のリマインダーはありません"
            else:
                # UTC+9時間の補正は本当はユーザーのタイムゾーンを使いましょうね
                return FlexSendMessage(
                    alt_text="リマインダー項目一覧",
                    contents={
                        "type": "carousel",
                        "contents": [self.get_item_bubble(item.id, item.remind_at + timedelta(hours=9), item.remind_text) for item in items]
                    }
                )
        finally:
            db.close()
