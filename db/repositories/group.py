import logging
from db.models import Group
import datetime

def register_group(session, chat_id, chat_title, currency, purpose):
    try:
        if is_group_registered(session, chat_id):
            logging.warning(f"⚠️ Group {chat_title} ({chat_id}) is already registered.")
            return None
        group = Group(chat_id=chat_id, name=chat_title, registered_at=datetime.datetime.now(), currency=currency, purpose=purpose)
        session.add(group)
        session.commit()
        logging.info(f"✅ Group registered: {chat_title} ({chat_id})")
        return group
    except Exception as e:
        session.rollback()
        logging.exception("❌ Failed to register group:")
        return None

def is_group_registered(session, chat_id: str) -> bool:
    try:
        return session.query(Group).filter_by(chat_id=chat_id).first() is not None
    except Exception as e:
        logging.exception("❌ Failed to check if group is registered:")
        return False

def get_group_info(session, chat_id: str):
    try:
        group = find_group(session, chat_id)
        if group:
            return {
                "chat_id": group.chat_id,
                "name": group.name,
                "registered_at": group.registered_at,
                "currency": group.currency,
                "purpose": group.purpose
            }
        else:
            logging.warning(f"⚠️ Group with chat_id {chat_id} not found.")
            return None
    except Exception as e:
        logging.exception("❌ Failed to get group info:")
        return None
    
def find_group(session, chat_id: str):
    try:
        group = session.query(Group).filter_by(chat_id=chat_id).first()
        if group:
            return group
        else:
            logging.warning(f"⚠️ Group with chat_id {chat_id} not found.")
            return None
    except Exception as e:
        logging.exception("❌ Failed to find group:")
        return None
    
def update_group_currency(session, chat_id: str, new_currency: str):
    try:
        group = find_group(session, chat_id)
        if group:
            group.currency = new_currency.upper()
            session.commit()
            logging.info(f"✅ Group currency updated: {chat_id} to {new_currency}")
            return True
        else:
            logging.warning(f"⚠️ Group with chat_id {chat_id} not found.")
            return False
    except Exception as e:
        session.rollback()
        logging.exception("❌ Failed to update group currency:")
        return False