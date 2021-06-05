import traceback
from datetime import datetime
import json
from flask import (
    Blueprint, Response,
    current_app, request, render_template, abort
)
from sqlalchemy import desc
from ..models import ConversationHistory

bp = Blueprint("conversation_history", __name__, template_folder="../templates")


@bp.app_template_filter("timestamp_to_str")
def timestamp_to_str(timestamp):
    if timestamp:
        return datetime.utcfromtimestamp(timestamp).\
            strftime("%Y/%m/%d %H:%M:%S")
    else:
        return "-"


@bp.app_template_filter("format_json")
def format_json(val):
    if val is None:
        return None
    elif isinstance(val, dict):
        return json.dumps(val, ensure_ascii=False, indent=2)
    else:
        return json.dumps(json.loads(val), ensure_ascii=False, indent=2)


@bp.route("/admin/history")
def conversation_history_index():
    db = current_app.bot.db_session()

    try:
        count = int(request.args.get("count", 50))
        if count < 0:
            count = 0
        offset = int(request.args.get("offset", 0))
        if offset < 0:
            offset = 0
        conversation_histories = db.query(ConversationHistory).\
            order_by(desc(ConversationHistory.updated_at)).\
            limit(count).offset(offset).all()

        return render_template(
            "history.html",
            data={
                "conversation_histories": conversation_histories,
                "count": count,
                "offset": offset
            }
        )

    except Exception as ex:
        current_app.bot.logger.error(
            "Error in getting index of message log: "
            + f"{str(ex)}\n{traceback.format_exc()}"
        )
        abort(500)

    finally:
        db.close()


@bp.route("/admin/history/<history_id>")
def conversation_history_detail(history_id):
    db = current_app.bot.db_session()

    try:
        conversation_history = db.query(ConversationHistory).\
            filter(ConversationHistory.id == history_id).first()

        if conversation_history:
            return render_template(
                "history_detail.html",
                data={
                    "ml": conversation_history
                }
            )

        else:
            # Use Response to avoid raising error
            return Response("History not found", status=404)

    except Exception as ex:
        current_app.bot.logger.error(
            "Error in getting detail of message log: "
            + f"{str(ex)}\n{traceback.format_exc()}"
        )
        abort(500)

    finally:
        db.close()
