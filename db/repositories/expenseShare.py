import logging
from db.models import ExpenseShare, Expense

def add_expense_share(session, expense_id, user_id, share_amount):
    try:
        share = ExpenseShare(
            expense_id=expense_id,
            user_id=user_id,
            share_amount=share_amount
        )
        session.add(share)
        session.commit()
        logging.info(f"✅ Expense share added: Expense ID {expense_id}, User ID {user_id}, Amount {share_amount}")
        return share
    except Exception as e:
        session.rollback()
        logging.exception("❌ Failed to add expense share:")
        return None

def get_expense_share_by_expense_id(session, expense_id):
    try:
        query = session.query(ExpenseShare)
        if expense_id is not None:
            query.filter(ExpenseShare.expense_id == expense_id)
        
        return query.first()
    except Exception as e:
        logging.exception("❌ Failed to get expense share.")
        return None
    

def get_all_expense_share(session, expense_id: int):
    try:
        query = session.query(ExpenseShare).filter(ExpenseShare.expense_id == expense_id)
        return query.all()
    except Exception as e:
        logging.exception("❌ Failed to get expense share.")
        return None
    
def get_expense_shares_by_chat_id(session, chat_id: str):
    try:
        return (
            session.query(ExpenseShare)
            .join(Expense)
            .filter(Expense.chat_id == chat_id)
            .all()
        )
    except Exception as e:
        logging.exception("❌ Failed to fetch expense shares by chat ID:")
        return []

def handle_delete_expense_share(session, expense_id):
    try:
        shares = get_all_expense_share(session, expense_id)
        for share in shares:
            session.delete(share)
        session.commit()
        logging.info(f"✅ Expense shares for ID {expense_id} deleted")
        return True
    except Exception as e:
        session.rollback()
        logging.exception("❌ Failed to delete expense share:")
        return False