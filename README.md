## MBTA Trips ##

This project was developed (1) to document how many MBTA vehicles are on the road at any given time and (2) to produce summary statistics about each individual trip.

It produces two *sqlite3* tables. The first maintains characteristics for each trip (eg. start location, end location, duration) while the second maintains the number of trips on each MBTA route every 10 seconds.

#### Usage ####

You can request an MTA API key [here](http://realtime.mbta.com/portal). Once you have an API key, you can simply drop a file called 'api_key.py' into the *settings* folder, whose only variable is: "API_KEY = < your_api_key >".

You will also require the *requests* and *sqlite3* modules for the program to work.

#### Known issues ####

Trips may sometimes appear, then disappear seconds or minutes later, only to reappear again. I contacted the MBTA about this and it is a known bug. Any analysis on trip durations must adjust for trips that are incomplete because of this bug.

#### License ####

Distributed under the MIT License.
See more at: [https://opensource.org/licenses/MIT](https://opensource.org/licenses/MIT)