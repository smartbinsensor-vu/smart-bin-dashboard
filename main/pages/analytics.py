from dash import Dash, html, register_page, dcc, callback, Input, Output, State, exceptions, no_update
import plotly.graph_objs as go
import pandas as pd
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta
import io

from data_utils import get_bin_data, get_bin_fill_history, get_time_to_80_data, get_daily_bin_collections, get_bin_fill_heatmap_data


#Register this file as a Dash page
register_page(__name__, path="/analytics", name="Data Analytics")


###################################################################
# Create Trend: Avg Bin fill level (weekly, monthly) Time-series chart
###################################################################
bin_df = get_bin_data()
#Get distinct Bin IDs for Bin ID dropdown selector
bin_ids = sorted(bin_df['bin_id'].unique())

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
    #Get today's date and replace with the first day of the Month
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


###################################################################
#Create the card layout for avg fill level by week
avg_fill_level_weekly_graph_card = html.Div([
    dbc.Card([
        dbc.CardHeader([
            dbc.Row([
                dbc.Col(html.H5("Daily Avg Fill Level by Week", className="card-title")) 
            ])
        ], style={
            "backgroundColor": "#F9F7FA", #Header bg colour
            "paddingTop": "15px",
            "borderBottom": "none", #Remove the grey border under cardheader
        }
        ), 

        dbc.CardBody([
            #Container for the 3 dropdowns
            html.Div([
                #Bin ID text
                html.Div("Bin ID:", style={"marginRight": "5px", "marginTop": "9px", "fontSize": "12px", "fontWeight": "bold"}),
                #Bin ID dropdown
                html.Div([
                    dcc.Dropdown(
                        id="weekly-fill-level-bin-id-dropdown",
                        options=[{"label": b, "value": b} for b in bin_ids], #Populate dropdown options from bin_ids df
                        value=bin_ids[0], #by default first ID will be selected
                        style={"width": "120px"},
                        clearable=False,
                    ),
                ], style={"flex": "auto", "marginRight": "20px"}),

                #Dropdown for month
                html.Div([
                    dcc.Dropdown(
                        id="weekly-fill-level-month-dropdown",
                        options=generate_month_options(),
                        value=get_current_month_value(),
                        style={"width": "180px"},
                        clearable=False,
                    ),
                ], style={"flex": "auto", "marginRight": "5px"}),

                #Dropdown for week of month
                html.Div([
                    dcc.Dropdown(
                        id="weekly-fill-level-week-dropdown",
                        options=[], #To be populated via callback
                        value=None, #Show the entire month if week not selected
                        placeholder="Select week",
                        style={"width": "200px"},
                        clearable=True,
                    ),
                ], style={"flex": "auto", "marginRight": "5px"}),

                #Dropdown for exporting avg fill level data -AN
                html.Div([
                    html.Div([
                        dcc.Dropdown(
                            id="export-dropdown",
                            options=[
                                {"label": "Export to Excel", "value": "excel"},
                                #{"label": "Export to PDF", "value": "pdf"}
                            ],
                            placeholder="Export...",
                            style={"width": "150px", "fontSize": "13px"},
                            clearable=True
                        ),
                        dcc.Download(id="download-export"),
                        dcc.Store(id="filtered-weekly-fill-data")
                    ])
                ], style={
                    "display": "flex",
                    "justifyContent": "flex-end",
                    "marginBottom": "10px"
                }),

            #Dropdowns container styling
            ], style={
                "display": "flex",
                "flexWrap": "wrap",
                "gap": "5px",
                #"alignItems": "center",
                "marginBottom": "10px",
                "fontFamily": "Arial",
                "fontSize": "13px",
            }
            ),

        #Create the time series graph
        dcc.Graph(id="weekly-fill-level-time-graph", config={"displayModeBar": False}), #Hide the bar with settings
        ])

    #Card styling
    ], style={
        "backgroundColor": "#ffffff",
        "boxShadow": "0 4px 12px rgba(0,0,0,0.1)",
        #"padding": "10px",
        #"borderRadius": "8px",
    }),
])


###################################################################
# Create Trend: Avg Time Taken For Bin to Get Full (80%) per Day
avg_time_bin_get_full_chart_card = html.Div([
    dbc.Card([
        dbc.CardHeader([
            dbc.Row([
                dbc.Col(html.H5("Avg Time For Bins To Reach 80% Full", className="card-title")) 
            ])
        ], style={
            "backgroundColor": "#F9F7FA", #Header bg colour
            "paddingTop": "15px",
            "borderBottom": "none", #Remove the grey border under cardheader
        }),

        dbc.CardBody([
            #Container for the 3 dropdowns
            html.Div([
                #Bin ID text
                html.Div("Bin ID:", style={"marginRight": "5px", "marginTop": "9px", "fontSize": "12px", "fontWeight": "bold"}),
                #Bin ID dropdown
                html.Div([
                    dcc.Dropdown(
                        id="to-80-full-bin-id-dropdown",
                        options=[{"label": b, "value": b} for b in bin_ids], #Populate dropdown options from bin_ids df
                        value=bin_ids[0], #by default first ID will be selected
                        style={"width": "120px"},
                        clearable=False,
                    ),
                ], style={"flex": "auto", "marginRight": "20px"}),

                #Dropdown for month
                html.Div([
                    dcc.Dropdown(
                        id="to-80-full-month-dropdown",
                        options=generate_month_options(),
                        value=get_current_month_value(),
                        style={"width": "180px"},
                        clearable=False,
                    ),
                ], style={"flex": "auto", "marginRight": "5px"}),

                #Dropdown for week of month
                html.Div([
                    dcc.Dropdown(
                        id="to-80-full-week-dropdown",
                        options=[], #To be populated via callback
                        value=None, #Show the entire month if week not selected
                        placeholder="Select week",
                        style={"width": "200px"},
                        clearable=True,
                    ),
                ], style={"flex": "auto", "marginRight": "5px"}),

                #Dropdown for exporting time to 80% data -AN
                html.Div([
                    dcc.Dropdown(
                        id="export-80-dropdown",
                        options=[
                            {"label": "Export to Excel", "value": "excel"},
                            #{"label": "Export to PDF", "value": "pdf"}
                        ],
                        placeholder="Export...",
                        style={"width": "150px", "fontSize": "13px"},
                        clearable=True
                    ),
                    dcc.Download(id="download-80-export"),
                    dcc.Store(id="filtered-80-data")
                ], style={
                    "display": "flex",
                    "justifyContent": "flex-end",
                    "marginBottom": "10px"
                }),

            #Dropdowns container styling
            ], style={
                "display": "flex",
                "flexWrap": "wrap",
                "gap": "5px",
                #"alignItems": "center",
                "marginBottom": "10px",
                "fontFamily": "Arial",
                "fontSize": "13px",
            }
            ),

        #Create the time series graph
        dcc.Graph(id="time-to-80-line-chart", config={"displayModeBar": False}), #Hide the bar with settings
        ])

    #Card styling
    ], style={
        "backgroundColor": "#ffffff",
        "boxShadow": "0 4px 12px rgba(0,0,0,0.1)",
    }),
])


###################################################################
# Create card for Total Daily Collections made per bin bar chart
daily_collections_bar_chart_card = html.Div([
    dbc.Card([
        dbc.CardHeader([
            dbc.Row([
                dbc.Col(html.H5("Total Collections Per Week", className="card-title"))
            ])
        ], style={
            "backgroundColor": "#F9F7FA", #Header bg colour
            "paddingTop": "15px",
            "borderBottom": "none", #Remove the grey border under cardheader
        }),

        dbc.CardBody([
            #Container for the 2 dropdowns
            html.Div([
                #Bin ID text
                html.Div("Bin ID:", style={"marginRight": "5px", "marginTop": "9px", "fontSize": "12px", "fontWeight": "bold"}),
                #Bin ID dropdown
                html.Div([
                    dcc.Dropdown(
                        id="daily-collections-bin-id-dropdown",
                        options=[{"label": b, "value": b} for b in bin_ids], #Populate dropdown options from bin_ids df
                        value=bin_ids[0], #by default first ID will be selected
                        style={"width": "120px"},
                        clearable=False,
                    ),
                ], style={"flex": "auto", "marginRight": "20px"}),

                #Dropdown for month
                html.Div([
                    dcc.Dropdown(
                        id="daily-collections-month-dropdown",
                        options=generate_month_options(),
                        value=get_current_month_value(),
                        style={"width": "180px"},
                        clearable=False,
                    ),
                ], style={"flex": "auto", "marginRight": "5px"}),

                #Dropdown for exporting daily collections data -AN
                html.Div([
                    dcc.Dropdown(
                        id="export-collections-dropdown",
                        options=[
                            {"label": "Export to Excel", "value": "excel"},
                            #{"label": "Export to PDF", "value": "pdf"}
                        ],
                        placeholder="Export...",
                        style={"width": "150px", "fontSize": "13px"},
                        clearable=True
                    ),
                    dcc.Download(id="download-collections-export"),
                    dcc.Store(id="filtered-collections-data")
                ], style={
                    "display": "flex",
                    "justifyContent": "flex-end",
                    "marginBottom": "10px"
                }),

            #Dropdowns container styling
            ], style={
                "display": "flex",
                "flexWrap": "wrap",
                "gap": "5px",
                "marginBottom": "10px",
                "fontFamily": "Arial",
                "fontSize": "13px",
            }
            ),

            dcc.Graph(id="daily-collections-bar-chart", config={"displayModeBar": False})
        ])
    #Card styling
    ], style={
        "backgroundColor": "#ffffff",
        "boxShadow": "0 4px 12px rgba(0,0,0,0.1)",
    })
])


###################################################################
# Create card for Time Of Day Bins were Emptied
bin_empty_times_bar_chart_card = html.Div([
    dbc.Card([
        dbc.CardHeader([
            dbc.Row([
                dbc.Col(html.H5("Time Of Day Bins Emptied", className="card-title"))
            ])
        ], style={
            "backgroundColor": "#F9F7FA", #Header bg colour
            "paddingTop": "15px",
            "borderBottom": "none", #Remove the grey border under cardheader
        }),

        dbc.CardBody([
            #Container for the 2 dropdowns
            html.Div([
                #Bin ID text
                html.Div("Bin ID:", style={"marginRight": "5px", "marginTop": "9px", "fontSize": "12px", "fontWeight": "bold"}),
                #Bin ID dropdown
                html.Div([
                    dcc.Dropdown(
                        id="time-emptied-bin-id-dropdown",
                        options=[{"label": b, "value": b} for b in bin_ids], #Populate dropdown options from bin_ids df
                        value=bin_ids[0], #by default first ID will be selected
                        style={"width": "120px"},
                        clearable=False,
                    ),
                ], style={"flex": "auto", "marginRight": "20px"}),

                #Dropdown for month
                html.Div([
                    dcc.Dropdown(
                        id="time-emptied-month-dropdown",
                        options=generate_month_options(),
                        value=get_current_month_value(),
                        style={"width": "180px"},
                        clearable=False,
                    ),
                ], style={"flex": "auto", "marginRight": "5px"}),

                #Dropdown for exporting Time of Day Bins EMptied data -AN
                html.Div([
                    html.Div([
                        dcc.Dropdown(
                            id="time-bins-emptied-export-dropdown",
                            options=[
                                {"label": "Export to Excel", "value": "excel"},
                                #{"label": "Export to PDF", "value": "pdf"}
                            ],
                            placeholder="Export...",
                            style={"width": "150px", "fontSize": "13px"},
                            clearable=True
                        ),
                        dcc.Download(id="time-bins-emptied-download-export"),
                        dcc.Store(id="time-bins-emptied-data")
                    ])
                ], style={
                    "display": "flex",
                    "justifyContent": "flex-end",
                    "marginBottom": "10px"
                }),

            #Dropdowns container styling
            ], style={
                "display": "flex",
                "flexWrap": "wrap",
                "gap": "5px",
                "marginBottom": "10px",
                "fontFamily": "Arial",
                "fontSize": "13px",
            }
            ),

            dcc.Graph(id="time-emptied-bar-chart", config={"displayModeBar": False})
        ])
    #Card styling
    ], style={
        "backgroundColor": "#ffffff",
        "boxShadow": "0 4px 12px rgba(0,0,0,0.1)",
    })
])



###################################################################
# Create card for Avg Hourly Fill Activity Heatmap
fill_activity_heatmap_card = html.Div([
    dbc.Card([
        dbc.CardHeader([
            dbc.Row([
                dbc.Col(html.H5("Avg Hourly Fill Level Activity Heatmap", className="card-title"))
            ])
        ], style={
            "backgroundColor": "#F9F7FA", #Header bg colour
            "paddingTop": "15px",
            "borderBottom": "none", #Remove the grey border under cardheader
        }),

        dbc.CardBody([
            #Container for the 2 dropdowns
            html.Div([
                #Bin ID text
                html.Div("Bin ID:", style={"marginRight": "5px", "marginTop": "9px", "fontSize": "12px", "fontWeight": "bold"}),
                #Bin ID dropdown
                html.Div([
                    dcc.Dropdown(
                        id="fill-activity-heatmap-bin-id-dropdown",
                        options=[{"label": b, "value": b} for b in bin_ids], #Populate dropdown options from bin_ids df
                        value=bin_ids[0], #by default first ID will be selected
                        style={"width": "120px"},
                        clearable=False,
                    ),
                ], style={"flex": "auto", "marginRight": "20px"}),

                #Dropdown for month
                html.Div([
                    dcc.Dropdown(
                        id="fill-activity-heatmap-month-dropdown",
                        options=generate_month_options(),
                        value=get_current_month_value(),
                        style={"width": "180px"},
                        clearable=False,
                    ),
                ], style={"flex": "auto", "marginRight": "5px"}),

                #Dropdown for exporting Fill Activity Heatmap data -AN
                html.Div([
                    html.Div([
                        dcc.Dropdown(
                            id="fill-activity-heatmap-export-dropdown",
                            options=[
                                {"label": "Export to Excel", "value": "excel"},
                                #{"label": "Export to PDF", "value": "pdf"}
                            ],
                            placeholder="Export...",
                            style={"width": "150px", "fontSize": "13px"},
                            clearable=True
                        ),
                        dcc.Download(id="fill-activity-heatmap-download-export"),
                        dcc.Store(id="fill-activity-heatmap-data")
                    ])
                ], style={
                    "display": "flex",
                    "justifyContent": "flex-end",
                    "marginBottom": "10px"
                }),

            #Dropdowns container styling
            ], style={
                "display": "flex",
                "flexWrap": "wrap",
                "gap": "5px",
                "marginBottom": "10px",
                "fontFamily": "Arial",
                "fontSize": "13px",
            }
            ),

            dcc.Graph(id="fill-activity-heatmap", config={"displayModeBar": False})
        ])
    #Card styling
    ], style={
        "backgroundColor": "#ffffff",
        "boxShadow": "0 4px 12px rgba(0,0,0,0.1)",
    })
])





###################################################################
# Callback for populating weekly fill level WEEK dropdown options
###################################################################
@callback(
    Output("weekly-fill-level-week-dropdown", "options"), #Week options in the filter
    Output("weekly-fill-level-week-dropdown", "value"),
    Input("weekly-fill-level-month-dropdown", "value"), #Change week options based on month selected
)
def update_week_dropdown_options(selected_month):
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
    
    #sets None weeks as default selection if not chosen (so entire month trend is shown)
    return weeks, None


###################################################################
#Callback for building the Weekly Fill Level Time-series Graph
@callback(
    Output("weekly-fill-level-time-graph", "figure"),
    Output("filtered-weekly-fill-data", "data"), #Store the filtered data for exporting -AN

    Input("weekly-fill-level-bin-id-dropdown", "value"), #Bin ID
    Input("weekly-fill-level-month-dropdown", "value"), #Month
    Input("weekly-fill-level-week-dropdown", "value"), #Week
)
def generate_weekly_fill_level_time_series(selected_bin_id, selected_month, selected_week_start):
    #Fetch bin fill level data
    df = get_bin_fill_history(selected_bin_id)

    if df.empty:
        #If no data, return empty graph
        return go.Figure(
            layout=go.Layout(
                title="No data available.",
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                plot_bgcolor="#F9F7FA"
            )
        ), []#and return empty data for the data store for exports
    
    #Get timestamps and format to datetime for handling
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    #Create a 'date' column to group by day
    df['date'] = df['timestamp'].dt.date #Get date only

    #Filter df rows by the selected month only, and format into string YYYY-MM
    df = df[df['timestamp'].dt.strftime("%Y-%m") == selected_month]

    #Filter data to the selected week if selected
    if selected_week_start:
        #Convert selected week start string (e.g. '2025-05-06') into datetime object (to compare with df['date'])
        week_start = pd.to_datetime(selected_week_start).date() #convert to Python datetime object to compare below
        week_end = week_start + timedelta(days=7)

        #Filter rows where date column is within week_start and end
        df = df[(df['date'] >= week_start) & (df['date'] < week_end)]
    
    #Group by the date and calc AVG, min and max
    daily_fill_stats = (
        df.groupby("date")['fill_level'] #Group fill level values by each date
        .agg(avg="mean", min="min", max="max") #Find the avg, min & max in each group of fill level values per date
        .reset_index() #groupby() makes the 'date' column the index, reset it to normal for plotting the graph
        .sort_values("date") #Sort date ascending
    )

    #If no data found AFTER filtering, return empty graph
    if daily_fill_stats.empty:
        return go.Figure(
            layout=go.Layout(
                title="No data available for selected filters.",
                xaxis=dict(title="Date", tickformat="%d %b"),
                yaxis=dict(title="Fill Level (%)", range=[0, 100]),
                plot_bgcolor="#F9F7FA"
            )
        ), []#and return empty data for the data store for exports

    #Build the time series graph
    fig = go.Figure()

    #AVG plots
    fig.add_trace(
        go.Scatter(
            x=daily_fill_stats["date"],
            y=daily_fill_stats["avg"],
            mode="lines+markers",
            name="Avg Fill",
            line=dict(color="#F08A07", shape="spline", smoothing=1.3), #Make the line curved and orange
        )
    ) 

    #MIN plots
    fig.add_trace(
        go.Scatter(
            x=daily_fill_stats["date"],
            y=daily_fill_stats["min"],
            mode="lines+markers",
            name="Min Fill",
            line=dict(color="#79C3F0", shape="spline", smoothing=1.3), #Make the line curved
        )
    )

    #MAX plots
    fig.add_trace(
        go.Scatter(
            x=daily_fill_stats["date"],
            y=daily_fill_stats["max"],
            mode="lines+markers",
            name="Max Fill",
            line=dict(color="#A981F0", shape="spline", smoothing=1.3), #Make the line curved
        
        )
    )

    #Style the figure layout
    fig.update_layout(
        title=f"Fill Level Trends for Bin: #{selected_bin_id}",
        xaxis=dict(title="Date", tickformat="%d %b"),
        yaxis=dict(title="Fill Level (%)", range=[0, 100]),
        hovermode="x unified", #Show single tooltip on hover
        margin=dict(l=40, r=20, t=50, b=40),
        plot_bgcolor="#F9F7FA", #extremely light purple chart bg colour
    )


    return fig, daily_fill_stats.to_dict("records")


###################################################################
# Callback for populating Time TAken to 80% Full WEEK dropdown options
@callback(
    Output("to-80-full-week-dropdown", "options"),
    Output("to-80-full-week-dropdown", "value"),
    Input("to-80-full-month-dropdown", "value"),
)
def update_time_to_80_week_dropdown_options(selected_month):
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
    
    #sets None weeks as default selection if not chosen (so entire month trend is shown)
    return weeks, None

###################################################################
# Callback for building Time TAken to 80% Full Chart
@callback(
    Output("time-to-80-line-chart", "figure"),
    Output("filtered-80-data", "data"), #Store the filtered data for exporting -AN

    Input("to-80-full-bin-id-dropdown", "value"), #Bin ID
    Input("to-80-full-month-dropdown", "value"), #Month
    Input("to-80-full-week-dropdown", "value"), #Week
)
def generate_time_to_80_chart(selected_bin_id, selected_month, selected_week_start):
    #Get df based on bin ID  selected
    df = get_time_to_80_data(selected_bin_id)

    if df.empty:
        #If no data, return empty graph
        return go.Figure(
            layout=go.Layout(
                title="No data available.",
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                plot_bgcolor="#F9F7FA"
            )
        ), []#and return empty data for the data store for exports

    #Get timestamps and format to datetime for handling
    df['date'] = pd.to_datetime(df['date'])

    #Filter df rows by the selected month only, and format into string YYYY-MM
    df = df[df['date'].dt.strftime("%Y-%m") == selected_month]

    #Filter data to the selected week if selected
    if selected_week_start:
        #Convert selected week start string (e.g. '2025-05-06') into datetime object (to compare with df['date'])
        week_start = pd.to_datetime(selected_week_start)
        week_end = week_start + timedelta(days=7)

        #Filter rows where date column is within week_start and end
        df = df[(df['date'] >= week_start) & (df['date'] < week_end)]

    #Find the avg times for bins to get full each day
    daily_avg_to_80_full = (
        df.groupby("date")['time_to_fill'] #Group values by each date
        .mean() #Find the avg in each group of time to 80% values per date
        .reset_index() #groupby() makes the 'date' column the index, reset it to normal for plotting the graph
        .sort_values("date") #Sort date ascending
    )
    
    #If no data found AFTER filtering, return empty graph
    if daily_avg_to_80_full.empty:
        return go.Figure(
            layout=go.Layout(
                title="No data available for selected filters.",
                xaxis=dict(title="Date", tickformat="%d %b"),
                yaxis=dict(title="Duration (days)", rangemode="tozero"),
                plot_bgcolor="#F9F7FA"
            )
        ), []#and return empty data for the data store for exports

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=daily_avg_to_80_full["date"],
            y=(daily_avg_to_80_full["time_to_fill"] / 1440).round(2), #There are 1440 minutes per day, divide by this to get days instead of minutes
            mode="lines+markers",
            name="Avg Time to 80%",
            line=dict(color="#22960B", shape="spline", smoothing=1.3),
            hovertemplate="Duration: %{y} days<extra></extra>" #Tooltip text, extra tags hides default text
        )
    )

    #Style the figure layout
    fig.update_layout(
        title=f"Avg Time to Reach 80% Full for Bin: #{selected_bin_id}",
        xaxis=dict(title="Date", tickformat="%d %b"),
        yaxis=dict(title="Duration (days)", rangemode="tozero"),
        hovermode="x unified", #Show single tooltip box for each marker
        margin=dict(l=40, r=20, t=50, b=40),
        plot_bgcolor="#F9F7FA",
    )

    return fig, daily_avg_to_80_full.to_dict("records")



###################################################################
# Callback for building WEEKLY Collections bar chart
@callback(
    Output("daily-collections-bar-chart", "figure"),
    Output("filtered-collections-data", "data"), #Store the filtered data for exporting -AN

    Input("daily-collections-bin-id-dropdown", "value"), #Bin ID
    Input("daily-collections-month-dropdown", "value"), #Month
)
def generate_collections_bar_chart(selected_bin_id, selected_month):
    #Get empty event timestamps for selected bin
    df = get_daily_bin_collections(selected_bin_id)

    if df.empty:
        #If no data, return empty graph
        return go.Figure(
            layout=go.Layout(
                title="No data available.",
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                plot_bgcolor="#F9F7FA"
            )
        ), []#and return empty data for the data store for exports

    #Get timestamps and format to datetime for handling
    df['date'] = pd.to_datetime(df['date'])

    #Filter df rows by the selected month only, and format into string YYYY-MM
    df = df[df['date'].dt.strftime("%Y-%m") == selected_month]

    #Create a column for the start of the week, to group the data by week
    df['week_start'] = df['date'] - pd.to_timedelta(df['date'].dt.weekday, unit='d') #Get the Monday of that week

    #Find the total collections per week for selected bin
    weekly_collection_counts = (
        df.groupby("week_start")['timestamp'] #Group by each Monday (week_start)
        .count() #Find the sum of collection events in each week
        .reset_index(name="collections") #groupby() makes the 'date' column the index, reset it to normal for plotting the graph
        .sort_values("week_start") #Sort ascending
    )

    #If no data found AFTER filtering, return empty graph
    if weekly_collection_counts.empty:
        return go.Figure(
            layout=go.Layout(
                title="No data available for selected filters.",
                xaxis=dict(title="Date", tickformat="%d %b"),
                yaxis=dict(title="Times Emptied"),
                plot_bgcolor="#F9F7FA"
            )
        ), []#and return empty data for the data store for exports

    #Create list of colours for the bars depending on collection value
    colours = []
    for count in weekly_collection_counts["collections"]:
        if count >= 5:
            colours.append("#A981F0")  # Purple

        elif count >= 3:
            colours.append("#79C3F0")  #Blue

        elif count >= 1:
            colours.append("#22960B")  #Green

        else:
            colours.append("#F08A07")  #Orange

    #Create the bar chart
    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=weekly_collection_counts["week_start"],
            y=weekly_collection_counts["collections"],
            marker_color=colours,
            hovertemplate="Total collections: %{y}<extra></extra>",
        )
    )

    #Style the figure layout
    fig.update_layout(
        title=f"Weekly Collections for Bin: #{selected_bin_id}",
        xaxis=dict(
            title="Weeks", 
            tickformat="%d %b", #day month
            tickmode="array",
            tickvals=weekly_collection_counts['week_start'], #Value of each x-axis tick is each Week's Monday
            #Manually set the text for each tick to be the date range of the week i.e. 1 Jul - 7 Jul
            ticktext=[
                f"{week.strftime('%d %b')} - {(week + timedelta(days=6)).strftime('%d %b')}" 
                for week in weekly_collection_counts['week_start']
            ]
        ),

        yaxis=dict(title="Total Times Emptied"),
        hovermode="x unified", #Show single tooltip box on hover of markers
        margin=dict(l=40, r=20, t=50, b=40),
        plot_bgcolor="#F9F7FA"
    )

    return fig, weekly_collection_counts.to_dict("records")


###################################################################
# Callback for building Time of Day Bins Emptied bar chart
@callback(
    Output("time-emptied-bar-chart", "figure"),
    Output("time-bins-emptied-data", "data"), #Store the filtered data for exporting

    Input("time-emptied-bin-id-dropdown", "value"), #Bin ID
    Input("time-emptied-month-dropdown", "value"), #Month
)
def generate_time_emptied_bar_chart(selected_bin_id, selected_month):
    #Get empty event timestamps for selected bin
    df = get_daily_bin_collections(selected_bin_id)

    if df.empty:
        #If no data, return empty graph
        return go.Figure(
            layout=go.Layout(
                title="No data available.",
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                plot_bgcolor="#F9F7FA"
            )
        ), []#and return empty data for the data store for exports

    #Get timestamps and format to datetime for handling
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    #Filter df rows by the selected month only, and format into string YYYY-MM
    df = df[df['timestamp'].dt.strftime("%Y-%m") == selected_month]

    #Make new column with only the hour value extracted from timestamp
    df['hour'] = df['timestamp'].dt.hour

    #Find the total collections per HOUR for selected bin
    collection_hour_counts = (
        df.groupby("hour")['timestamp'] #Group by each hour
        .count() #Find the sum of collections in each hour
        .reset_index(name="collections") #groupby() makes the 'date' column the index, reset it to normal for plotting the graph
        .sort_values("hour") #Sort ascending by hour
    )

    #If no data found AFTER filtering, return empty graph
    if collection_hour_counts.empty:
        return go.Figure(
            layout=go.Layout(
                title="No data available for selected filters.",
                xaxis=dict(title="Date", tickformat="%d %b"),
                yaxis=dict(title="Times Emptied"),
                plot_bgcolor="#F9F7FA"
            )
        ), []#and return empty data for the data store for exports
    
    #Represent all hours in the chart 0-2300
    #Create a dictionary with key 'hour' containing list of numbers from 0-23
    all_hours = pd.DataFrame({'hour': list(range(24))})

    #Then join collection_hour_counts table with table of all_hours
    #Join based on "hour" column
    #How='left' -> keep all rows from left table (all_hours)
    #Hours with no entries are filled with "0"
    collection_hour_counts = pd.merge(all_hours, collection_hour_counts, on='hour', how='left').fillna(0)

    #Convert column into integer to clean up any floats
    collection_hour_counts['collections'] = collection_hour_counts['collections'].astype(int)

    #Build bar chart
    fig = go.Figure(
        data=[
            go.Bar(
                x=collection_hour_counts['hour'],
                y=collection_hour_counts['collections'],
                #Set bar colours
                marker=dict(
                    color=collection_hour_counts['hour'],  #Use hour (x-axis) for gradient
                    colorscale='magenta', #gradient colour
                    showscale=False  #Hide scale legend
                ),
                hovertemplate="Hour: %{x}:00<br>Collections: %{y}<extra></extra>",
            )
        ]
    )

    #Style the figure layout
    fig.update_layout(
        title=f"Collection Times for Bin: #{selected_bin_id}",
        xaxis=dict(title="Hour of Day", dtick=1), #Ensure every hour (tick) has a label
        yaxis=dict(title="Total Collections"),
        margin=dict(l=40, r=20, t=50, b=40),
        hovermode="x unified", #single tooltip box
        plot_bgcolor="#F9F7FA"
    )

    return fig, collection_hour_counts.to_dict("records") 



###################################################################
# Callback for building Avg Hourly Fill Activity Heatmap
@callback(
    Output("fill-activity-heatmap", "figure"),
    Output("fill-activity-heatmap-data", "data"), #Store filtered data for exporting

    Input("fill-activity-heatmap-bin-id-dropdown", "value"), #Bin ID
    Input("fill-activity-heatmap-month-dropdown", "value"), #Month
)
def build_fill_activity_heatmap(selected_bin_id, selected_month):
    #Fetch the df and input the bin ID and month parameters via the dropdowns
    df = get_bin_fill_heatmap_data(selected_bin_id, selected_month)

    if df.empty:
        #If no data, return empty graph
        return go.Figure(
            layout=go.Layout(
                title="No data available.",
                xaxis=dict(title="Hour of Day", dtick=1), #each x-axis tick is an hour 
                yaxis=dict(title="Day of Week"),
                plot_bgcolor="#F9F7FA"
            )
        ), []#and return empty data for the data store for exports

    #Ensure the hour column is an int and not string
    df['hour'] = df['hour'].astype(int)

    #Rearrange the df into a table using the pivot method where:
    #Columns = hour of day from 0-23
    #Rows = days of the week (Mon-Sun)
    #Values = avg fill increases (per hour)
    #Since the heatmap requires these 3 parameters
    pivot = df.pivot(index='day_of_week', columns='hour', values='avg_fill_change')

    #Reorder the days of week again (pivot may alphabetically order them again),
    #And in case there is data on days missing
    ordered_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    pivot = pivot.reindex(ordered_days)

    #Ensure there are 0-23 hours on the x-axis, even if data is unavailable
    pivot = pivot.reindex(columns=list(range(24)), fill_value=None)

    #Create the heatmap
    fig = go.Figure(
        data=go.Heatmap(
            z=pivot.values, #avg fill increases 
            x=pivot.columns, #hours 0-23 x-axis
            y=pivot.index, #day of week y-axis
            colorscale='purples', #heat colour theme
            colorbar=dict(title="Avg Fill Increase (%)"), #Legend
            #Modify tooltip text
            hovertemplate="Hour: %{x}:00<br>%{y}<br>Avg Fill Increase: %{z}%<extra></extra>",
            
            texttemplate="%{z}", #Display heat values on cells
            textfont={"size":8.5}, #Font size for heat value text
            hoverongaps=False #Don't show tooltip for cells with no value
        )
    )

    #Style the heatmap layout
    fig.update_layout(
        title=f"Hourly Fill Activity for Bin: #{selected_bin_id}",
        xaxis=dict(title="Hour of Day", dtick=1), #each x-axis tick is an hour 
        yaxis=dict(title="Day of Week"),
        margin=dict(l=40, r=20, t=50, b=40),
        plot_bgcolor="#FCFCFC" #white bg
    )

    return fig, df.to_dict("records") 



###################################################################
# EXPORT Callbacks
###################################################################

# Callback for exporting Avg Weekly Fill Level to Excel or PDF -AN
@callback(
    Output("download-export", "data"),
    Input("export-dropdown", "value"),
    State("filtered-weekly-fill-data", "data"),
    allow_duplicate=True
)
def export_data(selected_option, stored_data):
    if not stored_data:
        return no_update

    df = pd.DataFrame(stored_data)

    if selected_option == "excel":
        with io.BytesIO() as buffer:
            df.to_excel(buffer, index=False)
            return dcc.send_bytes(buffer.getvalue(), filename="fill_level_report.xlsx")


    return no_update


###################################################################
# Callback for exporting Time to 80% Full data to Excel or PDF -AN
@callback(
    Output("download-80-export", "data"),
    Input("export-80-dropdown", "value"),
    State("filtered-80-data", "data"),
    allow_duplicate=True
)
def export_80_chart(option, data):
    if not data:
        return no_update

    df = pd.DataFrame(data)

    if option == "excel":
        with io.BytesIO() as buffer:
            df.to_excel(buffer, index=False)
            return dcc.send_bytes(buffer.getvalue(), filename="time_to_80_report.xlsx")


    return no_update


###################################################################
# Callback for exporting Daily Collections data to Excel or PDF -AN
@callback(
    Output("download-collections-export", "data"),
    Input("export-collections-dropdown", "value"),
    State("filtered-collections-data", "data"),
    allow_duplicate=True
)
def export_collections(option, data):
    if not data:
        return no_update

    df = pd.DataFrame(data)

    if option == "excel":
        with io.BytesIO() as buffer:
            df.to_excel(buffer, index=False)
            return dcc.send_bytes(buffer.getvalue(), filename="collections_report.xlsx")


    return no_update


###################################################################
# Callback for exporting Time Bins Emptied data to Excel or PDF -AN
@callback(
    Output("time-bins-emptied-download-export", "data"),
    Input("time-bins-emptied-export-dropdown", "value"),
    State("time-bins-emptied-data", "data"),
    allow_duplicate=True
)
def export_time_bins_emptied(option, data):
    if not data:
        return no_update

    df = pd.DataFrame(data)

    if option == "excel":
        with io.BytesIO() as buffer:
            df.to_excel(buffer, index=False)
            return dcc.send_bytes(buffer.getvalue(), filename="time_bins_emptied_report.xlsx")


    return no_update

###################################################################
# Callback for exporting Fill Activity Heatmap data to Excel or PDF -AN
@callback(
    Output("fill-activity-heatmap-download-export", "data"),
    Input("fill-activity-heatmap-export-dropdown", "value"),
    State("fill-activity-heatmap-data", "data"),
    allow_duplicate=True
)
def export_fill_activity_heatmap(option, data):
    if not data:
        return no_update

    df = pd.DataFrame(data)

    if option == "excel":
        with io.BytesIO() as buffer:
            df.to_excel(buffer, index=False)
            return dcc.send_bytes(buffer.getvalue(), filename="fill_activity_report.xlsx")


    return no_update






###################################################################
#######      LAYOUT       ######
###################################################################
layout = html.Div([
    dbc.Container([

        dbc.Row([
            dbc.Col(
                html.H4("Data Analytics", className="mb-4"),
                width=12
            )
        ]),

        #Card for average fill levels
        dbc.Row([
            dbc.Col(avg_fill_level_weekly_graph_card, xs=12, md=12)
        ], style={"marginBottom": "20px"}),

        #Card for avg duration to get full 80%
        dbc.Row([
            dbc.Col(avg_time_bin_get_full_chart_card, xs=12, md=12)
        ], style={"marginBottom": "20px"}),

        #Card for daily total collections
        dbc.Row([
            dbc.Col(daily_collections_bar_chart_card, xs=12, md=6),
            dbc.Col(bin_empty_times_bar_chart_card, xs=12, md=6)
        ], style={"marginBottom": "20px"}),

        #Card for Heat map avg fill activity
        dbc.Row([
            dbc.Col(fill_activity_heatmap_card, xs=12, md=12),
        ])

    ])
    
]) 
