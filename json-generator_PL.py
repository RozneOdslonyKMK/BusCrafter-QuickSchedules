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
# Opis: Generator plików JSON dla szybkich rozkładów w stylu rozkładów tramwajowych/autobusowych na krakowskich przystankach.
# Strona: https://rokmk.pl/
# Strona projektu: https://github.com/RozneOdslonyKMK/BusCrafter-QuickSchedules/

# Copyright:
# (c) ROKMK 2026 - Wszelkie prawa zastrzeżone
# NIE rozpowszechniaj tego kodu na żadnych stronach.
# Ten program może być opublikowany gdziekolwiek TYLKO za zgodą jego właściciela.
# Proszę, NIE publikuj tego kodu nigdzie w całośni, ani we fragmentach.


# --- WAŻNE! ---
# Ten kod jest edytowalnym przykładem, który bez modyfikacji wygeneruje plik JSON dla tramwajowej linii 3, który jest ważny od 31.08.2026.



#####################################
# ||=============================|| #
# ||           Importy           || #
# ||=============================|| #
#####################################

# Upewnij się, że masz zainstalowanego Python-3 i wykonałeś polecenie "pip install pandas" w swoim terminalu.

import pandas as pd
import json

#####################################
# ||=============================|| #
# ||        Edytowalny Kod       || #
# ||=============================|| #
#####################################

path = "./GTFS_KRK_T/"     # Możesz zmienić "GTFS_KRK_T" (dla tramwajów) na "GTFS_KRK_A" (dla autobusów) albo na "GTFS_KRK_M" (dla autobusów Mobilisu)
routes = pd.read_csv(path + "routes.txt", dtype={'route_short_name': str, 'route_id': str})
trips = pd.read_csv(path + "trips.txt")
stop_times = pd.read_csv(path + "stop_times.txt", dtype={'departure_time': str})
stops = pd.read_csv(path + "stops.txt", dtype={'stop_id': str, 'stop_code': str, 'stop_desc': str})
calendar = pd.read_csv(path + "calendar.txt")

dni_powszednie = "Dni powszednie"     # Możesz zmienić "Dni powszednie" na "Dzień powszedni" dla styli sprzed 2022 roku (to-2015 oraz to-2022)
soboty = "Soboty"
swieta = "Święta"

def build_service_day_map(calendar_dates_path="calendar_dates.txt"):
    df = pd.read_csv(calendar_dates_path, dtype={'service_id': str})
    
    active_dates = df[df['exception_type'] == 1].copy()
    
    active_dates['dt'] = pd.to_datetime(active_dates['date'].astype(str), format='%Y%m%d')
    active_dates['dow'] = active_dates['dt'].dt.dayofweek
    
    service_map = {}
    
    for service_id, group in active_dates.groupby('service_id'):
        sid_upper = str(service_id).upper()
        
        if sid_upper.endswith('_SO'):
            service_map[service_id] = "Soboty"
            continue
        elif sid_upper.endswith('_SW'):
            service_map[service_id] = "Święta"
            continue
        elif any(sid_upper.endswith(suf) for suf in ['_PO', '_PN', '_WT', '_ŚR', '_CZ', '_PT']):
            service_map[service_id] = "Dni powszednie"
            continue

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
    line_str = str(line_number).strip()
    routes_clean = routes.copy()
    routes_clean['route_short_name'] = routes_clean['route_short_name'].astype(str).str.strip()
    
    matching_routes = routes_clean[routes_clean['route_short_name'] == line_str]
    if matching_routes.empty:
        return {}
    
    route = matching_routes.iloc[0]
    route_id = str(route['route_id']).strip()

    trips_clean = trips.copy()
    trips_clean['route_id'] = trips_clean['route_id'].astype(str).str.strip()
    trips_clean['trip_id'] = trips_clean['trip_id'].astype(str).str.strip()
    
    line_trips = trips_clean[trips_clean['route_id'] == route_id]
    if line_trips.empty:
        return {}

    st_clean = stop_times.copy()
    st_clean['trip_id'] = st_clean['trip_id'].astype(str).str.strip()
    st_clean['stop_id'] = st_clean['stop_id'].astype(str).str.strip()

    stops_clean = stops.copy()
    stops_clean['stop_id'] = stops_clean['stop_id'].astype(str).str.strip()

    merged_st = line_trips.merge(st_clean, on='trip_id', how='inner')
    if merged_st.empty:
        return {}

    merged = merged_st.merge(stops_clean, on='stop_id', how='inner')
    if merged.empty:
        return {}

    unique_dirs = merged['direction_id'].nunique()
    
    if unique_dirs < 2 and 'trip_headsign' in merged.columns:
        headsigns = merged['trip_headsign'].dropna().unique()
        headsign_to_dir = {hs: idx for idx, hs in enumerate(headsigns)}
        merged['computed_direction'] = merged['trip_headsign'].map(headsign_to_dir)
        group_column = 'computed_direction'
    else:
        group_column = 'direction_id'

    directions_data = {}
    directions_streets = {}
    
    for dir_idx, dir_group in merged.groupby(group_column):
        dir_key = f"direction-{int(dir_idx)}"
        
        sample_trip_id = dir_group.groupby('trip_id')['stop_sequence'].max().idxmax()
        sample_trip_stops = dir_group[dir_group['trip_id'] == sample_trip_id].sort_values('stop_sequence')
        
        headsign = dir_group['trip_headsign'].iloc[0] if 'trip_headsign' in dir_group and not pd.isna(dir_group['trip_headsign'].iloc[0]) else "Nieznany"
        
        dir_custom_times = None
        if custom_times and isinstance(custom_times, dict):
            dir_custom_times = custom_times.get(dir_key)
        
        stops_dict = {}
        stop_order = 1
        
        for _, stop_row in sample_trip_stops.iterrows():
            stop_id = str(stop_row['stop_id']).strip()
            stop_code = str(stop_row.get('stop_code', stop_id)).strip()
            stop_name = str(stop_row['stop_name']).strip()
            
            raw_desc = stop_row.get('stop_desc', '')
            stop_desc = "" if pd.isna(raw_desc) else str(raw_desc).split('.')[0].strip().zfill(2)

            full_stop_name = f"{stop_name} {stop_desc}".strip() if stop_desc else stop_name

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

                time_str = str(dep['departure_time']).strip()
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
                "name": full_stop_name,
                "code": stop_code,
                "on-demand": False,                 # Sprawdź wygenerowany plik JSON, ponieważ ta wartość jest zawsze false. Musisz zmienić "false" na "true" dla przystanków "on-demand" w wygenerowanym pliku JSON.
                "time": travel_time,
                "departures": departures_sorted,
                "departure-merges": {}
            }
            stop_order += 1

        if dir_key == "direction-0":
            route_streets = "NOWY BIEŻANÓW P+R - Ćwiklińskiej, Teligi, Wielicka, Na Zjeździe, Starowiślna, Westerplatte, Pawia, Prądnicka, Doktora Twardego - KROWODRZA GÓRKA P+R"                      # Ulice z pętlami dla pierwszego kierunku. Format:     PĘTLA 1 - Ulica 1, Ulica 2, Ulica 3 - PĘTLA 2
            streets = "Ćwiklińskiej, Teligi, Wielicka, Na Zjeździe, Starowiślna, Westerplatte, Pawia, Prądnicka, Doktora Twardego"                            # Tylko ulice dla pierwszego kierunku. Format:         Ulica 1, Ulica 2, Ulica 3
        if dir_key == "direction-1":
            route_streets = "KROWODRZA GÓRKA P+R - Ździebły-Danowskiego, Doktora Twardego, Prądnicka, Pawia, Westerplatte, Starowiślna, Na Zjeździe, Limanowskiego, Wielicka, Teligi, Ćwiklińskiej - NOWY BIEŻANÓW P+R"                      # Ulice z pętlami dla drugiego kierunku. Format:       PĘTLA 1 - Ulica 1, Ulica 2, Ulica 3 - PĘTLA 2
            streets = "Ździebły-Danowskiego, Doktora Twardego, Prądnicka, Pawia, Westerplatte, Starowiślna, Na Zjeździe, Limanowskiego, Wielicka, Teligi, Ćwiklińskiej"                            # Tylko ulice dla drugiego kierunku. Format:           Ulica 1, Ulica 2, Ulica 3
        if dir_key == "direction-2":
            route_streets = ""                      # Ulice z pętlami dla trzeciego kierunku. Format:      PĘTLA 1 - Ulica 1, Ulica 2, Ulica 3 - PĘTLA 2
            streets = ""                            # Tylko ulice dla trzeciego kierunku. Format:          Ulica 1, Ulica 2, Ulica 3
        if dir_key == "direction-3":
            route_streets = ""                      # Ulice z pętlami dla czwartego kierunku. Format:      PĘTLA 1 - Ulica 1, Ulica 2, Ulica 3 - PĘTLA 2
            streets = ""                            # Tylko ulice dla czwartego kierunku. Format:          Ulica 1, Ulica 2, Ulica 3
        if dir_key == "direction-4":
            route_streets = ""                      # Ulice z pętlami dla piątego kierunku. Format:        PĘTLA 1 - Ulica 1, Ulica 2, Ulica 3 - PĘTLA 2
            streets = ""                            # Tylko ulice dla piątego kierunku. Format:            Ulica 1, Ulica 2, Ulica 3
        if dir_key == "direction-5":
            route_streets = ""                      # Ulice z pętlami dla szóstego kierunku. Format:       PĘTLA 1 - Ulica 1, Ulica 2, Ulica 3 - PĘTLA 2
            streets = ""                            # Tylko ulice dla szóstego kierunku. Format:           Ulica 1, Ulica 2, Ulica 3
        if dir_key == "direction-6":
            route_streets = ""                      # Ulice z pętlami dla siódmego kierunku. Format:       PĘTLA 1 - Ulica 1, Ulica 2, Ulica 3 - PĘTLA 2
            streets = ""                            # Tylko ulice dla siódmego kierunku. Format:           Ulica 1, Ulica 2, Ulica 3

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
            "line-type": "",                        # Możesz tutaj wpisać "Aglomeracyjna" dla linii 2xx/3xx/9xx, albo "Czasowa" dla linii 7x/7xx, albo "Specjalna" dla linii LRx oraz linii muzealnych, albo "Tramwajowa" / "Autobusowa" dla linii WOŚP.
            "line-operator": "MPK S.A. w Krakowie", # Możesz zmienić "MPK S.A. w Krakowie" na "Mobilis sp. z o.o." dla paczki GTFS_KRK_M albo na "MPK Kraków" lub "Mobilis" dla styli to-2015 i to-2022.
            "is-route-changed": False
        },
        "schedule-config": {
            "schedule-format": "from-2023",         # możliwe wartości:                     to-2015   to-2022   in-2022   from-2023
            "schedule-route": directions_streets,
            "schedule-watermark": "Disabled",       # możliwe wartości:                     None   Disabled   Museum   Cemetery   Airport   Bike
            "museum-line": False,                   # dodatkowy opis o taborze zabytkowym:  True   False
            "valid-from": "31.08.2026",             # format daty:                          DD.MM.YYYY
            "date-mode": "od"                       # możliwe wartości:                     od   w dniu
        },
        "route-config": directions_data
    }
    
    return output_json

# Ponieważ paczki GTFS nie posiadają sekcji "time" dla odjazdów, musisz sprawdzić trasę na https://mpk.krakow.pl/rozklad-embed/ i przepisać samemu minuty po lewej od nazw przystanków.
# Na przykład: trasa ma trzy przystanki, pierwszy z nich ma "0 min", drugi ma "2 min" i ostatni (trzeci) ma "3 min".
# Kod powinien wyglądać w następujący sposób:
# 
# TRAVEL_TIME = {
#    "direction-0": [0, 2, 3],
# }
# 
# Ale pamiętaj, aby sprawdzić, poprawny numer kierunku. Najłatwieszym sposobem na to jest wygenerowanie pliku JSON i sprawdzenie sekcji route-config.
# Tam możesz zobaczyć pierwszy przystanek i wtedy będziesz znać numer direction-X. Ten sam sposób możesz wykorzystać przy wpisywaniu ulic i ulic z pętlami.

TRAVEL_TIME = {
    "direction-0": [0, 1, 2, 3, 4, 6, 7, 8, 10, 12, 14, 16, 18, 21, 22, 25, 26, 28, 30, 32, 35, 37, 38, 39],
    "direction-1": [0, 1, 2, 3, 6, 8, 9, 11, 13, 15, 17, 18, 21, 23, 24, 26, 28, 31, 32, 33, 35, 37, 38, 39, 40]
}

# Wszystkie dni
# Odkomentuj kod poniżej, aby go włączyć, albo zakomentuj go (dodając "#" na początku linijki), aby go wyłączyć:

# --- POCZĄTEK SEKCJI KOMENTOWANIA ---

json_all = generate_line_json("3", day_mode="all", custom_times=TRAVEL_TIME)                      # zmień "3" na dowolną linię
with open("3.json", "w", encoding="utf-8") as f:                                                  # zmień "3" na dowolną linię
    json.dump(json_all, f, ensure_ascii=False, indent=4)

# ---  KONIEC SEKCJI KOMENTOWANIA  ---


# Tylko Dni powszednie
# Odkomentuj kod poniżej, aby go włączyć, albo zakomentuj go (dodając "#" na początku linijki), aby go wyłączyć:

# --- POCZĄTEK SEKCJI KOMENTOWANIA ---

# json_powszednie = generate_line_json("3", day_mode="weekdays", custom_times=TRAVEL_TIME)          # zmień "3" na dowolną linię
# with open("3_dp.json", "w", encoding="utf-8") as f:                                               # zmień "3_dp" na dowolną linię + "dp" (dla łatwej organizacji nazw dla dni powszednich)
#     json.dump(json_powszednie, f, ensure_ascii=False, indent=4)

# ---  KONIEC SEKCJI KOMENTOWANIA  ---


# Tylko Soboty i Święta
# Odkomentuj kod poniżej, aby go włączyć, albo zakomentuj go (dodając "#" na początku linijki), aby go wyłączyć:

# --- POCZĄTEK SEKCJI KOMENTOWANIA ---

# json_soboty_swieta = generate_line_json("3", day_mode="weekends", custom_times=TRAVEL_TIME)       # zmień "3" na dowolną linię
# with open("3_sś.json", "w", encoding="utf-8") as f:                                               # zmień "3_sś" na dowolną linię + "_sś" (dla łatwej organizacji nazw dla weekendów)
#     json.dump(json_soboty_swieta, f, ensure_ascii=False, indent=4)

# --- POCZĄTEK SEKCJI KOMENTOWANIA ---
