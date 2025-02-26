from flask import Flask, request, render_template
import yfinance as yf

app = Flask(__name__)

# Function to get stock data
def get_stock_data(symbol):
    ticker = yf.Ticker(symbol)
    data = ticker.history(period='1d')
    financials = ticker.financials

    if data.empty:
        return None

    return {
        "symbol": symbol,
        "stock_price": data['Close'][0],
        "financials": financials.to_dict()
    }

# Home Route
@app.route('/')
def home():
    return render_template("yahoo.html")  # Flask expects this inside /templates/

# API Route
@app.route('/get_stock_data', methods=['POST'])
def stock_data():
    symbol = request.form.get("symbol")
    if not symbol:
        return render_template("yahoo.html", error="Stock symbol is required")
    
    stock_info = get_stock_data(symbol)
    if not stock_info:
        return render_template("yahoo.html", error="Invalid stock symbol")

    return render_template("yahoo.html", stock_price=stock_info["stock_price"], symbol=symbol, financials=stock_info["financials"])

if __name__ == '__main__':
    app.run(debug=True, port=5001)

