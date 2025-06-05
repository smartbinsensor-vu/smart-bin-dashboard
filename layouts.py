#Design of the dashboard app here. Includes layouts, components, styles.
import dash_bootstrap_components as dbc
from dash import html, dcc

#Styles
##########################################################
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "14rem",
    "padding": "2rem 1rem",
    "background-color": "#542978", #purple sidebar bg
    "color": "#FFFFFF", #sidebar title colour
    "transition": "width 0.2s",
    "z-index": 100,
    "border-right": "1px solid",
    "boxShadow": "2px 0 6px rgba(0, 0, 0, 0.1)",  #right shadow, transparent black
	"overflowX": "hidden"
}

#Sidebar style when collapsed
SIDEBAR_COLLAPSED = SIDEBAR_STYLE.copy()
SIDEBAR_COLLAPSED["width"] = "5rem"
SIDEBAR_COLLAPSED["padding"] = "10rem 0rem" #Padding to centre the icon in the sidebar
SIDEBAR_COLLAPSED["alignItems"] = "center"

#Define content to the right of the sidebar
CONTENT_STYLE = {
    "margin-left": "16rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
    "transition": "margin-left 0.2s",
}

CONTENT_COLLAPSED = CONTENT_STYLE.copy()
CONTENT_COLLAPSED["margin-left"] = "6rem"

###########################################################
#Component Creation
###########################################################

#Sidebar layout. Does it need to be enclosed in a function????
sidebar = html.Div(
    id="sidebar",
    children=[
        #Creates header for the sidebar with toggle icon
        html.Div([
            #Header code goes before button else button always appears on the left
            html.H5("Smart Bin Dashboard", className="sidebar-header", style={"textAlign": "left", "paddingLeft": "10px"}),
            
            #Create the collapse toggle button
            html.Div(
                html.Button(
                    html.I(className="bi bi-list"),
                    id="btn-collapse",
                    n_clicks=0,
                    className="sidebar-collapse-btn",
                ),
                className="toggle-wrapper"
            ),
        ],
        className="sidebar-top"),
        
        html.Hr(), #Horizontal line

        #Create the sidebar navigation links
        dbc.Nav(
            [
                dbc.NavLink(
                    [html.I(className="bi bi-house-fill me-2"), html.Span("Home", className="link-text")],
                    href="/",
                    active="exact",
			        className="nav-item"                  
                ),

                #Create accordion-style dropdown menu for Bins
                html.Div([
                    dbc.NavLink(
                        html.Div([
                            html.Span([
                                html.I(className="bi bi-trash3-fill me-2"),
                                html.Span("Bins", className="link-text ms-2"),
                            ], className="d-flex align-items-center"),
                            #This is the bins menu toggle caret icon
                            html.I(className="bi bi-caret-down-fill caret-icon", id="bins-toggle-icon",
                                 style={"fontSize": "0.8rem"}),
                        ],
                        className="d-flex justify-content-between align-items-center w-100"),

                        href="#", #Prevents page reload when clicked
                        id="bins-toggle",
                        n_clicks=0,
                        className="nav-item",
                        style={ 
                               "alignItems": "center",  
                        }
                    ),
                    
                    #Dropdown menu for the bin links, which will appear when toggle button clicked
                    html.Div(
                        id="bins-collapse",
                        className="slide-toggle floating-bins-menu",
                        children=[
                            dcc.Link("Fill Levels & Collections", href="/bin-fill-levels", className="nav-item sub-link",
                                     style={"paddingLeft": "3rem", "paddingRight":"1rem"}),
                            dcc.Link("Map", href="/bin-map", className="nav-item sub-link",
                                     style={"paddingLeft": "3rem"}),                   
                        ],
                    ),
                ]),

                dbc.NavLink(
                    [html.I(className="bi bi-exclamation-triangle-fill me-2"), html.Span("Alerts", className="link-text")],
                    href="/alerts",
                    active="exact",
			        className="nav-item" 
                ),
                dbc.NavLink(
                    [html.I(className="bi bi-graph-up me-2"), html.Span("Analytics", className="link-text")],
                    href="/analytics",
                    active="exact",
			        className="nav-item" 
                ),
            ],
            vertical=True,
            pills=True,
        ),

    ],
    style=SIDEBAR_STYLE,
)

#For collapsed menu
floating_bins_menu = html.Div(
    id="bins-floating-submenu",
    className="floating-bins-menu",
    children=[
            dcc.Link("Fill Levels & Collections", href="/bin-fill-levels", className="nav-item sub-link", 
                     style={"paddingLeft": "5px"}),
            dcc.Link("Map", href="/bin-map", className="nav-item sub-link", 
                     style={"paddingLeft": "5px"}),
    ]
)    


