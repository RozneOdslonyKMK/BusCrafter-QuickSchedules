##############################################################################################
#                                                                                            #
#                                                                                            #
#     ██████╗ ██╗   ██╗███████╗ ██████╗██████╗  █████╗ ███████╗████████╗███████╗██████╗      #
#     ██╔══██╗██║   ██║██╔════╝██╔════╝██╔══██╗██╔══██╗██╔════╝╚══██╔══╝██╔════╝██╔══██╗     #
#     ██████╔╝██║   ██║███████╗██║     ██████╔╝███████║█████╗     ██║   █████╗  ██████╔╝     #
#     ██╔══██╗██║   ██║╚════██║██║     ██╔══██╗██╔══██║██╔══╝     ██║   ██╔══╝  ██╔══██╗     #
#     ██████╔╝╚██████╔╝███████║╚██████╗██║  ██║██║  ██║██║        ██║   ███████╗██║  ██║     #
#     ╚═════╝  ╚═════╝ ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝        ╚═╝   ╚══════╝╚═╝  ╚═╝     #
#                                                                                            #
#                            ██╗███╗   ██╗███████╗ ██████╗                                   #
#                            ██║████╗  ██║██╔════╝██╔═══██╗                                  #
#                            ██║██╔██╗ ██║█████╗  ██║   ██║                                  #
#                            ██║██║╚██╗██║██╔══╝  ██║   ██║                                  #
#                            ██║██║ ╚████║██║     ╚██████╔╝                                  #
#                            ╚═╝╚═╝  ╚═══╝╚═╝      ╚═════╝                                   #
#                                                                                            #
#                                                                                            #
##############################################################################################

# Autor: ROKMK - Różne Odsłony Komunikacji Miejskiej w Krakowie
# Description: Krakow bus/tram stops-like quick schedule json generator
# Website: https://rokmk.pl/
# Project website: https://github.com/RozneOdslonyKMK/BusCrafter-QuickSchedules/

# Copyright:
# (c) ROKMK 2026 - All rights reserved.
# Do NOT public this on any website.
# This program may only be published anywhere with the owner's consent.
# Please do NOT publish this code anywhere in its entirety or even in fragments.


# --- IMPORTANT! ---
# This code is an editable example, which without modifications will generate json for tram line 3 validate from 31.08.2026.



#####################################
# ||=============================|| #
# ||           Imports           || #
# ||=============================|| #
#####################################

# Please be sure, that you have installed Python-3 and you did "pip install pandas" command in your terminal.

import pandas as pd
import json

#####################################
# ||=============================|| #
# ||        Editable Code        || #
# ||=============================|| #
#####################################

path = "./GTFS_KRK_T/"     # You can change "GTFS_KRK_T" (for trams) to "GTFS_KRK_A" (for buses) or "GTFS_KRK_M" (for Mobilis buses)
routes = pd.read_csv(path + "routes.txt", dtype={'route_short_name': str, 'route_id': str})
trips = pd.read_csv(path + "trips.txt")
stop_times = pd.read_csv(path + "stop_times.txt", dtype={'departure_time': str})
stops = pd.read_csv(path + "stops.txt", dtype={'stop_id': str, 'stop_code': str, 'stop_desc': str})
calendar = pd.read_csv(path + "calendar.txt")

dni_powszednie = "Dni powszednie"     # You can change "Dni powszednie" to "Dzień powszedni" for styles before 2022 (to-2015 and to-2022)
soboty = "Soboty"
swieta = "Święta"

def build_service_day_map(calendar_dates_path="calendar_dates.txt"):
    df = pd.read_csv(calendar_dates_path)
    
    active_dates = df[df['exception_type'] == 1].copy()
    
    active_dates['dt'] = pd.to_datetime(active_dates['date'].astype(str), format='%Y%m%d')
    active_dates['dow'] = active_dates['dt'].dt.dayofweek
    
    service_map = {}
    
    for service_id, group in active_dates.groupby('service_id'):
        dows = group['dow'].tolist()
        
        weekdays = sum(1 for d in dows if d < 5)
        saturdays = sum(1 for d in dows if d == 5)
        sundays = sum(1 for d in dows if d == 6)
        
        if saturdays > weekdays and saturdays >= sundays:
            service_map[service_id] = soboty
        elif sundays > weekdays and sundays > saturdays:
            service_map[service_id] = swieta
        else:
            service_map[service_id] = dni_powszednie
            
    return service_map

SERVICE_DAY_MAP = build_service_day_map(path + "calendar_dates.txt")

def map_service_to_day_type(service_id):
    return SERVICE_DAY_MAP.get(str(service_id), dni_powszednie)

def generate_line_json(line_number, day_mode="all", custom_times=None):
    route = routes[routes['route_short_name'] == str(line_number)].iloc[0]
    route_id = route['route_id']
    
    line_trips = trips[trips['route_id'] == route_id]
    
    merged = line_trips.merge(stop_times, on='trip_id').merge(stops, on='stop_id')
    
    directions_data = {}
    directions_streets = {}
    
    for direction_id, dir_group in merged.groupby('direction_id'):
        dir_key = f"direction-{direction_id}"
        
        sample_trip_id = dir_group.groupby('trip_id')['stop_sequence'].max().idxmax()
        sample_trip_stops = dir_group[dir_group['trip_id'] == sample_trip_id].sort_values('stop_sequence')
        
        headsign = dir_group['trip_headsign'].iloc[0] if 'trip_headsign' in dir_group else "Nieznany"
        
        dir_custom_times = None
        if custom_times and isinstance(custom_times, dict):
            dir_custom_times = custom_times.get(dir_key)
        
        stops_dict = {}
        stop_order = 1
        
        for _, stop_row in sample_trip_stops.iterrows():
            stop_id = stop_row['stop_id']
            stop_code = stop_row.get('stop_code', f"{stop_id}")
            stop_name = stop_row['stop_name']
            stop_desc = stop_row['stop_desc']

            if dir_custom_times and (stop_order - 1) < len(dir_custom_times):
                travel_time = str(dir_custom_times[stop_order - 1])
            else:
                travel_time = str(stop_row['stop_sequence'] - 1)

            stop_departures = dir_group[dir_group['stop_id'] == stop_id]
            
            departures_raw = {
                dni_powszednie: {},
                soboty: {},
                swieta: {}
            }
            
            for _, dep in stop_departures.iterrows():
                day_type = map_service_to_day_type(dep['service_id'])

                if day_mode == "weekdays" and day_type != dni_powszednie:
                    continue
                elif day_mode == "weekends" and day_type == dni_powszednie:
                    continue

                time_str = dep['departure_time'].strip()
                
                parts = time_str.split(':')
                hour_int = int(parts[0]) % 24
                minute_str = parts[1]
                
                if hour_int not in departures_raw[day_type]:
                    departures_raw[day_type][hour_int] = set()
                
                departures_raw[day_type][hour_int].add(minute_str)

            departures_sorted = {}
            for day_type, hours_dict in departures_raw.items():
                if not hours_dict:
                    continue

                if day_mode == "weekdays" and day_type != dni_powszednie:
                    continue
                if day_mode == "weekends" and day_type == dni_powszednie:
                    continue

                departures_sorted[day_type] = {}
                
                for h in sorted(hours_dict.keys()):
                    sorted_minutes = sorted(list(hours_dict[h]))
                    departures_sorted[day_type][str(h)] = sorted_minutes

            stops_dict[str(stop_order)] = {
                "name": stop_name + " " + stop_desc,
                "code": stop_code,
                "on-demand": False,                 # You must check the generated json file, because this value is always false. You must change "false" to "true" for "on-demand" stops in the generated json file.
                "time": travel_time,
                "departures": departures_sorted,
                "departure-merges": {}
            }
            stop_order += 1

        if dir_key == "direction-0":
            route_streets = ""                      # Streets with loops for the 1st route. Format:     LOOP 1 - Street 1, Street 2, Street 3 - LOOP 2
            streets = ""                            # Only streets for the 1st route. Format:           Street 1, Street 2, Street 3
        if dir_key == "direction-1":
            route_streets = ""                      # Streets with loops for the 2nd route. Format:     LOOP 1 - Street 1, Street 2, Street 3 - LOOP 2
            streets = ""                            # Only streets for the 2nd route. Format:           Street 1, Street 2, Street 3
        if dir_key == "direction-2":
            route_streets = ""                      # Streets with loops for the 3rd route. Format:     LOOP 1 - Street 1, Street 2, Street 3 - LOOP 2
            streets = ""                            # Only streets for the 3rd route. Format:           Street 1, Street 2, Street 3
        if dir_key == "direction-3":
            route_streets = ""                      # Streets with loops for the 4th route. Format:     LOOP 1 - Street 1, Street 2, Street 3 - LOOP 2
            streets = ""                            # Only streets for the 4th route. Format:           Street 1, Street 2, Street 3
        if dir_key == "direction-4":
            route_streets = ""                      # Streets with loops for the 5th route. Format:     LOOP 1 - Street 1, Street 2, Street 3 - LOOP 2
            streets = ""                            # Only streets for the 5th route. Format:           Street 1, Street 2, Street 3
        if dir_key == "direction-5":
            route_streets = ""                      # Streets with loops for the 6th route. Format:     LOOP 1 - Street 1, Street 2, Street 3 - LOOP 2
            streets = ""                            # Only streets for the 6th route. Format:           Street 1, Street 2, Street 3
        if dir_key == "direction-6":
            route_streets = ""                      # Streets with loops for the 7th route. Format:     LOOP 1 - Street 1, Street 2, Street 3 - LOOP 2
            streets = ""                            # Only streets for the 7th route. Format:           Street 1, Street 2, Street 3

        directions_data[dir_key] = {
            "name": headsign,
            "streets": streets,
            "stops": {
                "zone-1": stops_dict,
                "departure-notes": {}
            }
        }

        directions_streets[dir_key] = route_streets

    output_json = {
        "line-config": {
            "line": str(line_number),
            "line-type": "",                        # You can write here "Aglomeracyjna" for 2xx/3xx/9xx lines or "Czasowa" for 7x/7xx lines or "Specjalna" for LRx and museum lines or "Tramwajowa" / "Autobusowa" for WOŚP lines
            "line-operator": "MPK S.A. w Krakowie", # You can change "MPK S.A. w Krakowie" to "Mobilis sp. z o.o." for GTFS_KRK_M package or to "MPK Kraków" or "Mobilis" for to-2015 and to-2022 styles.
            "is-route-changed": False
        },
        "schedule-config": {
            "schedule-format": "from-2023",         # possible values:                      to-2015   to-2022   in-2022   from-2023
            "schedule-route": directions_streets,
            "schedule-watermark": "Disabled",       # possible values:                      None   Disabled   Museum   Cemetery   Airport   Bike
            "museum-line": False,                   # extra description about old vehicles: True   False
            "valid-from": "31.08.2026",             # date format:                          DD.MM.YYYY
            "date-mode": "od"                       # possible values:                      od   w dniu
        },
        "route-config": directions_data
    }
    
    return output_json

# Because the GTFS packages doesn't have "time" section for departures, you must check the route on https://mpk.krakow.pl/rozklad-embed/ and rewrite mins on the left side of stop names by yourself.
# For example: the route has three stops, the first stop has "0 min", the second stop has "2 min" and the last (third) stop has "3 min".
# Code should be like this:
# 
# TRAVEL_TIME = {
#    "direction-0": [0, 2, 3],
# }
# 
# But remember to check that it's correct direction number. The easiest way to check it is generating the json and checking route-config section.
# There you can see the first stop and then you know the direction-X number. The same thing is with with streets and streets with loops.

TRAVEL_TIME = {
    "direction-0": [0, 1, 2, 3, 4, 6, 7, 8, 10, 12, 14, 16, 18, 21, 22, 25, 26, 28, 30, 32, 35, 37, 38, 39],
    "direction-1": [0, 1, 2, 3, 6, 8, 9, 11, 13, 15, 17, 18, 21, 23, 24, 26, 28, 31, 32, 33, 35, 37, 38, 39, 40]
}

# All days
# Please uncomment code below to apply it or comment (by adding "#" before text) for disapply:

# --- COMMENT / UNCOMMENT SECTION BELOW ---

json_all = generate_line_json("3", day_mode="all", custom_times=TRAVEL_TIME)                      # change "3" for any line number you want
with open("3.json", "w", encoding="utf-8") as f:                                                  # change "3" for any line number you want
    json.dump(json_all, f, ensure_ascii=False, indent=4)

# ---  COMMENT / UNCOMMENT SECTION END  ---


# Only weekdays (for bigger schedules)
# Please uncomment code below to apply it or comment (by adding "#" before text) for disapply:

# --- COMMENT / UNCOMMENT SECTION BELOW ---

# json_powszednie = generate_line_json("3", day_mode="weekdays", custom_times=TRAVEL_TIME)          # change "3" for any line number you want
# with open("3_dp.json", "w", encoding="utf-8") as f:                                               # change "3_dp" for any line number + "_dp" (for easy name for weekdays) you want
#     json.dump(json_powszednie, f, ensure_ascii=False, indent=4)

# ---  COMMENT / UNCOMMENT SECTION END  ---


# Only weekends (for bigger schedules)
# Please uncomment code below to apply it or comment (by adding "#" before text) for disapply:

# --- COMMENT / UNCOMMENT SECTION BELOW ---

# json_soboty_swieta = generate_line_json("3", day_mode="weekends", custom_times=TRAVEL_TIME)       # change "3" for any line number you want
# with open("3_sś.json", "w", encoding="utf-8") as f:                                               # change "3_sś" for any line number + "_sś" (for easy name for weekends) you want
#     json.dump(json_soboty_swieta, f, ensure_ascii=False, indent=4)

# ---  COMMENT / UNCOMMENT SECTION END  ---
