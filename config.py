"""
config.py

This file contains configuration settings for the license plate availability checker,
including URLs, HTTP headers, and payload templates for DMV API requests.
"""

from typing import Dict, Any
from yarl import URL

# URLs
REFERER_URL: str = "https://www.dmv.ca.gov/wasapp/ipp2/initPers.do"
CHECK_URL: str = "https://www.dmv.ca.gov/wasapp/ipp2/checkPers.do"
CHECK_URL_YARL: URL = URL(CHECK_URL)

# HTTP Headers for session validation
INITIAL_PAYLOAD: Dict[str, str] = {
    "acknowledged": "true", 
    "_acknowledged": "on" 
}

INITIAL_HEADERS: Dict[str, str] = {
    "Referer": REFERER_URL,
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
}

# HTTP Headers for plate check requests
HEADERS: Dict[str, str] = {
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": "https://www.dmv.ca.gov",
    "Referer": "https://www.dmv.ca.gov/wasapp/ipp2/startPers.do",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
}

# Payload Template
PAYLOAD_TEMPLATE: Dict[str, str] = {
    "plateType": "Z",
    "plateName": "California 1960s Legacy",
    "plateLength": "7",
    "vehicleType": "AUTO",
    **{f"plateChar{i}": "" for i in range(7)}
}


