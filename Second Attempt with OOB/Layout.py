from dash import Dash, html, dcc, Input, Output, State
import plotly.express as px
from dash import dash_table
import dash_bootstrap_components as dbc  
from main import sentiment_df

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP]) 

app.layout = html.Div(children=[
    html.H1(children='Sentiment Analysis Dashboard'),

    # Dropdown for selecting the column
    dcc.Dropdown(
        id='column-selector',
        options=[
            {'label': col, 'value': col} for col in sentiment_df.columns[1:]
        ],
        value=sentiment_df.columns[1],  # Default value
        multi=False
    ),

    # Pagination controls
    dcc.RangeSlider(
        id='pagination-slider',
        min=0,
        max=len(sentiment_df),
        step=1,
        marks={i: str(i) for i in range(0, len(sentiment_df), 10)},
        value=[0, 10]
    ),

    # Graph for sentiment analysis histogram
    dcc.Graph(
        id='sentiment-histogram'
    ),

    # Export button
    dbc.Button("Export Data", id="export-button", color="primary", className="mr-2"),

    # Button to update the database
    dbc.Button("Update Database", id="update-database-button", color="danger"),

    # Add a table
    dash_table.DataTable(
        id='sentiment-table',
        style_table={'height': '400px', 'overflowY': 'auto'},
        page_size=10  # Set the initial page size
    )
])

# Define a callback to update the histogram, table, and pagination based on user input
@app.callback(
    [Output('sentiment-histogram', 'figure'), Output('sentiment-table', 'data'), Output('sentiment-table', 'page_size')],
    Input('column-selector', 'value'),
    Input('pagination-slider', 'value'),
    Input('export-button', 'n_clicks'),
    Input('update-database-button', 'n_clicks'),
    State('sentiment-table', 'page_current'),  # Get the current page
)

def update_dashboard(selected_column, slider_value, export_clicks, update_db_clicks, current_page):
    # Slice the DataFrame based on the pagination slider value
    start_idx, end_idx = slider_value
    paginated_df = sentiment_df.iloc[start_idx:end_idx]

    # Create the histogram
    fig = px.histogram(paginated_df, x=selected_column, nbins=10, title=f"Sentiment Analysis Histogram ({selected_column})")

    # Update the table data
    table_data = paginated_df.to_dict('records')

    # Determine the new page size based on the total rows
    new_page_size = min(10, len(paginated_df))

    return fig, table_data, new_page_size

if __name__ == '__main__':
    app.run(debug=True)