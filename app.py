import random
import time
import threading
import pandas as pd
from collections import deque
from dash import Dash, html, dcc
import plotly.graph_objs as go

# Simulated live order flow data
orders = deque(maxlen=100)

def generate_fake_orders():
    while True:
        side = random.choice(["Buy", "Sell"])
        size = round(random.uniform(0.5, 10.0), 2)
        price = round(random.uniform(100, 200), 2)
        orders.append({"side": side, "size": size, "price": price})
        time.sleep(0.8)

# Start fake order feed
threading.Thread(target=generate_fake_orders, daemon=True).start()

# Dash app
app = Dash(__name__)
app.title = "Order Flow Visual"

app.layout = html.Div([
    html.H2("🟢 Order Flow Visualizer", style={"textAlign": "center"}),
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
    bubble_fig.update_layout(title="Live Market Orders", xaxis_title="Time", yaxis_title="Price")

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
