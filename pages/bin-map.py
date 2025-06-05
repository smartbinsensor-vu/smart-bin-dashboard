from dash import Dash, html, register_page, dcc, callback, Input, Output, exceptions, no_update, State, callback_context
import dash_leaflet as dl
import dash_bootstrap_components as dbc
import pandas as pd
import math
from collections import defaultdict
from data_utils import get_bin_data, get_marker_colour, get_bin_type_and_last_emptied


#Register this file as a Dash page
register_page(__name__, path="/bin-map", name="Map")

###################################################################
# Create the card for the large map and filters buttons
###################################################################

large_map_card = html.Div([
        #html.H4("Map of Bin Locations", className="mb-4"),
        dbc.Card(
            dbc.CardBody([
                html.Div([
                    #Bin id Search dropdown bar
                    html.Div([
                        dcc.Dropdown(
                            id='bin-search-dropdown',
                            options=[], #Dropdown options will be added using callback based on user input
                            placeholder="Search by Bin ID...",
                            searchable=True, #Enable typing and searching
                            style={"width": "200px", "marginRight": "10px",},
                            clearable=True, #Shows a small "x" to reset
                        ),            
                    ], style={
                        "zIndex": "4000", #Makes the dropdown options not get overlapped by the bin map nor fill level filter (when vertically stacked due to screen size)
                        "marginRight": "5px",
                        "flex": "auto", #enable auto resizing of dropdown
                        } 
                    ),

                    #Dropdown for fill level filter
                    html.Div([
                        dcc.Dropdown(
                            id='fill-level-filter',
                            options=[
                                {'label': 'Under 60%', 'value': 'lt60'},
                                {'label': '60% to 69%', 'value': '60-69'},
                                {'label': '70 to 79%', 'value': '70-79'},
                                {'label': '80 to 89%', 'value': '80-89'},
                                {'label': '90% and above', 'value': '90plus'},
                            ],
                            placeholder="Filter by fill level...", #Default dropdown text
                            multi=True, #Can select multiple ranges
                            clearable=True,
                            style={"width": "200px"}
                        ),                   
                    ], style={
                        "zIndex": "3000", #Makes the dropdown options not get overlapped by the bin map
                        "marginRight": "5px",
                        "flex": "auto" #enable auto resizing of dropdown
                        }
                    ),

                    #Address search input field
                    html.Div([
                        dcc.Dropdown(
                            id='address-search-dropdown',
                            className="address-search-dropdown-small",
                            options=[],  #Automatically filled based on user input via callback
                            placeholder="Search by street name...",
                            searchable=True,
                            clearable=True,
                            style={"width": "300px", "marginRight": "5px"},           
                        )
                    #Style the dropdown input field
                    ], style={
                        "zIndex": "2000",
                        "marginRight": "5px", 
                        "flex": "auto" #enable auto resizing of input field
                        }
                    ),


                    #Reset map button
                    dbc.Button(
                        "Reset", 
                        id="reset-large-map-button", 
                        className="custom-purple-button",
                        size="sm", 
                        outline=True,
                        style={"marginLeft": "auto"} #push button to the right
                    )
                ], style={
                    "display": "flex", 
                    "flexWrap": "wrap", #enable wrapping on small screens so items don't overflow off the card
                    "gap": "5px", #Spacing between filters and reset button
                    "alignItems": "center",
                    "fontFamily": "Arial",
                    "fontSize": "13px",  
                    "marginBottom": "10px"
                    }
                ),

                html.Div([
                    dcc.Loading(
                        id="large-map-loading",
                        type="circle",
                        children=dl.Map(
                            [
                                dl.LayersControl([
                                    dl.BaseLayer(dl.TileLayer(), name="Street View", checked=True), #Default Map view
                                    dl.BaseLayer(dl.TileLayer( #Satellite layer
                                        url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                                        attribution="Esri Satellite"
                                    ), name="Satellite View")
                                ])
                            ],
                            id="large-bin-map",
                            center=[-37.7749, 144.8930],
                            zoom=15,
                            style={"height": "700px", "width": "100%", "position": "relative"}
                        )
                    ),

                    #Add collapsible legend
                    html.Div([
                        # Toggle button
                        html.Div([
                            dbc.Button(
                                "-",
                                id="legend-toggle-button-large-map",
                                color="light",
                                size="sm",
                                style={
                                    "marginBottom": "1px",
                                    "fontSize": "1em",
                                    "fontWeight": "bold",
                                    "padding": "2px 6px",
                                    "width": "auto",
                                    "textAlign": "center",
                                    "marginLeft": "auto",
                                    "display": "block"
                                }
                            )
                        ], style={
                            "display": "flex",
                            "justifyContent": "flex-end",
                            "marginBottom": "2px"
                        }),

                        #Actual Legend Content
                        html.Div([
                            html.Span("Bin Fill Levels", style={"fontWeight": "bold", "fontSize": "0.8em"}),

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
                        id="legend-content-large-map",  #Give ID to toggle show/hide
                        style={"marginTop": "3px"})
                    ], style={ #Legend style
                        "position": "absolute",
                        "bottom": "5px",
                        "left": "5px",
                        "backgroundColor": "rgba(255, 255, 255, 0.8)",
                        "padding": "5px",
                        "borderRadius": "5px",
                        "boxShadow": "0 2px 6px rgba(0,0,0,0.2)",
                        "fontSize": "0.85em",
                        "zIndex": "1000",
                        "fontFamily": "'Segoe UI', 'Arial Unicode MS', 'Helvetica', sans-serif",
                        "color": "#333"
                    }),
                #Sets 15 minutely updates to map    
                dcc.Interval(
                    id='update-large-map-interval',
                    interval=900000,  
                    n_intervals=0   
                )
                
                ], style={"position": "relative"}),  #Outer container for map + legend
            
            ]),
            #Map card style
            style={
                "backgroundColor": "#FFFFFF",
                "boxShadow": "0 4px 12px rgba(0, 0, 0, 0.1)",
                "padding": "5px",
                "margin": "5px"
            }
        ),
])

###################################################################
# Build the Map markers, filters by bin if users inputs in search for callback later
# Builds only marker for filtered bin (if selected) by passing it to the function else builds all
def build_map_markers_using_bin_data(bin_data):
    #Get current time to for the "last updated" message
    now = pd.Timestamp.now()
    markers = []
    #Count how many bins at each address, for duplicates
    position_counts = defaultdict(int)
    #Offset duplicate bin position so that their markers don't completely overlap on the map
    position_offsets = defaultdict(int)

    for _, row in bin_data.iterrows():
        position_key = (round(row['latitude'], 6), round(row['longitude'], 6))
        position_counts[position_key] += 1

    for _, row in bin_data.iterrows():
        fill_level = row['fill_level']
        marker_colour = get_marker_colour(fill_level)
        last_updated = row['timestamp']

        # Calculate last updated message
        time_diff = now - last_updated
        minutes = int(time_diff.total_seconds() / 60)
        hours = int(minutes / 60)
        days = int(hours / 24)

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

        #Marker Icon creation for the map
        try:
            icon_url = {
                'green': '/assets/bin_icon_green.png',
                'yellow': '/assets/bin_icon_yellow.png',
                'orange': '/assets/bin_icon_orange.png',
                'red': '/assets/bin_icon_red.png',
                'bright_red': '/assets/bin_icon_bright_red.png',
                'black': '/assets/bin_icon_black.png',
            }[marker_colour]
        #If there's an error then use the black bin icon by default
        except KeyError:
            icon_url = '/assets/bin_icon_black.png'

        icon = dict(
            iconUrl=icon_url,
            iconSize=[30, 30],
            iconAnchor=[15, 30]
        )

        #Handle markers in duplicate lat/lon, offsetting position slightly for visibility
        position_key = (round(row['latitude'], 6), round(row['longitude'], 6))
        offset_index = position_offsets[position_key]
        offset_step = 0.00013

        if offset_index == 0:
            adjusted_lat = row['latitude']
            adjusted_lon = row['longitude']
        else:
            adjusted_lat = row['latitude']
            adjusted_lon = row['longitude'] + (offset_index * offset_step)

        position_offsets[position_key] += 1

        #Build markers
        markers.append(dl.Marker(
            id=f"bin-marker-{row['bin_id']}",
            position=[adjusted_lat, adjusted_lon],
            icon=icon,
            children=[
                dl.Popup(html.Div([
                    html.Div([
                        html.Span("Bin ID: ", style={"fontWeight": "bold", "fontSize": "0.9em"}),
                        html.Span(f"{row['bin_id']}")
                    ], style={"marginBottom": "4px"}),

                    html.Div([
                        html.Span("Fill Level: ", style={"fontWeight": "bold", "fontSize": "0.9em"}),
                        html.Span(f"{fill_level}%")
                    ], style={"marginBottom": "4px"}),

                    html.Div([
                        html.Span("Bin Type: ", style={"fontWeight": "bold", "fontSize": "0.9em"}),
                        html.Span(f"{row['bin_type']}")
                    ], style={"marginBottom": "4px"}),

                    html.Div([
                        html.Span("Last Emptied on: ", style={"fontWeight": "bold", "fontSize": "0.9em"}),
                        html.Span(f"{row['last_emptied_string']}")
                    ], style={"marginBottom": "4px"}),

                    html.Div([
                        html.Span("Address: ", style={"fontWeight": "bold", "fontSize": "0.9em"}),
                        html.Span(f"{row['bin_location']}", style={"fontSize": "0.9em"})
                    ], style={"marginBottom": "4px"}),

                    html.Div(
                        f"Last updated: {time_text}",
                        style={"fontSize": "0.8em", "color": "#666", "marginTop": "6px"}
                    )
                ], style={
                    "fontFamily": "'Segoe UI', 'Arial Unicode MS', 'Helvetica', sans-serif",
                    "fontSize": "1em",
                    "lineHeight": "1.4",
                    "padding": "2px",
                    "minWidth": "180px",
                    "maxWidth": "220px"
                }))
            ],
        ))

    return markers    




###################################################################
#Filtered bins table card
filtered_bins_table_card = html.Div([
    dbc.Card([
        dbc.CardHeader("Filtered Bins", style={"backgroundColor": "#FFFFFF"}, className="card-title"),
        dbc.CardBody([
            html.Div(id="filtered-bin-list-wrapper"),
            #Track what page the card is showing (after clicking Next button)
            dcc.Store(id="filtered-bins-card-page", data=0)
            
        ])
    ], className="m-2",
        style={
            "backgroundColor": "#FFFFFF",
            "boxShadow": "0 4px 12px rgba(0, 0, 0, 0.1)",
            "padding": "10px"
        }
    )
])



###################################################################
###################################################################
# Callbacks for updating map markers every 15 minutes + filters and
# Reset button control for resetting map view and zoom
@callback(
    Output('large-bin-map', 'children'), #Updates the map markers
    Output('large-bin-map', 'center'), #Centres the map on filted bin
    Output('large-bin-map', 'zoom'), #Zooms map onto the filtered bin
    Output('bin-search-dropdown', 'value'), #Resets the dropdown input if reset button clicked
    Output('fill-level-filter', 'value'), #Reset button will clear filter levels too
    Output('address-search-dropdown', 'value'), #Reset button will clear address search inputs
    [
        Input('large-bin-map', 'id'),   #Updates on Initial page load
        Input('update-large-map-interval', 'n_intervals'), #Auto update every 15 minutes
        Input('bin-search-dropdown', 'value'), #Update map based on search dropdown value (filtered bin ID)
        Input('reset-large-map-button', 'n_clicks'), #Reset map view button 
        Input('fill-level-filter', 'value'), #Fill level filter dropdown
        Input('address-search-dropdown', 'value'), #Address search dropdown
    ]
)
def update_large_map(_, __, selected_bin_id, reset_button_clicked, fill_level_filter, address_search_value):
    bin_data = get_bin_data() #Fetch bin data
    bin_type_emptied_date = get_bin_type_and_last_emptied() #Function with bin types + last emptied date
    bin_data = bin_data.merge(bin_type_emptied_date, on="bin_id", how="left") #Merge the two tables based on bin IDs

    #By default don't clear the bin ID filter dropdown user input unless reset button clicked
    clear_dropdown_input = no_update
    #By default don't clear the fill level filter inputs unless reset button clicked
    clear_fill_level_filter = no_update
    #By default don't clear the address filter inputs unless reset button clicked
    clear_address_search_dropdown = no_update

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
        mask = pd.Series(False, index=bin_data.index)
        #Then if selected filter is found in the filter_functions
        for key in fill_level_filter:
            if key in filter_functions:
                #apply 'OR' into the mask, changing the value to True |= (logical OR)
                mask |= filter_functions[key](bin_data)
        #Keeps the rows where bins match the selected fill levels (where mask is True)
        bin_data = bin_data[mask]        

    #Address search value is inputted, get data with matching bin location
    if address_search_value:
        bin_data = bin_data[bin_data['bin_location'] == address_search_value]

    #Check if reset button was clicked using callback_context
    ctx = callback_context
    reset_button_clicked = ctx.triggered and ctx.triggered[0]['prop_id'].startswith('reset-large-map-button')

    #If reset button is clicked
    if reset_button_clicked:
        center = [-37.7748, 144.8930]
        zoom = 15
        clear_dropdown_input = "" #Clears any user input in the bin ID filter dropdown bar with empty string
        clear_fill_level_filter = [] #Clears fill level filter with empty list
        clear_address_search_dropdown = "" #Clears any user input in address search field

    #Else if user input in bin ID filter exists
    elif selected_bin_id:
        #If a bin is chosen in the Bin ID search dropdown, filter map to that bin only
        bin_data = bin_data[bin_data['bin_id'].astype(str) == selected_bin_id]

        #And if the bin_data isn't empty
        if not bin_data.empty: #If a bin is searched for and its data isn't empty
            lat = bin_data.iloc[0]['latitude'] 
            lon = bin_data.iloc[0]['longitude']
            center = [lat, lon] #Centre the map onto the filtered bin's coords
            zoom = 16 #Zooms the map onto the filtered bin
        else:
            #Return default view otherwise
            center = [-37.7749, 144.8930] #Maribyrnong
            zoom = 15

    else:
        #If no bin is filtered for and no reset button click then default the map view
        center = [-37.7749, 144.8930] #Maribyrnong
        zoom = 15


    #returns only the markers that have been filtered
    markers = build_map_markers_using_bin_data(bin_data)

    return [
        dl.LayersControl([
            dl.BaseLayer(dl.TileLayer(), name="Street View", checked=True),
            dl.BaseLayer(dl.TileLayer(
                url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                attribution="Esri Satellite"
            ), name="Satellite View")
        ]),
        dl.LayerGroup(markers)
    ], center, zoom, clear_dropdown_input, clear_fill_level_filter, clear_address_search_dropdown


###################################################################
# Callback for collapsible legend box
@callback(
    Output('legend-content-large-map', 'style'),
    Output('legend-toggle-button-large-map', 'children'),
    Input('legend-toggle-button-large-map', 'n_clicks'),
    prevent_initial_call=True,

)
def toggle_legend(n_clicks):
    if n_clicks % 2 == 1:
        return {"display": "none"}, "+"
    else:
        return {"marginTop": "3px"}, "-"
    

###################################################################
# Callback for bin ID search dropdown options to autopopulate search options when user inputs
@callback(
    Output('bin-search-dropdown', 'options'),
    Input('bin-search-dropdown', 'search_value'),
)
def bin_search_dropdown_options(search_value):
    bin_data = get_bin_data()  #Get the bin list

    if not search_value:
        raise exceptions.PreventUpdate  #Don't get updates if nothing typed

    filtered_bins = bin_data[bin_data['bin_id'].astype(str).str.contains(search_value, case=False)]

    #Build dropdown options
    options = [{"label": str(bin_id), "value": str(bin_id)} for bin_id in filtered_bins['bin_id'].unique()]
    return options

###################################################################
#Callback for populating the address search dropdown when user inputs
@callback(
    Output("address-search-dropdown", "options"),
    Input("address-search-dropdown", "search_value")
)
def address_search_options(search_value):
    #If search field is empty or if it's just spaces then don't update dropdown options
    if not search_value or not search_value.strip():
        raise exceptions.PreventUpdate

    #Fetch bin data into a df
    df = get_bin_data()

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
# Callback for updating the NEXT/PREVIOUS page number of Filtered Bin Table card
@callback(
    Output('filtered-bins-card-page', 'data'),
    Input('next-filtered-bins-button', 'n_clicks'),
    Input('prev-filtered-bins-button', 'n_clicks'),
    State('filtered-bins-card-page', 'data'),
    prevent_initial_call=True
)
def update_filtered_page_num(next_clicks, prev_clicks, current_page):
    triggered_id = callback_context.triggered_id
    #Fallback in case current_page is undefined or None on page load
    current_page = current_page or 0 

    #If the Next page button was clicked
    if triggered_id == 'next-filtered-bins-button':
        return current_page + 1 #increment page by 1
    #If Previous page button was clicked
    elif triggered_id == 'prev-filtered-bins-button':
        return max(current_page - 1, 0) #decrement page by 1, and don't go below 0
    else:
        return current_page

#Callback to disable the Previous button on filtered bins card if on Page 0
@callback(
    Output('prev-filtered-bins-button', 'disabled'),
    Input('filtered-bins-card-page', 'data') #Listens to dcc.Store of input id
)
def disable_prev_button(page):
    return page == 0

###################################################################
#Callback for filtered bin table card to list filtered bins
@callback(
        Output("filtered-bin-list-wrapper", "children"),
        [ #Listens to same Inputs as the map filters
            Input('update-large-map-interval', 'n_intervals'), #Auto update every 15 minutes
            Input('bin-search-dropdown', 'value'), #Update map based on search dropdown value (filtered bin ID)
            Input('fill-level-filter', 'value'), #Fill level filter dropdown
            Input('reset-large-map-button', 'n_clicks'), #Reset map view button 
            Input('filtered-bins-card-page', 'data'), #Listen to the page on filtered bins list card
            Input('address-search-dropdown', 'value'), #Address search dropdown
        ]
)
def update_filtered_bin_card(_, selected_bin_id, fill_level_filter, reset_clicks, page, address_search_value):
    
    #Check if reset button was clicked using callback_context
    ctx = callback_context
    reset_button_clicked = ctx.triggered and ctx.triggered[0]['prop_id'].startswith("reset-large-map-button")

    #If reset button clicked, empty the card
    if reset_button_clicked:
        return html.Div("No bins filtered.", style={"fontSize": "0.9rem", "color": "#888"})  

    df = get_bin_data()
    df = df.merge(get_bin_type_and_last_emptied(), on="bin_id", how="left")

    #If no filters selected, display message
    if not fill_level_filter and not selected_bin_id and not address_search_value:
        return html.Div("No bins filtered.", style={"fontSize": "0.9rem", "color": "#888"})

    #If filters are applied to the map
    if fill_level_filter:
        filters = {
            'lt60': lambda df: df['fill_level'] < 60, 
            '60-69': lambda df: df['fill_level'].between(60, 69),
            '70-79': lambda df: df['fill_level'].between(70, 79),
            '80-89': lambda df: df['fill_level'].between(80, 89),
            '90plus': lambda df: df['fill_level'] >= 90
        }
        #Then create a mask (boolean Series) which applies False value to each row in bin_data
        mask = pd.Series(False, index=df.index)
        for key in fill_level_filter:
            #return a list of True or False depending on each rows fill level for each filter
            if key in filters:
                #apply 'OR' into the mask, changing the value to True |= (logical OR)
                mask |= filters[key](df)
        #Keeps the rows where bins match the selected fill levels (where mask is True)
        df = df[mask]

    #If Bin ID filter is selected, filter the DF to it
    if selected_bin_id:
        #Make it into a string for comparison
        df = df[df['bin_id'].astype(str) == selected_bin_id]

    #Sort by fill level descending
    df = df.sort_values(by='fill_level', ascending=False)

    #Address search value is inputted, get data with matching bin location
    if address_search_value:
        df = df[df['bin_location'] == address_search_value] 
   
    #Show message if there are no bins matching filters
    if df.empty:
        return html.Div("No bins match your filters.", style={"fontSize": "0.9rem", "color": "#888"})

    #Show sum of total bins filtered if filters applied
    total_bins_filtered_text = html.Div(
        f"{len(df)} bin{'s' if len(df) != 1 else ''} match your filters.",
        style={"fontSize": "0.75rem", "color": "#666", "marginBottom": "8px"}
    )

    #Limit the result on each page to 5
    each_page = 5
    #In case page = None or undefined on first load, default to True or 0
    page = page or 0
    #Find the total number of pages (results) to display Page X of Total text
    total_pages = math.ceil(len(df) / each_page)

    start = page * each_page #Starting row index (from 0) using the dcc.Store(filtered-bins-card-page, data=0)
                            #If page = 0 then *10 = 0 meaning show results for the first 10 (index 0-9)
    end = start + each_page #Calculate the ending row index for the current page, i.e. if start = 0 then +10=10 (fetches row 0-9)
    #Use Pandas method to get only rows between start and end from df
    paginated_df = df.iloc[start:end]

    #Build an ordered list of filtered bins for the card
    filtered_bins = []
    for _, row in paginated_df.iterrows():
        filtered_bins.append(html.Li([
            html.Div(f"Bin ID: #{row['bin_id']}", style={"fontWeight": "bold", "fontSize": "13px", "backgroundColor": "#F1EEF7"}), #Very light purple bg
            html.Div(f"Fill Level: {row['fill_level']}%", style={"fontWeight": "bold"}),
            html.Div(f"Address: {row['bin_location']}"),
            #Border beneath each row
            html.Hr(style={"margin": "6px 0", "borderTop": "3px solid #eee"})
        ], style={"marginBottom": "5px"}))
    
    #Display the ordered list of filtered bins
    filtered_bins_list = html.Ol(filtered_bins, start=str(start + 1), #start=start+1 so ordered list num continues on next page instead of resetting to 1
        style={
            "paddingLeft": "1.2rem", 
            "fontSize": "0.8rem",
            #"backgroundColor": "#f5f8ff"
        }
    )

    #Text to show Page X of Total
    page_x_of = html.Div(
        f"Page {page + 1} of {total_pages}",
        style={"fontSize": "0.75rem", "color": "#666", "marginTop": "10px", "textAlign": "right"}
    )

    #Create the NEXT and PREVIOUS buttons
    buttons = html.Div([
        dbc.Button("Previous", id="prev-filtered-bins-button", size="sm", className="custom-purple-button", outline=True, disabled=(page ==0), style={"marginRight": "2px"}),
        dbc.Button("Next", id="next-filtered-bins-button", size="sm", className="custom-purple-button", outline=True, disabled=(page + 1 >= total_pages)),
        #Style the buttons, spacing at far opposite ends    
    ], style={"display": "flex", "justifyContent": "space-between", "marginTop": "10px"}
    )

    return html.Div([total_bins_filtered_text, filtered_bins_list, page_x_of, buttons])








###################################################################
# Layout
###################################################################
layout = html.Div([
    dbc.Container([
        dbc.Row([
            #Page Header
            dbc.Col(
                html.H4("Map of Bin Locations", className="mb-4"),
                width=12
            )
        ]),
        #Top row with map + filtered bins card
        dbc.Row([
            dbc.Col(large_map_card, xs=12, md=9),
            dbc.Col(filtered_bins_table_card, xs=12, md=3),
        ]),
        #Row for Top 5 fullest bins card + weekly collection summary card

    ])
])

