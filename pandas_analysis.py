import os
BASE_DIR = "C:\\Users\\apetralia\\Desktop\\mbta"
os.chdir(BASE_DIR)

import pandas as pd
from geopy.distance import vincenty
import ast

from settings.settings import TABLE_ONE, TABLE_TWO
from trips_db import cursor as c

pd.set_option('display.width', 110)
pd.set_option('display.max_rows', 500)
pd.set_option('display.float_format', lambda x: '%.3f' % x)

# TODO: standardize durations.. eg. 1.5x average at this time
# TODO: for trips that are significantly less than their route length, remove them

if __name__ == '__main__':
    
    # View what is in table one (ie. completed trips)   
    query = c.execute("SELECT * FROM %s" % TABLE_ONE).fetchall()
    df = pd.DataFrame(data=query, columns=['ID', 'Trip_ID', 'Vehicle_ID', 'Direction', 'Route', 'Start location', 'End location', 'Start time', 'End time', 'Duration']).drop('ID', axis=1)
    
    # Add a distance column
    df['Start location'] = df['Start location'].apply(ast.literal_eval)
    df['End location'] = df['End location'].apply(ast.literal_eval)
    df['Distance (mi)'] = df.apply(lambda x: vincenty(x['Start location'], x['End location']).miles, axis=1)
    
    # Truncate microseconds
    for col in ['Start time', 'End time', 'Duration']:     
        df[col] = df[col].apply(lambda x: x.split('.')[0])

    ###########
    ### EDA ###
    ###########
        
    tmp = df[df['Route'] == 'Green Line C']
    
    df.sort('Distance (mi)', ascending=True).head(100)
    
    df[df['Vehicle_ID'] == 'y0452']
    # Notice the start and end times for short trips.. they start with the same vehicle shortly after the prior trip ends
    # Consolidation: if same vehicle, same direction and consecutive, then those rows should be considered a single trip
    
    df[df['Vehicle_ID'] == '3659']
    

#    
#    # View what is in table two (ie. number of cars on the track)
#    query = c.execute("SELECT * FROM %s" % TABLE_TWO).fetchall()
#    df = pd.DataFrame(data=query, columns=['ID', 'Timestamp', 'Count', 'Direction', 'Route']).drop('ID', axis=1)
#    # df[df['Route'] == 'Green Line B']['Count'].describe()
#    