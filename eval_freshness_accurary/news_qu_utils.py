from enum import Enum
import pycountry
import unicodedata
import logging
from typing import Optional, Dict, Any, List, Union

logger = logging.getLogger()

class NewsRouteType(str, Enum):
    """Enum for news query routing types."""
    TC = "tc"
    RAG = "rag"
    BRAVE = "brave"

class EntityType(str, Enum):
    """Enum for entity classification types."""
    NO_ENTITY = "no entity"
    SINGLE = "single"
    MULTIPLE = "multiple"

class TemporalType(str, Enum):
    """Enum for temporal query types."""
    CURRENT = "current"
    GENERAL = "general"
    RECENT = "recent"

COUNTRY_ALIASES = {
    "usa": "US",
    "u.s.a": "US",
    "united states": "US",
    "united states of america": "US",
    "america": "US",
    "uk": "GB",
    "u.k": "GB",
    "england": "GB",
    "scotland": "GB",
    "britain": "GB",
    "great britain": "GB",
    "south korea": "KR",
    "north korea": "KP",
    "russia": "RU",
    "vietnam": "VN",
    "iran": "IR",
    "syria": "SY",
    "czech republic": "CZ",
    "laos": "LA",
    "bolivia": "BO",
    "tanzania": "TZ",
    "venezuela": "VE",
    "uae": "AE",
    "united arab emirates": "AE",
    "hong kong": "HK",
    "macau": "MO",
    "ivory coast": "CI",
    "côte d'ivoire": "CI",
    "palestine": "PS",
}

def normalize_text(text: str) -> str:
    """Normalize text by removing accents and converting to lowercase."""
    return (
        unicodedata.normalize("NFKD", text)
        .encode("ASCII", "ignore")
        .decode("utf-8")
        .lower()
        .strip()
    )

def get_country_code(country_name: str) -> str:
    """
    Returns the ISO 3166-1 alpha-2 country code for a given country name.
    Includes fuzzy matching and aliases for common variants.
    
    Args:
        country_name (str): Full or partial country name (case-insensitive).

    Returns:
        str: ISO country code (e.g., 'US', 'IN'), or 'US' if not found or invalid.
    """
    try:
        if not country_name or str(country_name).lower() == "null" or str(country_name) == "":
            raise ValueError("Country name is None or 'null' or empty")

        name = normalize_text(str(country_name))

        # Alias lookup (fastest and most common)
        if name in COUNTRY_ALIASES:
            return COUNTRY_ALIASES[name]

        # Exact match
        for country in pycountry.countries:
            if normalize_text(country.name) == name:
                return country.alpha_2.upper()

        # Official name match
        for country in pycountry.countries:
            if hasattr(country, "official_name") and normalize_text(country.official_name) == name:
                return country.alpha_2.upper()

        # Partial match (substring)
        for country in pycountry.countries:
            if name in normalize_text(country.name):
                return country.alpha_2.upper()

        # Fallback: partial match in official name
        for country in pycountry.countries:
            if hasattr(country, "official_name") and name in normalize_text(country.official_name):
                return country.alpha_2.upper()

    except Exception as e:
        logger.error(f"Error getting country code for '{country_name}': {e}, defaulting to 'US'")
    # Default fallback
    return "US"

SUPPORTED_GEO = {"united states", "united kingdom", "default"}
SUPPORTED_TOPICS = {"politics", "business", "scienceandtechnology", "health", "sports", "entertainment", "education", "world", "national", "general"}

def validate_news_topics(news_topic: List[str]) -> List[str]:
    """
    Validates and normalizes news topics against the allowed list.
    
    Handles input type inconsistencies, removes duplicates, and logs invalid entries.

    Args:
        news_topic (List[str] | str): One or more topic strings.

    Returns:
        List[str]: Validated and normalized list of topics (lowercase).
    """
    try:
        # Handle null-like inputs
        if not news_topic or str(news_topic).lower() in {"none", "null"}:
            logger.warning("News topic is None or 'null', defaulting to []")
            return []

        # Normalize to list
        if isinstance(news_topic, str):
            # Split comma-separated strings if given as single string
            news_topic = [t.strip() for t in news_topic.split(",") if t.strip()]
        elif not isinstance(news_topic, list):
            logger.warning(f"Invalid type for news_topic: {type(news_topic)}, expected list or str, defaulting to []")
            return []

        # Clean and lower-case topics
        normalized_topics = [t.strip().lower() for t in news_topic if isinstance(t, str) and t.strip()]

        if not normalized_topics:
            return []

        # Filter valid vs invalid topics
        valid_topics = sorted(set(t for t in normalized_topics if t in SUPPORTED_TOPICS))
        invalid_topics = sorted(set(t for t in normalized_topics if t not in SUPPORTED_TOPICS))

        # Logging for diagnostics
        if invalid_topics:
            logger.warning(f"Invalid news topics filtered out: {', '.join(invalid_topics)}")

        return valid_topics

    except Exception as e:
        logger.exception(f"Error validating news topics: {e}")
        return []


def normalize(value):
    """Convert to lowercase string safely."""
    if isinstance(value, str):
        return value.strip().lower()
    if isinstance(value, list):
        return [normalize(item) for item in value]
    return value

def entity_type_from_list(entity):
    """Classify entity list into No/Single/Multiple."""
    if not isinstance(entity, list):
        return EntityType.NO_ENTITY.value
    if len(entity) == 0:
        return EntityType.NO_ENTITY.value
    if len(entity) == 1:
        return EntityType.SINGLE.value
    return EntityType.MULTIPLE.value

