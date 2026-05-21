"""
mcp_responses_server.py — A FastMCP server designed for the OpenAI Responses API.

Run this as a standalone HTTP server:
    python mcp_responses_server.py

Then expose it publicly with ngrok:
    ngrok http 8000
"""

import random, math, re
from typing import Annotated, Literal
from pydantic import Field
from fastmcp import FastMCP

mcp = FastMCP(
    name="UtilityServer",
    instructions="A collection of utility tools: dice rolling, weather (simulated), "
                 "text analysis, and unit conversion.",
)


# ── Tool 1: Dice roller ────────────────────────────────────────────────────────
@mcp.tool
def roll_dice(
    n_dice: Annotated[int, Field(description="Number of dice to roll", ge=1, le=20)],
    sides: Annotated[int, Field(description="Number of sides per die", ge=2, le=100)] = 6,
) -> dict:
    """Roll n_dice dice each with the given number of sides. Returns individual rolls and total."""
    rolls = [random.randint(1, sides) for _ in range(n_dice)]
    return {"rolls": rolls, "total": sum(rolls), "n_dice": n_dice, "sides": sides}


# ── Tool 2: Weather (simulated — replace with a real API in production) ─────────
@mcp.tool
def get_weather(
    city: Annotated[str, "Name of the city"],
    units: Annotated[Literal["celsius", "fahrenheit"], "Temperature unit"] = "celsius",
) -> dict:
    """
    Get current weather conditions for a city.
    Returns temperature, condition, humidity, and wind speed.
    Note: This server returns simulated data for demonstration purposes.
    """
    # Simulated data — in production replace with httpx call to a weather API
    base_data = {
        "manila":    {"temp_c": 32, "condition": "Partly Cloudy",  "humidity": 78, "wind_kph": 15},
        "tokyo":     {"temp_c": 18, "condition": "Overcast",        "humidity": 62, "wind_kph": 20},
        "london":    {"temp_c": 12, "condition": "Rainy",           "humidity": 85, "wind_kph": 25},
        "new york":  {"temp_c": 22, "condition": "Sunny",           "humidity": 55, "wind_kph": 18},
        "singapore": {"temp_c": 30, "condition": "Thunderstorm",   "humidity": 90, "wind_kph": 10},
        "sydney":    {"temp_c": 24, "condition": "Clear",           "humidity": 60, "wind_kph": 22},
    }
    data = base_data.get(city.lower(), {"temp_c": 20, "condition": "Unknown", "humidity": 60, "wind_kph": 10})
    temp = data["temp_c"] if units == "celsius" else round(data["temp_c"] * 9/5 + 32, 1)
    return {
        "city": city.title(),
        "temperature": temp,
        "units": units,
        "condition": data["condition"],
        "humidity_pct": data["humidity"],
        "wind_kph": data["wind_kph"],
    }


# ── Tool 3: Text analysis ─────────────────────────────────────────────────────
@mcp.tool
def analyze_text(text: str) -> dict:
    """
    Analyze a piece of text and return detailed statistics.
    Returns character count, word count, sentence count, paragraph count,
    reading time estimate, and the top 5 most frequent words.
    """
    from collections import Counter
    words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    stopwords = {"the","a","an","is","are","was","were","and","or","but","in","on","at","to","of","for"}
    content_words = [w for w in words if w not in stopwords]
    reading_time_s = round(len(words) / (200 / 60))  # avg 200 wpm
    return {
        "character_count": len(text),
        "word_count": len(words),
        "sentence_count": len(sentences),
        "paragraph_count": len(paragraphs),
        "estimated_reading_seconds": reading_time_s,
        "top_5_words": Counter(content_words).most_common(5),
        "avg_words_per_sentence": round(len(words) / len(sentences), 1) if sentences else 0,
    }


# ── Tool 4: Unit conversion ────────────────────────────────────────────────────
@mcp.tool
def convert_units(
    value: Annotated[float, "The numeric value to convert"],
    from_unit: Annotated[str, "Source unit (e.g. km, kg, usd, celsius)"],
    to_unit: Annotated[str, "Target unit (e.g. miles, lbs, php, fahrenheit)"],
) -> dict:
    """
    Convert a value between units. Supports:
    - Length: km ↔ miles, m ↔ ft, cm ↔ inches
    - Weight: kg ↔ lbs, g ↔ oz
    - Temperature: celsius ↔ fahrenheit
    - Currency (approx.): usd ↔ php, usd ↔ eur, usd ↔ sgd
    """
    conversions = {
        ("km",       "miles"):      lambda v: v * 0.621371,
        ("miles",    "km"):         lambda v: v / 0.621371,
        ("m",        "ft"):         lambda v: v * 3.28084,
        ("ft",       "m"):          lambda v: v / 3.28084,
        ("cm",       "inches"):     lambda v: v / 2.54,
        ("inches",   "cm"):         lambda v: v * 2.54,
        ("kg",       "lbs"):        lambda v: v * 2.20462,
        ("lbs",      "kg"):         lambda v: v / 2.20462,
        ("g",        "oz"):         lambda v: v / 28.3495,
        ("oz",       "g"):          lambda v: v * 28.3495,
        ("celsius",  "fahrenheit"): lambda v: v * 9/5 + 32,
        ("fahrenheit","celsius"):   lambda v: (v - 32) * 5/9,
        ("usd",      "php"):        lambda v: v * 56.20,
        ("php",      "usd"):        lambda v: v / 56.20,
        ("usd",      "eur"):        lambda v: v * 0.92,
        ("eur",      "usd"):        lambda v: v / 0.92,
        ("usd",      "sgd"):        lambda v: v * 1.34,
        ("sgd",      "usd"):        lambda v: v / 1.34,
    }
    key = (from_unit.lower(), to_unit.lower())
    fn = conversions.get(key)
    if not fn:
        return {"error": f"Conversion from '{from_unit}' to '{to_unit}' not supported.",
                "supported_pairs": [f"{a} → {b}" for a, b in conversions]}
    result = fn(value)
    return {"original": value, "from": from_unit, "result": round(result, 4), "to": to_unit}


# ── Tool 5: Calculator ────────────────────────────────────────────────────────
@mcp.tool
def calculate(expression: str) -> dict:
    """
    Evaluate a mathematical expression. Supports arithmetic, sqrt(), abs(),
    round(), log(), sin(), cos(), tan(), pi, e.
    Examples: "2**10", "sqrt(144) + 50", "round(pi, 4)"
    """
    safe_globals = {
        "sqrt": math.sqrt, "abs": abs, "round": round,
        "log": math.log, "log10": math.log10,
        "sin": math.sin, "cos": math.cos, "tan": math.tan,
        "pi": math.pi, "e": math.e, "__builtins__": {}
    }
    try:
        result = eval(expression, safe_globals)
        return {"expression": expression, "result": result}
    except Exception as ex:
        return {"expression": expression, "error": str(ex)}


if __name__ == "__main__":
    print("🚀 Starting UtilityServer on http://localhost:8000/mcp/")
    mcp.run(transport="http", port=8000)