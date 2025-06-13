from db.models import DebtSettlement
import logging 
import datetime

def add_debt_settlement(session, chat_id, payer_id, payee_id, amount):
    """
    Add a debt settlement record to the database.
    
    Args:
        session: SQLAlchemy session object.
        chat_id (int): ID of the chat.
        payer_id (int): ID of the user paying off the debt.
        payee_id (int): ID of the user receiving the payment.
        amount (float): Amount of the debt being settled.
        
    Returns:
        None
    """
    try:
        settlement = DebtSettlement(
            chat_id=chat_id,
            payer_id=payer_id,
            payee_id=payee_id,
            amount=amount,
            timestamp=datetime.datetime.now(),
        )
        session.add(settlement)
        session.commit()
        return True
    except Exception as e:
        logging.exception("❌ Error adding debt settlement")
        session.rollback()
        return False

def get_debt_settlements(session, chat_id):
    try:
        return session.query(DebtSettlement).filter(DebtSettlement.chat_id == chat_id).all()
    except Exception as e:
        logging.exception("❌ Error fetching debt settlements")
        return []