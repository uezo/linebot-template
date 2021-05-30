# linebot-template

LINE Botを超高速開発するためのテンプレート🚀

[🇬🇧English version is here](https://github.com/uezo/linebot-template/blob/main/README.md)

# これは何？ 🤔

これは以下3つの特徴を持つLINE Bot開発用の軽量プロジェクトテンプレートです。

- マルチスキル・マルチターンに対応（文脈ベースのルーティング）
- スケーラブル（最低限の超基本的な部分のみ）
- 継続的改善の支援（メッセージログ）

# クイックスタート

まずはこのリポジトリをダウンロードなりクローンなりしていただき、依存ライブラリをインストールしましょう。以下のコマンドを実行することで一括インストールができます。

NOTE: ライブラリをインストールする前に、`linebot-template`を任意のプロジェクト名に変更していくと良いと思います

```bash
$ pip install -r requirements-dev.txt
```

次に、LINE Developerで取得・確認できるChannelAccessTokenとChannelSecretを`config.ini`に設定します。あわせて`[DATABASE] > connection_string`を変更することでSQLAlchemyのサポートするお好みのデータベースを利用することもできます。

```ini
[LINE_API]
channel_access_token = YOUR_CHANNEL_ACCESS_TOKEN
channel_secret = YOUR_CHANNEL_SECRET

[DATABASE]
connection_string = sqlite:///linebot.db
```

これですべての準備が完了しました。`run.py`を実行してチャットボットを起動しましょう。

```bash
$ python run.py
```

もしローカルPC上で起動している場合は、Ngrokなどを利用してWebhookエンドポイントをインターネットに公開し、そのURLをLINE Developersに登録しましょう。

```bash
$ ngrok http 12345
```

(conversation image)

さて、もう一つだけご紹介したい機能があります。http://localhost:12345/admin/history にアクセスしてみてください。ユーザーとチャットボットとの会話の記録がブラウザで閲覧できるはずです。チャットボットが想定通りのシナリオで会話を進められているかのモニタリングや、豊富なデバッグ情報を利用した不具合対応など、なかなか強力なお役立ちツールとしてご活用頂けると思います。

(image)

タイムスタンプをクリックするとイベント処理前後のコンテキストや例外などより詳細な情報を確認することができます。

(image)


# チャットボットの開発方法

開発を進める前にアーキテクチャ、特にイベント処理のフローについてご説明しましょう。以下の図をご覧ください。

![linebot-template Architecture Overview](https://uezo.blob.core.windows.net/github/linebot-template/flow.ja.png)

手短に言うと、チャットボット開発のために必要な作業は`YourBot.extract_intent`と`YourSkill(s).process_request`を実装することです。他の汎用的な機能はテンプレート側で実装済みです。

- `extract_intent`は`Request`、`User`、`State`を引数として受け取ります。LINE APIからの`Event`オブジェクトには`request.event`を通じてアクセスすることができます。インテントが抽出された場合には、インテントは`str`、エンティティは`dict`でそれぞれリターンしてください。

```python
def extract_intent(self, request, user, state):
    if request.event.messages == "***":
        # インテントとエンティティを抽出した場合
        return "***", {"key1": "val1", "key2", "val2"}
    elif ... :
        # インテントのみを抽出した場合
        return "***"
```

- `process_request`も同様に`Request`、`User`、`State`を引数として受け取ります。ビジネスロジックを処理し、LINE APIに応答したい`Message`のリストを作成したら、これを`Response`オブジェクトにセットしてリターンしてください。なお`Response`オブジェクトの生成を省略して以下の型でリターンすることもできます。

    - `str`
    - `Message`
    - `str`の`list`
    - `Message`と`str`からなるリスト

```python
def process_request(self, request, user, state):
    text = do_something()
    message = TextSendMessage(text=text)
    return Response(messages=[message])
    # 👇 以下もOK
    # return text
    # return message
    # return [text]
    # return [message]
```

## おうむ返しBot

おうむ返しスキルのみを持つ最もシンプルなチャットボットの例です。

```python
from avril import SkillBase
from avril.channels.line import LineBotBase

class EchoSkill(SkillBase):
    # このスキルのトピック名称
    topic = "Echo"

    def process_request(self, request, user, state):
        # ユーザーの発話内容をそのまま返却
        return request.event.message.text

class EchoBot(LineBotBase):
    # このボットで利用するスキルの登録
    skills = [EchoSkill]

    def extract_intent(self, request, user, state):
        # 常におうむ返しインテントと判定
        return EchoSkill.topic
```

(実行例のimage)

## マルチターンのおうむ返しBot

あるトピックを複数ターンに渡って継続し、またコンテキスト情報を維持するためには、スキルからのレスポンスに`end_session=False`を設定します。これは今回の発話内容と前回の発話内容をあわせて表示するマルチターンなおうむ返しBotの例です。

```python
from avril import SkillBase
from avril.channels.line import LineBotBase, LineResponse

class MultiTurnEchoSkill(SkillBase):
    topic = "MultiTurnEcho"

    def process_request(self, request, user, state):
        current_text = request.event.message.text
        last_text = state.data.get("last_text")
        state.data["last_text"] = current_text

        message = f"今回の発話: {current_text}"
        if last_text:
            message += f"\n前回の発話: {last_text}"

        return LineResponse(
            messages=message,
            end_session=False   # 👈 コンテキスト情報を維持するためにセット
        )

class MultiTurnEchoBot(LineBotBase):
    skills = [MultiTurnEchoSkill]

    def extract_intent(self, request, user, state):
        if not state.topic:   # 👈 ターン継続中はインテントを判定しないように条件を追加
            return MultiTurnEchoSkill.topic
```


## Multi-skill bot

📝🤔

## Multi-turn and Multi-skill bot

📝🤔

# コンテキストのライフサイクル

コンテキスト情報はデフォルトでターン毎にクリアされますが、スキルのResponseに`end_session=False`をセットした場合にはクリアされずに次のターンまで保持されます。

削除される条件は以下の通り:

- スキルのResponseに`end_session=True`がセットされたとき。デフォルトでは`True`がセットされています
- タイムアウトしたとき。デフォルトでは最終更新から300秒です
- トピック（スキル）に紐づけられたインテントが抽出されたとき。別のトピックに変わったかどうかは問いません
- `BotBase.process_events`で例外がキャッチされたとき


# メッセージログのミュート

本番運用では、パフォーマンス上の理由や情報管理上の理由によりメッセージログをミュートしたくなる場合があります。そのような場合には`ConversationHistory`クラスを継承したクラスを作成して値を保持しないように修正します。これをBotの`conversation_history_class`に設定することで、当該項目の出力を抑止することができます。

```python
class MyConversationHistory(ConversationHistory):
    @property
    def state_on_start(self):
        super().state_on_start()

    # override not to set serialized value
    @state_on_start.setter
    def state_on_start(self, value):
        self.__state_on_start = None

class MyBot(LineBotBase):
    # Use custom message log class
    conversation_history_class = MyConversationHistory
        : (省略)
```


# テンプレートのカスタマイズ

pipでインストール可能なライブラリとしてではなくテンプレートとして公開しているのは、気に食わないところはご自身で直していただき、自らのコードとして扱っていただくためです。そのまま使っていただくのも結構ですが、慣れてきたらガンガンカスタマイズしましょう。


# Testing

📝🤔

