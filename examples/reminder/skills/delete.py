from linebot.models import (
    PostbackAction, TextSendMessage,
    QuickReply, QuickReplyButton
)
from avril import SkillBase
from avril.channels.line import LineResponse
from ..crud import RemindRepository


class ReminderDeleteSkill(SkillBase):
    topic = "ReminderDelete"

    def get_quick_reply(self):
        return QuickReply(
            items=[
                QuickReplyButton(
                    action=PostbackAction(
                        label="OK",
                        display_text="OK",
                        data="ok"
                    )
                ),
                QuickReplyButton(
                    action=PostbackAction(
                        label="キャンセル",
                        display_text="キャンセル",
                        data="cancel")
                ),
            ]
        )

    def process_request(self, request, user, state):
        if request.intent == self.topic:
            # 削除対象は必ず初回ターンで特定
            item_id = request.event.postback.data_as_dict["item_id_to_delete"][0]
            db = self.db_session()
            try:
                item = RemindRepository.get_item(db, item_id, user.id)
                if item:
                    state.data["item_id"] = item_id
                    state.data["remind_text"] = item.remind_text
            finally:
                db.close()

        if request.event.type == "postback":
            # 削除処理はクイックリプライのボタン応答でのみ実行
            if request.event.postback.data == "ok":
                db = self.db_session()
                try:
                    RemindRepository.delete_item(db, state.data["item_id"], user.id)
                    state.data["deleted"] = True
                finally:
                    db.close()
            elif request.event.postback.data == "cancel":
                state.data["canceled"] = True

        # ステートの状態に応じて応答
        if state.data.get("canceled"):
            return "削除を中止しました"
        elif not state.data.get("item_id"):
            return "削除対象の項目が見つかりません"
        elif not state.data.get("deleted"):
            return LineResponse(
                messages=[
                    TextSendMessage(
                        text=f'\"{state.data["remind_text"]}\"を削除します。よろしいですか？',
                        quick_reply=self.get_quick_reply()
                    )
                ],
                end_session=False
            )
        else:
            return "削除しました"
