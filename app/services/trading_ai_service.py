import random


async def market_recommendation() -> str:
    """
    Placeholder למודל המלצות מסחר  בשלב הבא אפשר לחבר ל-OpenAI/HF.
    """
    sentiments = ["bullish", "bearish", "neutral"]
    return random.choice(sentiments)
