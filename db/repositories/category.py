import logging
from db.models import Category
from utils.static import STATIC_CATEGORIES

def insert_static_categories(session, user_id, chat_id):
    """If its in a group, static categories will be added per chat_id"""
    try:
        for name in STATIC_CATEGORIES:
            exists = get_category(session, name=name, user_id=user_id, chat_id=chat_id)
            if not exists:
                session.add(Category(name=name, user_id=user_id, chat_id=chat_id))
        session.commit()
    finally:
        session.close()

def handle_add_category(session, user_id, chat_id, name=None, category_id=None):
    try:
        category = get_category(session, name=name, user_id=user_id, chat_id=chat_id, category_id=category_id)
        if not category:
            category = add_category(session, name, user_id=user_id, chat_id=chat_id)
        return category
    except Exception as e:
        session.rollback()
        logging.exception("❌ Failed to add category:")
        return None

def add_category(session, name, user_id=None, chat_id=None):
    try:
        category = Category(name=name, user_id=user_id, chat_id=chat_id)
        session.add(category)
        session.commit()
        logging.info(f"✅ Category added: {name}")
        return category
    except Exception as e:
        session.rollback()
        logging.exception("❌ Failed to add category:")
        return None

def delete_category(session, category_id, user_id=None, chat_id=None):
    try:
        category = get_category(session, category_id=category_id, user_id=user_id, chat_id=chat_id)
        if not category:
            logging.warning(f"⚠️ Category ID {category_id} not found.")
            return False
        
        session.delete(category)
        session.commit()
        logging.info(f"✅ Category ID {category_id} deleted")
        return True
    except Exception as e:
        session.rollback()
        logging.exception("❌ Failed to delete category:")
        return False

def get_category(session, *, category_id=None, name=None, user_id=None, chat_id=None):
    try:
        query = session.query(Category)

        if category_id is not None:
            query = query.filter(Category.id == category_id)
        if name is not None:
            query = query.filter(Category.name == name)
        if user_id is not None:
            query = query.filter(Category.user_id == user_id)
        if chat_id is not None:
            query = query.filter(Category.chat_id == chat_id)

        return query.first()
    except Exception:
        logging.exception("❌ Failed to get category with given filters.")
        return None

def get_all_categories(session, user_id, chat_id):
    try:
        query = session.query(Category)
        return query.filter_by(chat_id=str(chat_id), user_id=user_id).all()
    except Exception as e:
        logging.exception("❌ Failed to get all categories:")
        return []

def edit_category(session, old_name, new_name, user_id, chat_id):
    try:
        category = get_category(session, name=old_name, user_id=user_id, chat_id=chat_id)
        if not category:
            if chat_id:
                logging.warning(f"⚠️ Category ID {category.id} not found for chat")
            logging.warning(f"⚠️ Category ID {category.id} not found for user {user_id}")
            return None
        
        category.name = new_name
        session.commit()

        logging.info(f"✅ Category ID {category.id} updated to {new_name}")

        return category
    except Exception as e:
        session.rollback()
        logging.exception("❌ Failed to edit category:")
        return None
