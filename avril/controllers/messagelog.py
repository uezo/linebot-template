import traceback
from datetime import datetime
import json
from flask import Blueprint, current_app, request, render_template
from sqlalchemy import desc
from ..models import MessageLog

bp = Blueprint("message_log", __name__, template_folder="../templates")


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


@bp.route("/admin/messagelog")
def message_log_index():
    db = current_app.bot.db_session()

    try:
        count = int(request.args.get("count", 50))
        if count < 0:
            count = 0
        offset = int(request.args.get("offset", 0))
        if offset < 0:
            offset = 0
        message_logs = db.query(MessageLog).\
            order_by(desc(MessageLog.updated_at)).\
            limit(count).offset(offset).all()

        return render_template(
            "message_log.html",
            data={
                "message_logs": message_logs,
                "count": count,
                "offset": offset
            }
        )

    except Exception as ex:
        current_app.bot.logger.error(
            f"Error in getting index of message log: \
            {str(ex)}\n{traceback.format_exc()}"
        )

    finally:
        db.close()


@bp.route("/admin/messagelog/<messagelog_id>")
def message_log_detail(messagelog_id):
    db = current_app.bot.db_session()

    try:
        message_log = db.query(MessageLog).\
            filter(MessageLog.id == messagelog_id).first()

        if message_log:
            return render_template(
                "message_log_detail.html",
                data={
                    "ml": message_log
                }
            )

        else:
            return "404"

    except Exception as ex:
        current_app.bot.logger.error(
            f"Error in getting detail of message log: \
            {str(ex)}\n{traceback.format_exc()}"
        )

    finally:
        db.close()
