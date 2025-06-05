from dash import Dash, Input, Output, State, dcc, html, callback, callback_context, ctx 
from layouts import sidebar, CONTENT_STYLE, SIDEBAR_STYLE, SIDEBAR_COLLAPSED, CONTENT_COLLAPSED

from data_utils import get_alerts_data
import pandas as pd



#Callback for sidebar collapse to just icons
@callback(
	#Change the sidebar's width and padding
	Output("sidebar", "style"),
	#Change the content's margin-left
	Output("page-content", "style"),
	#Store the sidebar's collapsed state
	Output("sidebar-state", "data"),
	#Modify the class to CSS class .collapsed
	Output("sidebar", "className"),

	Input("sidebar-state", "data"),
	Input("btn-collapse", "n_clicks"),
)
def toggle_or_load_sidebar(sidebar_state, n):
    triggered_id = ctx.triggered_id
    collapsed = sidebar_state.get("collapsed", False)

    if triggered_id == "btn-collapse":
        collapsed = not collapsed

    class_name = "sidebar collapsed" if collapsed else "sidebar"
    sidebar_style = SIDEBAR_COLLAPSED if collapsed else SIDEBAR_STYLE
    content_style = CONTENT_COLLAPSED if collapsed else CONTENT_STYLE

    return sidebar_style, content_style, {"collapsed": collapsed}, class_name

#Callback for bin submenu to show/hide the links, rotate caret icon, floating box when sidebar collapsed
@callback(
	Output("bins-collapse", "className"), #Change the class of the bins submenu to show/hide it
	Output("bins-toggle-icon", "className"), #Change the class of the caret icon to rotate it
	Output("bins-floating-submenu", "style"), #Change the style of the floating box to show/hide it
	Output("bins-submenu-state", "data"), #Store the bins submenu state
	Output("outside-click-overlay", "style"), #Hides the floating submenu when clicking outside of it

	Input("bins-toggle", "n_clicks"), #Get the number of clicks on the toggle button
	Input("sidebar-state", "data"),
	Input("url", "pathname"), #Get the current URL path
	Input("outside-click-overlay", "n_clicks"), 

	State("bins-collapse", "className"), #Get the current class of the bins submenu
	State("bins-submenu-state", "data") #Get the current bins submenu state
)
def toggle_bins_submenu(n, sidebar_state, pathname, outside_clicks, current_class, bins_submenu_state):
    ctx = callback_context  #Get the context of the callback
    triggered_id = ctx.triggered_id

    submenu_was_open = bins_submenu_state["open"]
    collapsed = sidebar_state["collapsed"]

    #Function to set the overlay visibility
	#Used to hide the floating submenu when clicking outside of it
    def get_overlay_style(submenu_open):
        return {"display": "block" if submenu_open else "none",
                "position": "fixed",
                "top": 0, "left": 0, "width": "100vw", "height": "100vh",
                "zIndex": 999, "backgroundColor": "transparent"}

    # === CASE: Click outside floating submenu (outside overlay clicked) ===
    if triggered_id == "outside-click-overlay" and submenu_was_open:
        return "slide-toggle", "bi bi-caret-down-fill caret-icon", {"display": "none"}, {"open": False}, {"display": "none"}

    # === CASE: URL changed, close floating submenu ===
    if triggered_id == "url" and submenu_was_open:
        return "slide-toggle", "bi bi-caret-down-fill caret-icon", {"display": "none"}, {"open": False}, {"display": "none"}

    # === CASE: Sidebar expanded while floating submenu was open ===
    if triggered_id == "sidebar-state" and submenu_was_open and not collapsed:
        return "slide-toggle open", "bi bi-caret-down-fill caret-icon rotate", {"display": "none"}, {"open": True}, {"display": "none"}

    # === CASE: Toggle button clicked ===
    if triggered_id == "bins-toggle":
        submenu_open = not submenu_was_open

        #Determine caret icon rotation class
        caret_class = "bi bi-caret-down-fill caret-icon"
        if submenu_open:
            caret_class += " rotate" if not collapsed else " rotate-right"

        #Handle floating submenu based on sidebar state (collapsed)
        if collapsed:
            floating_style = {
                "display": "block" if submenu_open else "none",
                "position": "fixed", #make the submenu anchor to screen
                "top": "17.8rem", #Vertical position next to Bin icon
                "left": "5rem",
                "zIndex": 9000,
                "backgroundColor": "#542978",
                "padding": "0.5rem 1rem",
                "boxShadow": "2px 4px 10px rgba(0, 0, 0, 0.3)",
                "borderRadius": "10px", #rounded border
                "minWidth": "200px"
            }
            #Show overlay when submenu is open
            overlay_style = get_overlay_style(submenu_open)
            return "slide-toggle", caret_class, floating_style, {"open": submenu_open}, overlay_style

        #If sidebar is expanded, hide the floating submenu
        return "slide-toggle open" if submenu_open else "slide-toggle", caret_class, {"display": "none"}, {"open": submenu_open}, {"display": "none"}

    #Default fallback (return current state)
    return "slide-toggle", "bi bi-caret-down-fill caret-icon", {"display": "none"}, {"open": submenu_was_open}, {"display": "none"}



###################################################################
# Callback for loading get_alerts_data() results into the dcc.Store
###################################################################
@callback(
        Output("alerts-data-store", "data"),
        Input("alerts-data-update-interval", "n_intervals"), #Auto update every 15 minutes
)
def store_alerts_data(_): #don't care about actual parameter values
    df = get_alerts_data()
    return df.to_dict("records")

