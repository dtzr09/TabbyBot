from utils.static import group_purpose_map

# shared
def user_not_found(personal:bool=False):
    if personal:
        return "😺 Psst... it's me, Tabby! Looks like you haven’t started tracking any personal expenses yet! 💸 Let’s change that – just tell me something like: 10 coffee ☕️"
    return (
            f"😺 Psst... it's me, Tabby!\n"
            f"Looks like you haven’t started tracking any expenses yet! 💸\n"
            f"Let’s change that – just tell me something like:\n"
            f"10 ramen @alice @bob 🍜"  
            )

category_tied_to_expense = "⚠️ Oops! This category is still tied to some expenses. You’ll need to remove them first."
duplicate_category = "🚫 Oops! You’ve already got a category with that name. Pick a new one?"

def no_selection(item:str):
    return f"⚠️ Oops! No {item} selected. Try again?"

def not_found(item:str):
    return f"🤔 Hmm... the {item} doesn’t seem to exist. Try again? \n\n If the issue keeps happening, feel free to email us — we’ve got your back!"

def edit_fail(action:str):
    text = ""
    if action == "edit":
        text = "edition"
    elif action == "delete":
        text = "deletion"
    elif action == "rename":
        text = "renaming"
    elif action == "update":
        text = "updating"
    elif action == "create":
        text = "creation"
    elif action == "saving":
        text = "saving"
    elif action == "settle":
        text = "settle debts"
    else:
        text = "something"
    return f"❌ Yikes! {text.capitalize()} failed. Try again, or contact us if the issue persists."

def edit_category_success(action:str, category_name:str, new_name:str=None):
    text = ""
    if action == "rename" and new_name:
        text = f"✅ All set! {category_name} has been renamed to {new_name}"
    elif action == "delete":
        text = f"✅ Poof! {category_name} has been deleted."
    else:
        text = "Unexpected"
    return text

# group expenses
parse_group_expense_fail = (
    "🚨 Uh-oh! That didn’t look right.\n"
    "👉 Try one of these formats instead:\n\n"
    "• `10 lunch @user1 @user2`\n"
    "• `10 lunch @user1 5 @user2 10 @user3 20`\n"
    "• `10 lunch @user1 5 @user2 10 @me 20`\n"
    "• `10 lunch @user1 5 @user2 10 @me 20 DD/MM`\n\n"
    "🧠 Start with the amount, then the description, then who’s involved — and optionally, the date!"
)

no_new_admins = "🚫 Everyone’s already on the guest list! No new admins to add.\n\n💡Reminder: Only group *admins* can be added. Ask your friend to become one first!"
def add_new_admins_success(new_admins):
    txt = ""

    if len(new_admins) == 1:
        txt = f"@{new_admins[0]}"
    elif len(new_admins) == 2:
        txt = f"@{new_admins[0]} and @{new_admins[1]}"
    else:
        txt = f"@{', @'.join(new_admins[:-1])} and @{new_admins[-1]}"

    return f"✅ New admin crew assembled! Welcome aboard: {txt} 🎉"

start_group_text = (
    f"😺 Hey there\\! I'm Tabby\\!\n\n"
    f"Let’s get your group set up in just a few seconds 🚀\n\n"
    f"Please answer these two quick questions:\n"
    f"1️⃣ *What currency will you be using?* \\(e\\.g\\. SGD, USD, EUR\\)\n"
    f"2️⃣ *What’s this group for?* Choose a number:\n\n"
    f"   1\\. ✈️ {group_purpose_map[1]}\n"
    f"   2\\. 🏠 {group_purpose_map[2]}\n\n"
    f"📥 *How to reply:*\n\n"
    f"Just send your answers like this: `currency purpose`\n"
    f"E\\.g\\. `SGD 1` – for Singapore Dollars and a travel group\\!"
)

def get_validation_error_message(error, unique_mentions=None, custom_split=None, total_amount=0, duplicates=None):
    if error == "mismatch_mentions_splits":
        return (
            f"🧮 Oops! You gave me {len(unique_mentions)} mentions but {len(custom_split)} split values.\n"
            f"Everyone needs a slice of the pie! 🍰"
        )
    elif error == "split_amounts_mismatch":
        return (
            f"💸 Hmm… the math isn’t adding up!\n"
            f"Split total: {sum(custom_split.values()):.2f}, but the full amount is {total_amount:.2f}.\n"
            "Double-check those numbers!"
        )
    elif error == "duplicate_mentions":
        return (
            f"🙅‍♂️ Hold up! Looks like you mentioned someone more than once:\n"
            f"{', '.join(duplicates)}\n"
            "No need to tag them twice — they’re already in!"
        )
    elif error == "no_valid_participants":
        return "🙈 I can’t split with ghosts! Mention real users using @username."
    
def get_personal_entry_message(amount: float, user_name: str):
    return f"🧾 Got it! A personal expense of ${amount:.2f} has been added for {user_name}."


expense_deleted = "🗑️ Done! That expense is outta here."
expense_updated_success = "✅ Updated! That expense is looking fresh."
add_group_admin_failed = "❌ Uh-oh! Couldn't add the group admins. Try again in a bit?"
additional_info_fail = "📝 That field can’t be empty! Give me some details."
invalid_format_currency_purpose = "🧠 Brain freeze! Use this format: `SGD Lunch` — currency first, then purpose!"
invalid_currency = "🌍 That currency might be from another universe. Try SGD, USD, or EUR!"
group_not_registered = "🎬 Lights, camera... wait! This group isn’t registered yet.\nRun /start to kick off the expense adventure!"
no_pending_group_expense = "🕵️‍♂️ Nothing to see here — no pending group expense!"
new_cateogory_name = "✍️ Let’s name this new category. Fire away! Try something like `📁 Food`"
no_debts_to_settle = "💰 No debts found. You’re financially zen. 🧘"

def settle_amount_exceeds_debt(owe_amount):
    return f"💸 Whoa, I know you must be rich... but you’re trying to pay more than what’s owed (${owe_amount:.2f}). Generous, but unnecessary!"

settle_amount_less_than_debt = "🧐 Nice try, but you can’t pay zero or less."
invalid_amount = "💸 Oops! That amount doesn’t look right. Try a positive number?"

def log_personal_expense_success(description: str, category_name: str):
    return f"✅ Logged *{description}* as part of *{category_name}*. Budget on point!"
personal_expense_format_fail = "🧠 Brain fog? Try: `10 coffee` — numbers first, then what's it for!"

# personal expenses
incorrect_date_format = "📅 Oops! That date looks funky. Try using DD/MM — like `30/05`."
invalid_personal_expense_format= "🚧 Oops! I tripped over the format. Try something like: `10 lunch` or `10 lunch 12/06`"

# settings
def get_settings_menu_text(settings_type:str):
    if settings_type == "menu":
        return "🔧 Time for an update! What would you like to change?"
    elif settings_type == "view_categories":
        return "🔍 A quick peek at your categories:"
    elif settings_type == "rename_category":
        return "📝 Give one of your categories a glow-up — choose one:"
    elif settings_type == "add_category":
        return "📂 Give your new category a cool name:"
    elif settings_type == "delete_category":
        return "🚮 Choose a category to send to the void:"
    elif settings_type == "new_category":
        return (
            "📂 Let’s recategorize this expense!\n\n"
            "💡 *Heads up:* This will update all expenses with the same name — retroactive magic! ✨"
        )   
    elif settings_type == "currency":
        return "✈️ Jet-setting, are we? What currency do we need for this new adventure? (e.g., SGD, USD, EUR)"
    elif settings_type == "edit_expenses":
        return "🕵️‍♀️ Expense detective mode on — enter a keyword to search:"

def get_expense_details(expense, date_time):
    return (
        f"🧾 *Here’s what you logged:*\n"
        f"• 💰 *Amount:* ${expense.amount:.2f}\n"
        f"• ✏️ *Description:* {expense.description}\n"
        f"• 📆 *Date:* {date_time}\n"
        f"• 🗂 *Category:* {expense.category.name if expense.category else 'None'}\n"
    )
same_category_chosen = "👀 No updates made. Seems like you chose the same thing!"
empty_input = "❌ Oops! That field can’t be empty. Give me something to work with!"

def currency_change(currency: str):
    return f"🧳 New currency for a new journey: {currency.upper()} it is!"

