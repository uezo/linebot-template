from .models import ReminderItem


# リマインダーデータベース操作
class RemindRepository:
    @staticmethod
    def register_item(db, remind_to, remind_at, text):
        try:
            item = ReminderItem(
                remind_to=remind_to,
                remind_at=remind_at,
                remind_text=text)
            db.add(item)
            db.commit()
            return item

        except Exception as ex:
            db.rollback()
            raise ex

    @staticmethod
    def get_items(db, remind_to):
        return db.query(ReminderItem).\
            filter(
                ReminderItem.remind_to == remind_to,
                ReminderItem.reminded == 0).\
            order_by(
                ReminderItem.remind_at).\
            limit(10).all()

    @staticmethod
    def get_item(db, id, remind_to):
        return db.query(ReminderItem).\
            filter(
                ReminderItem.id == id,
                ReminderItem.remind_to == remind_to,
                ReminderItem.reminded == 0).first()

    @staticmethod
    def get_items_to_notify(db, baseline_dt):
        return db.query(ReminderItem).\
            filter(
                ReminderItem.remind_at <= baseline_dt,
                ReminderItem.reminded == 0).all()

    @staticmethod
    def delete_item(db, item_id, remind_to):
        try:
            item = db.query(ReminderItem).\
                filter(
                    ReminderItem.id == item_id,
                    ReminderItem.remind_to == remind_to).first()

            if not item:
                return False

            db.delete(item)
            db.commit()
            return True

        except Exception as ex:
            db.rollback()
            raise ex

    @staticmethod
    def close_item(db, item_id, remind_to):
        try:
            item = db.query(ReminderItem).\
                filter(
                    ReminderItem.id == item_id,
                    ReminderItem.remind_to == remind_to).first()

            if not item:
                return False

            item.reminded = 1
            db.commit()
            return True

        except Exception as ex:
            db.rollback()
            raise ex
