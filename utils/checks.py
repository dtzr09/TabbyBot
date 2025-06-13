from utils.static import CURRENCY_SYMBOLS
from utils.messages import *

def validate_group_expense_entry(mentions: list[str], custom_split: dict[str, float], total_amount: float, expected_amount: float, description: str) -> str | None:
    if not expected_amount or not description: 
        return (parse_group_expense_fail)   
    if len(mentions) == 0:
        return(get_validation_error_message("no_mentions"))

    if not custom_split:
        return None  # Not a custom split, no warning needed

    unique_mentions = set(mentions)

    # Check 1: Number of mentions matches number of splits
    if len(custom_split) != len(unique_mentions):
        return (get_validation_error_message(
            "mismatch_mentions_splits",
            unique_mentions,
            custom_split
        ))

    # Check 2: Split amounts sum up to total amount
    if abs(sum(custom_split.values()) - expected_amount) > 0.01:
        return (
            get_validation_error_message(
                "split_amounts_mismatch",
                unique_mentions=unique_mentions,
                total_amount=total_amount,
                custom_split=custom_split
            )
        )

    # Check 3: Duplicates in mentions
    duplicates = [name for name in unique_mentions if mentions.count(name) > 1]
    if duplicates:
        return (get_validation_error_message(
            "duplicate_mentions",
            duplicates=duplicates
        ))

    return None  # No issues

def validate_currency_selection(currency: str) -> bool:
    if currency.lower() not in (c.lower() for c in CURRENCY_SYMBOLS):
        return False
    return True