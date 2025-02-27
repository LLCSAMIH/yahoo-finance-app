from flask import Flask, render_template, request, jsonify
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Binance API key (replace with your actual key)
BINANCE_API_KEY = "WivcMWdjmRQVdXvxqcrdXA8k82QUxNyilXMeUr3Fi8ii1IqbH4lrCPmPjHRZbzkn"

app = Flask(__name__)

def get_binance_ticker(symbol):
    """Fetch the current ticker price from Binance for a given crypto pair."""
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    headers = {"X-MBX-APIKEY": BINANCE_API_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return {}

def get_binance_klines(symbol, interval="1d", limit=30):
    """Fetch historical klines from Binance for a given symbol."""
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    headers = {"X-MBX-APIKEY": BINANCE_API_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return []

@app.template_filter('datetimeformat')
def datetimeformat_filter(timestamp):
    """Custom filter to format Unix timestamps."""
    return datetime.fromtimestamp(timestamp).strftime('%b %d, %Y %H:%M')

@app.route("/crypto", methods=["GET", "POST"])
def crypto():
    crypto_price = None
    chart_labels = []  # x-axis labels for chart
    price_data = []    # Price (close) data for chart
    crypto_data = {}   # Latest ticker data from Binance
    time_frame = "1M"
    show_rsi = False    # Placeholder if you wish to compute indicators later
    show_macd = False
    show_volume = False

    if request.method == "POST":
        symbol = request.form.get("symbol", "").strip().upper()
        time_frame = request.form.get("time_frame", "1M")
        show_rsi = (request.form.get("rsi") == "on")
        show_macd = (request.form.get("macd") == "on")
        show_volume = (request.form.get("volume") == "on")
        
        if not symbol:
            return render_template("crypto.html",
                                   crypto_price="Invalid Symbol",
                                   symbol="",
                                   chart_labels=[],
                                   price_data=[],
                                   crypto_data={},
                                   time_frame=time_frame,
                                   show_rsi=show_rsi,
                                   show_macd=show_macd,
                                   show_volume=show_volume)
        try:
            # Get current ticker data from Binance
            ticker_data = get_binance_ticker(symbol)
            if ticker_data and "price" in ticker_data:
                crypto_price = float(ticker_data["price"])
            else:
                crypto_price = "N/A"
            crypto_data = ticker_data

            # Map the selected time frame to an interval and limit for Binance klines.
            if time_frame == "1D":
                interval = "5m"
                limit = 288  # Approximately 24 hours of 5m candles
            elif time_frame == "5D":
                interval = "15m"
                limit = 480  # Approximate; adjust as needed
            elif time_frame == "1M":
                interval = "1d"
                limit = 30
            elif time_frame == "6M":
                interval = "1d"
                limit = 180
            elif time_frame == "1Y":
                interval = "1d"
                limit = 365
            elif time_frame == "5Y":
                interval = "1d"
                limit = 1825
            elif time_frame == "Max":
                interval = "1d"
                limit = 1000  # Binance often limits to 1000 candles
            else:
                interval = "1d"
                limit = 30

            # Get historical kline data from Binance
            kline_data = get_binance_klines(symbol, interval=interval, limit=limit)
            if kline_data:
                # Each kline is a list: [openTime, open, high, low, close, volume, closeTime, ...]
                chart_labels = [datetime.fromtimestamp(item[0] / 1000).strftime("%b %d") for item in kline_data]
                price_data = [float(item[4]) for item in kline_data]
            else:
                chart_labels = []
                price_data = []
        except Exception as e:
            print(f"Error fetching crypto data: {e}")
            crypto_price = "Error"
            chart_labels = []
            price_data = []
            crypto_data = {}
        
        return render_template("crypto.html",
                               crypto_price=crypto_price,
                               symbol=symbol,
                               chart_labels=chart_labels,
                               price_data=price_data,
                               crypto_data=crypto_data,
                               time_frame=time_frame,
                               show_rsi=show_rsi,
                               show_macd=show_macd,
                               show_volume=show_volume)
    else:
        # GET request - just render an empty form.
        return render_template("crypto.html",
                               crypto_price=crypto_price,
                               symbol="",
                               chart_labels=[],
                               price_data=[],
                               crypto_data=crypto_data,
                               time_frame=time_frame,
                               show_rsi=show_rsi,
                               show_macd=show_macd,
                               show_volume=show_volume)

@app.route("/crypto/price/<symbol>")
def crypto_price_route(symbol):
    try:
        symbol = symbol.strip().upper()
        data = get_binance_ticker(symbol)
        if data and "price" in data:
            price = float(data["price"])
        else:
            price = None
        return jsonify({"price": price})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5001)
