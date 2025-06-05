from dash import Dash, html, register_page, dcc, Input, Output, callback, dash_table
import dash_bootstrap_components as dbc
from datetime import datetime


from data_utils import get_collection_history, get_bin_data


#Register this file as a Dash page
register_page(__name__, path="/bin-collection-history", name="Collection History")





###################################################################
# Layout
###################################################################
layout = html.Div([
    dbc.Container([
        dbc.Row([
            #Page Header
            dbc.Col(
                html.H4("Collection History", className="mb-4"),
                width=12
            )
        ]),

        dbc.Row([

        ])

    ])

])