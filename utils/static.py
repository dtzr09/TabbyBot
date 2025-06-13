from telegram.ext import filters

STATIC_CATEGORIES = [
    "🍔 Food",
    "🚕 Transport",
    "🛒 Groceries",
    "🔧 Utilities",
    "🎉 Entertainment",
    "🛍️ Shopping",
    "💸 Salary",
    "💰 Bonus",
    "💳 Bills",
    "💊 Health",
    "🛡️ Insurance",
    "📦 Miscellaneous",
]


group_purpose_map = {
    1 : "Group travel expenses",
    2 : "Family/shared expenses"
}

CURRENCY_SYMBOLS = [
    "USD",  # United States Dollar
    "EUR",  # Euro
    "SGD",  # Singapore Dollar
    "GBP",  # British Pound Sterling
    "JPY",  # Japanese Yen
    "CNY",  # Chinese Yuan Renminbi
    "HKD",  # Hong Kong Dollar
    "AUD",  # Australian Dollar
    "NZD",  # New Zealand Dollar
    "CAD",  # Canadian Dollar
    "CHF",  # Swiss Franc
    "SEK",  # Swedish Krona
    "NOK",  # Norwegian Krone
    "DKK",  # Danish Krone
    "INR",  # Indian Rupee
    "IDR",  # Indonesian Rupiah
    "MYR",  # Malaysian Ringgit
    "THB",  # Thai Baht
    "PHP",  # Philippine Peso
    "VND",  # Vietnamese Dong
    "KRW",  # South Korean Won
    "AED",  # United Arab Emirates Dirham
    "SAR",  # Saudi Riyal
    "TRY",  # Turkish Lira
    "ZAR",  # South African Rand
    "RUB",  # Russian Ruble
    "BRL",  # Brazilian Real
    "MXN",  # Mexican Peso
    "PLN",  # Polish Zloty
    "HUF",  # Hungarian Forint
    "CZK",  # Czech Koruna
    "ARS",  # Argentine Peso
    "CLP",  # Chilean Peso
    "COP",  # Colombian Peso
    "EGP",  # Egyptian Pound
    "PKR",  # Pakistani Rupee
    "BDT",  # Bangladeshi Taka
    "LKR",  # Sri Lankan Rupee
    "KES",  # Kenyan Shilling
    "NGN",  # Nigerian Naira
    "TZS",  # Tanzanian Shilling
    "GHS",  # Ghanaian Cedi
    "MAD",  # Moroccan Dirham
]

