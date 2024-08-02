# interactive_time_series_dashboard.py

import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Generate mock data
def generate_mock_data(start_date, num_days=7):
    data = []
    for i in range(num_days):
        date = start_date + timedelta(days=i)
        for second in range(86400):  # 86400 seconds in a day
            timestamp = date + timedelta(seconds=second)
            value = np.random.rand() * 100 + 50 * np.sin(second * 2 * np.pi / 86400)  # Random values with a daily cycle
            data.append((timestamp, value))
    return pd.DataFrame(data, columns=['timestamp', 'value'])

# Create mock data
start_date = datetime(2024, 1, 1)
df = generate_mock_data(start_date)

# Calculate daily averages
daily_avg = df.groupby(df['timestamp'].dt.date)['value'].mean().reset_index()
daily_avg.columns = ['date', 'value']

# Calculate hourly averages
df['date'] = df['timestamp'].dt.date
df['hour'] = df['timestamp'].dt.hour
hourly_avg = df.groupby(['date', 'hour'])['value'].mean().reset_index()

# Create timestamp columns for plotting
daily_avg['timestamp'] = pd.to_datetime(daily_avg['date'])
hourly_avg['timestamp'] = pd.to_datetime(hourly_avg['date']) + pd.to_timedelta(hourly_avg['hour'], unit='h')



# Initialize the Dash app
app = dash.Dash(__name__)

# Define the layout
app.layout = html.Div([
    dcc.Graph(id='chart'),
    html.Div(id='click-data'),
    html.Button('Reset to Weekly View', id='reset-button', n_clicks=0),
    dcc.Store(id='current-view', data='weekly')
])

# Callback to update the graph
@app.callback(
    Output('chart', 'figure'),
    Output('current-view', 'data'),
    Input('chart', 'clickData'),
    Input('reset-button', 'n_clicks'),
    State('current-view', 'data')
)
def update_graph(clickData, n_clicks, current_view):
    ctx = dash.callback_context
    if not ctx.triggered:
        return create_weekly_chart(), 'weekly'
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id == 'reset-button':
        return create_weekly_chart(), 'weekly'
    elif trigger_id == 'chart' and clickData is not None:
        if current_view == 'weekly':
            clicked_date = pd.to_datetime(clickData['points'][0]['x']).date()
            return create_daily_chart(clicked_date), 'daily'
        elif current_view == 'daily':
            clicked_datetime = pd.to_datetime(clickData['points'][0]['x'])
            return create_hourly_chart(clicked_datetime.date(), clicked_datetime.hour), 'hourly'
        elif current_view == 'hourly':
            clicked_datetime = pd.to_datetime(clickData['points'][0]['x'])
            return create_second_chart(clicked_datetime.replace(minute=0, second=0)), 'second'
    
    return create_weekly_chart(), 'weekly'

def create_weekly_chart():
    return {
        'data': [go.Scatter(
            x=daily_avg['timestamp'],
            y=daily_avg['value'],
            mode='markers+lines',
            marker=dict(size=10),
            hovertemplate='Date: %{x|%Y-%m-%d}<br>Average Value: %{y:.2f}<extra></extra>'
        )],
        'layout': go.Layout(
            title='Weekly Overview (Click on a point to see daily data)',
            xaxis=dict(title='Date'),
            yaxis=dict(title='Average Value')
        )
    }

def create_daily_chart(date):
    day_data = hourly_avg[hourly_avg['timestamp'].dt.date == date]
    return {
        'data': [go.Scatter(
            x=day_data['timestamp'],
            y=day_data['value'],
            mode='markers+lines',
            marker=dict(size=8),
            hovertemplate='Time: %{x|%H:%M}<br>Average Value: %{y:.2f}<extra></extra>'
        )],
        'layout': go.Layout(
            title=f'Hourly Data for {date} (Click on a point to see that hour\'s data)',
            xaxis=dict(
                title='Time',
                tickformat='%H:%M',
                dtick=3600000  # show ticks every hour
            ),
            yaxis=dict(title='Value')
        )
    }

def create_hourly_chart(date, hour):
    start_time = pd.Timestamp(date) + pd.Timedelta(hours=hour)
    end_time = start_time + pd.Timedelta(hours=1)
    hour_data = df[(df['timestamp'] >= start_time) & (df['timestamp'] < end_time)]
    
    return {
        'data': [go.Scatter(
            x=hour_data['timestamp'],
            y=hour_data['value'],
            mode='markers+lines',
            marker=dict(size=6),
            hovertemplate='Time: %{x|%H:%M:%S}<br>Value: %{y:.2f}<extra></extra>'
        )],
        'layout': go.Layout(
            title=f'Minute Data for {date} {hour:02d}:00 (Click on a point to see second-level data)',
            xaxis=dict(
                title='Time',
                tickformat='%H:%M:%S',
                dtick=300000  # show ticks every 5 minutes
            ),
            yaxis=dict(title='Value')
        )
    }

def create_second_chart(start_time):
    end_time = start_time + pd.Timedelta(minutes=1)
    minute_data = df[(df['timestamp'] >= start_time) & (df['timestamp'] < end_time)]
    
    return {
        'data': [go.Scatter(
            x=minute_data['timestamp'],
            y=minute_data['value'],
            mode='markers+lines',
            marker=dict(size=4),
            hovertemplate='Time: %{x|%H:%M:%S}<br>Value: %{y:.2f}<extra></extra>'
        )],
        'layout': go.Layout(
            title=f'Second-level Data for {start_time.strftime("%Y-%m-%d %H:%M")}',
            xaxis=dict(
                title='Time',
                tickformat='%H:%M:%S',
                dtick=1000  # show ticks every second
            ),
            yaxis=dict(title='Value')
        )
    }

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)