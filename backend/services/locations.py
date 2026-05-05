"""ISO country code → DataForSEO location_code + ISO language mapping.

Covers the most common markets. Unknown codes fall back to United States / English.
"""

# DataForSEO location codes: see https://docs.dataforseo.com/v3/serp/locations/
COUNTRY_TO_LOCATION_CODE = {
    "US": 2840, "GB": 2826, "UK": 2826, "CA": 2124, "AU": 2036, "NZ": 2554,
    "IT": 2380, "ES": 2724, "FR": 2250, "DE": 2276, "PT": 2620, "NL": 2528,
    "BE": 2056, "CH": 2756, "AT": 2040, "IE": 2372, "SE": 2752, "NO": 2578,
    "DK": 2208, "FI": 2246, "PL": 2616, "CZ": 2203, "RO": 2642, "GR": 2300,
    "TR": 2792, "RU": 2643, "UA": 2804, "BR": 2076, "MX": 2484, "AR": 2032,
    "CL": 2152, "CO": 2170, "PE": 2604, "JP": 2392, "KR": 2410, "CN": 2156,
    "HK": 2344, "TW": 2158, "IN": 2356, "ID": 2360, "TH": 2764, "VN": 2704,
    "MY": 2458, "PH": 2608, "SG": 2702, "AE": 2784, "SA": 2682, "IL": 2376,
    "EG": 2818, "ZA": 2710,
}

COUNTRY_TO_LANGUAGE = {
    "US": "en", "GB": "en", "UK": "en", "CA": "en", "AU": "en", "NZ": "en", "IE": "en",
    "IT": "it", "ES": "es", "FR": "fr", "DE": "de", "PT": "pt", "NL": "nl", "BE": "fr",
    "CH": "de", "AT": "de", "SE": "sv", "NO": "no", "DK": "da", "FI": "fi", "PL": "pl",
    "CZ": "cs", "RO": "ro", "GR": "el", "TR": "tr", "RU": "ru", "UA": "uk", "BR": "pt",
    "MX": "es", "AR": "es", "CL": "es", "CO": "es", "PE": "es", "JP": "ja", "KR": "ko",
    "CN": "zh-CN", "HK": "zh-HK", "TW": "zh-TW", "IN": "en", "ID": "id", "TH": "th",
    "VN": "vi", "MY": "ms", "PH": "en", "SG": "en", "AE": "ar", "SA": "ar", "IL": "he",
    "EG": "ar", "ZA": "en",
}


def location_code(country: str) -> int:
    return COUNTRY_TO_LOCATION_CODE.get(country.upper(), 2840)


def language_code(country: str) -> str:
    return COUNTRY_TO_LANGUAGE.get(country.upper(), "en")
