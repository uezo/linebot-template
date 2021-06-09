from datetime import datetime, timedelta
from linebot.models import (
    DatetimePickerAction, PostbackAction, TextSendMessage,
    QuickReply, QuickReplyButton
)
from avril import SkillBase
from avril.channels.line import LineResponse
from ..crud import RemindRepository

# 画像リマインド！おもしろい


# リマインダー登録スキル
class ReminderRegisterSkill(SkillBase):
    topic = "ReminderRegister"

    def to_remind_at(self, dt, now):
        remind_at = datetime(
            now.year, now.month, now.day,
            dt.hour, dt.minute
        )
        if now > remind_at:
            remind_at += timedelta(days=1)
        return remind_at

    def get_quick_reply(self, morning_dt, noon_dt, evening_dt):
        now = datetime.utcnow()
        return QuickReply(
            items=[
                QuickReplyButton(
                    action=PostbackAction(
                        label="1時間後",
                        display_text="1時間後",
                        data=f"{(now + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M')}")
                ),
                QuickReplyButton(
                    action=PostbackAction(
                        label="🐓",
                        display_text="🐓朝",
                        data=f"{self.to_remind_at(morning_dt, now).strftime('%Y-%m-%dT%H:%M')}")
                ),
                QuickReplyButton(
                    action=PostbackAction(
                        label="☀️",
                        display_text="☀️昼",
                        data=f"{self.to_remind_at(noon_dt, now).strftime('%Y-%m-%dT%H:%M')}")
                ),
                QuickReplyButton(
                    action=PostbackAction(
                        label="🌙",
                        display_text="🌙夜",
                        data=f"{self.to_remind_at(evening_dt, now).strftime('%Y-%m-%dT%H:%M')}")
                ),
                QuickReplyButton(
                    action=DatetimePickerAction(
                        label="日時を選択",
                        mode="datetime",
                        data="picker"
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
            # 初回ターンはエンティティからのリマインド内容取得を試みる
            remind_text = request.entities.get("remind_text")
            if remind_text:
                # リマインド対象文字列がエンティティに含まれている場合はステートにセット
                state.data["remind_text"] = remind_text

        elif not state.data.get("remind_text"):
            # 初回ターン以後はリマインドする文言がステートにない場合は発話内容をリマインド文言とみなして保持
            state.data["remind_text"] = request.event.message.text

        elif request.event.type == "postback":
            # リマインド内容があってポストバックリクエストの場合はリマインド日時を処理
            if request.event.postback.data == "cancel":
                state.data["canceled"] = True
            elif request.event.postback.data == "picker":
                # Pickerからリマインド日時を取得（「日時を選択」）
                remind_at_jst = datetime.strptime(request.event.postback.params["datetime"].upper(), "%Y-%m-%dT%H:%M")
                # JST-9時間の補正は本当はユーザーのタイムゾーンを使いましょうね
                state.data["remind_at"] = remind_at_jst + timedelta(hours=-9)
            else:
                # ポストバックデータからリマインド日時を取得（「1時間後」または「定時」）
                state.data["remind_at"] = datetime.strptime(request.event.postback.data.upper(), "%Y-%m-%dT%H:%M")

            if state.data.get("remind_at"):
                # リマインド日時が決定したらリマインダーを登録
                db = self.db_session()
                try:
                    if not RemindRepository.register_item(
                        db, user.id,
                        state.data["remind_at"],
                        state.data["remind_text"]
                    ):
                        state.data["failed"] = True
                finally:
                    db.close()

        # ステートの状態に応じて応答
        if state.data.get("canceled"):
            return "リマインダー登録を中止します"
        elif state.data.get("failed"):
            return "リマインダー登録に失敗しました"
        elif not state.data.get("remind_text"):
            return LineResponse(
                messages="リマインドして欲しい内容を入力してください",
                end_session=False
            )
        elif not state.data.get("remind_at"):
            return LineResponse(
                messages=[
                    # 【やってみよう】朝・昼・晩はユーザーの設定で変えられるようにしてみましょう
                    TextSendMessage(
                        text="いつリマインドしますか",
                        quick_reply=self.get_quick_reply(
                            datetime(1900, 1, 1, 23, 0, 0),  # 朝8時
                            datetime(1900, 1, 1, 3, 0, 0),   # 正午
                            datetime(1900, 1, 1, 11, 0, 0),  # 夜8時
                        )
                    )
                ],
                end_session=False
            )
        else:
            # UTC+9時間の補正は本当はユーザーのタイムゾーンを使いましょうね
            return f'{(state.data.get("remind_at") + timedelta(hours=9)).strftime("%m/%d %H:%M")}\n"{state.data.get("remind_text")}"'
