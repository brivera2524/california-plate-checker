# config.py

# HTTP Headers
HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": "https://www.dmv.ca.gov",
    "Referer": "https://www.dmv.ca.gov/wasapp/ipp2/startPers.do",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
}

# Payload Template
PAYLOAD_TEMPLATE = {
    "plateType": "Z",
    "plateName": "California 1960s Legacy",
    "plateLength": "7",
    "vehicleType": "AUTO",
    **{f"plateChar{i}": "" for i in range(7)}
}

# URLs
INIT_URL = "https://www.dmv.ca.gov/wasapp/ipp2/initPers.do"
CHECK_URL = "https://www.dmv.ca.gov/wasapp/ipp2/checkPers.do"
