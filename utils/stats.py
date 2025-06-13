from collections import defaultdict
from db.repositories.expense import get_all_group_expenses
from db.repositories.expenseShare import get_expense_shares_by_chat_id
from db.repositories.user import get_all_users
from db.repositories.debtSettlement import get_debt_settlements

def get_raw_debts(session, chat_id):
    expenses = get_all_group_expenses(session, chat_id)
    expense_shares = get_expense_shares_by_chat_id(session, chat_id)

    expense_to_payer = {e.id: e.payer_id for e in expenses}
    debts = defaultdict(lambda: defaultdict(float))

    for s in expense_shares:
        payer_id = expense_to_payer[s.expense_id]
        if s.user_id != payer_id:
            debts[s.user_id][payer_id] += s.share_amount
    
    return debts

def get_cleaned_debts(debts):
    cleaned_debts = defaultdict(lambda: defaultdict(float))
    for debtor, creditors in debts.items():
        for creditor, amount in creditors.items():
            if round(amount, 2) > 0:
                cleaned_debts[debtor][creditor] = round(amount, 2)

    return cleaned_debts

def compute_net_balances(cleaned_debts, users_by_id):
    """
    Simplify all mutual debts and return a human-readable summary.
    
    Input: {
        user_id1: {user_id2: amount},
        user_id2: {user_id1: amount}
    }

    Output (string):
    User A owes:
      • User B – $X.XX
    """
    net_balances = defaultdict(dict)
    processed = set()

    for debtor in list(cleaned_debts.keys()):
        for creditor in list(cleaned_debts[debtor].keys()):
            if (debtor, creditor) in processed or (creditor, debtor) in processed:
                continue

            amt = cleaned_debts[debtor][creditor]
            reverse_amt = cleaned_debts[creditor].get(debtor, 0)

            if amt == 0 and reverse_amt == 0:
                continue

            if amt >= reverse_amt:
                net_amt = round(amt - reverse_amt, 2)
                if net_amt > 0:
                    net_balances[debtor][creditor] = net_amt
            else:
                net_amt = round(reverse_amt - amt, 2)
                if net_amt > 0:
                    net_balances[creditor][debtor] = net_amt

            # Remove both from balances so we don't double-count
            processed.add((debtor, creditor))
            processed.add((creditor, debtor))
    

    result = []
    debtors = list(net_balances.items())
    for i, (debtor, creditors) in enumerate(debtors):
        debtor_name = users_by_id.get(debtor, str(debtor)) if users_by_id else str(debtor)
        result.append(f"{debtor_name.capitalize()} owes:")
        for creditor, amt in creditors.items():
            creditor_name = users_by_id.get(creditor, str(creditor)) if users_by_id else str(creditor)
            result.append(f"  • {creditor_name.capitalize()} – ${amt:.2f}")
        if i < len(debtors) - 1:
            result.append("")  # Add newline only if there's a next item


    net_balances_summary = "\n".join(result) if result else "✅ No outstanding balances."

    return net_balances, net_balances_summary

def apply_past_settlements_to_debts(debts, session, chat_id):
    settlements = get_debt_settlements(session, chat_id)

    for s in settlements:
        # Payer is the one who paid, payee is the one who received
        debts[s.payer_id][s.payee_id] -= s.amount
    
    return debts

def get_group_balances_stats(session, chat_id):
    users = {u.id: u.name for u in get_all_users(session, chat_id)}

    raw_debts = get_raw_debts(session, chat_id)

    debts = apply_past_settlements_to_debts(raw_debts, session, chat_id)

    cleaned_debts = get_cleaned_debts(debts)

    # Step 4: Format string summary
    result = []
    for debtor, creditors in cleaned_debts.items():
        result.append(f"{users[debtor].capitalize()} owes:")
        for creditor, amt in creditors.items():
            result.append(f"  • {users[creditor].capitalize()} – ${amt:.2f}")
    detailed_balances = "\n".join(result)

    net_balances, net_balances_summary = compute_net_balances(cleaned_debts, users)

    return {
        "detailed_balances": detailed_balances,
        "cleaned_debts": cleaned_debts,
        "net_balances": net_balances,
        "net_balances_summary": net_balances_summary
    }
