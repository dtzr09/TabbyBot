from db.models import Expense
import logging
from db.repositories.user import get_user
from db.repositories.keywordMapping import edit_keyword_category_mapping, add_keyword_category_mapping, handle_delete_keyword_category_mapping, get_keyword_category_mapping
from db.repositories.expenseShare import handle_delete_expense_share, get_all_expense_share

def handle_add_expense(session, db_user, amount, description, date, category_id, chat_id):
    try:
        user = get_user(
            session,
            telegram_id=db_user.telegram_id,
            chat_id=chat_id
        )
        expense = add_expense(
            session,    
            user_id=user.id,
            amount=amount,
            description=description,
            date=date,
            chat_id=chat_id,
            category_id=category_id 
        )

        return expense

    except Exception as e:
        session.rollback()
        logging.exception("❌ Failed to add expense:")
        return False

def add_expense(session, user_id, amount, description, date, category_id, chat_id):
    try:
        expense = Expense(
            payer_id=user_id,
            amount=amount,
            description=description,
            date=date,
            chat_id=chat_id,
            category_id=category_id
        )
        session.add(expense)
        session.commit()
        logging.info(f"✅ Expense added: {amount} - {description} (Category ID: {category_id})")
        return expense
    except Exception as e:
        session.rollback()
        logging.exception("❌ Failed to add expense:")
        return None

def get_expense_by_id(session, expense_id, category_id=None):
    try:
        query = session.query(Expense)
        if category_id is not None:
            query = query.filter(Expense.category_id == category_id)
        if expense_id is not None:
            query = query.filter(Expense.id == expense_id)
        return query.first()
    except Exception as e:
        logging.exception("❌ Failed to get expense by ID:")
        return None
    
def get_expenses(session, chat_id=None, category_id=None):
    try:
        query = session.query(Expense)
        
        if chat_id:
            query = query.filter(Expense.chat_id == chat_id)
        if category_id:
            query = query.filter(Expense.category_id == category_id)
        
        expenses = query.all()
        return expenses
    except Exception as e:
        session.rollback()
        logging.exception("❌ Failed to get expenses:")
        return None
    
def get_expenses_within_date_range(session, start_date, end_date, user_id=None, chat_id=None):
    try:
        query = session.query(Expense)

        print(f"🔍 Getting expenses from {start_date} to {end_date} for user {user_id} in chat {chat_id}")
        
        if user_id:
            query = query.filter(Expense.payer_id == user_id)
        if chat_id:
            query = query.filter(Expense.chat_id == chat_id)
        
        expenses = query.filter(Expense.date.between(start_date, end_date)).all()
        return expenses
    except Exception as e:
        session.rollback()
        logging.exception("❌ Failed to get expenses within date range:")
        return None

def handle_delete_expense(session, expense_id):
    try:
        expense = get_expense_by_id(session, expense_id)
        if not expense:
            logging.warning(f"⚠️ Expense ID {expense_id} not found")
            return False

        mapping = get_keyword_category_mapping(session=session, keyword=expense.description, chat_id=str(expense.chat_id), category_id=expense.category_id)
        if mapping:
            session.delete(mapping)
            logging.info(f"✅ Mapping deleted: {expense.description} -> Category ID {expense.category_id}")
        else:
            raise ValueError(f"❌ Mapping not found for expense ID {expense_id}")
       
        shares = get_all_expense_share(session, expense_id)
        for share in shares:
            session.delete(share)

        session.delete(expense)
        session.commit()
        logging.info(f"✅ Expense ID {expense_id} deleted")
        return True
    except Exception as e:
        session.rollback()
        logging.exception("❌ Failed to delete expense:")
        return False
    
def edit_expense(session, expense_id, amount=None, description=None, date=None, category_id=None):
    try:
        expense = get_expense_by_id(session, expense_id)
        old_category_id = None
        old_description = None
        if not expense:
            logging.warning(f"⚠️ Expense ID {expense_id} not found")
            return None
        if amount is not None:
            expense.amount = amount
        if description is not None:
            old_description = expense.description
            expense.description = description
        if date is not None:
            expense.date = date
        if category_id is not None:
            old_category_id = expense.category_id
            expense.category_id = category_id

        if description and old_description and old_description != description or (old_category_id and old_category_id != category_id):
            add_keyword_category_mapping(
                session=session,
                keyword=description if description else expense.description,
                category_id=category_id if category_id else expense.category_id,
                chat_id=expense.chat_id,
                expense_id=expense.id
            )
        session.commit()
        logging.info(f"✅ Expense ID {expense_id} updated")
        return expense
    except Exception as e:
        session.rollback()
        logging.exception("❌ Failed to edit expense.")
        return None
    
def edit_expenses(session, chat_id, user_id, old_category_id, new_category_id, name):
    try:
        expenses = get_expenses_by_name(session, chat_id, user_id, name)
        for expense in expenses:
            expense.category_id = new_category_id

        keyword_map_exists = get_keyword_category_mapping(
            session=session,
            keyword=name,
            chat_id=chat_id,
            keyword_only=True
        )
        if keyword_map_exists:
            mapping = edit_keyword_category_mapping(session, keyword=name, old_category_id=old_category_id, new_category_id=new_category_id, chat_id=chat_id)
        else:
            mapping = add_keyword_category_mapping(
                session=session,
                keyword=name,
                category_id=new_category_id,
                chat_id=chat_id,
                expense_id=expenses[0].id
            )

        if not mapping:
            logging.error(f"❌ Failed to update keyword-category mapping for {name}.")
            return None
        session.commit()
        logging.info(f"✅ Updated {len(expenses)} expenses to category ID {new_category_id}.")
        return expenses
    except Exception as e:
        session.rollback()
        logging.exception("❌ Failed to edit expenses by name.")
        return None

def get_expenses_by_name(session, chat_id, user_id, name):
    try:
        if user_id:
            expenses = session.query(Expense).filter_by(payer_id=user_id, description=name, chat_id=str(chat_id)).all()
        else:
            expenses = session.query(Expense).filter_by(description=name, chat_id=str(chat_id)).all()
        return expenses
    except Exception as e:
        session.rollback()
        logging.exception("❌ Failed to get expenses by name.")
        return None

def get_all_group_expenses(session, chat_id):
    try:
        expenses = session.query(Expense).filter_by(chat_id=chat_id).all()
        return expenses
    except Exception as e:
        session.rollback()
        logging.exception("❌ Failed to get expenses.")
        return None
    
def search_expenses(session, keyword:str, page: int, PAGE_SIZE: int = 10, user_id: str = None, chat_id: str = None):
    results_count = session.query(Expense).filter(
            Expense.chat_id == chat_id if chat_id else Expense.payer_id == user_id,
            Expense.description.ilike(f"%{keyword}%")
        ).count()
    
    results = session.query(Expense).filter(
            Expense.chat_id == chat_id if chat_id else Expense.payer_id == user_id,
            Expense.description.ilike(f"%{keyword}%")
        ).order_by(Expense.date.desc()).offset(page * PAGE_SIZE).limit(PAGE_SIZE).all()
    

    return results_count, results