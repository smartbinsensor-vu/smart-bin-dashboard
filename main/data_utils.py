import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime, timedelta

#MySQL credentials
username = 'admin'
password = '2025BinSensors'
host = 'smart-bin-sensors.cf2w6okcuabo.ap-southeast-2.rds.amazonaws.com'
port = '3306'
database = 'smart-bin-sensors'

#Create connection to the MySQL engine
engine = create_engine(
    f'mysql+pymysql://{username}:{password}@{host}:{port}/{database}',
    pool_recycle=3600,  #recycle connection every hour
    pool_pre_ping=True  #auto-check if connection is still alive
)

########################################################
# Get current fill level stats for home page widget
########################################################
def get_fill_level_stats():
    query = """
        WITH ranked_fill AS (
            SELECT 
                *,
                ROW_NUMBER() OVER (PARTITION BY bin_id ORDER BY timestamp DESC) AS rn
            FROM sensor_table
        )
        SELECT
            fill_category.fill_category,
            COUNT(ranked_fill.bin_id) AS count
        FROM (
            SELECT 'Getting Full' AS fill_category, 60 AS min_val, 69 AS max_val
            UNION ALL
            SELECT 'Moderately Full', 70, 79
            UNION ALL
            SELECT 'Almost Full', 80, 89
            UNION ALL
            SELECT 'Overfill Risk', 90, 100
        ) AS fill_category
        LEFT JOIN ranked_fill
        ON ranked_fill.fill_level BETWEEN fill_category.min_val AND fill_category.max_val
        WHERE rn = 1  -- Pick only the latest record per bin
        GROUP BY fill_category.fill_category
        ORDER BY fill_category.min_val
    """
    #Run the sql query using the engine connection and store it into a DataFrame
    df = pd.read_sql(query, engine)
    return df

#############################################################
# Get bins recently emptied for home page widget
#############################################################
def get_recently_emptied_bins():
    query = """
    WITH fill_changes AS (
        SELECT
            bin_id,
            timestamp,
            fill_level,
            LAG(fill_level) OVER (PARTITION BY bin_id ORDER BY timestamp) AS prev_fill_level
        FROM sensor_table
    ),
    
    empties AS (
        SELECT
            bin_id,
            Timestamp AS emptied_at
        FROM fill_changes
        WHERE
            fill_level <= 10 AND
            (prev_fill_level IS NULL OR prev_fill_level > 10)
    )
    
    SELECT DISTINCT
        e.bin_id,
        b.bin_location,
        e.emptied_at
    FROM empties e
    JOIN bin_table b ON b.bin_id = e.bin_id
    ORDER BY e.emptied_at DESC
    LIMIT 12;
    """
    df = pd.read_sql(query, engine)

    #Make emptied_at into a datetime object for Pandas
    if 'emptied_at' in df.columns:
        df['emptied_at'] = pd.to_datetime(df['emptied_at'], dayfirst=True)
        #Convert to a string for display in the card
        df['emptied_at_string'] = df['emptied_at'].dt.strftime('%d/%m %H:%M')


    #Split bin_location into street and suburb for display
    if 'bin_location' in df.columns and not df.empty:
        df[['street', 'suburb']] = df['bin_location'].str.extract(r'^(.*?),\s*(.*)$')
        #Remove the state, keep postcode in address
        df['suburb'] = df['suburb'].str.replace(r',\s+[A-Za-z]{2,3}\s+', ', ', regex=True)
    
    
    else:
        # Add empty columns to ensure headers still show up
        df = pd.DataFrame(columns=['bin_id', 'bin_location', 'emptied_at', 'street', 'suburb'])

    return df   


#############################################################
# Mini Map card
#############################################################

#Create the function to fetch bin locations and fill levels from database
def get_bin_data():
    query = """
    WITH ranked_sensor_data AS (
    SELECT 
        r.bin_id,
        b.bin_location,
        r.fill_level,
        b.bin_latitude AS latitude,
        b.bin_longitude AS longitude,
        r.timestamp,
        ROW_NUMBER() OVER (PARTITION BY r.bin_id ORDER BY r.timestamp DESC) AS rn
    FROM sensor_table r
    INNER JOIN bin_table b ON r.bin_id = b.bin_id
    )
    SELECT
        bin_id,
        bin_location,
        fill_level,
        latitude,
        longitude,
        timestamp
    FROM ranked_sensor_data
    WHERE rn = 1
    """
    df = pd.read_sql(query, engine)
    return df

#Function for colour-coded icons based on fill level
def get_marker_colour(fill_level):
    if fill_level is None or pd.isna(fill_level):
        return 'black'  # Treat missing fill level as black icon
    try:
        fill_level = float(fill_level)
    except (ValueError, TypeError):
        return 'black'

    if fill_level < 60: # 0-59%
        return 'green'
    elif fill_level < 70: # 60-69%
        return 'yellow'
    elif fill_level < 80: # 70-79%
        return 'orange'
    elif fill_level < 90: # 80-89%
        return 'red'
    else:
        return 'bright_red' # 90+%
    

#############################################################
# Large Map card
#############################################################
#Function to fetch last bin emptied date + bin type
def get_bin_type_and_last_emptied():
    query = """
    WITH fill_changes AS (
        SELECT
            bin_id,
            timestamp,
            fill_level,
            LAG(fill_level) OVER (PARTITION BY bin_id ORDER BY timestamp) AS prev_fill_level
        FROM sensor_table
    ),
    
    empties AS (
        SELECT
            bin_id,
            MAX(timestamp) AS last_emptied
        FROM fill_changes
        WHERE
            fill_level <= 10 AND
            (prev_fill_level IS NULL OR prev_fill_level > 10)
        GROUP BY bin_id
    ),
    
    bin_table_ranked AS (
        SELECT
            b.bin_id,
            b.bin_type,
            ROW_NUMBER() OVER (PARTITION BY b.bin_id ORDER BY b.bin_id) AS row_num
        FROM bin_table b
    )

    SELECT 
        btr.bin_id,
        btr.bin_type,
        e.last_emptied
    FROM bin_table_ranked btr
    LEFT JOIN empties e ON btr.bin_id = e.bin_id
    WHERE btr.row_num = 1
    """
    df = pd.read_sql(query, engine)

    # Format the emptied date
    df['last_emptied'] = pd.to_datetime(df['last_emptied'], errors='coerce')
    df['last_emptied_string'] = df['last_emptied'].dt.strftime('%d/%m %H:%M').fillna("N/A")

    return df

#############################################################
#Function for Top 5 fullest bins card
def get_top_fullest_bins(n=5): #get 5 results by default
    df = get_bin_data()
    #Sort the DF by fill level desc
    df = df.sort_values(by='fill_level', ascending=False)
    #Select following columns from DF for display, and return first 'n' rows (top 5 default)
    df = df[['bin_id', 'fill_level', 'bin_location', 'timestamp']].head(n)
    #Convert timestamp column (in case its strings) to datetime objects
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    #Create new DF last_updated by using timestamp, format the datetime into d/m H:M
    df['last_updated'] = df['timestamp'].dt.strftime('%d/%m %H:%M')
    #Create new DF fill_level_string to convert int into str + % for text display
    df['fill_level_string'] = df['fill_level'].round().astype(int).astype(str) + '%'
    return df

#############################################################
#Function for getting weekly bin collection stats
#Where week=0 gets data for current week, -1 for last week
def get_weekly_collection_stats(week=0):
    query = """
        WITH fill_changes AS (
            SELECT
                bin_id,
                timestamp,
                fill_level,
                LAG(fill_level) OVER (PARTITION BY bin_id ORDER by timestamp) AS prev_fill
            FROM sensor_table
        ),

        emptied_bins AS (
            SELECT
                bin_id,
                timestamp,
                prev_fill
            FROM fill_changes
            WHERE fill_level <= 10 AND (prev_fill IS NULL or prev_fill > 10)
        )

        SELECT
            bin_id,
            timestamp,
            prev_fill
        FROM emptied_bins
    """
    df = pd.read_sql(query, engine)
    #Convert timestamp column to datetime format
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    #Get start and end dates of the target week (week=0 or -1)
    #Get today's date and remove time part
    today = pd.Timestamp.now().normalize()
    #Find current week's Monday by subtracting no. of days since Monday
    this_monday = today - pd.Timedelta(days=today.weekday())
    #Find the start of the week of either current week (week=0) or last week (week=-1)
    week_start = this_monday + pd.Timedelta(weeks=week)
    #Find end of the week by adding 7 days to the start
    week_end = week_start + pd.Timedelta(days=7)

    #Filter data to only rows from target week (start and end)
    df = df[(df['timestamp'] >= week_start) & (df['timestamp'] < week_end)]   
    #Make a new column 'weekday' with list of weekday names from the datetime object
    df['weekday'] = df['timestamp'].dt.day_name()

    #Group the data by weekday by making it the index
    summary = df.groupby('weekday').agg(
        #Count total for how many bins emptied
        total_bins_emptied=('bin_id', 'count'),
        #Find average fill level before emptied
        avg_fill_before_empty=('prev_fill', 'mean'),
        #Count how many bins were over 90% full before being emptied
        bins_above_90=('prev_fill', lambda x: (x >= 90).sum())
    #Show the weekdays in order even if its missing from the data
    ).reindex([
        'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
    #If no bins emptied on a day, show '0' instead of NaN
    ]).fillna(0)
    #Round fill % to 1 decimal place
    summary['avg_fill_before_empty'] = summary['avg_fill_before_empty'].round(1)
    #Convert both columns into integers so don't see decimals
    summary['bins_above_90'] = summary['bins_above_90'].astype(int)
    summary['total_bins_emptied'] = summary['total_bins_emptied'].astype(int)

    #Reset the index (weekday) back to just numbers again
    return summary.reset_index(), week_start.date(), (week_end - pd.Timedelta(days=1)).date() #week end is - 1 day to remove Monday from range

#############################################################
# Function for combining get_bin_data()
# To get following: bin id, fill level, location, bin type, last emptied
# New columns: bin_status, bin height, temperature, 

def get_complete_bin_table():
    bin_data = get_bin_data() #fetches bin id, fill level, location, timestamp

    #Fetch bin_status, bin_height, last emptied, bin type
    query = """
        WITH fill_changes AS (
            SELECT
                bin_id,
                timestamp,
                fill_level,
                LAG(fill_level) OVER (PARTITION BY bin_id ORDER BY timestamp) AS prev_fill_level
            FROM sensor_table
        ),
        
        empties AS (
            SELECT
                bin_id,
                MAX(timestamp) AS last_emptied
            FROM fill_changes
            WHERE
                fill_level <= 10 AND (prev_fill_level IS NULL OR prev_fill_level > 10)
            GROUP BY bin_id
        ),

        extra_bin_table AS (
            SELECT
                bin_id,
                bin_type,
                bin_status,
                bin_height,
                ROW_NUMBER() OVER (PARTITION BY bin_id ORDER BY bin_id) AS rn
            FROM bin_table
        )

        SELECT 
            extra.bin_id,
            extra.bin_type,
            extra.bin_status,
            extra.bin_height,
            e.last_emptied
        FROM extra_bin_table extra
        LEFT JOIN empties e ON extra.bin_id = e.bin_id
        WHERE extra.rn = 1
    """
    #Store query into a dataframe
    new_data = pd.read_sql(query, engine)

    #Merge get_bin_data() and new query into a single df
    df = bin_data.merge(new_data, on="bin_id", how="left")


    #Format the fill level as a string with % for display only
    df['fill_level_display'] = df['fill_level'].round().astype(int).astype(str) + '%'

    #Format the last_emptied column into a datetime format
    df['last_emptied'] = pd.to_datetime(df['last_emptied'], errors='coerce')
    #Format it to a readable string for display
    df['last_emptied'] = df['last_emptied'].dt.strftime('%d/%m/%Y %H:%M')

    return df[['bin_id', 'fill_level', 'fill_level_display', 'bin_location', 'bin_type', 'last_emptied', 'bin_status', 'bin_height']]

#############################################################
# Function for getting collection history of bins based on bin ID
#Find the fill level before emptying event, and time taken to empty bin after reaching 80%
#############################################################
def get_collection_history(bin_id):
    query = """
    WITH fill_changes AS (
        SELECT 
            bin_id,
            timestamp,
            fill_level,
            LAG(fill_level) OVER (PARTITION BY bin_id ORDER BY timestamp) AS prev_fill,
            LAG(timestamp) OVER (PARTITION BY bin_id ORDER BY timestamp) AS prev_time
        FROM sensor_table
        WHERE bin_id = %s
    ),
    
    alert_and_empty AS (
        SELECT 
            bin_id,
            timestamp AS collection_timestamp,
            prev_fill AS fill_level,
            prev_time,
            prev_fill
        FROM fill_changes
        WHERE 
            fill_level <= 10 AND 
            prev_fill >= 80
    )

    SELECT 
        bin_id,
        collection_timestamp,
        fill_level,
        TIMESTAMPDIFF(MINUTE, prev_time, collection_timestamp) AS time_since_full
    FROM alert_and_empty
    ORDER BY collection_timestamp DESC
    LIMIT 20
    """
    df = pd.read_sql(query, engine, params=(bin_id,)) #Pass bin_id as a 1 element tuple to use with params

    def time_taken_to_empty_format(minutes):
        minutes = int(minutes)
        hours = int(minutes / 60)
        days = int(hours / 24)

        if pd.isnull(minutes):
            return "N/A"
        
        #If less than 60 minutes
        if minutes < 60:
            return f"{int(minutes)} minute{'s' if minutes != 1 else ''}" #Show min text
        #If less than 24 hours
        elif hours < 24:
            return f"{hours} hour{'s' if hours != 1 else ''}" #Show hour in text if less than 24
        #If greater than 24 hours
        else:
            remaining_hours = hours % 24
            time_text = f"{days} day{'s' if days != 1 else ''}"
            #Show hours with day
            time_text += f" {remaining_hours} hour{'s' if remaining_hours != 1 else ''}"
            return time_text

    if not df.empty:
        #convert collection timestamp to datetime format
        df['collection_timestamp'] = pd.to_datetime(df['collection_timestamp'])
        #Convert to string in readable format for display
        df['collection_timestamp_string'] = df['collection_timestamp'].dt.strftime('%d/%m/%Y %H:%M')
        #Time since bin became full converted to string with min text
        df['time_since_full_string'] = df['time_since_full'].apply(time_taken_to_empty_format)

    else: #if it's empty return the columns still
        df = pd.DataFrame(columns=[
            'bin_id', 'collection_timestamp_string', 'fill_level', 'time_since_full_string', 'time_since_full'
        ])

    return df[['bin_id', 'collection_timestamp_string', 'fill_level', 'time_since_full_string', 'time_since_full']]




#############################################################
# Get the bin fill history for selected bin
#############################################################
def get_bin_fill_history(bin_id):
    query = """
        SELECT 
            bin_id,
            timestamp,
            fill_level
        FROM sensor_table
        WHERE bin_id = %s
        ORDER BY timestamp DESC
        LIMIT 100
    """
    df = pd.read_sql(query, engine, params=(bin_id,)) #Pass bin_id as a 1 element tuple to use with params

    #Determine the % change in fill level based on previous reading
    #Use .diff(periods=-1) to calculate difference in current row compared with next row (next older record)
    df['fill_level_change'] = df['fill_level'].diff(periods=-1)
    
    #Format to show if change was increase/decrease %
    df['fill_level_change_string'] = df['fill_level_change'].apply( #run lambda function on each value x (fill change) to add + before 'x' if increase
        lambda x: f"{'+' if x > 0 else ''}{round(x)}%" if pd.notnull(x) else "N/A" #If value is missing return "N/A", round x to nearest whole number instead of decimals
    )

    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        #convert timestamp to readable string for display
        df['timestamp_string'] = df['timestamp'].dt.strftime('%d/%m/%Y %H:%M')
        #Convert fill level as string with % for display only, round to nearest whole number
        df['fill_level_display'] = df['fill_level'].round().astype(int).astype(str) + '%'
    #If df empty just return empty table
    else:
        df = pd.DataFrame(columns=['bin_id', 'timestamp_string', 'fill_level_display'])

    return df[['bin_id', 'fill_level_change_string', 'timestamp_string', 'fill_level_display', 'fill_level', 'timestamp', 'fill_level_change']]



#############################################################
# Get alerts table data
#############################################################
def get_alerts_data():
    query = """
        SELECT
            alert_id,
            bin_id,
            sensor_id,
            alert_type,
            alert_message,
            triggered_time,
            resolved_time,
            COALESCE(status, 'Active') AS status,
            user_notes
        FROM alerts_table
        ORDER BY triggered_time DESC
        """
    df = pd.read_sql(query, engine)

    if not df.empty:
        #Convert the date columns into datetime objects
        df['triggered_time'] = pd.to_datetime(df['triggered_time'])
        df['resolved_time'] = pd.to_datetime(df['resolved_time'])

        #Convert the datetimes into string and format data for display as D/M/Y H:M
        df['triggered_time_string'] = df['triggered_time'].dt.strftime('%d/%m/%Y %H:%M')

        df['resolved_time_string'] = df['resolved_time'].dt.strftime('%d/%m/%Y %H:%M')
        df['resolved_time_string'] = df['resolved_time_string'].fillna('').astype(str) #Make sure undefined columns are empty string

        #Format user_notes as empty string if undefined
        df['user_notes'] = df['user_notes'].fillna('')

    else: #Show empty table with columns 
        df = pd.DataFrame(columns=[
            'alert_id', 'bin_id', 'sensor_id', 'alert_type', 'alert_message', 'triggered_time_string', 'resolved_time_string', 'status', 'user_notes'])


    return df[['alert_id', 'bin_id', 'sensor_id', 'alert_type', 'alert_message', 'triggered_time_string', 'triggered_time', 'resolved_time_string', 'resolved_time', 'status', 'user_notes']]


#############################################################
# Get Sensor Health data for alerts page
#############################################################
def get_sensor_health_data():
    query = """
        SELECT 
            s.sensor_id,
            s.bin_id,
            s.battery_voltage,
            s.temperature,
            s.timestamp,
            b.bin_status
        FROM sensor_table s
        LEFT JOIN bin_table b ON s.bin_id = b.bin_id
    """
    df = pd.read_sql(query, engine)

    #Convert timestamp to datetime format
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

    #Sort df on timestamp per sensor ID DESCENDING (we want the latest records)
    df = df.sort_values(by=['sensor_id', 'timestamp'], ascending=[True, False])

    #Drop duplicate sensor_ids to keep only most recent one
    df = df.drop_duplicates(subset='sensor_id', keep='first')

    #Format the timestamp for display
    df['last_seen'] = df['timestamp'].dt.strftime('%d/%m/%Y %H:%M')

    #Find the timestamps of sensors that haven't been updated in >12 hours
    current_time = datetime.now()
    #inactive_sensor = True if last reading >12 hours ago
    df['inactive_sensor'] = df['timestamp'] < (current_time - timedelta(hours=12))
    #Format the boolean value as a lowercase string instead for Dash to process
    df['inactive_sensor'] = df['inactive_sensor'].astype(str).str.lower()

    return df[['bin_id', 'sensor_id', 'battery_voltage', 'temperature', 'last_seen', 'bin_status', 'inactive_sensor']]


#############################################################
# Get timestamps when bins reached 80% Fill level
# Time from when bin was <= 10% full to 80% full
#############################################################
def get_time_to_80_data(bin_id):
    query = """
        WITH fill_changes AS (
            SELECT 
                bin_id,
                timestamp,
                fill_level,
                LAG(fill_level) OVER (PARTITION BY bin_id ORDER BY timestamp) AS prev_fill,
                LAG(timestamp) OVER (PARTITION BY bin_id ORDER BY timestamp) AS prev_time
            FROM sensor_table
            WHERE bin_id = %s
        ),

        empties AS (
            SELECT 
                bin_id,
                timestamp AS start_time
            FROM fill_changes
            WHERE fill_level <= 10 AND (prev_fill IS NULL OR prev_fill > 10)
        ),

        fulls AS (
            SELECT 
                bin_id,
                timestamp AS end_time
            FROM fill_changes
            WHERE fill_level >= 80 AND (prev_fill IS NULL OR prev_fill < 80)
        ),

        paired_events AS (
            SELECT 
                e.start_time,
                MIN(f.end_time) AS full_time
            FROM empties e
            JOIN fulls f
              ON f.end_time > e.start_time
            GROUP BY e.start_time
        )

        SELECT 
            start_time AS emptied_at,
            full_time AS full_at,
            TIMESTAMPDIFF(MINUTE, start_time, full_time) AS time_to_fill
        FROM paired_events
        ORDER BY full_at
        LIMIT 100
    """

    df = pd.read_sql(query, engine, params=(bin_id,))

    if not df.empty:
        df['full_at'] = pd.to_datetime(df['full_at'])
        #Get the date only to group by date
        df['date'] = df['full_at'].dt.date

    else:
        df = pd.DataFrame(columns=["emptied_at", "full_at", "time_to_fill", "date"])

    return df


#############################################################
# Get timestamps for each time bin was emptied
# empty event = where current fill level is <=30 and prev_fill was >30%,
# And is used to determine collections
#############################################################
def get_daily_bin_collections(bin_id):
    query = """
        WITH fill_changes AS (
            SELECT
                bin_id,
                timestamp,
                fill_level,
                LAG(fill_level) OVER (PARTITION BY bin_id ORDER BY timestamp) AS prev_fill
            FROM sensor_table
            WHERE bin_id = %s
        )
        SELECT
            bin_id,
            timestamp
        FROM fill_changes
        WHERE fill_level <= 30 AND (prev_fill IS NULL OR prev_fill > 30)
    """
    df = pd.read_sql(query, engine, params=(bin_id,))

    if not df.empty:
        #Format timestamp column to datetime for handling
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        #Get the date only to group by date
        df['date'] = df['timestamp'].dt.date

    else:
        df = pd.DataFrame(columns=['bin_id', 'timestamp', 'date'])

    return df


#############################################################
# Get AVG fill level increase per hour for heat map
# Grouped by each day of the week
# Also filter df by month
#############################################################
def get_bin_fill_heatmap_data(bin_id, selected_month):
    query = """
        WITH fill_changes AS (
            SELECT
                bin_id,
                timestamp,
                fill_level,
                LAG(fill_level) OVER (PARTITION BY bin_id ORDER BY timestamp) AS prev_fill
            FROM sensor_table
            WHERE bin_id = %s
        ),
        
        hourly_changes AS (
            SELECT
                bin_id,
                timestamp,
                HOUR(timestamp) AS hour,
                DAYNAME(timestamp) AS day_of_week,
                (fill_level - prev_fill) AS fill_change
            FROM fill_changes
            WHERE prev_fill IS NOT NULL AND (fill_level - prev_fill) > 0 AND DATE_FORMAT(timestamp, '%%Y-%%m') = %s
        )

        SELECT 
            day_of_week,
            hour,
            ROUND(AVG(fill_change), 1) AS avg_fill_change
        FROM hourly_changes
        GROUP BY day_of_week, hour
    """
    df = pd.read_sql(query, engine, params=(bin_id, selected_month))
    
    #Order days of the week properly (instead of alphabetical order)
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    #Make day_of_week column into categories and specify order
    df['day_of_week'] = pd.Categorical(df['day_of_week'], categories=day_order, ordered=True)
    
    #Then sort the df rows by day of week first, then by hours ascending
    df = df.sort_values(['day_of_week', 'hour'])

    return df