# Stock-Analysis-Render-App

Welcome to the Stock Price Analysis & Investment Recommendations app! This application is designed to assist users in identifying underpriced and overpriced stocks by analyzing recent stock price trends and predictions. The app is hosted on Render and is accessible at the following URL: [Stock Price Analysis App](https://stockscreenerapp-ro3v.onrender.com/)


## User Guide
#### Overview
This application enables users to analyze the performance of up to 30 stock tickers at once and provides actionable insights into their current valuation compared to predicted values.

## Features
#### Stock Selection:

Users can input up to 30 stock tickers, comma-separated, into a text box.
A default list of tickers is pre-populated for convenience.
#### Price Analysis:

The app retrieves the last one year of stock price data for each ticker.
It generates predictions for the past 14 days using a forecasting model and compares these with the actual prices.
#### Actionable Insights:

Stocks where the actual price deviates by more than 5% (up or down) from the prediction over the last 2 days are highlighted in a results table.
#### Deep Dive Analysis:

Users can select individual stock tickers from a dropdown for detailed analysis.
This view includes:
Price trends over the past year.
7-day and 21-day moving averages.
Model-generated predictions.


## Technical Details
#### Tools & Libraries
Stock Price Data: [Yahoo Finance](https://finance.yahoo.com/)

Forecasting Model: FB Prophet

Programming Language: Python

User Interface: Dash

## How to Use the App
1. Navigate to the app URL: https://stockscreenerapp-ro3v.onrender.com/
2. Enter a comma-separated list of up to 30 stock tickers in the text box or use the default list.
3. Press the Submit button to start the analysis.
4. Review the results in the generated table to identify underpriced or overpriced stocks.
5. Use the dropdown menu for detailed insights into individual stock performance and predictions.

## Contributing
This repository welcomes contributions. If you'd like to improve or extend the functionality, please fork the repository and submit a pull request. For any bugs or feature requests, feel free to open an issue.
