from sqlalchemy import Column, Integer, Float, String, Date, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String)
    name = Column(String)
    categories = relationship("Category", back_populates="user")
    chat_id = Column(String)  
    username = Column(String) 
    currency = Column(String, default="SGD")

class Expense(Base):
    __tablename__ = 'expenses'
    id = Column(Integer, primary_key=True)
    payer_id = Column(Integer, ForeignKey('users.id'))
    amount = Column(Float)
    category_id = Column(Integer, ForeignKey('categories.id'))
    description = Column(String)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    chat_id = Column(String)  

    category = relationship("Category")
    payer = relationship("User")


class ExpenseShare(Base):
    __tablename__ = 'expense_shares'
    id = Column(Integer, primary_key=True)
    expense_id = Column(Integer, ForeignKey('expenses.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    share_amount = Column(Float)

    expense = relationship("Expense")
    user = relationship("User")
    
class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)    
    chat_id = Column(String)                              

    user = relationship("User", back_populates="categories")

class KeywordCategoryMap(Base):
    __tablename__ = 'keyword_category_map'
    id = Column(Integer, primary_key=True)
    keyword = Column(String)
    category_id = Column(Integer, ForeignKey('categories.id'))
    chat_id = Column(String) 
    expense_id = Column(Integer, ForeignKey('expenses.id'))

class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True)
    chat_id = Column(String, unique=True)
    name = Column(String)
    registered_at = Column(DateTime, default=datetime.datetime.utcnow)
    currency = Column(String, nullable=False)  # Default currency for the group
    purpose = Column(Integer, default=1)  # Default purpose for the group

class DebtSettlement(Base):
    __tablename__ = "debt_settlements"

    id = Column(Integer, primary_key=True)
    chat_id = Column(String, nullable=False)
    payer_id = Column(ForeignKey("users.id"), nullable=False)   # who paid
    payee_id = Column(ForeignKey("users.id"), nullable=False)   # who received
    amount = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
