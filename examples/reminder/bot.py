import urllib.parse
from avril.channels.line import LineBotBase
from .skills import (
    ReminderRegisterSkill,
    ReminderListSkill,
    ReminderDeleteSkill
)


# チャットボット本体
class ReminderBot(LineBotBase):
    skills = [ReminderRegisterSkill, ReminderListSkill, ReminderDeleteSkill]

    def extract_intent(self, request, user, state):
        # メッセージイベント
        if request.event.type == "message":
            if request.event.message.type == "text":
                if request.event.message.text == "一覧":
                    return ReminderListSkill.topic
                if request.event.message.text == "新規":
                    return ReminderRegisterSkill.topic, {"remind_text": None}
                if not state.topic:
                    # 進行中のトピックがない場合は常に新規登録スキル
                    return ReminderRegisterSkill.topic, {"remind_text": request.event.message.text}

            elif request.event.message.type == "image":
                # 【やってみよう】画像をリマインダー登録＆通知する仕組みを作ってみると理解が深まると思います
                print(request.event.message)

        # ポストバックイベント
        if request.event.type == "postback":
            # dictにパースしたデータを追加
            request.event.postback.data_as_dict = \
                urllib.parse.parse_qs(request.event.postback.data)
            if request.event.postback.data_as_dict.get("item_id_to_delete"):
                # 削除対象のIDがセットされている場合は削除スキル
                return ReminderDeleteSkill.topic
