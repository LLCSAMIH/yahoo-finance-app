from flask import Flask, render_template, request
import yfinance as yf
import pandas as pd

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def home():
    stock_price = None
    financials = {}

    if request.method == "POST":
        symbol = request.form.get("symbol", "").strip().upper()
        
        if not symbol:
            return render_template("yahoo.html", stock_price="Invalid Symbol", financials={})
        
        try:
            stock = yf.Ticker(symbol)

            # Get stock price
            hist = stock.history(period="1d")
            if not hist.empty:
                stock_price = hist["Close"].iloc[-1]
            else:
                stock_price = "N/A"

            # Get financials
            df = stock.financials
            if df is not None and not df.empty:
                financials = df.to_dict()
            else:
                financials = {}

        except Exception as e:
            print(f"Error fetching data: {e}")  # Debugging output
            stock_price = "Error fetching stock data"
            financials = {}

    return render_template("yahoo.html", stock_price=stock_price, financials=financials)

if __name__ == "__main__":
    app.run(debug=True)
