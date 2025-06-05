from dash import Dash, html, register_page, dcc, callback, Input, Output, dash_table, exceptions, State
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta


from data_utils import get_complete_bin_table, get_collection_history, get_bin_data, get_bin_fill_history

#Register this file as a Dash page
register_page(__name__, path="/bin-fill-levels", name="Fill Level & Collection Activity")




###################################################################
# Create bin fill history card to show last 100 records
###################################################################
bin_df = get_bin_data() #Fetch latest bin data
#Get distinct bin IDs from the bin data into bin_ids
bin_ids = sorted(bin_df['bin_id'].unique())

bin_history_card = html.Div([
    dbc.Card([
        dbc.CardHeader(
            #Card header
            dbc.Row([
                dbc.Col(html.H5("Latest Fill Level Records", className="card-title"))
            ]), 
            style={
                "backgroundColor": "#FFFFFF", #Header bg colour 
                "paddingTop": "15px",
                "borderBottom": "none" #Remove the grey border under cardheader
            } 
        ),

        dbc.CardBody([
            html.Div([
                html.H6("Bin ID:", style={"marginRight": "5px", "fontSize": "12px", "fontWeight": "bold"}),
                #Dropdown selection for Bin IDs
                dcc.Dropdown(
                    id='fill-history-bin-id-dropdown',
                    #Populate dropdown options with bin_ids created earlier
                    options=[{'label': b, 'value': b} for b in bin_ids],
                    value=bin_ids[0], #Set the first index item as the default bin ID
                    placeholder='Select Bin ID',
                    #multi=True, #Can select multiple bins
                    style={
                        'width': '200px'
                    }                   
                ),               
            #Style for dropdown and header container
            ], style={
                "display": "flex",
                "flexWrap": "wrap", #enable wrapping on small screens so items don't overflow off the card
                "alignItems": "center",
                "marginBottom": "10px",
                "fontFamily": "Arial", #dropdown font
                "fontSize": "13px",
                }
            ),

            #Create DataTable for Bin fill history
            dash_table.DataTable(
                id="bin-fill-history-table",
                columns=[
                    {'name': '#', 'id': 'row_number'},
                    {'name': 'Fill Level', 'id': 'fill_level_display'},
                    {'name': 'Δ Fill Level', 'id': 'fill_level_change_string'},
                    {'name': 'Timestamp', 'id': 'timestamp_string'},                   
                ],

                data=[], #populated via callback
                page_size=10,
                cell_selectable=False, #DON'T allow cells to be selected/highlighted to prevent default styles from overriding
                
                style_table={
                    'overflowX': 'auto',
                    'paddingLeft': '5px',
                    'marginBottom': '10px',
                },

                style_cell={
                    'textAlign': 'center',
                    'fontFamily': 'Arial',
                    'fontSize': '14px',
                    'padding': '6px'
                },

                style_header={
                    'fontWeight': 'bold',
                    'backgroundColor': '#893FB5', #Header purple
                    'fontSize': '15px',
                    'textAlign': 'center',
                    'padding': '10px',
                    'color': 'white',
                },

                #Conditional cell styling
                style_data_conditional=[
                    #Striped rows
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': '#F1EEF7' #very light purplre
                    },

                    #If fill level 80-89 make cell bg red
                    {
                        'if': {
                            'filter_query': '{fill_level} >= 80 && {fill_level} < 90',
                            'column_id': 'fill_level_display'
                        },
                        'backgroundColor': '#C2171D', #Dark red
                        'color': 'black'
                    },

                    #If fill level 90+ make cell bg bright red
                    {
                        'if': {
                            'filter_query': '{fill_level} >= 90',
                            'column_id': 'fill_level_display'
                        },
                        'backgroundColor': '#E62727', #Bright red
                        'color': 'black'
                    },
                ]
            )
        ])
    #Style the card    
    ], style={
        "backgroundColor": "#FFFFFF",
        "boxShadow": "0 4px 12px rgba(0, 0, 0, 0.1)",
    }),

    #Update card every 15 minutes
    dcc.Interval(
    id='update-bin-fill-history-table-interval',
    interval=15 * 60 * 1000,  #15 minutes in milliseconds
    n_intervals=0
)
])


###################################################################
# Create the bin fill history line chart
###################################################################

#Function for populating weekly dropdown filter with options (with their dates)
def generate_week_options(n_weeks=4):
    #Get current date but only date not time
    today = datetime.now().date()
    #Get beginning date of current week (most recent Monday)
    current_week_start = today - timedelta(days=today.weekday())

    #Populate dropdown weekly options
    options = []
    for i in range(n_weeks): #where if i=0 is current week, i=1 is last week, up to n_weeks -1 etc
        #calculate start and end date for each loop (week)
        week_start = current_week_start - timedelta(weeks=i) #weeks=i shifts back to i number of weeks
        week_end = week_start + timedelta(days=6)
        #Format date range to string DD Month - DD Month
        label = f"{week_start.strftime('%d %b')} – {week_end.strftime('%d %b')}"
        #Add the week dates to a dictionary
        options.append({'label': label, 'value': -i})
    
    return options

#Function for populating the MONTHS filter options
def generate_month_options(n_months=12): #Default last 12 months of data
    #Get today's date and replace if with the first day of the Month
    today = datetime.today().replace(day=1) #use datetime.today() because it has the methods for .replace() and pd.dateOffset() expects a datetime
    
    #Return a list of dictionary items for the dropdown options
    return [
        {   #For each of past n_months (0 to 11), subtract i from today
            ##i=0 is current month, i=1 is previous month, etc
            'label': (today - pd.DateOffset(months=i)).strftime('%B %Y'), #What is displayed in dropdown options, converted to full month and year
            'value': (today - pd.DateOffset(months=i)).strftime('%Y-%m') #What's used for calculations
        }
        #Loop over i from 0 to 11 (if n_months = 12 default)
        for i in range(n_months)
    ]

#Get the current month in format YYYY-MM
def get_current_month_value():
    return datetime.today().strftime('%Y-%m')


bin_fill_history_line_chart = html.Div([
    dbc.Card([
        dbc.CardBody([
            html.Div([
            #Dropdown for months
            dcc.Dropdown(
                id="fill-history-line-chart-month-dropdown",
                options=generate_month_options(),
                value=get_current_month_value(),
                clearable=False,
                style={
                    "width": "200px",
                }
            ),

            #Dropdown for weeks based on selected month
            dcc.Dropdown(
                id="fill-history-line-chart-week-dropdown",
                options=[], #Populate dropdown with the weeks of the selected month
                value=None, #Current week by default
                clearable=False,
                style={
                    'width': '230px',
                }
            ),

            html.Div([
                #Header for Bin ID
                html.H6(
                    id="selected-bin-id-line-chart-title",
                    style={
                        "fontSize": "12px",
                        "fontWeight": "bold",
                        "margin": "0",
                    }
                )
            ], style={
                "marginLeft": "auto", #Push bin id header to far right
                "display": "flex",
                "alignItems": "center"
            }),
        
        #Styling for dropdown filters container
        ], style={
            "display": "flex",
            "gap": "10px",
            "marginBottom": "10px",
            "flexWrap": "wrap", #enable wrapping on small screens so items don't overflow off the card
            "alignItems": "center",
            "fontFamily": "Arial", #dropdown font
            "fontSize": "13px",
        }
        ),

        #Line chart
        dcc.Graph(id="fill-history-line-chart")
        ])
    
    #Style the card
    ], style={
        "backgroundColor": "#FFFFFF",
        "boxShadow": "0 4px 12px rgba(0, 0, 0, 0.1)",
        "padding": "3px",
    })
])





###################################################################
# Create the collection table card
###################################################################

collection_table_card = html.Div([
    dbc.Card([
        dbc.CardHeader(
            #Card header
            dbc.Row([
                dbc.Col(html.H5("Collection History", className="card-title"))
            ]), style={
                "backgroundColor": "#FFFFFF", #Header bg colour
                "paddingTop": "15px",
                "borderBottom": "none" #Remove the grey border under cardheader
            } 
        ),    

        dbc.CardBody([
            html.Div([
                html.H6("Bin ID:", style={"marginRight": "5px", "fontSize": "12px", "fontWeight": "bold"}),
                #Dropdown selection for Bin IDs
                dcc.Dropdown(
                    id='collection-table-bin-id-dropdown',
                    #Populate dropdown options with bin_ids created earlier
                    options=[{'label': b, 'value': b} for b in bin_ids],
                    value=bin_ids[0], #Set the first index item as the default bin ID
                    placeholder='Select Bin ID',
                    #multi=True, #Can select multiple bins
                    style={
                        'width': '200px'
                    }                   
                ),               
            ], style={
                "display": "flex",
                "flexWrap": "wrap", #enable wrapping on small screens so items don't overflow off the card
                "alignItems": "center",
                "marginBottom": "15px",
                "fontFamily": "Arial", #dropdown font
                "fontSize": "13px",
                }
            ),

            #Create the datatable
            dash_table.DataTable(
                id="collection-history-table",
                columns=[
                    {'name': 'Collection Date', 'id': 'collection_timestamp_string'},
                    {'name': 'Fill Level at Time of Collection', 'id': 'fill_level'},
                    {'name': 'Time Taken to Empty Since Reaching 80% Full', 'id': 'time_since_full_string'},
                ],
                data=[],
                sort_action='custom',
                sort_mode='single',
                cell_selectable=False, #DON'T allow cells to be selected/highlighted to prevent default styles from overriding

                style_table={
                    'overflowX': 'auto',
                    'paddingLeft': '5px',
                    #'border': '1px solid #ccc', #grey border around table
                },

                style_cell={
                    'textAlign': 'center',
                    "fontFamily": "Arial", 
                    "fontSize": "14px",
                    "padding": "6px",
                },
                
                #Table header columns
                style_header={
                    "fontWeight": "bold", 
                    "fontFamily": "Arial", 
                    "fontSize": "15px",
                    "textAlign": "center",
                    "backgroundColor": "#893FB5", #Header purple
                    "padding": "10px",
                    'color': 'white'
                },

                #Conditional styling of the cells
                style_data_conditional=[                    
                #Change cell bg colour based on fill level
                {
                    'if': {
                        'filter_query': '{fill_level} >= 90', 
                        'column_id': 'fill_level' #output bg colour to this column
                    },
                    'backgroundColor': '#E62727', #Bright red
                    'color': 'black'
                },

                #Highlight delay in emptying (12+ hours) very full bins <90
                {
                    'if': {
                        'filter_query': '{fill_level} > 90 && {time_since_full} >= 720',
                        'column_id': 'time_since_full_string'
                    },
                    'backgroundColor': '#E62727', # Bright red
                    'color': 'black'
                },

                ],

                #Adjust width of columns
                style_cell_conditional=[
                        {'if': {'column_id': 'collection_timestamp_string'}, 'width': '180px'},
                        {'if': {'column_id': 'fill_level'}, 'width': '100px'},
                        {'if': {'column_id': 'time_since_full_string'}, 'width': '250px'},
                ],

                page_size=15,

            ),

            #Message if no data is found when a Bin ID is selected for filter in collection history table
            html.Div(
                id="no-data-message", 
                style={
                    'marginTop': '20px', 
                    'color': '#666', #grey 
                    'textAlign': 'center',
                    "fontFamily": "Arial",
                    }
            ),

            #Last updated Time message below collection Table
            html.Div(
                id="collection-table-last-updated-msg", 
                style={
                    'marginTop': '10px',
                    'fontSize': '10px',
                    'color': '#666', #grey
                    'textAlign': 'right',
                    'fontStyle': 'italic',
                }
            ),

        ])



    #Card styling
    ], style={
            "backgroundColor": "#FFFFFF",
            "boxShadow": "0 4px 12px rgba(0, 0, 0, 0.1)",
        }
    ),

    #Update card every 15 min
    dcc.Interval(
        id='update-collection-table-interval',
        interval=15 * 60 * 1000,  #15 minutes in milliseconds
        n_intervals=0
    )
])





###################################################################
# Callback for populating the bin fill history table with data
###################################################################
@callback(
    Output('bin-fill-history-table', 'data'),
    Input('fill-history-bin-id-dropdown', 'value'), #Bin ID filter
    Input('update-bin-fill-history-table-interval', 'n_intervals') #Update every 15 min
)
def update_bin_fill_history_table(selected_bin, n_intervals):
    if not selected_bin:
        return [] #Return empty table if dropdown filter is cleared
    
    df = get_bin_fill_history(selected_bin)

    #Add a column showing row numbers
    #Insert new column named 'row_number' at index 0
    #Start from 1, up to the number of rows in that df
    df.insert(0, 'row_number', range(1, len(df) + 1))

    return df.to_dict('records')

###################################################################
# Callback for bin fill level history line chart
# Includes filters 
@callback(
        Output('fill-history-line-chart', 'figure'),
        Input('fill-history-bin-id-dropdown', 'value'),
        Input('fill-history-line-chart-week-dropdown', 'value'), #Filter line chart by week start date
)
def update_fill_history_line_chart(selected_bin_id, selected_week_start):
    if not selected_bin_id or not selected_week_start:
        return go.Figure().update_layout(
            title="No bin selected.",
            plot_bgcolor="#F9F7FA")
    
    df = get_bin_fill_history(selected_bin_id)

    if df.empty:
        return go.Figure()
    
    
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    #Convert selected week start into datetime
    week_start = pd.to_datetime(selected_week_start)
    week_end = week_start + timedelta(days=7)

    #Filter data to the selected week
    df = df[(df['timestamp'] >= week_start) & (df['timestamp'] < week_end)] #Get a copy of the df, not just a view, in case of warning message
    
    #If df empty after filtering show empty graph
    if df.empty:
        return go.Figure().update_layout(
            title="No data for selected week.",
            plot_bgcolor="#F9F7FA")

    fig = go.Figure()
    
    #Line chart for fill level
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['fill_level'],
        name='Fill Level',
        mode='lines+markers+text', #show lines, markers (dots), text
        text=df['fill_level'].round().astype(int).astype(str) + '%', #Text showing fill level above marker
        textposition='top center', #Position relative to markers
        line=dict(color='#22960B'), #green line
        yaxis='y1'
    ))

    #Secondary line chart overlay for CHANGES in fill level
    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['fill_level_change'],
        name='Δ Fill Level',
        mode='lines+markers+text',
        text=df['fill_level_change'].apply(
            lambda x: f"{'+' if x > 0 else ''}{round(x)}%" if pd.notnull(x) else "N/A" #If value is missing return "N/A", round x to nearest whole number instead of decimals
        ), #Text showing fill changes number
        textposition='bottom center', #text position relative to markers
        line=dict(color='#741B7C', dash='dot'), #make it a dash line, purple
        opacity=0.8
    ))

    
    fig.update_layout(
        title="Fill Levels Throughout the Day",
        xaxis=dict(title='Timestamp'),
        yaxis=dict(
            title='Fill Level', 
            range=[-100, 110], #Set range restriction for y-axis
            tickformat='.0f', #Don't use decimals
        ),
        #Legend size
        legend=dict(x=0.01, y=0.99),
        plot_bgcolor="#F9F7FA", #extremely light purple chart bg colour
        margin=dict(t=40, b=30, l=60, r=20),
    )

    return fig

###################################################################
# Callback for populating the WEEKS in MONTH dropdown filters for fill history line chart
@callback(
    Output('fill-history-line-chart-week-dropdown', 'options'), #Week options in the filter
    Output('fill-history-line-chart-week-dropdown', 'value'), #Set the default selected value (to current month/week)
    Input('fill-history-line-chart-month-dropdown', 'value') #Based on the month selected
)
def update_fill_history_line_chart_week_dropdown(selected_month):
    #If no month selected, don't populate the week dropdown filter
    if not selected_month:
        raise exceptions.PreventUpdate
    
    #Convert the string value of the selected month filter, to datetime
    month_start = pd.to_datetime(selected_month)
    weeks = [] #empty list for storing the weeks of the selected month

    for i in range(5): #Maximum of 5 weeks per month
        #Find the start of each week where i=0 for first week, i=1 for second week, etc
        week_start = month_start + timedelta(weeks=i)
        
        #If the new week start date isn't inside the selected month then stop loop
        if week_start.month != month_start.month:
            break
        
        #Calculate end date of the week by adding 6 days to the start day
        week_end = week_start + timedelta(days=6)
        #Format the dropdown display option to "DD Month - DD Month"
        label = f"{week_start.strftime('%d %b')} - {week_end.strftime('%d %b')}"
        
        #Append the dictionary values to the weeks list
        weeks.append({
            'label': label,
            'value': week_start.strftime('%Y-%m-%d') 
        })
    
    #sets weeks[0]['value'] (first week) as default selection if there are any weeks (dropdown options)
    return weeks, weeks[0]['value'] if weeks else None

# Callback for updating the selected bin ID title in fill history line chart
@callback(
        Output('selected-bin-id-line-chart-title', 'children'),
        Input('fill-history-bin-id-dropdown', 'value')
)
def update_bin_id_line_chart_title(selected_bin_id):
    if not selected_bin_id:
        return ""
    return f"Bin ID: {selected_bin_id}"

###################################################################
# Callback for populating the collection history table with data
#Includes column sorting function
###################################################################
@callback(
    Output('collection-history-table', 'data'),
    Output('no-data-message', 'children'),
    Output('collection-table-last-updated-msg', 'children'), #Last updated message 
    Input('collection-table-bin-id-dropdown', 'value'),
    Input('collection-history-table', 'sort_by'), #for column sorting
    Input('update-collection-table-interval', 'n_intervals') #update every 15 min
)
def update_collection_history_table(selected_bin, sort_by, n_intervals):
    if selected_bin is None:
        return [], '', '' #Return empty table if dropdown is cleared of any bin ID 
    
    df = get_collection_history(selected_bin)

    if df.empty:
        return [], f"No past collection records found.", '' #REturn blank string for last updated message
    
    if sort_by:
        col_id = sort_by[0]['column_id']
        direction = sort_by[0]['direction']
        ascending = direction == 'asc'

        if col_id == 'fill_level':
            df = df.sort_values(by='fill_level', ascending=ascending)

        elif col_id == 'time_since_full_string':
            # Use hidden numeric value for accurate sorting
            df = df.sort_values(by='time_since_full', ascending=ascending)

        else:
            df = df.sort_values(by=col_id, ascending=ascending)

    #Format Last Updated message timestamp
    #Get current date and time, convert to string displaying H:M AM/PM
    #Strip leading 0's from the hour
    #Replace any " 0" from minute value with just space in case
    last_updated = datetime.now().strftime("Last updated at %I:%M %p").lstrip("0").replace(" 0", " ")

    return df.to_dict('records'), '', last_updated #'' used to clear the no data message line if df not empty


###################################################################
# Layout
###################################################################
layout = html.Div([
    dbc.Container([
        dbc.Row([
            #Page Header
            dbc.Col(
                html.H4("Fill Level & Collection Activity", className="mb-4"),
                width=12
            )
        ]),


        #Row for bin history table + line chart
        dbc.Row([
            dbc.Col(bin_history_card, xs=12, md=6),
            dbc.Col(bin_fill_history_line_chart, xs=12, md=6),
        ], style={"marginBottom": "20px"}
        ),

        #Row for collection history table
        dbc.Row([
            dbc.Col(collection_table_card, xs=12, md=12),
        ]
        ),
    
    ])

])