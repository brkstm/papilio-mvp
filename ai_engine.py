from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_analysis(data, company, country, industry, entry_mode):

    prompt = f"""
You are a senior strategy consultant writing for a Head of Strategy.

ABSOLUTE RULES:
- ONLY use the provided data block
- DO NOT use external knowledge
- DO NOT invent numbers
- DO NOT overinterpret weak signals
- If something is missing, write "data not available"
- Every statement with a number must include the exact source
- Write in precise, board-level business language
- Avoid generic phrases such as "substantial economy", "viable market", "welcoming environment", "growth potential"

TASK:
Write a concise board-level market entry note for {company} entering {country} in the sector {industry} via {entry_mode}.

STRUCTURE:
1. Market Context
2. Entry Implication
3. Key Risks

STYLE REQUIREMENTS:
- Be analytical, concise, and implication-driven
- Tie every observation to the market entry decision
- Do not make broad claims unless directly supported by the data
- If evidence is limited, say so explicitly

OUTPUT REQUIREMENTS:
- Use short paragraphs
- Include exact values, years, and sources
- Focus on what matters for the entry decision

DATA:
{data}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.1,
            messages=[
                {"role": "system", "content": "You are a precise and factual strategy analyst."},
                {"role": "user", "content": prompt}
            ]
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"ERROR: {str(e)}"

