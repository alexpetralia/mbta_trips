import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__ + "\\.."))
DATABASE_PATH = BASE_DIR + "\\mbta_trips.db"

TABLE_ONE = "completed_trip_history"
TABLE_TWO = "trip_lengths"