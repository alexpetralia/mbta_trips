import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__ + "\\.."))
os.chdir(BASE_DIR)

from datetime import datetime as dt, time
import time as chron

from settings.api_key import API_KEY
from settings.routes import ROUTES
from mbta_trips import init_logging, get_json

def in_between(now, start, end): # @ J.F. Sebastian on StackOverflow
    if start <= end:
        return start <= now < end
    else: # over midnight e.g., 23:30-04:15
        return start <= now or now < end
   
start_time = time(23,30)
end_time = time(6,30)
half_hour = 60 * 30

while True:
    
    curr_time = dt.today().now().time()
    
    while in_between(curr_time, start_time, end_time):
    
        JSON_DUMPS_PATH = BASE_DIR + "\\logs\\json_dumps"
        if not os.path.exists(JSON_DUMPS_PATH):
            os.mkdir(JSON_DUMPS_PATH)
            
        logger = init_logging("\\json_dumps\\" + dt.today().now().strftime('%Y-%m-%d,%H.%M.%S'))
    
        BASE_URL = 'http://realtime.mbta.com/developer/api/v2/' \
               'vehiclesbyroutes?api_key=%s&routes=%s&format=json' % (API_KEY, ROUTES)
    
        response = get_json(BASE_URL, logger)
        logger.info(response)
    
        chron.sleep(half_hour)
    
    
