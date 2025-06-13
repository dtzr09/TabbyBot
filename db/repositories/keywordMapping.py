import logging
from db.models import KeywordCategoryMap

def handle_add_keyword_category_mapping(session, keyword, category_id, chat_id, expense_id):
    try:
        mapping = get_keyword_category_mapping(session, keyword=keyword, chat_id=chat_id, category_id=category_id)
        if not mapping:
            mapping = add_keyword_category_mapping(session, keyword, category_id, chat_id, expense_id=expense_id)
        return mapping
    except Exception as e:
        session.rollback()
        logging.exception("❌ Failed to add keyword-category mapping:")
        return None

def get_keyword_category_mapping(session, keyword:str,  chat_id:str, keyword_only=False, category_id = None):
    try:
        if keyword_only:
            return session.query(KeywordCategoryMap).filter_by(keyword=keyword, chat_id=chat_id).first()
        elif category_id is not None:
            return session.query(KeywordCategoryMap).filter_by(keyword=keyword, category_id=category_id, chat_id=chat_id).first()
    except Exception as e:
        logging.exception("❌ Failed to get keyword-category mapping:")
        return None

def handle_delete_keyword_category_mapping(session, keyword, category_id, chat_id):
    try:
        mapping = get_keyword_category_mapping(session=session, keyword=keyword, chat_id=str(chat_id), category_id=category_id)
        if mapping:
            session.delete(mapping)
            session.commit()
            logging.info(f"✅ Mapping deleted: {keyword} -> Category ID {category_id}")
            return True
        else:
            logging.error(f"❌ Mapping not found for keyword {keyword}, Category ID {category_id}, Chat ID {chat_id}")
            return False
    except Exception as e:
        session.rollback()
        logging.exception("❌ Failed to delete keyword-category mapping:")
        return False

def add_keyword_category_mapping(session, keyword, category_id, chat_id, expense_id):
    if not keyword or not category_id or not chat_id:
        logging.error("❌ Keyword, Category ID, and Chat ID must be provided.")
        return None
    try:
        mapping = KeywordCategoryMap(
            keyword=keyword,
            category_id=category_id,
            chat_id=chat_id,
            expense_id=expense_id
        )
        session.add(mapping)
        session.commit()
        logging.info(f"✅ Mapping added: {keyword} -> Category ID {category_id}")
        return mapping
    except Exception as e:
        session.rollback()
        logging.exception("❌ Failed to add keyword-category mapping:")
        return None

def edit_keyword_category_mapping(session, keyword=None, old_category_id=None, new_category_id=None, chat_id=None):
    try:
        mapping = session.query(KeywordCategoryMap).filter_by(keyword=keyword, category_id=old_category_id, chat_id=chat_id).all()
        if not mapping:
            logging.error(f"❌ Mapping with keyword {keyword}, Category ID {old_category_id}, and Chat ID {chat_id} not found.")
            return None
        if new_category_id is not None:
            for m in mapping:
                m.category_id = new_category_id

        session.commit()
        logging.info(f"✅ Mapping updated: {keyword} -> Category ID {new_category_id}")
        return mapping
    except Exception as e:
        session.rollback()
        logging.exception("❌ Failed to edit keyword-category mapping:")
        return None