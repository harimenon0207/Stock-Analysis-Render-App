import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from dash import dash_table
import plotly.graph_objs as go
import yfinance as yf
import pandas as pd
import numpy as np
from prophet import Prophet
from datetime import datetime

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# Read in list of Stock Tickers

tckrs = pd.read_csv('watch_list_tickers.csv',header=None,names = ['Tickers','NA'])
tckrs = ','.join(tckrs['Tickers'].unique().astype(str).flatten())

# Layout of the app
app.layout = dbc.Container([
    html.H1("Stock Price Analysis & Investment Recommendations"),
    html.Hr(),
    html.H4("List out all Stock Tickers required for analysis"),    
    dbc.Row([
        dbc.Col([
            dcc.Input(
                id='stock-input', 
                type='text', 
                placeholder='Enter stock tickers separated by comma', 
                value=tckrs,
                style={'width':1000}
            ),
        ], width=12)
    ]),
    html.Br(),
    dbc.Row([
        dbc.Col([
            dbc.Button('Get latest data', id='update-button', n_clicks=0, color='primary', className='ml-2'),
            html.Br(),
            html.Div(id='latest-update', children='No data fetched yet'),
        ], width=6)
    ]),

    html.Hr(),


    dbc.Row([
        dbc.Col([
            html.H4('Stock prices under forecast(Last 2 days)'),
            dash_table.DataTable(id='underpriced-table', columns=[
                {'name': 'Ticker', 'id': 'ticker'},
                {'name': 'Latest Price', 'id': 'latest_price'},
                {'name': '1 Week Prediction Avg', 'id': 'prediction_avg'},
                {'name': '% Below Prediction', 'id': 'percent_below'}],
                style_as_list_view=True,
                style_cell={'padding': '5px'},
                style_header={'backgroundColor': 'white','fontWeight': 'bold'}
                ),
        ], width=6),
        dbc.Col([
            html.H4('Stock prices above forecast(Last 2 days)'),
            dash_table.DataTable(id='overpriced-table', columns=[
                {'name': 'Ticker', 'id': 'ticker'},
                {'name': 'Latest Price', 'id': 'latest_price'},
                {'name': '1 Week Prediction Avg', 'id': 'prediction_avg'},
                {'name': '% Above Prediction', 'id': 'percent_above'}],
                style_as_list_view=True,
                style_cell={'padding': '5px'},
                style_header={'backgroundColor': 'white','fontWeight': 'bold'}                
                ),
        ], width=6)
    ]),
    html.Hr(),

    dbc.Row([
        dbc.Col([
            html.H3('Select a Ticker below for deeper analysis'),
            dcc.Dropdown(id='ticker-dropdown', multi=False, placeholder='Select a Stock'),
            dcc.Graph(id='price-chart'),
        ], width=12)
    ]),
    html.Hr(),

    dbc.Row([
        dbc.Col([
            html.H3('Historical & Predicted Data (Last 60 days)'),
            dcc.Graph(id='historical-predicted-chart'),
        ], width=12)
    ]),

    dbc.Row([
        dbc.Col([
            dbc.Button('Download Data', id='download-button', color='secondary'),
            dcc.Download(id="download-data")
        ], width=12)
    ]),
])

# Callback for updating stock data and predictions for all tickers
@app.callback(
    [Output('ticker-dropdown', 'options'),
     Output('latest-update', 'children'),
     Output('underpriced-table', 'data'),
     Output('overpriced-table', 'data')],
    Input('update-button', 'n_clicks'),
    State('stock-input', 'value')
)
def update_stock_data(n_clicks, tickers):
    if n_clicks > 0:
        tickers = [ticker.strip() for ticker in tickers.split(',')]
        underpriced_data = []
        overpriced_data = []
        
        # Fetch stock data and run Prophet predictions for all tickers
        for ticker in tickers:
            stock_data = yf.download(ticker, period='1y')
            stock_data.columns = stock_data.columns.map('_'.join)
            stock_data.columns = ['Close','High','Low','Open','Volume']
            # Remove the last 7 days for training
            last_7_days = stock_data.iloc[-7:]
            train_data = stock_data.iloc[:-7]

            # Prophet model for Bayesian structural time series forecasting
            df = train_data.reset_index()[['Date', 'Close']]
            df.columns = ['ds', 'y']
            model = Prophet()
            model.fit(df)

            # Predict for the next 14 days
            future = model.make_future_dataframe(periods=14)
            forecast = model.predict(future)
            forecast_tail = forecast[['ds', 'yhat']].iloc[-14:]  # Take the last 14 days of predictions
            last_7_days_forecast = forecast_tail.iloc[:7]  # First 7 are the predictions for missing days
            avg_prediction = last_7_days_forecast['yhat'].mean()
            latest_price = last_7_days['Close'].iloc[-1]
            last_2_days_avg = last_7_days['Close'][-2:].mean()

            # Identify underpriced or overpriced stocks
            if last_2_days_avg < avg_prediction * 0.95:
                underpriced_data.append({
                    'ticker': ticker,
                    'latest_price': f'{latest_price:.2f}',
                    'prediction_avg': f'{avg_prediction:.2f}',
                    'percent_below': f'{(avg_prediction - last_2_days_avg) / avg_prediction * 100:.2f}%'
                })
            elif last_2_days_avg > avg_prediction * 1.05:
                overpriced_data.append({
                    'ticker': ticker,
                    'latest_price': f'{latest_price:.2f}',
                    'prediction_avg': f'{avg_prediction:.2f}',
                    'percent_above': f'{(last_2_days_avg - avg_prediction) / avg_prediction * 100:.2f}%'
                })

        # Get the latest timestamp
        latest_update = f"Latest data fetched on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        # Dropdown options for the chart
        options = [{'label': ticker, 'value': ticker} for ticker in tickers]

        return options, latest_update, underpriced_data, overpriced_data

    return [], 'No data fetched yet', [], []

# Callback for displaying the price chart with moving averages
@app.callback(
    Output('price-chart', 'figure'),
    Input('ticker-dropdown', 'value'),
    State('stock-input', 'value')
)
def update_chart(selected_ticker, tickers):
    if not selected_ticker:
        return go.Figure()
    
    tickers = [ticker.strip() for ticker in tickers.split(',')]
    stock_data = yf.download(selected_ticker, period='1y')
    stock_data.columns = stock_data.columns.map('_'.join)
    stock_data.columns = ['Close','High','Low','Open','Volume']
    # Calculate 7-day and 21-day moving averages
    stock_data['7-day MA'] = stock_data['Close'].rolling(window=7).mean()
    stock_data['21-day MA'] = stock_data['Close'].rolling(window=21).mean()

    # Plotting the stock price and moving averages
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Close'], mode='lines', name=f'{selected_ticker} Price'))
    fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['7-day MA'], mode='lines', name='7-Day MA'))
    fig.add_trace(go.Scatter(x=stock_data.index, y=stock_data['21-day MA'], mode='lines', name='21-Day MA'))

    # Add hover data for date and price
    fig.update_layout(title=f'Stock Prices of {selected_ticker}', hovermode='x unified')

    return fig

# Callback for displaying the historical and predicted stock data in a combined chart
@app.callback(
    Output('historical-predicted-chart', 'figure'),
    Input('ticker-dropdown', 'value')
)
def update_historical_predicted_chart(selected_ticker):
    if not selected_ticker:
        return go.Figure()
    
    stock_data = yf.download(selected_ticker, period='1y')
    stock_data.columns = stock_data.columns.map('_'.join)
    stock_data.columns = ['Close','High','Low','Open','Volume']
    # Remove the last 7 days for training
    last_7_days = stock_data.iloc[-7:]
    train_data = stock_data.iloc[:-7]

    # Prophet model for Bayesian structural time series forecasting
    df = train_data.reset_index()[['Date', 'Close']]
    df.columns = ['ds', 'y']
    model = Prophet()
    model.fit(df)
    
    # Predict for the next 14 days
    future = model.make_future_dataframe(periods=14)
    forecast = model.predict(future)

    # Plot historical data
    fig = go.Figure()
    stock_data_last_60_days = stock_data.tail(60)
    fig.add_trace(go.Scatter(x=stock_data_last_60_days.index, y=stock_data_last_60_days['Close'], mode='lines', name=f'{selected_ticker} Price'))

    # Plot predicted data (last 14 days)
    predicted_last_14_days = forecast[['ds', 'yhat']].tail(14)
    fig.add_trace(go.Scatter(x=predicted_last_14_days['ds'], y=predicted_last_14_days['yhat'], mode='lines+markers', name=f'{selected_ticker} Predicted Price'))

    # Add hover data
    fig.update_layout(title=f'Historical and Predicted Prices for {selected_ticker}', hovermode='x unified')

    return fig

# Callback to download stock data
@app.callback(
    Output("download-data", "data"),
    Input("download-button", "n_clicks"),
    State('stock-input', 'value')
)
def download_stock_data(n_clicks, tickers):
    if n_clicks:
        tickers = [ticker.strip() for ticker in tickers.split(',')]
        data = []
        for ticker in tickers:
            stock_data = yf.download(ticker, period='1y')
            stock_data.columns = stock_data.columns.map('_'.join)
            stock_data.columns = ['Close','High','Low','Open','Volume']
            stock_data.reset_index(inplace=True)
            stock_data['Ticker'] = ticker
            data.append(stock_data[['Date', 'Ticker', 'Close']])

        df = pd.concat(data)
        return dcc.send_data_frame(df.to_csv, filename="stock_data.csv")
    return None

# Run the app locally
if __name__ == '__main__':
    app.run_server(debug=True)
