from livekit.agents import function_tool
from app.rag.pinecone_client import search_properties as _pinecone_search


# ── Voice-friendly formatting ─────────────────────────────────────────────────

def _price_to_words(price: float | int | None) -> str:
    """Convert raw INR number to speakable words. No symbols."""
    if price is None:
        return "price on request"
    price = float(price)
    if price >= 10_000_000:
        return f"{price / 10_000_000:.1f} crore rupees"
    elif price >= 100_000:
        return f"{price / 100_000:.1f} lakh rupees"
    else:
        return f"{int(price)} rupees"


def _format_for_voice(results: list[dict]) -> str:
    """
    Format Pinecone results into a string the LLM will speak naturally.
    Rules:
      - No rupee symbol, no markdown, no bullet points
      - Numbers spoken as words
      - Max 3 results to keep voice response short
    """
    if not results:
        return "No properties found matching those criteria."

    # Cap at 3 for voice — listing 5 properties aloud is painful to hear
    results = results[:3]

    lines = [f"I found {len(results)} {'property' if len(results) == 1 else 'properties'} for you."]

    for i, p in enumerate(results, 1):
        beds = f"{int(p['bedrooms'])} bedroom" if p.get("bedrooms") else "open plot"
        area = f"{int(p['area_sqft'])} square feet" if p.get("area_sqft") else ""
        price = _price_to_words(p.get("price"))
        desc = p.get("description", "")[:120]  # trim long descriptions

        lines.append(
            f"Option {i}: {p['title']}. "
            f"This is a {beds} {p.get('property_type', '')} in {p.get('city', '').title()}. "
            f"Area is {area}. Price is {price}. {desc}."
        )

    return " ".join(lines)


# ── Sanitize raw Ollama arguments ─────────────────────────────────────────────

def _clean(val):
    """Ollama sends {}, 'null', '' for optional fields — normalize all to None."""
    if val is None:
        return None
    if isinstance(val, dict) and not val:
        return None
    if isinstance(val, str) and val.strip().lower() in ("", "null", "none"):
        return None
    return val


# ── Tool Definition ───────────────────────────────────────────────────────────

@function_tool(
    name="property_search",
    description=(
        "Search the property database. "
        "ONLY call this after you know BOTH the city AND the property type from the user. "
        "Never guess these — always ask first if missing."
    ),
    raw_schema={
        "name": "property_search",
        "description": (
            "Search the property database. "
            "ONLY call this after you know BOTH the city AND the property type from the user."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language summary of what the user wants, e.g. 'spacious 2BHK apartment in Mumbai near station'",
                },
                "city": {
                    "type": "string",
                    "description": "City name in lowercase, e.g. 'mumbai', 'delhi', 'bangalore', 'hyderabad'",
                },
                "property_type": {
                    "type": "string",
                    "description": "Exact type — one of: 'apartment', 'villa', 'plot'",
                },
                "bedrooms": {
                    "type": "integer",
                    "description": "Number of bedrooms. 2BHK means 2, 3BHK means 3. Omit if not mentioned.",
                },
                "min_price": {
                    "type": "number",
                    "description": "Minimum price in INR. Convert: 1 lakh = 100000, 1 crore = 10000000. Omit if not mentioned.",
                },
                "max_price": {
                    "type": "number",
                    "description": "Maximum price in INR. Convert: 1 lakh = 100000, 1 crore = 10000000. Omit if not mentioned.",
                },
            },
            "required": ["query", "city", "property_type"],  # city + type are mandatory
        },
    },
)
async def property_search(raw_arguments: dict[str, object]) -> str:
    # ── Extract and sanitize ──────────────────────────────────────────────────
    query         = _clean(raw_arguments.get("query")) or "property search"
    city          = _clean(raw_arguments.get("city"))
    property_type = _clean(raw_arguments.get("property_type"))
    bedrooms      = _clean(raw_arguments.get("bedrooms"))
    min_price     = _clean(raw_arguments.get("min_price"))
    max_price     = _clean(raw_arguments.get("max_price"))

    # Normalize strings
    if isinstance(city, str):
        city = city.strip().lower()
    if isinstance(property_type, str):
        property_type = property_type.strip().lower()

    # Coerce numeric types safely
    try:    min_price = float(min_price) if min_price is not None else None
    except (ValueError, TypeError): min_price = None

    try:    max_price = float(max_price) if max_price is not None else None
    except (ValueError, TypeError): max_price = None

    try:    bedrooms = int(bedrooms) if bedrooms is not None else None
    except (ValueError, TypeError): bedrooms = None

    # ── Hard guard — bounce if mandatory fields still missing ─────────────────
    # (Shouldn't happen since they're in "required", but Ollama ignores that)
    missing = []
    if not city:          missing.append("city")
    if not property_type: missing.append("property type")

    if missing:
        return (
            f"I still need the following before I can search: {', '.join(missing)}. "
            "Please ask the user and call this tool again once you have them."
        )

    # ── Query Pinecone ────────────────────────────────────────────────────────
    print(
        f"[property_search] city={city} | type={property_type} | "
        f"beds={bedrooms} | price={min_price}-{max_price} | query={query!r}"
    )

    results = _pinecone_search(
        query=query,
        city=city,
        property_type=property_type,
        bedrooms=bedrooms,
        min_price=min_price,
        max_price=max_price,
        top_k=5,
    )

    return _format_for_voice(results)