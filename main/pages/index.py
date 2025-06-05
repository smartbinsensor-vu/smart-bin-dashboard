from dash import Dash, html, Input, Output, dcc, register_page, callback, dash_table, exceptions
import dash_bootstrap_components as dbc
import dash_leaflet as dl
from datetime import datetime
import pandas as pd
import math
import plotly.express as px

#import layouts, componenets, styles here
from data_utils import get_fill_level_stats, get_recently_emptied_bins, get_bin_data, get_marker_colour, get_top_fullest_bins, get_weekly_collection_stats, get_complete_bin_table, get_alerts_data
from layouts import sidebar, CONTENT_STYLE
import callbacks


#Register this file as a Dash page
#This is the main page of the app, so it is registered with a path of "/"
register_page(__name__, path="/", name="Smart Bin Dashboard") 


###################################################################
# Create the cards to show total alerts in each table at top of page
###################################################################
total_active = html.Div([
    #Redirect card to alerts page
    dcc.Link(
        href="/alerts", style={"textDecoration": "none", #Turns off the underlines with links
                           "color": "inherit"}, #Inherit the parent colour so that default bootstrap theme for links colours rgba(var(--bs-link-color-rgb) in green doesn't show
        children=dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col(
                        html.I(className="bi bi-exclamation-triangle", 
                            style={
                                "fontSize": "2rem", #icon size
                                "color": "white",
                                "textAlign": "center",
                                "display": "flex",
                                "alignItems": "center",
                                "justifyContent": "center",
                                "height": "100%",                
                                }),
                                width=5
                    ),
                    dbc.Col([
                        html.H6("Active",
                        style={
                            "color": "white",
                        }
                        ),
                        html.H2(
                            id="active-alerts-count",
                            style={
                                "color": "white",
                                "fontWeight": "bold",
                            }
                        ),
                    ], width=7, style={"textAlign": "left"})
                ], align="center", style={"height": "100%"})
                
            ])
        #Style card
        ], style={
            "backgroundColor": "#DB2225", #red bg
            "textAlign": "center",
            "borderRadius": "10px",
            "boxShadow": "0 4px 12px rgba(0, 0, 0, 0.1)",
            "padding": "5px",
            "fontFamily": "Verdana",
        }),
    )
])

total_ignored = html.Div([
    #Redirect card to alerts page
    dcc.Link(
        href="/alerts", style={"textDecoration": "none", #Turns off the underlines with links
                           "color": "inherit"}, #Inherit the parent colour so that default bootstrap theme for links colours rgba(var(--bs-link-color-rgb) in green doesn't show
        children=dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col(
                        #Icon
                        html.I(className="bi bi-dash-circle-dotted", 
                            style={
                                "fontSize": "2rem", #icon size
                                "color": "white",
                                "textAlign": "center",
                                "display": "flex",
                                "alignItems": "center",
                                "justifyContent": "center",
                                "height": "100%",                
                                }),
                                width=5
                    ),
                    dbc.Col([
                        html.H6("Ignored",
                        style={
                            "color": "white"
                        }
                    ),
                    html.H2(
                        id="ignored-alerts-count",
                        style={
                            "color": "white",
                            "fontWeight": "bold",
                        }
                    ),
                    ], width=7, style={"textAlign": "left"})
                ], align="center", style={"height": "100%"}) #row styling
            
            ])
        #Style card
        ], style={
            "backgroundColor": "#612C80", #purple bg
            "textAlign": "center",
            "borderRadius": "10px",
            "boxShadow": "0 4px 12px rgba(0, 0, 0, 0.1)",
            "padding": "5px",
            "fontFamily": "Verdana",
        }),
    )
])

total_overfill_risk = html.Div([
    #Redirect card to alerts page
    dcc.Link(
        href="/alerts", style={"textDecoration": "none", #Turns off the underlines with links
                           "color": "inherit"}, #Inherit the parent colour so that default bootstrap theme for links colours rgba(var(--bs-link-color-rgb) in green doesn't show
        children=dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col(
                        #Icon
                        html.I(className="bi bi-trash3", 
                            style={
                                "fontSize": "2rem", #icon size
                                "color": "white",
                                "textAlign": "center",
                                "display": "flex",
                                "alignItems": "center",
                                "justifyContent": "center",
                                "height": "100%",                
                                }),
                                width=5
                    ),
                    dbc.Col([
                        html.H6("Overfill Risk",
                        style={
                            "color": "white"
                        }
                    ),
                    html.H2(
                        id="overfill-alerts-count",
                        style={
                            "color": "white",
                            "fontWeight": "bold",
                        }
                    ),
                    ], width=7, style={"textAlign": "left"})
                ], align="center", style={"height": "100%"}) #row styling
            
            ])
        #Style card
        ], style={
            "backgroundColor": "#F08A07",
            "textAlign": "center",
            "borderRadius": "10px",
            "boxShadow": "0 4px 12px rgba(0, 0, 0, 0.1)",
            "padding": "5px",
            "fontFamily": "Verdana",
        }),
    )
])



"""
total_resolved = html.Div([
    dbc.Card([
        dbc.CardBody([
            html.H6("Resolved",
                    style={
                        "color": "white"
                    }
            ),
            html.H2(
                id="resolved-alerts-count",
                style={
                    "color": "white",
                    "fontWeight": "bold",
                }
            ),
            
        ])
    #Style card
    ], style={
        "backgroundColor": "#6FB838",
        "textAlign": "center",
        "borderRadius": "10px",
        "boxShadow": "0 4px 12px rgba(0, 0, 0, 0.1)",
        "padding": "5px",
        "fontFamily": "Verdana",
    }),
])
"""
###########################################################################
#Create the mini card for Today's NEw and Resolved alerts
todays_alerts_card = html.Div([
    #Redirect card to alerts page
    dcc.Link(
        href="/alerts", style={"textDecoration": "none", #Turns off the underlines with links
                           "color": "inherit"}, #Inherit the parent colour so that default bootstrap theme for links colours rgba(var(--bs-link-color-rgb) in green doesn't show
        children=dbc.Card([
            dbc.CardBody([
                #Card header
                html.Div("Today's Stats", style={
                    "textAlign": "left",
                    "fontSize": "0.75rem",
                    "fontWeight": "bold",
                    "color": "white",
                    "marginBottom": "7px",
                    "marginTop": "0px", #No top margin
                }),

                dbc.Row([
                    dbc.Col([
                        #Create the icon
                        html.I(className="bi bi-bar-chart-steps", 
                            style={
                                    "fontSize": "1.75rem", 
                                    "color": "white", 
                                    "textAlign": "center", 
                                    "display": "block",
                                    #"marginRight": "5px", #shift icon to the right a bit
                        })
                    ], width=2, style={"display": "flex", "alignItems": "center"}),
                    #Header
                    dbc.Col([
                        html.Div([
                            #New Alerts Today
                            dbc.Row([
                                dbc.Col([
                                    html.H6("New Alerts", style={"color": "white"}),                    
                                ], width=8, style={"textAlign": "right"}),
                                dbc.Col([
                                    html.H6(id="todays-new-alerts", style={"fontWeight": "bold"}),
                                ], width=4, style={"textAlign": "right"}),
                            ]),

                            #Resolved Alerts Today
                            dbc.Row([
                                dbc.Col([
                                    html.H6("Resolved", style={"color": "white"}),                   
                                ], width=8, style={"textAlign": "right"}),
                                dbc.Col([
                                    html.H6(id="todays-resolved-alerts", style={"fontWeight": "bold"}),
                                ], width=4, style={"textAlign": "right"})
                            ])

                        ], style={"marginTop": "8px", "marginLeft": "5px"}) #slight vertical and hoeizontal spacing               
                    ], width=10)
                ])         
                
            ])
        #Card styling    
        ], style={
            "backgroundColor": "#3196F0", 
            "color": "white",
            "borderRadius": "10px",
            "paddingLeft": "10px",
            "paddingRight": "10px",
            "paddingTop": "0px", #Reduce top padding between header
            "paddingBottom": "5px",
            "fontFamily": "Verdana",
            "boxShadow": "0 4px 12px rgba(0, 0, 0, 0.1)",
            #"minHeight": "125px",
            #"height": "100%"  # Consistent height with others
        })
    )
])






###########################################################################
# For the Bin Fill Level Stats card
###########################################################################
#Colours for each fill level category
fill_colours = {
	"Getting Full": "#FFCC00", #Yellow
	"Moderately Full": "#FF9900", #Orange
	"Almost Full": "#C2171D", #Dark Red
	"Overfill Risk": "#FF1E27" #Bright Red
}

#Define fill level ranges for each category header + subheader
fill_ranges = {
	"Getting Full": "(>60%)",
	"Moderately Full": "(>70%)",
	"Almost Full": "(>80%)",
	"Overfill Risk": "(>90%)"
}

#Function to build the rows for the fill level stats card
def build_fill_level_rows(fill_df):
    stat_rows = []
    for _, row in fill_df.sort_values(by="fill_category", key=lambda x: x.map({
        "Getting Full": 1,
        "Moderately Full": 2,
        "Almost Full": 3,
        "Overfill Risk": 4
    }), ascending=False).iterrows():
        category = row['fill_category']
        count = row['count']
        color = fill_colours.get(category, "#95A5A6")  #Default color if not found
        fill_range = fill_ranges.get(category, "")
        
        stat_rows.append(
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Strong(category),
                        html.Div(fill_range, style={"fontSize": "0.8em", "color": "#666"})  # Smaller font for range               
                    ])
                ], width=9),
                dbc.Col([
                    html.Div(str(count), style={"textAlign": "right", "fontWeight": "bold"})
                ], width=3),
            ], className="mb-3", 
            style={
                "borderLeft": f"5px solid {color}", 
                "paddingLeft": "10px", 
                "transition": "background-color 0.2s",
            })
        )    
    return stat_rows  

#Builds the full card widget for Current Bin fill stats
def build_fill_level_card():
    fill_df = get_fill_level_stats()  # Get the latest fill level stats
    stat_rows = build_fill_level_rows(fill_df)
    
    #Build the full card widget for Bin fill stats
    return html.Div(
        children=[
            dbc.Card([
                dbc.CardHeader(
                    dbc.Row([
                        dbc.Col(html.H5("Current Fill Stats", className="card-title"))
                    ]), style={
                    "backgroundColor": "#FFFFFF", 
                    "paddingTop": "2px",
                    "paddingLeft": "5px", #move text left a little
                    "borderBottom": "none", #Remove the grey border under cardheader
                    }
                ),
                dbc.CardBody([
                    html.Div(id="fill-level-data", children=stat_rows)
                ]),            
            ],
                style={
                    "backgroundColor": "#FFFFFF",
                    "boxShadow": "0 4px 12px rgba(0, 0, 0, 0.1)",
                    "borderRadius": "5px",
                    "padding": "20px",
                    "height": "100%",
                    "minHeight": "300px",
                    "width": "100%"
                }
            ),

            #Auto update every 15 minutes
            dcc.Interval(
                id='update-fill-level-stats',
                interval=900000,  #15 minutes in milliseconds
                n_intervals=0
            )
        ]
    )

    
#Now create the initial fill level stats card and layout
fill_level_card = build_fill_level_card()

###################################################################
# Callback for updating the Current fill stats card 
###################################################################
@callback(
    Output('fill-level-data', 'children'),
    Input('update-fill-level-stats', 'n_intervals')
)
def update_fill_level_stats(n):
    #Fetch the fill level data
    fill_df = get_fill_level_stats()
    #Update the rows for each fill level category
    stat_rows = build_fill_level_rows(fill_df)

    return stat_rows




###################################################################
# Create the card for the bin table with full bin info
###################################################################
#Fetch the data using the function
bin_table_df = get_complete_bin_table()

bin_data_table_card = html.Div([
    dbc.Card([
        dbc.CardHeader(
            #Card header
            dbc.Row([
                dbc.Col(html.H5("Bins Summary", className="card-title", style={"marginBottom": "0"}))
            ]), style={
                "backgroundColor": "#FFFFFF", #Header bg colour
                "paddingTop": "15px",
                "borderBottom": "none" #Remove the grey border under cardheader
            }
        ),    
        dbc.CardBody([
            html.Div([
                #Bin id Search dropdown bar
                html.Div([
                    dcc.Dropdown(
                        id='bin-table-id-dropdown',
                        options=[], #Dropdown options will be added using callback based on user input
                        placeholder="Search Bin ID...",
                        searchable=True, #Enable typing and searching
                        style={"width": "130px", "marginRight": "10px"},
                        clearable=True, #Shows a small "x" to reset
                    ),            
                ], style={
                    "zIndex": "4000", #Makes the dropdown options not get overlapped (when vertically stacked due to screen size)
                    "marginRight": "5px",
                    "flex": "auto", #enable auto resizing of dropdown
                    } 
                ),

                #Fill Level filter dropdown
                html.Div([
                    dcc.Dropdown(
                        id='bin-table-fill-level-dropdown',
                        options=[
                            {'label': 'Under 60%', 'value': 'lt60'},
                            {'label': '60% to 69%', 'value': '60-69'},
                            {'label': '70% to 79%', 'value': '70-79'},
                            {'label': '80% to 89%', 'value': '80-89'},
                            {'label': '90% and above', 'value': '90plus'},
                        ],
                        placeholder="Filter by Fill Level",
                        multi=True, #Can select multiple ranges
                        clearable=True,
                        style={"width": "150px"}
                    )
                ], style={
                    "zIndex": "3000", #Makes the dropdown options not get overlapped by the address search bar
                    "marginRight": "5px", 
                    "flex": "auto"
                }),

                #Bin Type filter dropdown
                html.Div([
                    dcc.Dropdown(
                        id='bin-table-bin-type-dropdown',
                        options=[
                            {'label': 'General Waste', 'value': 'General Waste'},
                            {'label': 'Recycling', 'value': 'Recycling'},
                        ],
                        placeholder="Filter by Bin Type",
                        multi=True, #Can select multiple ranges
                        clearable=True,
                        style={"width": "150px"}
                    )
                ], style={
                    "zIndex": "2500", #Makes the dropdown options not get overlapped by the address search bar
                    "marginRight": "5px", 
                    "flex": "auto"
                }),

                #Address search input field
                html.Div([
                    dcc.Dropdown(
                        id='bin-table-address-search-dropdown',
                        className="address-search-dropdown-small",
                        options=[],  #Automatically filled based on user input via callback
                        placeholder="Search Address...",
                        searchable=True,
                        clearable=True,
                        style={"width": "200px", "marginRight": "5px"},           
                    )
                #Style the dropdown input field
                ], style={
                    "zIndex": "2000",
                    "marginRight": "5px", 
                    "flex": "auto" #enable auto resizing of input field
                    }
                )
            #Style the container of filter dropdowns
            ], style={
                "display": "flex",
                "flexWrap": "wrap", #enable wrapping on small screens so items don't overflow off the card
                "alignItems": "center",
                "marginBottom": "10px",
                "gap": "5px", #gap between each filter dropdown box (when vertically stacked in small screen)
                "fontFamily": "Arial", #dropdown font
                "fontSize": "13px",
                }
            ),
               
            
            #Create the bin table using Dash DataTable
            dash_table.DataTable(
                id="bin-data-table",
                columns=[
                    {"name": "Bin ID", "id": "bin_id"},
                    {"name": "Fill Level", "id": "fill_level_display"},
                    {"name": "Bin Type", "id": "bin_type"},
                    {"name": "Address", "id": "bin_location"},
                    {"name": "Height", "id": "bin_height"},
                    #{"name": "Status", "id": "bin_status"},
                    {"name": "Last Collection Date", "id": "last_emptied"},
                ],

                data=[], #Will be populated via callback
                sort_action="custom", #manual sorting 
                sort_mode="single", #sorts by one column at a time

                #Enable key features
                page_size=10, #Items per page
                cell_selectable=False, #DON'T allow cells to be selected/highlighted to prevent default styles from overriding


                #Style the DataTable
                style_table={
                    "overflowX": "auto",
                },
                
                #Style the cells
                style_cell={
                    "textAlign": "center",
                    "verticalAlign": "middle", 
                    "fontFamily": "Arial", 
                    "fontSize": "12px",
                    "padding": "3px"
                },
                
                #Table header columns
                style_header={
                    "fontWeight": "bold", 
                    "fontFamily": "Arial", 
                    "fontSize": "13px",
                    "textAlign": "center",
                    "backgroundColor": "#893FB5", #header purple
                    "color": "white",
                    "padding": "6px",
                },

                #Conditional styling of the cells
                style_data_conditional=[
                    #Striped rows
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': '#F1EEF7' #very light purplre
                    },

                    #Change cell bg colour based on fill level
                    {
                        'if': {
                            'filter_query': '{fill_level_numeric} >= 90', #colour bg based on hidden column
                            'column_id': 'fill_level_display' #output bg colour to this column
                        },
                        'backgroundColor': '#E62727', #Bright red
                        'color': 'black'
                    },
                    {
                        'if': {
                            'filter_query': '{fill_level_numeric} >= 80 && {fill_level_numeric} < 90',
                            'column_id': 'fill_level_display'
                        },
                        'backgroundColor': '#C2171D', #Dark red
                        'color': 'black'
                    },
                    {
                        'if': {
                            'filter_query': '{fill_level_numeric} >= 70 && {fill_level_numeric} < 80',
                            'column_id': 'fill_level_display'
                        },
                        'backgroundColor': '#E58531', #Orange
                        'color': 'black'
                    },
                                        {
                        'if': {
                            'filter_query': '{fill_level_numeric} >= 60 && {fill_level_numeric} < 70',
                            'column_id': 'fill_level_display'
                        },
                        'backgroundColor': '#F2DA5A', #Yellow
                        'color': 'black'
                    },

                    #Bold the bin_id column cells
                    {
                        'if': {'column_id': 'bin_id'},
                        'fontWeight': 'bold'
                    },
                    

                ]

            ),
            #Last updated Time message below Bin Info Table
            html.Div(
                id="bin-data-table-last-updated-msg", 
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
            "height": "100%",
            #"padding": "5px",
        }
    ),

    #Update the table every 15 minutes
    dcc.Interval(
        id='update-bin-data-table-interval',
        interval=15 * 60 * 1000,  #15 minutes in milliseconds
        n_intervals=0  #start count at 0
    )
])


###################################################################
# Callback for getting bin ID/Address search input results in the Bin Table
# Includes column sorting function, bin type filter
#update table every 15 min
###################################################################
@callback(
    Output("bin-data-table", "data"),
    Output("bin-data-table-last-updated-msg", "children"), #Last updated message under Bin table
    Input("bin-data-table", "sort_by"), #sorting columns with arrows built in by DashTable; dash passes sort_by value tellign you which column clicked
    Input("bin-table-id-dropdown", "value"), #Bin ID filter
    Input("bin-table-address-search-dropdown", "value"), #Address search filter
    Input("bin-table-fill-level-dropdown", "value"), #Fill level filter
    Input("bin-table-bin-type-dropdown", "value"), #Bin Type dropdown filter
    Input("update-bin-data-table-interval", "n_intervals"), #Update every 15 min
)
def update_bin_data_table(sort_by, selected_bin_id, address_search_value, fill_level_filter, selected_bin_type, n_intervals):
    df = get_complete_bin_table() #Fetch bin data

    #If no filters inputted, return full table records as default
    #if not selected_bin_id and not address_search_value and not fill_level_filter:
        #return df.to_dict("records") #return converted df to dictionary for DataTable formatting
    
    #If bin ID filter is selected apply the filter
    if selected_bin_id:
        #Get the entire bin_id column from df as a string where == to filter ID
        df = df[df['bin_id'].astype(str) == selected_bin_id] 

    #If address search filter is selected apply filter
    if address_search_value:
        #Get entire bin_location column from df where == to address search value
        df = df[df['bin_location'] == address_search_value]

    #If the fill level filter is selected, filter based on selected filters
    if fill_level_filter:
        #Create a dictionary to hold filter values (key) and lambda functions (value)
        filter_functions = {
            'lt60': lambda df: df['fill_level'] < 60, 
            '60-69': lambda df: (df['fill_level'] >=60) & (df['fill_level'] <= 69),
            '70-79': lambda df: (df['fill_level'] >= 70) & (df['fill_level'] <= 79),
            '80-89': lambda df: (df['fill_level'] >= 80) & (df['fill_level'] <= 89),
            '90plus': lambda df: df['fill_level'] >= 90,
        }

        #Then create a mask which applies False value to each row in bin_data 
        mask = pd.Series(False, index=df.index)
        #Then if selected filter is found in the filter_functions
        for key in fill_level_filter:
            if key in filter_functions:
                #apply 'OR' into the mask, changing the value to True |= (logical OR)
                mask |= filter_functions[key](df)
        #Keeps the rows where bins match the selected fill levels (where mask is True)
        df = df[mask]   

    #Bin Type filter
    if selected_bin_type:
        df = df[df['bin_type'].isin(selected_bin_type)]


    #Manual column sorting feature using Dash's sort_by prop
    #If sort_by variable has a value (when arrows clicked)
    if sort_by:
        col_id = sort_by[0]["column_id"] #extracts id of the column selected for sorting, giving the first item in teh list [0]
        direction = sort_by[0]["direction"] #the direction to sort in asc/desc
        ascending = direction == "asc" #convert direction into Boolean value (True/False), True=asc, False=desc

        #Sorting logic for fill level numeric column
        if col_id == 'fill_level_display':
            #Convert str column to numeric, strip the % for sorting, into a temporary column
            df['_tmp'] = df['fill_level_display'].str.rstrip("%").astype(int)
            df = df.sort_values("_tmp", ascending=ascending).drop(columns="_tmp") #Drop the temp column
            
        #Sort logic for datetime format
        elif col_id == 'last_emptied':
            #Convert to datetime format, specifying the Day comes first since order is d/m/y
            df["_tmp"] = pd.to_datetime(df["last_emptied"], dayfirst=True, errors="coerce") 
            #Sort and drop the temp column
            df = df.sort_values("_tmp", ascending=ascending).drop(columns="_tmp")
        
        #sort the rest lexicographically
        else:
            df = df.sort_values(by=col_id, ascending=ascending)

    #Return a column of fill_level keeping the int format for styling
    df['fill_level_numeric'] = df['fill_level']

    #Format Last Updated message timestamp
    #Get current date and time, convert to string displaying H:M AM/PM
    #Strip leading 0's from the hour
    #Replace any " 0" from minute value with just space in case
    last_updated = datetime.now().strftime("Last updated at %I:%M %p").lstrip("0").replace(" 0", " ")

    return df.to_dict("records"), last_updated


###################################################################
# Callback for bin ID search dropdown options to autopopulate search options when user inputs
@callback(
    Output('bin-table-id-dropdown', 'options'),
    Input('bin-table-id-dropdown', 'search_value'),
)
def bin_search_dropdown_options(search_value):
    bin_data = get_complete_bin_table()  #Get the bin list

    if not search_value:
        raise exceptions.PreventUpdate  #Don't get updates if nothing typed

    filtered_bins = bin_data[bin_data['bin_id'].astype(str).str.contains(search_value, case=False)]

    #Build dropdown options
    options = [{"label": str(bin_id), "value": str(bin_id)} for bin_id in filtered_bins['bin_id'].unique()]
    return options

###################################################################
#Callback for populating the address search dropdown when user inputs
@callback(
    Output("bin-table-address-search-dropdown", "options"),
    Input("bin-table-address-search-dropdown", "search_value")
)
def address_search_options(search_value):
    #If search field is empty or if it's just spaces then don't update dropdown options
    if not search_value or not search_value.strip():
        raise exceptions.PreventUpdate

    #Fetch bin data into a df
    df = get_complete_bin_table()

    #Filter the df to only records where search_value is found in bin_location
    #case=False (case-insensitive), na=False (ignore rows with undefined bin_location)
    filter_for_address = df[df['bin_location'].str.contains(search_value, case=False, na=False)]
    
    #Get bin_location column from filtered rows
    # .dropna() = remove blank addresses 
    # .unique() = return array of DISTINCT matches, no duplicates
    address_matches = filter_for_address['bin_location'].dropna().unique()

    #label = dropdown option value shown
    #value = data used when user selects the label
    return [{"label": addr, "value": addr} for addr in address_matches]




###################################################################
# Fill level Bar chart card
###################################################################
fill_level_bar_chart_card = html.Div([
    dbc.Card([
        dbc.CardHeader(
            dbc.Row([
                dbc.Col(html.H5("Current Fill Levels", className="card-title", style={"marginBottom": "0"}))
            ]), style={
                "backgroundColor": "#FFFFFF", #Header bg colour
                "paddingTop": "10px",
                "borderBottom": "none" #Remove the grey border under cardheader
            }
        ),
        dbc.CardBody([
            dcc.Graph(id="fill-level-bar-chart", config={"displayModeBar": False}, style={"height": "100%"})

        ])
    #Card styling
    ], style={
            "backgroundColor": "#FFFFFF",
            "borderRadius": "5px", #rounded borders if removing Card
            "boxShadow": "0 4px 12px rgba(0, 0, 0, 0.1)",
            "padding": "5px",
            "height": "100%",
            #"minHeight": "400px"
    }
    )
])


###################################################################
# Callback for bar chart data, input data from the DataTable
@callback(
    Output('fill-level-bar-chart', 'figure'),
    Input('bin-data-table', 'data') #Get data from the bin DataTable to input
)
def update_fill_level_bar_chart(data):
    #If there's no data available, show empty chart
    if not data:
        return px.bar() #empty chart
    
    #Pass the DataTable's data into a df
    df = pd.DataFrame(data)

    #Make sure the fill_level column is numeric
    df['fill_level'] = pd.to_numeric(df['fill_level'], errors="coerce")

    #Drop any undefined records with NaN (Not a Number)
    df = df.dropna(subset=['fill_level'])

    #Set the "bin" ranges (fill level) in 10% increments
    #pd.cut divides the continuous fill level column into discrete categories
    df['bin_ranges'] = pd.cut(
        df['fill_level'],
        bins=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100], #The range of bins for x axis
        labels=["0–9%", "10–19%", "20–29%", "30–39%", "40–49%", "50–59%", "60–69%", "70–79%", "80–89%", "90–100%"],
        include_lowest=True, #include 0 in the first bin (bar)
        right=True #sets intervals to be right-inclusive (10% belongs to 10-19% bin instead of 0-9%)
    )
    #Group "bin" and counts (count total bins (.value_counts) for that "bin" range)
    #.reset_index converts from a Series to a dataframe with two columns (bin label and count)
    bin_counts = df['bin_ranges'].value_counts().sort_index().reset_index()
    #Rename the columns where fill_range is for the fill level ranges (0-9%, etc)
    bin_counts.columns = ['fill_range', 'count']
    #Add a new column to use for the count text labels for each bar so that Plotly knows which text value belongs to which bar
    bin_counts['count_label'] = bin_counts['count'].astype(str)

    #Assign colours for each "bin" range (bar colours)
    bin_colours = {
        "0–9%": "#84D96D",  #light green
        "10–19%": "#84D96D", #light green
        "20–29%": "#6DB35A", #medium green
        "30–39%": "#6DB35A", #medium green
        "40–49%": "#609E4F", #medium-dark green
        "50–59%": "#568C46", #dark green
        "60–69%": "#F2DA5A", #yellow
        "70–79%": "#E58531", #orange
        "80–89%": "#C72B1E", #dark red
        "90–100%": "#E62727" #bright red
    }

    #Create bar chart
    fig = px.bar(
        bin_counts, #data source
        x="fill_range", #specify x-axis data
        y='count', #specify y-axis data
        text="count_label", #The count text label for each bar
        labels={
            "fill_range": "Fill Level Range",
            "count": "Total Bins"
        },
        #title="Current Fill Levels",
        color='fill_range', #colour the bars based on fill_range (fill level ranges)
        color_discrete_map=bin_colours #apply the custom colours from dictioanry
    )

    #Style the bars
    fig.update_traces(
        #marker_line_width=0.1, #add very thin border around bars
        #marker_line_color='white',
        #Customise the tooltip text, hide count_label text with extra/extra
        hovertemplate='Fill Range: %{x}<br>Total Bins: %{y}<extra></extra>'
    )
    #Style the count_label text
    fig.update_traces(
        textfont=dict(size=9, color="black"),
    )
    
    #Style the chart's layout
    fig.update_layout(
        bargap=0.05, #Gap between the bars
        xaxis_title="Fill Level", #x-axis label
        yaxis_title="Number of Bins", #y axis title
        legend_title_text="Fill Ranges",
        height=440, #align with height of bins summary table
        #Set padding around the chart
        margin=dict(
            t=10, #50px padding at the top 
            b=0, #bottom padding
            l=0, #left margin
            r=0 #right margin
        ),
        showlegend=False, #hide legend
        
        #Style the chart colours, font
        plot_bgcolor="#F9F7FA", #extremely light purple chart bg colour
        
    ),



    return fig



###################################################################
# Create the Recently Emptied Bins card
###################################################################
emptied_bins_card = html.Div([    
    dbc.Card([
        #Card Header
        dbc.CardHeader(
            dbc.Row([
                dbc.Col(html.H5("Recently Emptied Bins", className="card-title"))
            ]),
            style={
                "backgroundColor": "#FFFFFF",
                "paddingTop": "15px",
                "borderBottom": "none" #Remove bottom border
            }
        ),     
        dbc.CardBody([
            
            dash_table.DataTable(
                id="emptied-bins-table",
                columns=[
                    {"name": "Bin ID", "id": "bin_id"},
                    {"name": "Street", "id": "street"},
                    {"name": "Suburb", "id": "suburb"},
                    {"name": "Last Emptied", "id": "emptied_at_string"},
                ],
                data=[], #populated via callback

                page_size=10,
                cell_selectable=False, #DON'T allow cells to be selected/highlighted to prevent default styles from overriding

                style_table={
                    "overflowX": "auto"
                },

                style_cell={
                    "textAlign": "center",
                    "verticalAlign": "middle",
                    "fontFamily": "Arial",
                    "fontSize": "12px",
                    "padding": "3px",
                },
                style_header={
                    "fontWeight": "bold",
                    "fontFamily": "Arial",
                    "fontSize": "13px",
                    "textAlign": "center",
                    "backgroundColor": "#893FB5", #purple header
                    "color": "white", #white text
                    "padding": "6px",
                },

                style_data_conditional=[
                    #Alternate row bg colour
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': '#F1EEF7' #very light purple
                    },

                    #Bold hte bin ID column
                    {
                        'if': {'column_id': 'bin_id'},
                        'fontWeight': 'bold'
                    }
                ]
            ),
        ])
    ],
    style={
        "backgroundColor": "#FFFFFF",
        "boxShadow": "0 4px 12px rgba(0, 0, 0, 0.1)"
    }),

    #Auto refresh every 15 minutes
    dcc.Interval(
        id='update-emptied-bins',
        interval=900000, #15 minutes in milliseconds
        n_intervals=0
    )
])

################################################################################
# Callback for updating Recently Emptied Bins card from home page
# Update interval: 15 minutely
################################################################################
@callback(
    Output("emptied-bins-table", "data"),
    Input("update-emptied-bins", "n_intervals")
)
def update_recently_emptied_bins(n):
    df = get_recently_emptied_bins()
    return df.to_dict("records")


###################################################################
# Build the card for Mini Map
###################################################################

#Build the Mini map card
def generate_minimap_markers():
    bin_data = get_bin_data()
    #Parse timestamp column if needed for pandas
    bin_data['timestamp'] = pd.to_datetime(bin_data['timestamp'])

    #Current time for comparison
    now = datetime.now()

    #Create bin markers (icons on map)
    markers = []

    #Build a count of how many bins are at each lat/long
    from collections import defaultdict
    bin_location_counts = defaultdict(int)

    for _, row in bin_data.iterrows():
        position_key = (round(row['latitude'], 6), round(row['longitude'], 6))
        bin_location_counts[position_key] += 1

    position_offsets = defaultdict(int)  #Track how many markers placed at each location

    #Now build each bin marker
    for _, row in bin_data.iterrows():
        fill_level = row['fill_level']
        marker_colour = get_marker_colour(fill_level)
        #Find how long ago the map was last updated
        last_updated = row['timestamp']

        #Calculate time difference
        time_diff = now - last_updated
        minutes = int(time_diff.total_seconds() / 60)
        hours = int(minutes / 60)
        days = int(hours / 24)

        #Modify last updated message in either minutes, hours, days
        if minutes < 60:
            time_text = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif hours < 24:
            time_text = f"{hours} hour{'s' if hours != 1 else ''} ago"
        else:
            remaining_hours = hours % 24
            time_text = f"{days} day{'s' if days != 1 else ''}"
            if remaining_hours > 0:
                time_text += f" {remaining_hours} hour{'s' if remaining_hours != 1 else ''}"
            time_text += " ago"

        #Colour-coded icons from assets folder
        try:
            icon_url = {
                'green': '/assets/bin_icon_green.png',
                'yellow': '/assets/bin_icon_yellow.png',
                'orange': '/assets/bin_icon_orange.png',
                'red': '/assets/bin_icon_red.png',
                'bright_red': '/assets/bin_icon_bright_red.png',
                'black': '/assets/bin_icon_black.png',
            }[marker_colour]
        except KeyError:
            icon_url = '/assets/bin_icon_black.png'  #fallback if no colour coded (error)

        #Set the marker icon
        icon = dict(
            iconUrl=icon_url,
            iconSize=[30, 30],
            iconAnchor=[15, 30]
        )

        #Determine the bin marker positions on the map, slightly offsetting multiple bins at same location
        position_key = (round(row['latitude'], 6), round(row['longitude'], 6))
        offset_index = position_offsets[position_key]
        offset_step = 0.00013  #about 5 metres per marker

        # Always allow slight offset if offset_index > 0
        if offset_index == 0:
            adjusted_lat = row['latitude']
            adjusted_lon = row['longitude']
        else:
            adjusted_lat = row['latitude']
            adjusted_lon = row['longitude'] + (offset_index * offset_step)

        position_offsets[position_key] += 1

        #Add the markers to the map
        markers.append(dl.Marker(
            id=f"bin-marker-{row['bin_id']}", #Give each map marker a unique ID (because multiple bin_ids can have same exact location so only one of them will appear on map otherwise)
            position=[adjusted_lat, adjusted_lon],  # Use adjusted position
            icon=icon,
            children=[
                #Pop up message when clicking on bin icon on mini map
                dl.Popup(html.Div([
                    html.Div([
                        html.Span("Bin ID: ", style={"fontWeight": "bold", "fontSize": "0.9em"}),
                        html.Span(f"{row['bin_id']}")
                    ], style={"marginBottom": "4px"}), #space between each line

                    html.Div([
                        html.Span("Fill Level: ", style={"fontWeight": "bold", "fontSize": "0.9em"}),
                        html.Span(f"{fill_level}%")
                    ], style={"marginBottom": "4px"}),

                    html.Div([
                        html.Span("Address: ", style={"fontWeight": "bold", "fontSize": "0.9em"}),
                        html.Span(f"{row['bin_location']}", style={"fontSize": "0.9em"})
                    ], style={"marginBottom": "4px"}),

                    html.Div(
                        f"Last updated: {time_text}",
                        style={"fontSize": "0.8em", "color": "#666", "marginTop": "6px"}
                    )
                #Style the popup box    
                ], style={
                    "fontFamily": "'Segoe UI', 'Arial Unicode MS', 'Helvetica', sans-serif",
                    "fontSize": "1em",
                    "lineHeight": "1.4",
                    "padding": "2px",
                    "minWidth": "130px",    #Popup width
                    "maxWidth": "200px",    
                }))
            ],
        ))

    return markers

#Create the layout for the Mini Map
minimap_card = html.Div([  #Wrap in html.Div to group Card + update interval properly
    dbc.Card(
        dbc.CardBody([
            #Header and reset button row container
            html.Div([
                #Wrap header in .Link to make it a link to Maps page
                dcc.Link(
                    html.H6("Mini Map", className="card-title"),
                    href="/bin-map", #Redirection link
                    style={"textDecoration": "none", #Turns off the underlines with links
                           "color": "inherit"} #Inherit the parent colour so that default bootstrap theme for links colours rgba(var(--bs-link-color-rgb) in green doesn't show
                ),

                #Reset map zoom button
                dbc.Button(
                    "Reset", 
                    id="reset-minimap-button", 
                    className="custom-purple-button",
                    size="sm",
                    outline="true",
                    style={"marginLeft": "auto"}
                )
                #Align the reset button to far right from the header    
            ], style={"display": "flex", "alignItems": "center", "justifyContent": "space-between", "marginBottom": "10px"}),

            html.Div([
                #Wrap the map in this to show a spinning icon when it loads
                dcc.Loading(
                    id="minimap-loading",
                    type="circle",
                    fullscreen=False,
                    children=dl.Map(
                        [dl.TileLayer()], #Loads the base map 
                        id='minimap',
                        style={'height': '280px', "width": "100%", "position": "relative"},
                        center=[-37.7749, 144.8930], #Centres the map on Maribyrnong
                        zoom=14 #was 15
                    ),
                    style={"position": "relative"}  # stays in place over the map nicely
                ),
                
                #Container for collapsible legend toggle button
                html.Div([
                    #Container for the toggle button on its own
                    html.Div([
                        dbc.Button(
                            "-",
                            id="legend-toggle-button",
                            color="light",
                            size="sm",
                            style={
                                "marginBottom": "1px",
                                "fontSize": "1em",
                                "fontWeight": "bold",
                                "padding": "2px 6px",
                                "width": "auto",
                                "textAlign": "center",
                                "marginLeft": "auto",  #Pushes button to the right
                                "display": "block"
                            }
                        )
                    ], style={
                        "display": "flex",
                        "justifyContent": "flex-end",  #Align button to right end
                        "marginBottom": "2px"  #Space between toggle button + legend title
                    }),

                    #Create floating legend in map
                    html.Div([
                        html.Span("Bin Fill Levels", style={"fontWeight": "bold", "fontSize": "0.8em"}),
                        #Bright red bin
                        html.Div([
                            html.Img(src="/assets/bin_icon_bright_red.png", style={"height": "14px", "marginRight": "5px"}),
                            html.Span("≥ 90%", style={"fontSize": "0.8em"})
                        ], style={"display": "flex", "alignItems": "center", "marginBottom": "2px"}),

                        html.Div([
                            html.Img(src="/assets/bin_icon_red.png", style={"height": "14px", "marginRight": "5px"}),
                            html.Span("80-89%", style={"fontSize": "0.8em"})
                        ], style={"display": "flex", "alignItems": "center", "marginBottom": "2px"}),

                        html.Div([
                            html.Img(src="/assets/bin_icon_orange.png", style={"height": "14px", "marginRight": "5px"}),
                            html.Span("70-79%", style={"fontSize": "0.8em"})
                        ], style={"display": "flex", "alignItems": "center", "marginBottom": "2px"}),

                        html.Div([
                            html.Img(src="/assets/bin_icon_yellow.png", style={"height": "14px", "marginRight": "5px"}),
                            html.Span("60-69%", style={"fontSize": "0.8em"})
                        ], style={"display": "flex", "alignItems": "center", "marginBottom": "2px"}),

                        html.Div([
                            html.Img(src="/assets/bin_icon_green.png", style={"height": "14px", "marginRight": "5px"}),
                            html.Span("< 60%", style={"fontSize": "0.8em"})
                        ], style={"display": "flex", "alignItems": "center", "marginBottom": "2px"}),
                    ],
                    id="legend-content", 
                    style={"marginTop": "3px"})
                #Style for the legend box
                ], style={
                    "position": "absolute",
                    "bottom": "5px",
                    "left": "5px",
                    "backgroundColor": "rgba(255, 255, 255, 0.8)",
                    "padding": "3px",
                    "borderRadius": "5px",
                    "boxShadow": "0 2px 6px rgba(0,0,0,0.2)",
                    "fontSize": "0.85em",
                    "zIndex": "1000",
                    "fontFamily": "'Segoe UI', 'Arial Unicode MS', 'Helvetica', sans-serif",
                    "fontSize": "0.85em",
                    "color": "#333"
                })
            ], style={"position": "relative"})  #Outer container makes map + legend

        ]),
        style={
            "backgroundColor": "#FFFFFF",
            "boxShadow": "0 4px 12px rgba(0, 0, 0, 0.1)",
            #"padding": "0px",
            "display": "flex",         
        }
    ),

    #Set the interval to update mini map every 15 minutes
    dcc.Interval(
        id='update-minimap-interval',
        interval=900000,  #15 minutes in milliseconds
        n_intervals=0     #start from 0
    )
])



###################################################################
#Weekly collection stats card
weekly_collection_card = html.Div([
    dbc.Card([
        #Card header + radio button in same
        dbc.CardHeader(
            dbc.Row([
                dbc.Col(html.H5("Weekly Collection Summary", className="card-title", style={"marginBottom": "0"}), width="auto"),
                dbc.Col(
                    dcc.RadioItems(
                        id='last-week-collection-toggle',
                        options=[
                            {'label': 'Current Week', 'value': 0},
                            {'label': 'Last Week', 'value': -1}                        
                        ],
                        value=0,  #default to current week
                        labelStyle={'display': 'block'}, #display radio button vertically
                        inputStyle={'marginRight': '0.4rem'}, #Style the label input
                        style={                    
                            "fontSize": "0.85rem",
                        }
                    ),
                    width="auto", 
                    style={"marginLeft": "auto", "textAlign": "right"}
                )
                           
            ], align="center"), #Align both elements vertically center
            style={
                "backgroundColor": "#FFFFFF", #white header bg
                "paddingTop": "10px",
                "borderBottom": "none" #remove header border
                }
        ),

        dbc.CardBody([
            #html.Hr(style={"marginTop": "0.5rem", "marginBottom": "0.5rem", "borderTop": "2px solid #ccc"}),
            html.Div(id="weekly-collection-columns") #Refer to callback below
        ]), 
    ],
        #Card style
        style={
            "backgroundColor": "#FFFFFF",
            "boxShadow": "0 4px 12px rgba(0, 0, 0, 0.1)",
            "paddingBottom": "10px"
        }
    ),
    #Update the weekly collections card every 6 hours
    dcc.Interval(
        id="update-weekly-collection-card-interval",
        interval=6 * 60 * 60 * 1000,  #6 hours in milliseconds
        n_intervals=0 #Card will update on page load and refreshes
    )
])


###################################################################
# Callback for donut chart for Active alert types
###################################################################
@callback(
    Output("active-alert-type-donut-chart", "figure"),
    Input("alerts-data-store", "data"), #fetch alerts data from the dcc.Store
)
def update_active_alert_type_donut(data):
    #If there's no data to populate the donut chart
    if not data:
        return px.pie(title="No active alerts")
    
    df = pd.DataFrame(data)

    #Filter for only active alerts with no resolved time
    df_active = df[(df["status"] == "Active") & (df["resolved_time_string"] == "")]

    #Group by alert_types and get their count
    type_counts = df_active["alert_type"].value_counts().reset_index()
    type_counts.columns = ["alert_type", "count"]

    #Create the donut chart
    fig = px.pie(
        type_counts,
        values="count",
        names="alert_type",
        hole=0.7,  #Makes it a donut chart
        color="alert_type",
        color_discrete_map={
            "Battery": "#A5D477",      
            "Sensor": "#7AC5F2",       
            "Temperature": "#FFEC4D",  
            "Overfill": "#DB4B4D",
            }
    )

    #Customize appearance
    fig.update_layout(
        showlegend=True,
        height=260,
        margin=dict(t=10, b=20, l=0, r=0),
        #legend_title_text="Category",
        legend=dict(
            orientation="h", #Horizontal legend
            yanchor="bottom", #Anchor to bottom of chart
            y=-0.3, #position below the chart
            xanchor="center", #horizontally centre legend
            x=0.5 #centre positioning
        ),
    )
    return fig

#Put the donut chart into a card to give rounded borders
alerts_donut_card = html.Div([
    dbc.Card([
        dbc.CardHeader(
            dbc.Row([
                dbc.Col(html.H5("Active Alerts Categories", className="card-title"))
            ]), style={
                "backgroundColor": "#FFFFFF",
                "paddingTop": "20px",
                "borderBottom": "none"
            }        
        ),

        dbc.CardBody([
            dcc.Graph(id="active-alert-type-donut-chart", 
                      config={"displayModeBar": False},
                      style={"height": "260px"}
            )
        ])
    ], style={
        "backgroundColor": "#FFFFFF",
        "boxShadow": "0 4px 12px rgba(0, 0, 0, 0.1)",
        "borderRadius": "5px", #round the borders a bit
        "height": "100%",
        "width": "100%",
    }),
])


###################################################################
# Callback to fetch alerts data from dcc.Store to populate the total alert count cards
@callback(
        Output("active-alerts-count", "children"), #total active alerts
        Output("ignored-alerts-count", "children"), #total ignored alerts
        Output("overfill-alerts-count", "children"), #total resolved alerts

        Input("alerts-data-store", "data"), #Data in the store
)
def populate_total_alerts_cards(data):
    #If no data return 0 to each card
    if not data:
        return 0, 0, 0
    
    df = pd.DataFrame(data)

    #return the alert counts for each status
    return (
        len(df[(df['status'] == 'Active') & (df['resolved_time_string'] == '')]),
        len(df[df['status'] == 'Ignore']),
        len(df[df['alert_type'] == 'Overfill'])
    )

###################################################################
# Callback for mini card: Total new alerts + Total resolved TODAY
@callback(
        Output("todays-new-alerts", "children"),
        Output("todays-resolved-alerts", "children"),
        Input("alerts-data-store", "data"),
)
def update_todays_alerts(data):
    if not data:
        return 0, 0
    
    df = pd.DataFrame(data)

    #Get today's date without the time
    today = datetime.today().date()

    #Convert to datetime objects
    df['triggered_time'] = pd.to_datetime(df['triggered_time'], errors='coerce')
    df['resolved_time'] = pd.to_datetime(df['resolved_time'], errors='coerce')

    #Filter for alerts triggered today
    todays_alerts = df[df['triggered_time'].dt.date == today]

    #Filter for alerts resolved today
    todays_resolved = df[df['resolved_time'].dt.date == today]

    #Return the count in each
    return len(todays_alerts), len(todays_resolved)


###################################################################
# Callback to update mini map on page load AND every 15 minutes
###################################################################
@callback(
    Output('minimap', 'children'),
    [Input('minimap', 'id'),
     Input('update-minimap-interval', 'n_intervals')]
)
def update_minimap(_, __):
    markers = generate_minimap_markers()

    return [
        dl.TileLayer(),
        dl.LayerGroup(markers),
    ]
###################################################################
# Callback for reset button mini map
@callback(
    Output('minimap', 'center'),
    Output('minimap', 'zoom'),
    Input('reset-minimap-button', 'n_clicks'),
    prevent_initial_call=True
)
def reset_map_view(n_clicks):
    #Default center and zoom after reset
    return [-37.7749, 144.8930], 14 #originally 15 zoom

###################################################################
# Callback for collapse/expand button for legend
@callback(
    Output('legend-content', 'style'),
    Output('legend-toggle-button', 'children'),
    Input('legend-toggle-button', 'n_clicks'),
    prevent_initial_call=True
)
def toggle_legend(n_clicks):
    if n_clicks % 2 == 1:
        #If odd clicks: hide content
        return {"display": "none"}, "+"
    else:
        #If even clicks: show content
        return {"marginTop": "3px"}, "-"



###################################################################
#Callback for Weekly Collection Stats card
@callback(
    Output("weekly-collection-columns", "children"),
    Input("update-weekly-collection-card-interval", "n_intervals"), #Updates the card 6 hourly
    Input("last-week-collection-toggle", "value") #Either 0(current weel) or -1(last week) radio button
)
def update_weekly_collection_card(_, week):
    df, week_start, week_end = get_weekly_collection_stats(week)

    #Display the date range for that week
    weekly_date_range = html.Div(
        f"{week_start.strftime('%d %b %Y')} – {week_end.strftime('%d %b %Y')}",
        style={"fontSize": "0.85rem", "color": "#666", "marginBottom": "20px"}   
    )

    #Header rows
    header_row = dbc.Row([
        dbc.Col(html.Div("", style={"fontWeight": "bold", "fontSize": "0.9rem"})),
        dbc.Col(html.Div("Total Collections", style={"fontWeight": "bold", "fontSize": "0.9rem"})),
        dbc.Col(html.Div("Avg Fill % on Pickup", style={"fontWeight": "bold", "fontSize": "0.9rem"})),
        dbc.Col(html.Div("Total Bins ≥ 90%", style={"fontWeight": "bold", "fontSize": "0.9rem"})),
    ], style={"marginBottom": "10px"})

    #Create a row for each day of the week
    data_rows = []
    for _, row in df.iterrows():
        data_rows.append(
            dbc.Row([
                dbc.Col(html.Div(row['weekday'], style={"fontWeight": "bold", "fontSize": "0.9rem"})),
                dbc.Col(html.Div(str(row['total_bins_emptied']), style={"fontSize": "0.85rem", "textAlign": "center"})),
                dbc.Col(html.Div(f"{row['avg_fill_before_empty']}%", style={"fontSize": "0.85rem", "textAlign": "center"})),
                dbc.Col(html.Div(str(row['bins_above_90']), style={"fontSize": "0.85rem", "textAlign": "center"})),
            ], style={
                "marginBottom": "4px",
                "borderBottom": "2px solid #F1EEF7",
                "paddingBottom": "11px"})
        )

    # Combine and return header + data rows
    return [weekly_date_range, header_row] + data_rows









########################################################################
# Define page layout
########################################################################
layout = html.Div([
    
    dbc.Container([
        dbc.Row([
            #Page Header
            dbc.Col(
                html.H4("Overview", className="mb-4"),
                width=12
            )
        ]),

        #Top Row: for TOTAL alerts in each table cards + Daily summary
        dbc.Row([
            dbc.Col(total_active, xs=6, md=3),
            dbc.Col(total_ignored, xs=6, md=3),
            dbc.Col(total_overfill_risk, xs=6, md=3),
            dbc.Col(todays_alerts_card, xs=8, md=3),                       
        ], style={"marginBottom": "30px"}
        ),

        #Middle Row: Donut chart, Fill Stats, Mini Map
        dbc.Row([
            dbc.Col(alerts_donut_card, xs=6, md=3),
            dbc.Col(fill_level_card, xs=6, md=3), #sets width for xs for extra-small screen, md for medium screen using responsive classes
            dbc.Col(minimap_card, xs=12, md=6), 
        ], style={"marginBottom": "30px"} 
        ),
        

        #Row for the Bin Data Table
        dbc.Row([
            dbc.Col(bin_data_table_card, xs=12, md=8),
            dbc.Col(fill_level_bar_chart_card, xs=12, md=4),
        ], style={"marginBottom": "20px"}
        ),

        #Recently Empited Bins card
        dbc.Row([
                dbc.Col(weekly_collection_card, xs=12, md=6),  
                dbc.Col(emptied_bins_card, xs=12, md=6), 
        ],
        ),

    ], fluid=True)

])