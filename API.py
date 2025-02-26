from flask import Flask, render_template, request, jsonify
import yfinance as yf
import pandas as pd
import numpy as np

app = Flask(__name__)

def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    # Fill the initial NaN values with a backward fill.
    rsi = rsi.fillna(method='bfill')
    return rsi

def compute_macd(series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return macd_line, signal_line

@app.route("/", methods=["GET", "POST"])
def home():
    stock_price = None
    financials = {}
    kpis = {}
    symbol = None
    chart_labels = []  # x-axis labels
    price_data = []    # Price (Close) data

    # Indicator data (empty by default)
    rsi_data = []
    macd_data = []
    macd_signal_data = []
    volume_data = []
    volume_colors = []

    # Defaults
    time_frame = "1M"
    show_rsi = False
    show_macd = False
    show_volume = False

    if request.method == "POST":
        symbol = request.form.get("symbol", "").strip().upper()
        time_frame = request.form.get("time_frame", "1M")
        show_rsi = (request.form.get("rsi") == "on")
        show_macd = (request.form.get("macd") == "on")
        show_volume = (request.form.get("volume") == "on")
        
        if not symbol:
            return render_template(
                "yahoo.html",
                stock_price="Invalid Symbol",
                financials={}, 
                kpis={}, 
                symbol=symbol,
                chart_labels=chart_labels, 
                price_data=price_data,
                time_frame=time_frame,
                show_rsi=show_rsi, 
                show_macd=show_macd, 
                show_volume=show_volume,
                rsi_data=rsi_data, 
                macd_data=macd_data, 
                macd_signal_data=macd_signal_data,
                volume_data=volume_data, 
                volume_colors=volume_colors
            )
        try:
            stock = yf.Ticker(symbol)

            # Get the latest price (from 1d history)
            hist = stock.history(period="1d")
            if not hist.empty:
                stock_price = hist["Close"].iloc[-1]
            else:
                stock_price = "N/A"

            # Financials
            df = stock.financials
            if df is not None and not df.empty:
                financials = df.to_dict()
            else:
                financials = {}

            # KPIs from stock.info
            info = stock.info
            kpis = {
                "P/E Ratio": info.get("trailingPE", "N/A"),
                "P/B Ratio": info.get("priceToBook", "N/A"),
                "EPS": info.get("trailingEps", "N/A"),
                "Revenue Growth": info.get("revenueGrowth", "N/A"),
                "Dividend Yield": info.get("dividendYield", "N/A"),
                "ROE": info.get("returnOnEquity", "N/A"),
                "Free Cash Flow": info.get("freeCashflow", "N/A"),
                "Debt-to-Equity": info.get("debtToEquity", "N/A"),
                "EV/EBITDA": info.get("enterpriseToEbitda", "N/A"),
                "Profit Margins": info.get("profitMargins", "N/A")
            }
            
            # Map time frame to period and interval
            if time_frame == "1D":
                period = "1d"
                interval = "5m"
            elif time_frame == "5D":
                period = "5d"
                interval = "15m"
            elif time_frame == "1M":
                period = "1mo"
                interval = "1d"
            elif time_frame == "6M":
                period = "6mo"
                interval = "1wk"
            elif time_frame == "1Y":
                period = "1y"
                interval = "1mo"
            elif time_frame == "5Y":
                period = "5y"
                interval = "1mo"
            elif time_frame == "Max":
                period = "max"
                interval = "1mo"
            else:
                period = "1mo"
                interval = "1d"

            # For longer time frames (1Y and greater), use daily data to resample to monthly
            if time_frame in ["1Y", "5Y", "Max"]:
                daily_hist = stock.history(period=period, interval="1d")
                if not daily_hist.empty:
                    # Resample daily price to monthly (last available price)
                    price_monthly = daily_hist["Close"].resample("M").last()
                    price_data = price_monthly.tolist()
                    chart_labels = list(price_monthly.index.strftime("%b %Y"))
                    if show_rsi:
                        rsi_daily = compute_rsi(daily_hist["Close"], period=14)
                        rsi_df = pd.DataFrame({"RSI": rsi_daily})
                        rsi_monthly = rsi_df.resample("M").last()
                        rsi_data = rsi_monthly["RSI"].tolist()
                    if show_macd:
                        macd_series, signal_series = compute_macd(daily_hist["Close"])
                        # Resample MACD values to monthly using the last value in each month
                        macd_monthly = pd.DataFrame({"MACD": macd_series, "Signal": signal_series}).resample("M").last()
                        macd_data = macd_monthly["MACD"].tolist()
                        macd_signal_data = macd_monthly["Signal"].tolist()
                    if show_volume:
                        volume_monthly = daily_hist["Volume"].resample("M").last()
                        volume_data = volume_monthly.tolist()
                        volume_colors = []
                        # For volume colors, determine based on daily data within each month,
                        # here we simply use the last day's comparison.
                        for date, row in daily_hist.groupby(pd.Grouper(freq="M")).last().iterrows():
                            if row["Close"] >= row["Open"]:
                                volume_colors.append("green")
                            else:
                                volume_colors.append("red")
                else:
                    chart_labels = []
                    price_data = []
            else:
                # For shorter time frames, use chart_hist directly.
                chart_hist = stock.history(period=period, interval=interval)
                if not chart_hist.empty:
                    if time_frame == "1D":
                        chart_labels = list(chart_hist.index.strftime("%H:%M"))
                    elif time_frame in ["5D", "1M", "6M"]:
                        chart_labels = list(chart_hist.index.strftime("%b %d"))
                    else:
                        chart_labels = list(chart_hist.index.strftime("%b %Y"))
                    price_data = list(chart_hist["Close"])
                    if show_rsi:
                        rsi_period = 14
                        if len(chart_hist["Close"]) < rsi_period:
                            rsi_period = len(chart_hist["Close"]) if len(chart_hist["Close"]) > 0 else 14
                        rsi_series = compute_rsi(chart_hist["Close"], period=rsi_period)
                        rsi_data = rsi_series.tolist()
                    if show_macd:
                        macd_series, signal_series = compute_macd(chart_hist["Close"])
                        macd_data = macd_series.tolist()
                        macd_signal_data = signal_series.tolist()
                    if show_volume:
                        volume_series = chart_hist["Volume"].tolist()
                        volume_data = volume_series
                        for idx, row in chart_hist.iterrows():
                            if row["Close"] >= row["Open"]:
                                volume_colors.append("green")
                            else:
                                volume_colors.append("red")
                else:
                    chart_labels = []
                    price_data = []
        except Exception as e:
            print(f"Error fetching data: {e}")
            stock_price = "Error fetching stock data"
            financials = {}
            kpis = {}
            chart_labels = []
            price_data = []
            rsi_data = []
            macd_data = []
            macd_signal_data = []
            volume_data = []
            volume_colors = []

    return render_template(
        "yahoo.html",
        stock_price=stock_price,
        financials=financials,
        kpis=kpis,
        symbol=symbol,
        chart_labels=chart_labels,
        price_data=price_data,
        time_frame=time_frame,
        show_rsi=show_rsi,
        show_macd=show_macd,
        show_volume=show_volume,
        rsi_data=rsi_data,
        macd_data=macd_data,
        macd_signal_data=macd_signal_data,
        volume_data=volume_data,
        volume_colors=volume_colors
    )

@app.route("/price/<symbol>")
def price(symbol):
    try:
        symbol = symbol.strip().upper()
        stock = yf.Ticker(symbol)
        hist = stock.history(period="1d")
        if not hist.empty:
            latest_price = hist["Close"].iloc[-1]
        else:
            latest_price = None
        return jsonify({"price": latest_price})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5001)
