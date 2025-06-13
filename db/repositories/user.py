from db.models import User
import logging

def handle_add_user(session, telegram_user, chat_id):
    try:
        user = get_user(
            session,
            telegram_id=telegram_user.id,
            chat_id=chat_id
        )

        if not user:
            user = add_user(session, telegram_user, chat_id)
        return user
    except Exception as e:
        session.rollback()
        logging.exception("❌ Failed to add user:")
        return None
    
def add_user(session, telegram_user, chat_id):
    try:
        user = User(
            telegram_id=str(telegram_user.id),
            name=telegram_user.full_name.capitalize(),
            chat_id=chat_id,
            username=telegram_user.username 
        )
        session.add(user)
        session.commit()
        logging.info(f"✅ User added: {user.name} ({user.telegram_id})")
        return user
    except Exception as e:
        session.rollback()
        logging.exception("❌ Failed to add user:")
        return None

def update_user(session, telegram_id, chat_id, currency:str):
    """
    Edits the user with the given user_id to update their currency.
    """
    try:
        user = get_user(session=session, telegram_id=telegram_id, chat_id=chat_id)
        if user:
            user.currency = currency
            session.commit()
            logging.info(f"✅ User {user.name} ({user.telegram_id}) updated to currency: {currency}")
            return True
        else:
            logging.warning(f"❌ User with ID {telegram_id} not found.")
            return False
    except Exception as e:
        session.rollback()
        logging.exception("❌ Failed to edit user:")
        return False

def get_user(session, *, telegram_id=None, user_id=None, username=None, chat_id=None):
    try:
        query = session.query(User)

        if telegram_id is not None:
            query = query.filter(User.telegram_id == str(telegram_id))
        if user_id is not None:
            query = query.filter(User.id == user_id)
        if username is not None:
            query = query.filter(User.username == username)
        if chat_id is not None:
            query = query.filter(User.chat_id == str(chat_id))

        return query.first()
    except Exception as e:
        logging.exception("❌ Failed to get user.")
        return None
    
def get_all_users(session, chat_id=None):
    """
    Retrieves all users from the database.
    If a chat_id is provided, it filters users by that chat ID.
    """
    try:
        if chat_id:
            return session.query(User).filter_by(chat_id=str(chat_id)).all()
        else:
            return session.query(User).all()
    except Exception as e:
        logging.exception("❌ Failed to get all users ")
        return []


def find_users_by_username_and_chat_id(session, usernames, chat_id):
    try:
        return session.query(User).filter(User.username.in_(usernames), User.chat_id == str(chat_id)).all()
    except Exception as e:
        logging.exception("❌ Failed to find user by username and chat ID:")
        return None

def get_all_group_members(session, chat_id):
    try:
        return session.query(User).filter_by(chat_id=str(chat_id)).all()
    except Exception as e:
        logging.exception("❌ Failed to get all group members:")
        return []
    
