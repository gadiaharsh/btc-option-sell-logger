
import requests
import time
import csv
from datetime import datetime

# === CONFIG ===
BASE_URL = "https://api.delta.exchange"
SPOT_ENDPOINT = "/v2/tickers/BTCUSDT"
MARKET_DATA_ENDPOINT = "/v2/options/market_data/"
STRIKE_INTERVAL = 200
STRIKE_OFFSETS = [-9, -6, -3, 0, 3, 6, 9]
EXPIRY_DAYS = 3  # T+0, T+1, T+2

# === STRIKE SYMBOL BUILDER ===
def get_expiry_labels():
    from datetime import timedelta
    labels = []
    today = datetime.utcnow()
    for i in range(EXPIRY_DAYS):
        expiry = today + timedelta(days=i)
        labels.append(expiry.strftime("%d%m%y"))
    return labels

def get_current_atm_strike():
    res = requests.get(BASE_URL + SPOT_ENDPOINT)
    spot = float(res.json()['mark_price'])
    return round(spot / STRIKE_INTERVAL) * STRIKE_INTERVAL

def generate_symbols(atm):
    expiries = get_expiry_labels()
    symbols = []
    for exp in expiries:
        for offset in STRIKE_OFFSETS:
            strike = atm + (offset * STRIKE_INTERVAL)
            for opt_type in ['C', 'P']:
                symbol = f"{opt_type}-BTC-{strike}-{exp}"
                symbols.append(symbol)
    return symbols

# === DATA LOGGER ===
def fetch_option_data(symbol):
    try:
        url = BASE_URL + MARKET_DATA_ENDPOINT + symbol
        res = requests.get(url)
        data = res.json()
        return [
            symbol,
            data['mark_price'],
            data.get('delta', 'NA'),
            data.get('open_interest', 'NA')
        ]
    except Exception as e:
        return [symbol, "ERR", "ERR", "ERR"]

def main():
    atm = get_current_atm_strike()
    symbols = generate_symbols(atm)
    print(f"Tracking ATM: {atm} | Total Strikes: {len(symbols)}")

    with open("option_data_log.csv", mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Time", "Symbol", "Price", "Delta", "OI"])

        while True:
            now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            for sym in symbols:
                row = fetch_option_data(sym)
                writer.writerow([now] + row)
                print(f"[{now}] {row}")
            time.sleep(60)

if __name__ == "__main__":
    main()
