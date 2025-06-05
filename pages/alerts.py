from dash import Dash, html, register_page, dcc, callback, Input, Output, dash_table, exceptions, State, callback_context, no_update
import dash_bootstrap_components as dbc
import pandas as pd
from sqlalchemy import text #needed to insert raw SQL data from user editing table
from datetime import datetime
import plotly.express as px

from data_utils import engine, get_sensor_health_data


#Register this file as a Dash page
register_page(__name__, path="/alerts", name="Alerts")


###################################################################
# Create the alerts Datatable to reuse in each card
###################################################################
def reusable_alerts_data_table(title, table_id, custom_card_style=None, header_style=None):
    return dbc.Card([
        dbc.CardHeader(
            dbc.Row([
                dbc.Col(html.H5(title)) #Title to be passed as parameter later              
            ]), style={
                "backgroundColor": "#FFFFFF", #Header bg colour
                "paddingTop": "15px",
                "borderBottom": "none", #Remove the grey border under cardheader
                **(header_style or {}), #Apply custom header styling for each table here
            } 
        ),
        
        dbc.CardBody([
            #Create the table of alerts
            dash_table.DataTable(
                id=table_id, #table id will be passed as parameter when makign the three separate cards
                columns=[
                    {'name': 'Alert #', 'id': 'alert_id'},
                    {'name': 'Bin ID', 'id': 'bin_id'},
                    {'name': 'Sensor ID', 'id': 'sensor_id'},
                    {'name': '', 'id': 'alert_icon', 'presentation': 'markdown'}, #column for images based on alert type
                    {'name': 'Type', 'id': 'alert_type'},
                    {'name': 'Message', 'id': 'alert_message'},
                    {'name': 'Triggered Time', 'id': 'triggered_time_string'},
                    {'name': 'Resolved Time', 'id': 'resolved_time_string'}, 
                    {'name': 'Status', 'id': 'status', 'presentation': 'dropdown', 'editable': True, 'type': 'text'}, #presentation: tell Dash to make it a dropdown editable column
                    {'name': 'Comments', 'id': 'comment_button', 'presentation': 'markdown'}, #Users can add comments here
                ],
                data=[], #df to be populated via callback

                editable=True, #User can edit the cell value (for status)
                dropdown={ #Dropdown label values
                    'status': {
                        'options': [
                            {'label': 'Active', 'value': 'Active'},
                            {'label': 'Ignore', 'value': 'Ignore'},
                            {'label': 'Resolved', 'value': 'Resolved'}
                        ]
                    }
                },

                page_size=10,
                markdown_options={"html": True}, #enable use of HTML within cells

                cell_selectable=False, #DON'T allow cells to be selected/highlighted to prevent default styles from overriding

                style_table={
                    "overflowX": "auto",
                    'paddingLeft': '5px',
                    "maxWidth": "100%", #set max width to be within card width
                },

                style_cell={
                    "textAlign": "center",
                    "verticalAlign": "middle",
                    "padding": "1px 2px",
                    "fontFamily": "Arial", 
                    "fontSize": "13px",
                    "height": "auto", #adjust height according to width and text wrap
                    "whiteSpace": "normal", #enable text wrapping to next line
                    
                },

                style_header={
                    "fontWeight": "bold",
                    "fontFamily": "Arial", 
                    "fontSize": "13px",
                    "backgroundColor": "#893FB5", #Header purple
                    "color": "white", #white text
                    "padding": "6px",
                    "textAlign": "center",
                },

                style_data_conditional=[
                    #Striped rows
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': '#F1EEF7' #extremely light purple
                    },

                    #Bold the alert ID column
                    {
                        'if': {'column_id': 'alert_id'},
                        'fontWeight': 'bold',
                        'textAlign': 'center',
                        'fontSize': '14px',
                        'color': '#3B3B3B', #dark grey text
                        'backgroundColor': '#F2F2F2' #light grey
                    },

                    #Adjust left padding for sensor icon because it doesn't center like the others
                    {
                        'if': {
                            'filter_query': '{alert_type} = "Sensor"', 
                            'column_id': 'alert_icon' 
                        },
                        'paddingLeft': '5px',
                    },

                    #Adjust left padding for temperature icon because it doesn't center like the others
                    {
                        'if': {
                            'filter_query': '{alert_type} = "Temperature"', 
                            'column_id': 'alert_icon' 
                        },
                        'paddingLeft': '10px',
                    },

                    #Adjust left padding for battery icon because it doesn't center like the others
                    {
                        'if': {
                            'filter_query': '{alert_type} = "Battery"', 
                            'column_id': 'alert_icon' 
                        },
                        'paddingLeft': '5px',
                    },

                    #Adjust left padding for Bin icon to centre it
                    {
                        'if': {
                            'filter_query': '{alert_type} = "Overfill"', 
                            'column_id': 'alert_icon' 
                        },
                        'paddingLeft': '6px',
                    },

                    #Format Status cells as UPPERCASE for display only
                    {
                        'if': {'column_id': 'status'},
                        'textTransform': 'uppercase',
                        'fontSize': '13px',
                        'textAlign': 'left'
                    },

                    #Format Alert Type cells as UPPERCASE for display only
                    {
                        'if': {'column_id': 'alert_type'},
                        'textTransform': 'uppercase',
                        'fontSize': '13px',
                        'textAlign': 'center',
                        'fontWeight': 'bold',
                    },

                    #Battery cell color orange
                    {
                        'if': {
                            'filter_query': '{alert_type} = "Battery"', 
                            'column_id': 'alert_type' 
                        },
                        'backgroundColor': '#A5D477',
                    },

                    #Sensor cell color blue
                    {
                        'if': {
                            'filter_query': '{alert_type} = "Sensor"', 
                            'column_id': 'alert_type' 
                        },
                        'backgroundColor': '#7AC5F2',
                    },

                    #Temp cell color yellow
                    {
                        'if': {
                            'filter_query': '{alert_type} = "Temperature"', 
                            'column_id': 'alert_type' 
                        },
                        'backgroundColor': '#FFEC4D',
                    },

                    #OVerfill cell color red
                    {
                        'if': {
                            'filter_query': '{alert_type} = "Overfill"', 
                            'column_id': 'alert_type' 
                        },
                        'backgroundColor': '#DB4B4D',
                    },
                    
                    

                ],

                style_cell_conditional=[
                    
                    #Adjust widths of all columns
                    #{'if': {'column_id': 'alert_id'}, 'width': '50px'},
                    #{'if': {'column_id': 'bin_id'}, 'width': '50px'},
                    #{'if': {'column_id': 'sensor_id'}, 'maxWidth': '50px'},
                    {'if': {'column_id': 'alert_type'}, 'minWidth': '110px'},
                    #{'if': {'column_id': 'alert_message'}, 'width': '180px'},
                    {'if': {'column_id': 'triggered_time_string'}, 'width': '180px'},
                    {'if': {'column_id': 'resolved_time_string'}, 'width': '180px'},
                    #{'if': {'column_id': 'status'}, 'minWidth': '80px'},
                    {'if': {'column_id': 'comment_button'}, 'maxWidth': '100px'},
                    
                    
                    #Center the alert_icon column
                    {
                        'if': {'column_id': 'alert_icon'},
                        'textAlign': 'center',
                        'paddingLeft': '8px', #move it horizontally center
                        'paddingTop': '20px', #move it vertically center
                        'width': '30px',
                    },

                    #Center Triggered time column
                    {
                        'if': {'column_id': 'triggered_time_string'},
                        'textAlign': 'center'
                    },

                    #Center Resolved time column
                    {
                        'if': {'column_id': 'resolved_time_string'},
                        'textAlign': 'center'
                    },


                ]

            )
        ])
    #Card styling
    ], style={
            "backgroundColor": "#FFFFFF",
            "boxShadow": "0 4px 12px rgba(0, 0, 0, 0.1)",
            **(custom_card_style or {}) #card style for specific Alerts table applied here
                                        #** = unpack the key-value pairs in the dictionary and insert them here
        }
    )



###################################################################
# Card for ACTIVE alerts
###################################################################
active_alerts_table = reusable_alerts_data_table(
    "Active Alerts", 
    "active-alerts-table",
    custom_card_style={
        "borderLeft": "5px solid #DB2225", #red border
        "borderRight": "5px solid #DB2225"
    }, 
    header_style={"color": "#C21E21"} #red heading text, "backgroundColor": "#FFFAFB",
    )


###################################################################
# Card for Ignored alerts
###################################################################
ignored_alerts_table = reusable_alerts_data_table(
    "Ignored Alerts", 
    "ignored-alerts-table",
    custom_card_style={
        "borderLeft": "5px solid #612C80", #purple border
        "borderRight": "5px solid #612C80",
    }, 
    header_style={"color": "#4F2469"} #purple heading text, "backgroundColor": "#FCFAFF"
    )


###################################################################
# Card for Resolved alerts
###################################################################
resolved_alerts_table = reusable_alerts_data_table(
    "Resolved Alerts", 
    "resolved-alerts-table",
    custom_card_style={
        "borderLeft": "5px solid #22960B", #green border
        "borderRight": "5px solid #22960B",
    },
    header_style={"color": "#1B7809"} #green heading text, "backgroundColor": "#F9FFF9"
    )


#Assign icon images to alert_icon column
alert_icon_url = {
    'Sensor': '/assets/sensor_icon.png',
    'Overfill': '/assets/overfill_icon.png',
    'Battery': '/assets/battery_icon.png',
    'Temperature': '/assets/temperature_icon.png',
}



###################################################################
# Card for Sensor Health Table
###################################################################
def sensor_health_data_table(table_id="sensor-health-table"):
    return dbc.Card([
        dbc.CardHeader(html.H5("Sensor Health Overview"), 
                       style={
                           "backgroundColor": "#FFFFFF", #header bg colour
                           "paddingTop": "10px",
                           "borderBottom": "none", #Remove the grey border under cardheader
                        } 
        ),
        dbc.CardBody([

            dash_table.DataTable(
                id=table_id,
                columns=[
                    {'name': 'Sensor ID', 'id': 'sensor_id'},
                    {'name': 'Bin ID', 'id': 'bin_id'},                    
                    {'name': 'Battery Voltage (V)', 'id': 'battery_voltage'},
                    {'name': 'Temperature (°C)', 'id': 'temperature'},
                    {'name': 'Last Sent Data', 'id': 'last_seen'},
                    {'name': 'Bin Status', 'id': 'bin_status'},
                ],

                data=[],  #Filled in via callback
                page_size=5, #show 5 results per page

                sort_action="custom", #Enable manual sorting of columns
                sort_mode="single", #Sort only one column at a time
                sort_by=[], #Initialise sort state

                cell_selectable=False, #DON'T allow cells to be selected/highlighted to prevent default styles from overriding
                
                style_table={
                    "overflowX": "auto", #allows horizontal scrolling when cut off
                    "paddingLeft": "5px",
                }, 

                style_cell={
                    "textAlign": "center",
                    "fontFamily": "Arial",
                    "fontSize": "13px",
                    "whiteSpace": "normal",
                    "fontFamily": "Arial",
                },

                style_header={
                    "backgroundColor": "#893FB5", #purple header
                    "fontWeight": "bold",
                    "textAlign": "center",
                    "color": "white", #white text
                },

                style_data_conditional=[
                    #Striped rows
                    {
                        "if": {"row_index": "odd"},
                        "backgroundColor": "#F1EEF7" #extremely light purple alt rows
                    },

                    #Highlight sensors that haven't sent data > 12 hours
                    {
                        "if": {
                            "filter_query": "{inactive_sensor} = true", #Dash requires string not boolean
                            "column_id": "last_seen"
                        },
                        "backgroundColor": "#8FCFFA", #blue
                        "fontWeight": "bold"
                    },

                    #Highlight cells where temperature > 55
                    {
                        "if": {
                            "filter_query": "{temperature} > 55",
                            "column_id": "temperature"
                        },
                        "backgroundColor": "#FAEB89", #Yellow
                        "fontWeight": "bold"
                    },

                    #Highlight cells where battery voltage < 2.7
                    {
                        "if": {
                            "filter_query": "{battery_voltage} < 2.7",
                            "column_id": "battery_voltage"
                        },
                        "backgroundColor": "#B68FFA", #Purple
                        "fontWeight": "bold"
                    },

                    #Highlight cells where bin status = Needs Maintenance
                    {
                        "if": {
                            "filter_query": "{bin_status} = 'Needs Maintenance'",
                            "column_id": "bin_status"
                        },
                        "backgroundColor": "#CEFA99", #green
                        "fontWeight": "bold"
                    },

                    #Bold the Sensor ID column
                    {
                        'if': {'column_id': 'sensor_id'},
                        'fontWeight': 'bold',
                        'textAlign': 'center',
                        'color': '#1B2F5C', #dark blue
                    },

                ]
            )
        ]),
        #Update every 15 minutes
        dcc.Interval(
        id="update-sensor-health-table-interval",
        interval=900000, #15 minutes
        n_intervals=0
        ),

    ], style={
            "backgroundColor": "#FFFFFF",
            "boxShadow": "0 4px 12px rgba(0, 0, 0, 0.1)",
            #"padding": "5px"
        }
    
    )


###################################################################
# Callback for loading ACTIVE alerts table data
###################################################################
@callback(
    Output("active-alerts-table", "data"),
    Input("active-alerts-table", "id"),  #triggers once on load (when card is instantiated)
    Input("alerts-data-store", "data"), #Get alerts data from dcc.Store in index.py

)
def load_active_alerts_table(_, data):
    df_alerts = pd.DataFrame(data)
    #Filter for alerts with 'Active' status AND no resolved time
    df_active = df_alerts[(df_alerts['status'] == 'Active') & (df_alerts['resolved_time_string'] == '')]
    
    #Map the alert icons to the alert_type and use markdown to render image
    #Loops over each type and applies the lambda function
    # ![icon] = markdown syntax to display image
    df_active['alert_icon'] = df_active['alert_type'].map(
        lambda t: f"![icon]({alert_icon_url.get(t, '')})"
    )

    #Assign emoji icon to comment button column cells
    df_active['comment_button'] = df_active.apply(
        lambda row: (
                f'<div>'
                #Assign unique span ID based on alert_id for each button (to anchor popover to it)
                f'<span id="comment-icon-{row["alert_id"]}" style="cursor:pointer;">📝</span>'
                #Display any existing user comments underneath the button
                f'<div style="font-size:11px; color:#3D3D3D; margin-top:5px;">{row["user_notes"] or ""}</div>'
                f'</div>'
        ), axis=1    
    )

    return df_active.to_dict("records")

###################################################################
# Callback for loading IGNORED alerts table data
###################################################################
@callback(
    Output("ignored-alerts-table", "data"),
    Input("ignored-alerts-table", "id"), #triggers once on load (when card is instantiated)
    Input("alerts-data-store", "data"), #Get alerts data from dcc.Store in index.py
)
def load_ignored_alerts(_, data):
    df = pd.DataFrame(data)

    #Filter for records with 'Ignore' status
    df_ignored = df[df['status'] == 'Ignore']
    
    #Map the alert icons to the alert_type and use markdown to render image
    #Loops over each type and applies the lambda function
    # ![icon] = markdown syntax to display image
    df_ignored['alert_icon'] = df_ignored['alert_type'].map(
        lambda t: f"![icon]({alert_icon_url.get(t, '')})"
    )

    #Assign emoji icon to comment button column cells
    df_ignored['comment_button'] = df_ignored.apply(
        lambda row: (
                f'<div>'
                #Assign unique span ID based on alert_id for each button (to anchor popover to it)
                f'<span id="comment-icon-{row["alert_id"]}" style="cursor:pointer;">📝</span>'
                #Display any existing user comments underneath the button
                f'<div style="font-size:11px; color:#3D3D3D; margin-top:5px;">{row["user_notes"] or ""}</div>'
                f'</div>'
        ), axis=1 
    )

    return df_ignored.to_dict("records")

###################################################################
# Callback for loading RESOLVED alerts table data
###################################################################
@callback(
    Output("resolved-alerts-table", "data"),
    Input("resolved-alerts-table", "id"), #triggers once on load (when card is instantiated)
    Input("alerts-data-store", "data"), #Get alerts data from dcc.Store in index.py
)
def load_resolved_alerts(_, data):
    df = pd.DataFrame(data)

    #Filter for alerts where resolved time string is NOT empty
    #df_resolved = df[df['resolved_time_string'] != '']
    #Filter for alerts with the status Resolved
    df_resolved = df[df['status'] == 'Resolved']
    
    #Map the alert icons to the alert_type and use markdown to render image
    #Loops over each type and applies the lambda function
    # ![icon] = markdown syntax to display image
    df_resolved['alert_icon'] = df_resolved['alert_type'].map(
        lambda t: f"![icon]({alert_icon_url.get(t, '')})"
    )

    #Assign emoji icon to comment button column cells
    df_resolved['comment_button'] = df_resolved.apply(
        lambda row: (
                f'<div>'
                #Assign unique span ID based on alert_id for each button (to anchor popover to it)
                f'<span id="comment-icon-{row["alert_id"]}" style="cursor:pointer;">📝</span>'
                #Display any existing user comments underneath the button
                f'<div style="font-size:11px; color:#3D3D3D; margin-top:5px;">{row["user_notes"] or ""}</div>'
                f'</div>'
        ), axis=1 
    )

    return df_resolved.to_dict("records")





###################################################################
# Callback for SAVING the updated STATUS column of alerts tables to database
###################################################################
@callback(
    Output("active-alerts-table", "data", allow_duplicate=True), #Save the edited status cells
    Output("ignored-alerts-table", "data", allow_duplicate=True),
    Output("resolved-alerts-table", "data", allow_duplicate=True),
    Output("status-edit-saved-msg", "data"), #Store the status edit update message

    Input("active-alerts-table", "data_previous"), #The data before it is edited, used to compare with new value
    Input("ignored-alerts-table", "data_previous"),
    Input("resolved-alerts-table", "data_previous"),

    State("active-alerts-table", "data"), #Save the state of the edits 
    State("ignored-alerts-table", "data"),
    State("resolved-alerts-table", "data"),

    prevent_initial_call='initial_duplicate' #Don't run the callback on page load or if no edits made
)
def update_alert_status(active_old, ignored_old, resolved_old,
                        active_new, ignored_new, resolved_new): #Parameters to pass are the previous and new values of the status cells when edited
    
    #Create table dictionary to fetch old and new data for each table based on triggered input
    table_map = {
        "active-alerts-table": (active_old, active_new),
        "ignored-alerts-table": (ignored_old, ignored_new),
        "resolved-alerts-table": (resolved_old, resolved_new),
    }    
     
    #Identify which input triggered the callback (from active, ignored, or resolved tables)
    triggered = callback_context.triggered_id
    print("Triggered by:", triggered)

    if triggered is None or triggered not in table_map:
        raise exceptions.PreventUpdate


    #Depending on table that triggered callback, fetch the table's old and new data
    prev_data, current_data = table_map[triggered]

    #If no previous data, don't update
    if prev_data is None:
        raise exceptions.PreventUpdate


    #Create the status edit saved message when a status is saved
    status_update_text = []

    #Loop through EACH row in the table to compare OLD and NEW status values
    #Store the alert id corresponding to the edited status cell in list changed_rows
    changed_rows = []

    #Check for edits to the STATUS column
    for old, new in zip(prev_data, current_data):
        alert_id = new["alert_id"]
        old_status = old["status"]
        new_status = new["status"]

        if old["status"] != new["status"]: #If there's been a change to teh status value           
            #Add the new values to changed_rows list to be updated in database
            changed_rows.append((alert_id, "status", new_status))

            #Create the toast message informing of update made
            status_update_text.append(
                f"Alert #{alert_id} status updated from '{old_status}' to '{new_status}'.")

            #If the updated status is changed to RESOLVED auto-add current date
            if new_status == "Resolved":
                #Get the current datetime to insert into Resolved Time column
                resolved_time_now = datetime.now().strftime("%Y-%m-%d %H:%M")
                
                changed_rows.append((alert_id, "resolved_time", resolved_time_now))
                status_update_text.append(
                    f"Resolved time has been set to '{resolved_time_now}'."
                )

            #Otherwise if status was changed FROM Resolved to Active/Ignore, remove Resolved time
            elif old_status == "Resolved" and new_status in ["Active", "Ignore"]:
                #Insert value None (null)
                changed_rows.append((alert_id, "resolved_time", None))
                status_update_text.append(
                    f"Resolved time has been cleared."
                )

        #Create variables for old and new comments column
        old_notes = old.get("user_notes", "") #Use .get instead of old["user_notes"], because if no notes exist or NULL, will give error
        new_notes = new.get("user_notes", "") #return empty string if no notes exist

        #Check if notes were added/edited to insert into database
        if old_notes != new_notes:
            changed_rows.append((alert_id, "user_notes", new_notes))
            status_update_text.append(
                f"Alert #{alert_id} comments updated."
            )

    #If no edits made, don't update
    if not changed_rows:
        raise exceptions.PreventUpdate

    #Connect to mysQL database to update STATUS or RESOLVED TIME
    with engine.begin() as conn:
        #For each changed row, loop through and...
        for alert_id, column, new_value in changed_rows: #each parameter is in changed_rows, where column = status or resolved_time_string
             
            #run an SQL query to update that record in the DB
            conn.execute(
                text(f"UPDATE alerts_table SET {column} = :val WHERE alert_id = :alert_id"),
                {"val": new_value, "alert_id": alert_id}
            )
    
    #Return the status update message if it's defined
    status_toast = "\n".join(status_update_text) if status_update_text else None

    #Return updated data only to the table that triggered it, for other tables don't update
    return (
        current_data if triggered == "active-alerts-table" else no_update,
        current_data if triggered == "ignored-alerts-table" else no_update,
        current_data if triggered == "resolved-alerts-table" else no_update,
        status_toast #Save the message to dcc.Store
    )


###################################################################
# Callback to display toast message for status updates
@callback(
    Output("status-edit-saved-toast", "is_open"),
    Output("status-edit-saved-toast", "children"),
    Input("status-edit-saved-msg", "data"),
    prevent_initial_call=True
)
def show_toast(message):
    if message:
        return True, message #Change is_open to True (displays it) and show the message text
    raise exceptions.PreventUpdate


###################################################################
# Callback to OPEN the comment popover on clicking emoji icon
@callback(
    Output("comment-popover", "is_open"), #opens the popover
    Output("comment-popover", "target"), #anchors popover to the table
    Output("comment-box", "value"), #users input/comment
    Output("comment-alert-id", "data"), #Stores the alert ID of row being edited

    Input("active-alerts-table", "active_cell"),
    Input("ignored-alerts-table", "active_cell"),
    Input("resolved-alerts-table", "active_cell"),

    State("active-alerts-table", "data"),
    State("ignored-alerts-table", "data"),
    State("resolved-alerts-table", "data"),
    prevent_initial_call=True
)
def show_comment_popover(active_cell, ignored_cell, resolved_cell,
                         active_data, ignored_data, resolved_data):
    
    #Use callback context to figure out which table's cell was clicked
    ctx = callback_context
    #If callback was somehow triggered by nothing, don't do anything
    if not ctx.triggered:
        raise exceptions.PreventUpdate
    
    triggered_id = ctx.triggered_id #will be either IDs for each 3 tables
    row, data = None, None #placeholders for now

    if triggered_id == "active-alerts-table" and active_cell and active_cell["column_id"] == "comment_button":
        row = active_cell["row"]
        data = active_data

    elif triggered_id == "ignored-alerts-table" and ignored_cell and ignored_cell["column_id"] == "comment_button":
        row = ignored_cell["row"]
        data = ignored_data

    elif triggered_id == "resolved-alerts-table" and resolved_cell and resolved_cell["column_id"] == "comment_button":
        row = resolved_cell["row"]
        data = resolved_data

    else:
        raise exceptions.PreventUpdate

    #Get alert ID and user_notes from selected row
    alert_id = data[row]["alert_id"]
    comment = data[row].get("user_notes", "") #Use .get so that if user_notes is empty, don't get error
    target_id = f"comment-icon-{alert_id}" #Match the span id of each unique comment button to anchor popover to it

    return True, target_id, comment, alert_id #comment prefills the textbox if existing comment, and store alert id for if comment is saved later

###################################################################
#Callback to SAVE comment edits to database user_notes column
@callback(
    Output("status-edit-saved-msg", "data", allow_duplicate=True), #Show successfully saved popup toast
    Output("comment-popover", "is_open", allow_duplicate=True), #close popover after saving
    Input("save-comment-button", "n_clicks"),
    State("comment-alert-id", "data"), #stored in dcc.Store to hold alert ID of row being edited
    State("comment-box", "value"), #text being typed into the box by user
    prevent_initial_call=True #only trigger callback when Save button clicked
)
def save_comment_to_db(n_clicks, alert_id, comment):
    #If no alert id exists, don't do anything to prevent errors
    if not alert_id:
        raise exceptions.PreventUpdate
    
    #Enforce the character restriction to 100
    comment = comment[:100] if comment else "" #Only saves first 100 chars, else if empty,return empty string

    with engine.begin() as conn:
        conn.execute(
            text("UPDATE alerts_table SET user_notes = :val WHERE alert_id = :alert_id"),
            {"val": comment, "alert_id": alert_id}
        )
    #return the toast message, and close popover
    return f"Comment updated for Alert #{alert_id}", False

###################################################################
#Callback for "Cancel" button of popover to close it
@callback(
    Output("comment-popover", "is_open", allow_duplicate=True),
    Input("cancel-comment-button", "n_clicks"),
    prevent_initial_call=True
)
def cancel_popover_button(n_clicks):
    return False #change is_open to False (closes it)

###################################################################
# Callback to update character count limit and disable Save button if goes over 100
@callback(
    Output("character-count", "children"),
    Output("save-comment-button", "disabled"), #Disable save button
    Input("comment-box", "value"),
    prevent_initial_call=True
)
def update_character_count(value):
    #If nothing entered in the comment box
    if not value:
        return "0 / 100 characters", False #and don't disable Save button
    
    #Find number of characters in the comment input
    length = len(value)
    #Set restriction to 100 characters
    exceed_max = length > 100

    return f"{length} / 100 characters", exceed_max


###################################################################
# Callback for populating Sensor Health Table
@callback(
    Output("sensor-health-table", "data"),
    Input("sensor-health-table", "sort_by"), #Sorting function
    Input("sensor-health-table", "id"), #Load the table on page load
    Input("update-sensor-health-table-interval", "n_intervals") #Refresh data every 15 min
)
def load_sensor_health_data(sort_by, _, n_intervals):
    df = get_sensor_health_data()

    #Manual column sorting feature using Dash's sort_by prop
    #If sort_by variable has a value (when arrows clicked)
    if sort_by:
        col_id = sort_by[0]["column_id"] #extracts id of the column selected for sorting, giving the first item in teh list [0]
        direction = sort_by[0]["direction"] #the direction to sort in asc/desc
        ascending = direction == "asc" #convert direction into Boolean value (True/False), True=asc, False=desc

        #Sort logic for datetime format
        if col_id == 'last_seen':
            #Convert to datetime format, specifying the Day comes first since order is d/m/y
            df["_tmp"] = pd.to_datetime(df["last_seen"], dayfirst=True, errors="coerce") 
            #Sort and drop the temp column
            df = df.sort_values("_tmp", ascending=ascending).drop(columns="_tmp")   

        #For numeric columns i.e. battery & temp, sort normally
        elif col_id in ["battery_voltage", "temperature"]:
            df = df.sort_values(by=col_id, ascending=ascending)

        #All other columns sort lexicographically
        else:
            df = df.sort_values(by=col_id, ascending=ascending)

    return df.to_dict("records")






###################################################################
# Layout
###################################################################
layout = html.Div([

    #Store message for any saved edits to Status column
    dcc.Store(id="status-edit-saved-msg"),
    
    #Use Toast to create the message
    dbc.Toast(
        id="status-edit-saved-toast",
        header=html.Span([ #Header message on toast
            html.I(className="bi bi-check-square-fill", style={"color": "green", "marginRight": "8px"}),
            html.Strong("Status Updated")
        ]), 
        is_open=False, #Hidden at first
        duration=5000, #Message auto disappears
        #icon="success",
        dismissable=True, #User can manually close message
        style={
            "position": "fixed",
            "top": 10,
            "right": 10,
            "width": 350,
            "zIndex": 9999,
        }
    ),

    #Popover for user to enter commments/notes in 
    html.Div([
        dbc.Popover([
            dbc.PopoverHeader("Edit Comment", style={"backgroundColor": "#1B2F5C", "color": "white"}),
            dbc.PopoverBody([
                dcc.Textarea(
                    id="comment-box", 
                    style={"width": "100%"},
                    maxLength=100, #Set text char limit to 100
                ),
                #Text show character out of 100 limit
                html.Div(
                    id="character-count",
                    style={
                        "fontSize": "10px",
                        "color": "grey",
                        "marginTop": "1px",
                        "textAlign": "right",
                    }
                ),
                
                html.Br(),
                html.Div([
                    dbc.Button("Save", 
                            id="save-comment-button",
                            size="sm",
                            className="me-2 mt-1"),
                    dbc.Button("Cancel",
                            id="cancel-comment-button",
                            size="sm",
                            className="mt-1")
                ], style={"textAlign": "right"}), #align buttons right
            ])
        ], id="comment-popover",
            target="",
            is_open=False,
            trigger="legacy", #control the popover open/close using is_open via callbacks
            style={
                "border": "1px solid #ccc",
                "borderRadius": "8px",
                "boxShadow": "0 4px 8px rgba(0, 0, 0, 0.1)",
            },
        ),
        #Store the alert-id belonging to the comment button clicked on to save comment to that alert id
        dcc.Store(id="comment-alert-id")
    ]),
    
    dbc.Container([
        dbc.Row([
            #Page Header
            dbc.Col(
                html.H4("Alerts", className="mb-4"),
                width=12
            )
        ]),

        #Row for Sensor Health Table
        dbc.Row([
            dbc.Col(sensor_health_data_table(), xs=12, md=7),
        ], style={"marginBottom": "20px"}, justify="center"
        ),

        #Row for ACTIVE alerts table
        dbc.Row([
            dbc.Col(active_alerts_table, xs=12, md=12),
        ], style={"marginBottom": "20px"}
        ),

        #Row for IGNORED alerts table
        dbc.Row([
            dbc.Col(ignored_alerts_table, xs=12, md=12),
        ], style={"marginBottom": "20px"}
        ),


        #Row for RESOLVED alerts  table
        dbc.Row([
            dbc.Col(resolved_alerts_table, xs=12, md=12),
        ]),

    
    ])

])