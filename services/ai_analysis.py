
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

def analyze_player(stats):

    prompt = f"""
    Ты профессиональный аналитик CS2.

    Проанализируй статистику игрока:

    {stats}

    Дай ответ на русском языке.

    Структура:
    1. Общая оценка от 1 до 10.
    2. Общий анализ.
    3. Сильные стороны.
    4. Слабые стороны.
    5. Рекомендации по улучшению.
    6. Итоговый вердикт.

    Не придумывай данные, которых нет в статистике.
    """

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt
    )

    return response.output_text
