import os
from google import genai
from app.infrastructure.persistence.models import UserModel


def warn_if_needed(user: UserModel, percent_used: float, top_categories: list[dict]) -> dict:
    if percent_used < 80:
        return {"alert": False, "message": None}

    top_str = ", ".join(
        f"{c['category']} ({c['co2_kg']:.1f} kg)" for c in top_categories[:3]
    )
    prompt = (
        f"O usuário usou {percent_used:.0f}% do limite mensal de CO2. "
        f"As categorias que mais pesaram foram: {top_str}. "
        f"Gere um aviso motivacional em 1-2 frases em português, mencionando as categorias reais."
    )

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
    return {"alert": True, "message": response.text}
