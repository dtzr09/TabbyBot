import datetime
from utils.checks import validate_group_expense_entry
from db.models import ExpenseShare
from collections import defaultdict
from db.repositories.user import get_user, find_users_by_username_and_chat_id
from db.repositories.expenseShare import add_expense_share
from utils.messages import *

income_keywords = {"salary", "bonus", "income"}

def parse_expense_text(text: str):
    try:
        parts = text.strip().split()
        if len(parts) < 2:
            return {"warning": invalid_personal_expense_format}

        amount = float(parts[0])
        maybe_date = parts[-1]
        date = None

        # Try parsing the last word as a date
        try:
            date = datetime.datetime.strptime(maybe_date, "%d/%m")
            date = date.replace(year=datetime.datetime.today().year)
            description = ' '.join(parts[1:-1])  # Exclude date from description
        except ValueError:
            if "/" in maybe_date:
                return {"warning": incorrect_date_format}
            description = ' '.join(parts[1:])
            date = datetime.datetime.now()

        keyword = description.split()[0].lower() if description else ""

        return {
            "amount": amount,
            "description": description,
            "keyword": keyword,
            "date": date
        }

    except Exception:
        return {"warning": invalid_personal_expense_format}


def parse_group_expense_input(session, chat_id:str, text: str, sender):
    parts = text.strip().split()
    if len(parts) < 3:
        return {"warning": parse_group_expense_fail}

    expected_amount = None
    description = []
    mentions = []
    custom_split = defaultdict(float)
    mentions_ids = []
    date = datetime.datetime.now()

    is_equal_split = True

    last_part = parts[-1]  
    if "/" in last_part:
        try:
            day, month = map(int, last_part.split("/"))
            date = datetime.date(datetime.datetime.now().year, month, day)
            parts = parts[:-1]  # Remove the date from parts
        except:
            return {"warning": incorrect_date_format}
        

    # Step 1: Get total amount
    if parts[0].replace('.', '', 1).isdigit():
        expected_amount = float(parts[0])
    else:
        return {"warning": parse_group_expense_fail}

    # Step 3: Start from index 1 to find description until first mention
    idx = 1
    while idx < len(parts) and not parts[idx].startswith("@"):
        description.append(parts[idx])
        idx += 1

    # Step 4: From first mention onward, parse as @user amount
    while idx < len(parts):
        user = parts[idx].lstrip("@")
        if user == "me":
            user = sender.username
        mentions.append(user)

        idx += 1
        if idx < len(parts) and parts[idx].replace('.', '', 1).isdigit():
            custom_split[user] += float(parts[idx])
            is_equal_split = False
            idx += 1

   
    warning = validate_group_expense_entry(
        mentions=mentions,
        custom_split=custom_split,
        total_amount=expected_amount,
        expected_amount=expected_amount,
        description=description
    )

    if not warning: 
        users = find_users_by_username_and_chat_id(session, mentions, chat_id)
        mentions_ids = [user.id for user in users]

    return {
        "amount": expected_amount,
        "description": " ".join(description),
        "is_equal_split": is_equal_split,
        "custom_split": dict(custom_split),
        "date": date,
        "warning": warning,
        "mentions_ids": mentions_ids,
    }

def handle_expense_split(session, expense, payer_id, participant_ids, chat_id, amount, custom_split, is_equal_split = True):
    if is_equal_split:
        return assign_expense_shares(session, expense, payer_id, participant_ids, chat_id, amount)

    return assign_unequal_expense_shares(session, expense, payer_id, participant_ids, chat_id, amount, custom_split)

def assign_expense_shares(session, expense, payer_id, participant_ids, chat_id, amount):
    """
    Creates ExpenseShare entries based on who paid and who participated.

    Case 1: Payer in participants → split equally
    Case 2: Payer only participant → personal expense
    Case 3: Payer not in participants → all participants owe payer
    """

    participants = []
    
    if len(participant_ids) == 1 and payer_id == participant_ids[0]:
        # Case 2: Personal expense
        user = get_user(
            session,
            user_id=payer_id,
            chat_id=chat_id
        )
        add_expense_share(session, expense.id, user.id, amount)
        participants.append(user)
        return participants, get_personal_entry_message(
            amount=amount,
            user_name=user.name
        )

    share_amount = round(amount / len(participant_ids), 2)

    for uid in participant_ids:
        user = get_user(
            session,
            user_id=uid,
            chat_id=chat_id
        )
        participants.append(user)
        session.add(ExpenseShare(
            expense_id=expense.id,
            user_id=user.id,
            share_amount=share_amount
        ))

    session.commit()

    payer = get_user(
        session=session,
        user_id=payer_id,
        chat_id=chat_id
    )

    if len(participants) == 2 :
        # Special case for 2 participants, use their names directly
        participant_names = " and ".join([u.name for u in participants])
    else:
        participant_names = ", ".join([u.name for u in participants])

    participants_text = ""
    for p in participants:
        if(p.id != payer_id):
            participants_text += f"         • {p.name} - ${share_amount:.2f}\n"
    
    if payer_id in participant_ids:
        return participants, (
            f"🤝 {payer.name} paid ${amount:.2f} for {expense.description}.\n"
            f"🪙 Split between {participant_names}. Only those who didn’t pay owe their fair share:\n"
            f"{participants_text}"
        )   
    else:
        text = f"🤝 {payer.name} paid ${amount:.2f} for {expense.description}.\n"
        if len(participants) == 1:
            text += f"💸 {participant_names} owe {payer.name} ${share_amount:.2f}."
        else:
            text += f"🪙 Split between {participant_names} — here’s what each of you owes {payer.name} for the good times:\n"
            text += f"{participants_text}"

        return participants, (text)

def assign_unequal_expense_shares(session, expense, payer_id, participant_ids, chat_id, amount, custom_split):
    """
    Creates ExpenseShare entries based on who paid and who participated.

    Case 1: Payer in participants → split base on custom_split
    Case 2: Payer only participant → personal expense
    Case 3: Payer not in participants → all participants owe payer base on their respective splits
    """
    participants = []
    if len(participant_ids) == 1 and payer_id == participant_ids[0]:
        # Case 2: Personal expense
        user = get_user(
            session=session,
            user_id=payer_id,
            chat_id=chat_id
        )
        add_expense_share(session, expense.id, user.id, amount)
        participants.append(user)
        return participants, get_personal_entry_message(
            amount=amount,
            user_name=user.name
        )

    users = find_users_by_username_and_chat_id(session, custom_split.keys(), chat_id)
    for user in users:
        session.add(ExpenseShare(
            expense_id = expense.id,
            user_id = user.id,
            share_amount = custom_split[user.username]
        ))
    session.commit()

    payer = get_user(
        session=session,
        user_id=payer_id,
        chat_id=chat_id
    )

    split_text = []
    for key, value in custom_split.items():
        user = get_user(
            session=session,
            username=key,
            chat_id=chat_id
        )
        split_text.append(f"    • {user.name} - ${value:.2f}")

    if payer_id in participant_ids:
        # Case 1: Payer is part of the participants – split base on custom_split
        return participants, (
            f"🤝 {payer.name} paid ${amount:.2f} for {expense.description}.\n"
            f"🪙 Time to split the love — here’s who owes what:\n"
            f"{"\n".join(split_text)}"
        )
    elif payer_id not in participant_ids:
        # Case 3: Payer is not in participants – reimbursement model
        return participants, (
            f"💳 {payer.name} went full hero mode and paid ${amount:.2f} for {expense.description}.\n"
            f"🙌 Now it’s your turn - cough it up, team:\n"
            f"{"\n".join(split_text)}"
        )

    return None

