<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stock Data and Financials</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
        }
        h1 {
            text-align: center;
        }
        form {
            text-align: center;
            margin-bottom: 20px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th, td {
            padding: 10px;
            text-align: center;
            border: 1px solid #ddd;
        }
        th {
            background-color: #f2f2f2;
        }
    </style>
</head>
<body>
    <h1>Enter a Stock Ticker to Retrieve Data</h1>
    <form method="POST">
        <input type="text" name="symbol" placeholder="Enter Stock Ticker" required>
        <button type="submit">Get Data</button>
    </form>

    {% if stock_price %}
        <h2>Stock Data for {{ symbol }}</h2>
        <p><strong>Latest Stock Price:</strong> ${{ stock_price }}</p>
        
        {% if financials is not none %}
        <h3>Financial Data</h3>
        <table>
            <thead>
                <tr>
                    <th>Metric</th>
                    {% for col in financials.columns %}
                        <th>{{ col }}</th>
                    {% endfor %}
                </tr>
            </thead>
            <tbody>
                {% for index, row in financials.iterrows() %}
                    <tr>
                        <td>{{ index }}</td>
                        {% for value in row %}
                            <td>{{ value }}</td>
                        {% endfor %}
                    </tr>
                {% endfor %}
            </tbody>
        </table>
        {% endif %}
    {% endif %}
</body>
</html>
