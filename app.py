import json
import threading
import pandas as pd
from collections import deque
from dash import Dash, html, dcc
import plotly.graph_objs as go
import websocket

# Store last 200 trades
orders = deque(maxlen=200)

# === Real-time WebSocket connection to Binance ===
def handle_trade(trade):
    """Process each trade message."""
    side = "Buy" if trade["m"] == False else "Sell"  # 'm' = true means maker is seller (so trade is a buy)
    price = float(trade["p"])
    size = float(trade["q"])
    orders.append({"side": side, "size": size, "price": price})

def on_message(ws, message):
    data = json.loads(message)
    handle_trade(data)

def on_error(ws, error):
    print("WebSocket error:", error)

def on_close(ws, close_status_code, close_msg):
    print("WebSocket closed")

def start_stream():
    socket = "wss://stream.binance.com:9443/ws/btcusdt@trade"
    ws = websocket.WebSocketApp(socket, on_message=on_message, on_error=on_error, on_close=on_close)
    ws.run_forever()

# Start WebSocket thread
threading.Thread(target=start_stream, daemon=True).start()

# === Dash App ===
app = Dash(__name__)
app.title = "Live Order Flow Visualizer"

app.layout = html.Div([
    html.H2("💹 BTC/USDT Live Order Flow", style={"textAlign": "center"}),
    dcc.Graph(id="order-bubbles", style={"height": "70vh"}),
    dcc.Graph(id="heatmap", style={"height": "40vh"}),
    dcc.Interval(id="interval", interval=1000, n_intervals=0)
])

@app.callback(
    [dcc.Output("order-bubbles", "figure"),
     dcc.Output("heatmap", "figure")],
    [dcc.Input("interval", "n_intervals")]
)
def update_graphs(n):
    df = pd.DataFrame(orders)
    if df.empty:
        return go.Figure(), go.Figure()

    colors = df["side"].map({"Buy": "green", "Sell": "red"})

    # Bubbles = each live order
    bubble_fig = go.Figure(data=[
        go.Scatter(
            x=df.index,
            y=df["price"],
            mode="markers+text",
            marker=dict(size=df["size"] * 5, color=colors, opacity=0.6),
            text=df["size"].astype(str),
            textposition="top center"
        )
    ])
    bubble_fig.update_layout(title="Live Market Orders", xaxis_title="Trade Index", yaxis_title="Price")

    # Heatmap = price levels & total volume
    heatmap_data = pd.pivot_table(df, values="size", index="price", columns="side", aggfunc="sum", fill_value=0)
    heatmap_fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=heatmap_data.columns,
        y=heatmap_data.index,
        colorscale="RdYlGn"
    ))
    heatmap_fig.update_layout(title="Order Size Heatmap")

    return bubble_fig, heatmap_fig

if __name__ == "__main__":
    app.run_server(debug=True)
