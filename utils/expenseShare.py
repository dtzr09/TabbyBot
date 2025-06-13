from db.repositories.expenseShare import get_all_expense_share
import logging
from collections import defaultdict
from db.repositories.user import get_user

def get_splits(session, expense_id, chat_id):
    try:
        splits = get_all_expense_share(session, expense_id)
        split_dict = defaultdict(float)
        for split in splits:
            user_id = split.user_id
            user = get_user(
                session, user_id=user_id, chat_id=str(chat_id)
            )
            if not user:
                logging.warning(f"⚠️ User with ID {user_id} not found for expense ID {expense_id}.")
                continue
            user_name = user.name
            split_dict[user_name] += split.share_amount
        if not splits:
            return None
        return split_dict
    except Exception as e:
        session.rollback()
        logging.exception("❌ Failed to get splits for expense ID:")
        return None
    
