# webapp/utils/currency.py
"""
Определение валюты пользователя на основе страны
"""

def get_ui_currency(country: str | None) -> str:
    """
    Определяет валюту на основе страны пользователя
    
    Args:
        country: Код страны (GB, DE, FR и т.д.) или None
        
    Returns:
        Код валюты: "GBP", "EUR" или "USD"
    """
    if country == "GB":
        return "GBP"
    if country in {"DE", "FR", "ES", "IT", "NL", "PL", "IE", "AT", "BE", "PT", "FI", "GR"}:
        return "EUR"
    return "USD"


def get_currency_symbol(currency: str) -> str:
    """
    Возвращает символ валюты
    
    Args:
        currency: Код валюты ("USD", "EUR", "GBP")
        
    Returns:
        Символ валюты: "$", "€" или "£"
    """
    symbols = {
        "USD": "$",
        "EUR": "€",
        "GBP": "£"
    }
    return symbols.get(currency, "$")