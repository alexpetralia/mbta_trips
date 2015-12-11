# @author: apetralia

# TODO: write docstrings

import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

from datetime import datetime as dt
import requests
import time
import logging

from settings.api_key import API_KEY
from settings.settings import TABLE_ONE, TABLE_TWO
from settings.routes import ROUTES
from trips_db import cursor, connection

class Route():
    
    def __init__(self, route_name):
        self.directions = {}
        self.route_name = route_name
        
    def update_route(self, json):
        """ TODO: Add doc string """
        
        for direction in json['direction']:
        
            # Scrape this direction's metadata from .json dump
            direction_name = direction['direction_name']
            
            # If direction_name doesn't already exist as Direction object, create it
            if not self.directions.get(direction_name):
                self.directions[direction_name] = Direction(direction_name, self.route_name, ignored_trips)
            
            # MBTA API initializes a trip with in the format: <vehicle_ID>_[0,1]. 
            # The trip is then removed once the car starts moving and renamed to
            # format: <trip_id>_[0,1]. Initialized trips should be ignored (ie.
            # if trip_id == vehicle_id), while only moving trips should count.
            all_trips_json = direction['trip']
            relevant_trips = get_relevant_trips(all_trips_json)
                    
            # Open this direction's Direction object
            this_direction = self.directions.get(direction_name)
            
            # PART 1: Update Direction
            this_direction.update_trips(relevant_trips, cursor)
            
            # PART 2: Write count to sqlite3
            this_direction.write_count_to_sql(relevant_trips, cursor)
        
class Direction():
    
    def __init__(self, direction_name, route_name, ignored_trips):
        self.pre_update_trips = {}
        self.updated_trips = {}
        self.direction_name = direction_name
        self.route_name = route_name
        self.ignored_trips = ignored_trips
    
    def update_trips(self, curr_trips_json, cursor):
        """ TODO: Add doc string """
        
        new_trips, finished_trips = [], [] # for logging
        
        # Check if current trips already exist
        for curr_trip in curr_trips_json:
            trip_id = curr_trip['trip_id']
            lat = curr_trip['vehicle']['vehicle_lat']
            long = curr_trip['vehicle']['vehicle_lon']
            vehicle_id = curr_trip['vehicle']['vehicle_id']
            location = (lat, long)
            
            # If current trip already in Direction object, update the Trip's location
            if trip_id in self.pre_update_trips.keys():
                self.pre_update_trips[trip_id].update_location(location)
            # If current trip not already in Direction object, add it as a new Trip()
            else:
                new_trip = Trip(trip_id, vehicle_id,
                                location, self.direction_name, self.route_name)
                self.updated_trips[trip_id] = new_trip
                new_trips.append(new_trip)
                
        # Check if prior trips still currently exist
        curr_trip_ids = [x['trip_id'] for x in curr_trips_json]
        for pre_update_trip_id in self.pre_update_trips.keys():
            trip_obj = self.pre_update_trips[pre_update_trip_id]
            trip_id = trip_obj.get()['Trip ID']
            
            # If pre-update trip is not in current trips, it has terminated
            if trip_id not in curr_trip_ids:
                trip_obj.end_trip()
                del self.updated_trips[trip_id]
                finished_trips.append(trip_obj)
                
                # Only write to sqlite3 if finished_trip 
                # is not a trip beginning before runtime               
                if trip_id not in self.ignored_trips:
                    trip_obj.write_trip_to_sql(cursor)
                
        # Update set of pre_updated trips after extracting new/finished trips
        self.pre_update_trips = self.updated_trips.copy()
        
        # Logging
        new_trip_ids = [x.get()['Trip ID'] for x in new_trips]
        if new_trip_ids:
            logger.info("New trips (%s, %s): %s" % (route_name, self.direction_name, new_trip_ids))
        finished_trip_ids = [x.get()['Trip ID'] for x in finished_trips]
        if finished_trip_ids:
            logger.info("Finished trips (%s, %s): %s" % \
                (route_name, self.direction_name, finished_trip_ids))
                        
    def write_count_to_sql(self, curr_trips, cursor):
        """ TODO: Add doc string """
        
        row = {"Time": format(dt.now()),
               "Count": len(curr_trips),
               "Direction": self.direction_name,
               "Route": self.route_name}          
        sql = ("INSERT INTO %s (datetime, count, direction, route) \
                VALUES (?, ?, ?, ?)" % TABLE_TWO)
        cursor.execute(sql, 
            [str(row['Time']), str(row['Count']), 
             str(row['Direction']), str(row['Route'])] )

class Trip():
    
    def __init__(self, trip_id, vehicle_id, location, direction, route):
        self.trip_id = trip_id
        self.vehicle_id = vehicle_id
        self.direction = direction
        self.start_location = location
        self.end_location = self.start_location
        self.route = route
        self.start_time = dt.now()
        self.end_time = None
        self.duration = None
        self.curr_location = None
                
    def end_trip(self):
        self.end_time = dt.now()
        self.duration = self.end_time - self.start_time
        
    def get(self):
        return { "Trip ID": self.trip_id,
                 "Vehicle ID": self.trip_id,
                 "Start location": self.start_location,
                 "End location": self.end_location,
                 "Direction": self.direction,
                 "Route": self.route,
                 "Start time": format(self.start_time),
                 "End time": format(self.end_time),
                 "Duration": format(self.duration) }
                 
    def update_location(self, location):
        self.end_location = location
        
    def write_trip_to_sql(self, cursor):
        """ TODO: Add doc string """
    
        sql = ("INSERT INTO %s \
              (trip_id, vehicle_id, direction, route, start_location, \
              end_location, start_time, end_time, duration) \
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)" % TABLE_ONE)
        row = [str(self.trip_id), str(self.vehicle_id), 
               str(self.direction), str(self.route), 
               str(self.start_location), str(self.end_location), 
               str(self.start_time), str(self.end_time), 
               str(self.duration)]
        cursor.execute(sql, row)    
                                
def ignore_trips(response):
    ignored_trips = []
    for mode in response['mode']:
        for route in mode['route']:
            for direction in route['direction']:
                for trip in direction['trip']:
                    ignored_trips.append(trip['trip_id'])
    return ignored_trips
    
def get_relevant_trips(all_trips_json):
    relevant_trip_ids = []
    for trip in all_trips_json:
        vehicle_id = trip['vehicle']['vehicle_id']
        stripped_trip_id = trip['trip_id'].split("_")[0]
        if vehicle_id != stripped_trip_id:
            relevant_trip_ids.append(trip['trip_id'])
    relevant_trips_json = [x for x in all_trips_json if x['trip_id'] in relevant_trip_ids]
    return relevant_trips_json
    
def get_json(url, logger):
    while True:
        try:        
            response = requests.get(url).json()
            return response
        except requests.exceptions.RequestException as e:
            logger.debug(e)
            logger.debug("Retrying in 10 seconds...")
            time.sleep(10)
    
def init_logging(logname):
    LOGS_PATH = BASE_DIR + "/logs"
    if not os.path.exists(LOGS_PATH):
        os.mkdir(LOGS_PATH)
       
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    
    handler = logging.FileHandler(LOGS_PATH + "/%s.txt" % logname)
    handler.setLevel(logging.INFO)
    fmt = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')
    handler.setFormatter(fmt)
    
    logger.addHandler(handler)
    return logger

if __name__ == "__main__":   
    
    today = dt.today().strftime('%Y-%m-%d')
    logger = init_logging(today)

    BASE_URL = 'http://realtime.mbta.com/developer/api/v2/' \
               'vehiclesbyroutes?api_key=%s&routes=%s&format=json' % (API_KEY, ROUTES)
    
    # Ignore all trips at runtime because start time cannot be determined
    ignored_trips = ignore_trips( requests.get(BASE_URL).json() )

    Routes = {}
    while True:
        
        response = get_json(BASE_URL, logger)
        
        try:
            modes = response['mode']
        except KeyError as e:
            logger.debug(e)
            time.sleep(300)
            continue
            
        for mode in modes:
            for route in mode['route']:
                route_name = route['route_name']

                # If route_name doesn't already exist as Route object, create it
                if not Routes.get(route_name):
                    Routes[route_name] = Route(route_name)
                    
                # Open this route's Route object
                this_route = Routes.get(route_name)
        
                # Update Route
                this_route.update_route(route)
    
        connection.commit()
        
        # Log next iteration        
        for route_name, route_obj in Routes.items():
            for direction_name, direction_obj in route_obj.directions.items():
                logger.info("Currently active trips (%s, %s): %s" % \
                            (route_name, direction_name,
                             list(direction_obj.pre_update_trips)))
        
        logger.info("*** Starting next .json dump... ***")
        
        time.sleep(10)