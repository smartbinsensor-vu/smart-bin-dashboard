from dash import Dash, html, dcc, page_container, page_registry
import dash_bootstrap_components as dbc
import callbacks
from layouts import sidebar, floating_bins_menu, CONTENT_STYLE

#Dash constructor: initialises the app
app = Dash(
    __name__, #Tells Dash this is the main script
    use_pages=True, #Enables multi-page support
    suppress_callback_exceptions=True, #Suppresses errors in callback components when not found as they'll show up later ater loading
    external_stylesheets=[
        dbc.themes.FLATLY, 
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css",
    ]
)
app.title = "Smart Bin Dashboard"

#App layout
def serve_layout():
    return html.Div([
        dcc.Store(id="sidebar-state", data={"collapsed": False}, storage_type="session"), #Keeps track of if the sidebar is collapsed
        dcc.Store(id="bins-submenu-state", data={"open": False}), #Keeps track of if the bins submenu is open
        dcc.Location(id="url", refresh=False), #Keeps track of the current URL     
        sidebar, #Sidebar component
        floating_bins_menu, #Floating bins submenu component
        
        #Auto update the alerts data store every 15 min
        dcc.Interval(
            id="alerts-data-update-interval",
            interval=900000,  #15 minutes in milliseconds
            n_intervals=0 #updates on every page refresh, resets n_intervals back to 0
        ),
        #Store for the get_alerts_data() results shared with alerts.py
        dcc.Store(id="alerts-data-store", storage_type="session"),
        
        #page content auto-switches via page_container
        html.Div(page_container, id="page-content", style=CONTENT_STYLE),
        html.Div(id="outside-click-overlay", n_clicks=0, style={"display": "none"}), #Used to hide the floating submenu when clicking outside of it
    ])

app.layout = serve_layout


#Runs the app on the local development server, with live-reloading
if __name__ == '__main__':
    app.run(debug=True)