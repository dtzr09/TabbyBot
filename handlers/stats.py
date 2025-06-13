from db import SessionLocal
import datetime
from collections import defaultdict
from telegram import Update
from telegram.ext import ContextTypes
from db.models import User
from utils.expense import income_keywords
from db.repositories.user import get_user
from db.repositories.expenseShare import get_all_expense_share
from db.repositories.expense import get_expenses_within_date_range
from db.repositories.group import get_group_info, is_group_registered
from utils.stats import get_group_balances_stats
import logging
from utils.messages import *

def get_month_range():
    now = datetime.datetime.now()
    start = datetime.date(now.year, now.month, 1)
    if now.month == 12:
        end = datetime.date(now.year + 1, 1, 1)
    else:
        end = datetime.date(now.year, now.month + 1, 1)
    return start, end
    
# Personal expenses
async def handle_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = SessionLocal()
    try:
        chat_id = str(update.effective_chat.id) if update.effective_chat else None
        if not chat_id:
            await update.message.reply_text("❗Chat ID not found. Please try again.")
            return
        
        user = update.effective_user
        db_user = get_user(
            session,
            telegram_id=user.id,
            chat_id=chat_id
        )

        if not db_user:
            await update.message.reply_text(user_not_found(personal=True)
            )
            return

        start_date, end_date = get_month_range()

        expenses = get_expenses_within_date_range(
            session=session,
            user_id=db_user.id,
            start_date=start_date,
            end_date=end_date
        )

        if not expenses:
            await update.message.reply_text("📊 No expenses recorded this month.")
            return

        # Totals
        total_expense = 0
        total_income = 0
        category_totals = defaultdict(float)
        income_totals = defaultdict(float)

        for exp in expenses:
            amount = exp.amount
            category = exp.category.name if exp.category else "Uncategorized"

            is_income = any(kw in category.lower() for kw in income_keywords)

            if is_income:
                total_income += amount
                income_totals[category] += amount
            else:
                total_expense += amount
                category_totals[category] += amount

        def format_category_stats():
            lines = []
            for cat, amt in sorted(category_totals.items(), key=lambda x: -x[1]):
                pct = round(amt / total_expense * 100)
                lines.append(f" {int(amt):,} ({pct}%) – {cat}")
            return "\n".join(lines)
        
        def format_income_stats():
            lines = []
            for cat, amt in sorted(income_totals.items(), key=lambda x: -x[1]):
                pct = round(amt / total_income * 100)
                lines.append(f" {int(amt):,} ({pct}%) – {cat}")

            if len(lines) == 0:
                return "No income recorded this month."
            return "\n".join(lines)
        
        net_savings = total_income - total_expense
        currency = db_user.currency

        text = (
            f"*Statistics for {start_date.strftime('%B')}*\n\n"
            f"*💸 Expenses Breakdown:*\n{format_category_stats()}\n\n"
            f"*💰 Income Breakdown:*\n{format_income_stats()}\n\n"
            f"*📈 Summary:*\n"
            f"*Total expenses:* {int(total_expense):,} {currency}\n"
            f"*Total income:* {int(total_income):,} {currency}\n"
            f"*Net Savings:* {int(net_savings):,} {currency} {int(net_savings) >= 0 and '🤑' or '😵'}\n"
        )

        await update.message.reply_text(text, parse_mode="Markdown")

    finally:
        session.close()

# Group expenses
async def handle_group_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = SessionLocal()
    try:
        chat_id = str(update.effective_chat.id)

        if not is_group_registered(session, chat_id):
            await update.message.reply_text(group_not_registered)
            return
    
        start_date, end_date = get_month_range()

        expenses = get_expenses_within_date_range(
            session=session,
            chat_id=chat_id,
            start_date=start_date,
            end_date=end_date
        )

        if not expenses:
            await update.message.reply_text("📊 No group expenses recorded this month.")
            return

        # Income keywords
        income_keywords = {"salary", "bonus", "income"}

        # Totals
        category_totals = defaultdict(float)
        income_totals = defaultdict(float)
        personal_expenses = defaultdict(float)
        personal_incomes = defaultdict(float)

        total_expense = 0
        total_income = 0

        for exp in expenses:
            amount = exp.amount
            category = exp.category.name if exp.category else "Uncategorized"
            is_income = any(kw in category.lower() for kw in income_keywords)

            if is_income:
                income_totals[category] += amount
                personal_incomes[exp.payer_id] += amount
                total_income += amount
            else:
                category_totals[category] += amount
                total_expense += amount

                # Add to each share
                shares = get_all_expense_share(
                    session=session,
                    expense_id=exp.id
                )
                for share in shares:
                    personal_expenses[share.user_id] += share.share_amount

        def format_category_stats(data, total):
            cat_stats = [
                f"{cat} – ${round(amt, 2):,} ({round(amt / total * 100)}%) "
                for cat, amt in sorted(data.items(), key=lambda x: -x[1])
            ]
            return "\n".join(cat_stats)
        
        group_info = get_group_info(session, chat_id)

        def format_user_shares(user_map, total_map):
            users = session.query(User).filter(User.id.in_(total_map.keys())).all()
            id_to_user = {u.id: f"{u.name}" for u in users}

            lines = []
            for uid, amt in sorted(total_map.items(), key=lambda x: -x[1]):
                name = id_to_user.get(uid, "Unknown")
                pct = round(amt / sum(total_map.values()) * 100)
                lines.append(f"👤 {name} – ${round(amt, 2):,} ({pct}%)")
            return "\n".join(lines)

        net = total_income - total_expense

        text = (
            f"*📊 Group statistics – ({start_date.strftime('%B')})*\n\n"

            f"*– Category Breakdown:*\n{format_category_stats(category_totals, total_expense)}\n\n"
            f"*– Expenses Breakdown:*\n{format_user_shares(session, personal_expenses)}\n\n"
        )

        # Only include income section if any income exists
        if total_income > 0:
            text += (
                f"*– Incomes:*\n{format_category_stats(income_totals, total_income)}\n\n"
                f"{format_user_shares(session, personal_incomes)}\n\n"
            )

        result = get_group_balances_stats(session, chat_id)

        # text += (
        #     f"*🔁 Group Balances Breakdown:*\n"
        #     f"{summary_text}\n\n"
        # )

        text += (
            f"*– Net Balances:*\n"
            f"{result['net_balances_summary']}\n\n"
        )

        text += (
            f"*– Final Summary:*\n"
            f"• Total Expenses: *{int(total_expense):,}* {group_info['currency']}\n"
        )

        if group_info['purpose'] == 2:
            text += f"• Total Incomes: *{int(total_income):,}* {group_info['currency']}\n"
            text += f"• Net Savings: *{int(net):,}* {group_info['currency']} {'🤑' if net >= 0 else '😵'}\n"

        await update.message.reply_text(text, parse_mode="Markdown")

    except Exception:
        logging.exception("❌ Error generating group stats")
        await update.message.reply_text("❌ Failed to generate statistics.")
    finally:    
        session.close()
