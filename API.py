from flask import Flask, render_template, request
import yfinance as yf

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def home():
    stock_price = None
    financials = {}

    if request.method == "POST":
        symbol = request.form.get("symbol")
        if symbol:
            stock = yf.Ticker(symbol)
            
            # Get stock price
            stock_price = stock.history(period="1d")["Close"].iloc[-1] if not stock.history(period="1d").empty else "N/A"
            
            # Get financials
            financial_data = stock.financials.to_dict() if stock.financials is not None else {}

            # Convert financial data to dictionary
            for metric, values in financial_data.items():
                financials[metric] = {str(year): val for year, val in values.items()}

    return render_template("yahoo.html", stock_price=stock_price, financials=financials)

if __name__ == "__main__":
    app.run(debug=True)
