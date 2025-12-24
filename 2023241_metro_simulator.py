# 2023241_metro_simulator.py
# Bidirectional metro arrival calculator.
# Produces next arrivals for BOTH directions (start->end and end->start).

def metro_timing_module():
    main_timing()

METRO_FILE = "metro_data.txt"

# metro start and end timing
START_TIME_HHMM = (6, 0)   # 06:00
END_TIME_HHMM   = (23, 0)  # 23:00

# metro frequency periods and timing
PEAK_PERIODS = [((8,0),(10,0)), ((17,0),(19,0))]
PEAK_FREQ_MIN = 4
OFFPEAK_FREQ_MIN = 8

# Convert an (hour, minute) tuple into "minutes since midnight"
def hhmm_to_minutes(hhmm):
    h, m = hhmm
    return h * 60 + m

# Convert minutes since midnight into 'HH:MM' 24-hour formatted string.
# Keeps values wrapped inside 24-hour limit using modulus.
def minutes_to_hhmm_str(total_min):
    total_min = total_min % (24*60)
    h = total_min // 60
    m = total_min % 60
    return f"{h:02d}:{m:02d}"

# Parse a 'HH:MM' string and return (hour, minute) tuple.
# Does not combine to minutes-of-day; helper function used by another helper.
def time_str_to_minutes(s):
    s = s.strip()
    if ':' not in s:
        raise ValueError("Time must be HH:MM")
    parts = s.split(':')
    h = int(parts[0])
    m = int(parts[1])
    return h * 60 + m

# Return True if a given minute-of-day lies inside any defined peak interval.
def in_peak(min_of_day):
    for (sh, sm), (eh, em) in PEAK_PERIODS:
        start = hhmm_to_minutes((sh, sm))
        end   = hhmm_to_minutes((eh, em))
        if start <= min_of_day < end:
            return True
    return False


# Build and return a sorted list of departure times (in minutes since midnight) for trains departing from a terminal during the day, based on the peak/off-peak frequency rules and the global start/end times.
def build_departure_schedule():
    schedule = []
    cur = hhmm_to_minutes(START_TIME_HHMM)
    end = hhmm_to_minutes(END_TIME_HHMM)
    while cur <= end:
        schedule.append(cur)
        freq = PEAK_FREQ_MIN if in_peak(cur) else OFFPEAK_FREQ_MIN
        cur += freq
    return schedule


# Parse the metro data text file and return: lines, graph and station_index
def parse_metro_file(path):
    lines = {}
    current_section = None
    with open(path, 'r', encoding='utf-8') as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            # Section header
            if line.startswith('[') and line.endswith(']'):
                current_section = line[1:-1].strip()
                lines[current_section] = {
                    'header': current_section,
                    'info': {},
                    'stations': []  # (station_name, time_to_next)
                }
                continue

            if current_section is None:
                # ignore lines before any section
                continue

            # Info lines like: Info: Start_Point=Dwarka Sector 21
            if line.startswith('Info:'):
                try:
                    _, rest = line.split(':',1)
                    k, v = rest.strip().split('=',1)
                    lines[current_section]['info'][k.strip()] = v.strip()
                except:
                    pass
                continue
            
            # Skip format header lines like: "Format: Station Name | Approx Time to Next | ..."
            if line.lower().startswith("format:"):
                continue
            
            # Station data lines - split by '|' and take first two fields (name, time_to_next)
            if '|' in line:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 2:
                    station_name = parts[0]
                    try:
                        time_to_next = int(parts[1])
                    except:
                        time_to_next = 0
                    lines[current_section]['stations'].append((station_name, time_to_next))
    # build offsets from start and from end
    for sec, data in lines.items():
        offsets_start = []
        cum = 0
        for (st, t) in data['stations']:
            offsets_start.append((st, cum))
            cum += t
        data['station_offsets_from_start'] = offsets_start
        # offsets from end: compute distances measured from final station as 0
        offsets_end = []
        # total length:
        total = sum(t for _, t in data['stations'])
        # For each station, offset_from_end = total - offset_from_start
        for st, off in offsets_start:
            off_from_end = total - off
            offsets_end.append((st, off_from_end))
        data['station_offsets_from_end'] = offsets_end
        # store start and end station names
        if data['stations']:
            data['line_start'] = data['stations'][0][0]
            data['line_end']   = data['stations'][-1][0]
        else:
            data['line_start'] = data['line_end'] = None

    print("LOADED LINES:", list(lines.keys()))

    return lines


def levenshtein(a, b):
    """Compute Levenshtein distance between strings a and b."""
    # Used to allow small-typo matching (e.g., 'voilet' -> 'violet').
    a = a or ""
    b = b or ""
    n, m = len(a), len(b)
    if n == 0: return m
    if m == 0: return n
    # create 2 rows only to save memory
    prev = list(range(m+1))
    cur  = [0] * (m+1)
    for i in range(1, n+1):
        cur[0] = i
        ai = a[i-1]
        for j in range(1, m+1):
            cost = 0 if ai == b[j-1] else 1
            cur[j] = min(prev[j] + 1,        # deletion
                         cur[j-1] + 1,      # insertion
                         prev[j-1] + cost)  # substitution
        prev, cur = cur, prev
    return prev[m]

def normalize_string(s):
    # lower, strip punctuation-ish chars, collapse spaces for better comparison
    return ''.join(ch for ch in s.lower() if ch.isalnum() or ch.isspace()).strip()

def find_best_line_match(lines_dict, user_line_input):
    u = user_line_input.strip()
    if not u:
        return None

    # 1) exact case-insensitive match
    for key in lines_dict:
        if u.lower() == key.lower():
            return key

    # 2) substring match (case-insensitive)
    substr_matches = [k for k in lines_dict if u.lower() in k.lower() or k.lower() in u.lower()]
    if len(substr_matches) == 1:
        return substr_matches[0]
    if len(substr_matches) > 1:
        # prefer startswith or the shortest name
        for k in substr_matches:
            if k.lower().startswith(u.lower()):
                return k
        return substr_matches[0]

    # 3) fuzzy match using normalized Levenshtein distance
    u_norm = normalize_string(u)
    best_key = None
    best_dist = None
    for key in lines_dict:
        key_norm = normalize_string(key)
        d = levenshtein(u_norm, key_norm)
        if best_dist is None or d < best_dist:
            best_dist = d
            best_key = key

    # Decide threshold: accept only if distance is reasonably small relative to length
    if best_dist is not None:
        # threshold example: allow up to 30% of the length (rounded) or at most 3 edits
        max_allowed = max(1, min(3, len(normalize_string(best_key)) // 3))
        if best_dist <= max_allowed:
            return best_key

    # no good match
    return None


def find_station_offsets(line_data, station_name):
    sname = station_name.strip().lower()
    # exact match first
    for st, off in line_data['station_offsets_from_start']:
        if sname == st.lower():
            # find corresponding offsets from end too
            off_end = next((oe for s2, oe in line_data['station_offsets_from_end'] if s2 == st), None)
            return (off, off_end, st)
    # partial match
    candidates = []
    for st, off in line_data['station_offsets_from_start']:
        if sname in st.lower():
            off_end = next((oe for s2, oe in line_data['station_offsets_from_end'] if s2 == st), None)
            candidates.append((off, off_end, st))
    if candidates:
        # prefer startswith
        for off, off_end, st in candidates:
            if st.lower().startswith(sname):
                return (off, off_end, st)
        return candidates[0]
    return (None, None, None)

def compute_next_arrivals(departures_from_endpoint, station_offset, current_min, max_results=6):

#     Given a series of departure times (minutes since midnight) from an endpoint,
#     compute the next arrival times at the station (arrival = departure + station_offset).
#     Filters arrivals outside operating hours and returns up to max_results upcoming arrivals.

    arrivals = []
    end_day = hhmm_to_minutes(END_TIME_HHMM)
    for dep in departures_from_endpoint:
        arr_time = dep + station_offset
        if arr_time < hhmm_to_minutes(START_TIME_HHMM):
            continue
        if arr_time > end_day:
            continue
        if arr_time >= current_min:
            arrivals.append(arr_time)
            if len(arrivals) >= max_results:
                break
    return arrivals

def shift_schedule_for_endpoint(departure_schedule, endpoint_offset=0):

    # If departures are generated as minutes-of-day when trains leave "line start"
    # and we want departures from the END endpoint we can treat each depot as having
    # its own departure schedule. Simpler: build identical schedule for both endpoints.
    # For now we return a copy (they are departures measured from 00:00 of day).

    return list(departure_schedule)

def main_timing():
    lines = parse_metro_file(METRO_FILE)
    if not lines:
        print("Couldn't parse metro file or file is empty.")
        return

    print("Enter Line (e.g., BLUE LINE - BRANCH, MAGENTA LINE, BLUE LINE - MAIN, RED LINE, YELLOW LINE, PINK LINE, VOILET LINE):")
    user_line = input().strip()
    chosen_line_key = find_best_line_match(lines, user_line)
    if not chosen_line_key:
        print("No matching line found.")
        return
    line_data = lines[chosen_line_key]

    print("Enter Station (exact or partial name):")
    user_station = input().strip()
    off_start, off_end, station_realname = find_station_offsets(line_data, user_station)
    if off_start is None:
        print("Station not found on line. Available (sample):")
        for st, _ in line_data['station_offsets_from_start'][:20]:
            print(" -", st)
        return

    print("Enter current time HH:MM (24-hour Format, e.g., 09:18):")
    try:
        user_time_str = input().strip()
        current_min = time_str_to_minutes(user_time_str)
    except:
        print("Invalid time format.")
        return

    start_min = hhmm_to_minutes(START_TIME_HHMM)
    end_min = hhmm_to_minutes(END_TIME_HHMM)
    if current_min > end_min:
        print("No more metros today (after end time).")
        return
    if current_min < start_min:
        print(f"Service hasn't started. First trains at {minutes_to_hhmm_str(start_min)}.")
        current_min = start_min

    departures = build_departure_schedule()
    # For both endpoints we just use same schedule of departures (trains start regularly from both ends)
    departures_from_start = shift_schedule_for_endpoint(departures)
    departures_from_end   = shift_schedule_for_endpoint(departures)

    # For 'start -> end', station arrival = departure_from_start + offset_from_start
    arrivals_forward = compute_next_arrivals(departures_from_start, off_start, current_min, max_results=6)
    # For 'end -> start', station arrival = departure_from_end + offset_from_end
    # but note offset_from_end was computed as (total - offset_from_start). To get correct arrival
    # when a train departs the END at minute D, arrival_time = D + offset_from_end_distance_from_end_to_station.
    arrivals_reverse = compute_next_arrivals(departures_from_end, off_end, current_min, max_results=6)

    # Direction labels using line endpoints
    dir_to_end_label = f"towards {line_data.get('line_end','END')}"
    dir_to_start_label = f"towards {line_data.get('line_start','START')}"

    print()
    print(f"Line: {chosen_line_key}")
    print(f"Station: {station_realname}")
    print(f"Current time: {minutes_to_hhmm_str(current_min)}")
    print()

    if arrivals_forward:
        print(f"Trains {dir_to_end_label}:")
        print("  " + ", ".join(minutes_to_hhmm_str(a) for a in arrivals_forward))
    else:
        print(f"No more trains {dir_to_end_label} today.")

    if arrivals_reverse:
        print(f"\nTrains {dir_to_start_label}:")
        print("  " + ", ".join(minutes_to_hhmm_str(a) for a in arrivals_reverse))
    else:
        print(f"\nNo more trains {dir_to_start_label} today.")



def ride_journey_planner():
    main_ride()

# journey_plan_distance_fare.py
# Reads /mnt/data/metro_data.txt (expects Distance(km) as last column)
# Prints compact journey plan and computes total distance + fare based on distance.

METRO_FILE = "metro_data.txt"

# timing constants (minutes)
DWELL_TIME = 0.5        # 30 seconds boarding dwell
INTERCHANGE_TIME = 2  # 30 seconds transfer/walking
START_SERVICE = (6,0)
END_SERVICE = (23,0)
PEAK_PERIODS = [((8,0),(10,0)), ((17,0),(19,0))]
PEAK_FREQ = 4
OFFPEAK_FREQ = 8

# -------------------- time helpers --------------------
def hhmm_to_min(hm): return hm[0]*60 + hm[1]

def min_to_hhmm(m):
    m = int(round(m)) % (24*60)
    return f"{m//60:02d}:{m%60:02d}"

def time_str_to_min(s):
    s = s.strip()
    if ':' not in s: raise ValueError("Time must be HH:MM")
    a,b = s.split(':'); return int(a)*60 + int(b)

def in_peak(x):
    for (sh,sm),(eh,em) in PEAK_PERIODS:
        if hhmm_to_min((sh,sm)) <= x < hhmm_to_min((eh,em)): return True
    return False

def min_to_ampm(m):
    """Convert minutes-of-day (int) -> 'HH:MM AM/PM' string."""
    m = int(round(m)) % (24*60)
    h = m // 60
    mm = m % 60
    suffix = "AM" if h < 12 else "PM"
    h12 = h % 12
    if h12 == 0:
        h12 = 12
    return f"{h12:02d}:{mm:02d} {suffix}"


# -------------------- parse metro file (reads distance field) --------------------
def parse_metro_file2(path):
    lines = {}
    cur = None
    with open(path, 'r', encoding='utf-8') as f:
        for raw in f:
            line = raw.strip()
            if not line: continue
            if line.startswith('[') and line.endswith(']'):
                cur = line[1:-1].strip()
                lines[cur] = {'stations': [], 'info': {}}
                continue
            if cur is None: continue
            if line.lower().startswith('info:'):
                try:
                    _, rest = line.split(':',1)
                    k,v = rest.strip().split('=',1)
                    lines[cur]['info'][k.strip()] = v.strip()
                except: pass
                continue
            if line.lower().startswith('format:'): continue
            if '|' in line:
                parts = [p.strip() for p in line.split('|')]
                # Expect at least 6 parts now: name, time, interchange, layout, parking, distance
                while len(parts) < 6: parts.append('-')
                name = parts[0]
                try: tnext = float(parts[1])
                except: tnext = 0.0
                inter = parts[2] if parts[2] else '-'
                layout = parts[3] if parts[3] else '-'
                parking = parts[4] if parts[4] else '-'
                # distance (km)
                try:
                    dist = float(parts[5]) if parts[5] not in ('-', '') else 0.0
                except:
                    dist = 0.0
                lines[cur]['stations'].append({
                    'name': name,
                    'time': tnext,
                    'interchange': inter,
                    'layout': layout,
                    'parking': parking,
                    'distance': dist
                })
    # build quick lookup index and offsets
    station_index = {}
    for lname, data in lines.items():
        cum = 0.0
        offsets = {}
        for s in data['stations']:
            station_index.setdefault(s['name'], []).append(lname)
            offsets[s['name']] = cum
            cum += s['time']
        data['offsets_from_start'] = offsets
        data['total_length'] = cum
    return lines, station_index

# -------------------- schedule helpers --------------------
def build_departures():
    deps = []
    cur = hhmm_to_min(START_SERVICE)
    end = hhmm_to_min(END_SERVICE)
    while cur <= end:
        deps.append(cur)
        cur += PEAK_FREQ if in_peak(cur) else OFFPEAK_FREQ
    return deps

def next_train_at_station_for_direction(line_stations, station_name, current_min, towards_end=True):
    departures = build_departures()
    offsets = {}
    cum = 0.0
    for s in line_stations:
        offsets[s['name']] = cum
        cum += s['time']
    total = cum
    if towards_end:
        off = offsets.get(station_name, 0.0)
        for d in departures:
            arr = d + off
            if arr >= current_min: return arr
    else:
        off_from_end = total - offsets.get(station_name, 0.0)
        for d in departures:
            arr = d + off_from_end
            if arr >= current_min: return arr
    return None

# -------------------- formatting & meta --------------------
def pretty_line(line_header):
    base = line_header.split('-')[0].strip()
    return base.title()

def normalize_parking(val):
    if not val or val.strip() in ('-', ''): return "No"
    low = val.strip().lower()
    if low in ('available','yes','y','true'): return "Yes"
    return "No"

def get_station_meta(lines_data, station):
    """Return (layout, parking, sample_line_header, distance_at_station) for the station (first found)."""
    for ln, data in lines_data.items():
        for s in data['stations']:
            if s['name'] == station:
                return (s.get('layout','-'), normalize_parking(s.get('parking','-')), ln, s.get('distance', 0.0))
    return ("-","No","", 0.0)

# -------------------- single-line trip calculator --------------------
def calculate_single_line_trip(lines_data, line_name, start_station, end_station):
    stations = lines_data[line_name]['stations']
    idx_a = -1; idx_b = -1
    for i,s in enumerate(stations):
        if s['name'] == start_station: idx_a = i
        if s['name'] == end_station: idx_b = i
    if idx_a == -1 or idx_b == -1:
        return None, 99999.0
    path = []; time = 0.0
    if idx_a < idx_b:
        subset = stations[idx_a: idx_b + 1]
        for i in range(len(subset)-1):
            path.append(subset[i]['name'])
            time += float(subset[i]['time']) + DWELL_TIME
        path.append(subset[-1]['name'])
    else:
        subset = stations[idx_b: idx_a + 1]
        subset = list(reversed(subset))
        for i in range(len(subset)-1):
            path.append(subset[i]['name'])
            time += float(subset[i]['time']) + DWELL_TIME
        path.append(subset[-1]['name'])
    return path, time

# -------------------- distance helpers --------------------
def compute_distance_on_line(lines_data, line_name, start_station, end_station):
    """Sum distances (km) along line segments between start and end (order-aware)."""
    stations = lines_data[line_name]['stations']
    # build list of station names and distances (distance is distance to NEXT from that station)
    names = [s['name'] for s in stations]
    # find indices
    try:
        i_start = names.index(start_station)
        i_end = names.index(end_station)
    except ValueError:
        return 0.0
    total = 0.0
    if i_start <= i_end:
        # sum distance field for stations i_start .. i_end-1 (distance values are per station to next)
        for i in range(i_start, i_end):
            total += float(stations[i].get('distance', 0.0))
    else:
        # reverse direction: sum distances from i_end .. i_start-1
        for i in range(i_end, i_start):
            total += float(stations[i].get('distance', 0.0))
    return total

# -------------------- fare by distance (slab) --------------------
def fare_by_distance_km(dist_km):
    # Slab-based fare (example table). Adjust if you have a specific tariff.
    if dist_km <= 2.0: return 10
    if dist_km <= 5.0: return 20
    if dist_km <= 12.0: return 30
    if dist_km <= 21.0: return 40
    if dist_km <= 32.0: return 50
    return 60

# -------------------- planner (compact output) --------------------
def plan_journey_compact(lines_data, station_index, src_pref, dst_pref, start_time_str):
    # match prefix to exact station name (case-insensitive)
    def match_station(pref):
        pref_l = pref.strip().lower()
        # prefer exact match
        for s in station_index.keys():
            if s.lower() == pref_l:
                return s
        for s in station_index.keys():
            if s.lower().startswith(pref_l):
                return s
        return None

    src = match_station(src_pref)
    dst = match_station(dst_pref)
    if not src or not dst:
        print("❌ Station not found.")
        return

    src_lines = station_index[src]
    dst_lines = station_index[dst]

    best_path = []
    min_time = 99999.0
    best_plan = None

    # Direct route journey planner
    common = set(src_lines).intersection(dst_lines)
    for ln in common:
        path, dur = calculate_single_line_trip(lines_data, ln, src, dst)
        if dur < min_time:
            min_time = dur; best_path = path; best_plan = ('direct', ln)

    # Single transfer
    for la in src_lines:
        for lb in dst_lines:
            if la == lb: continue
            sta_a = [s['name'] for s in lines_data[la]['stations']]
            sta_b = [s['name'] for s in lines_data[lb]['stations']]
            possible_interchanges = set(sta_a).intersection(sta_b)
            # consider interchange tokens on line la
            for s in lines_data[la]['stations']:
                tok = s.get('interchange','').strip()
                if tok and tok != '-':
                    for item in [t.strip() for t in tok.split(',') if t.strip()]:
                        if item in sta_b: possible_interchanges.add(item)
                        for linekey in lines_data.keys():
                            if item.lower() in linekey.lower():
                                for s2 in lines_data[linekey]['stations']:
                                    if s2['name'] in sta_b and s2['name'] in sta_a:
                                        possible_interchanges.add(s2['name'])
            for transfer_point in possible_interchanges:
                path1, t1 = calculate_single_line_trip(lines_data, la, src, transfer_point)
                path2, t2 = calculate_single_line_trip(lines_data, lb, transfer_point, dst)
                total = t1 + INTERCHANGE_TIME + t2
                if total < min_time:
                    min_time = total
                    best_path = path1 + path2[1:]
                    best_plan = ('transfer', la, lb, transfer_point)

    if min_time == 99999.0:
        print("❌ No route found (Direct or Single Transfer).")
        return
    
    
    # schedule-aware times
    start_min = time_str_to_min(start_time_str)
    service_start_min = hhmm_to_min(START_SERVICE)
    service_end_min   = hhmm_to_min(END_SERVICE)

    # If request is outside service hours — inform user and STOP (no journey printed)
    if start_min < service_start_min or start_min > service_end_min:
        print(f"⚠ Requested time {min_to_hhmm(start_min)} is outside service hours.")
        print(f"   Metro service runs from {min_to_ampm(service_start_min)} TO {min_to_ampm(service_end_min)}.")
        return



    # print compact journey plan
    print("\nJourney Plan:")

    if best_plan[0] == 'direct':
        _, line_used = best_plan
        # start meta
        layout_src, parking_src, ln_src, _ = get_station_meta(lines_data, src)
        print(f"Start at {src} ({pretty_line(ln_src)}), layout - {layout_src}, Parking - {parking_src}")

        # direction
        stations = [s['name'] for s in lines_data[line_used]['stations']]
        if len(best_path) >= 2:
            towards_end = stations.index(best_path[1]) > stations.index(src)
        else:
            towards_end = True

        next_arr = next_train_at_station_for_direction(lines_data[line_used]['stations'], src, start_min, towards_end)
        if next_arr is None:
            print("Next metro at: No service")
            return
        print(f"Next metro at {min_to_hhmm(next_arr)}")

        # compute arrival time at destination using offsets (minutes)
        offsets = lines_data[line_used]['offsets_from_start']
        travel_offset = abs(offsets.get(best_path[-1], 0.0) - offsets.get(src, 0.0))
        arrival_time = next_arr + travel_offset + DWELL_TIME


        # destination meta
        layout_dst, parking_dst, ln_dst, _ = get_station_meta(lines_data, best_path[-1])
        print(f"Arrive at {best_path[-1]} at {min_to_hhmm(arrival_time)}, layout - {layout_dst}, Parking - {parking_dst}")

        # compute distance (sum distances along line)
        dist_km = compute_distance_on_line(lines_data, line_used, src, best_path[-1])
        print(f"Total distance: {dist_km:.2f} km")

        # fare by distance slabs
        fare = fare_by_distance_km(dist_km)
        # actual travel time (schedule-aware)
        total_minutes = int(round(arrival_time - start_min))
        print(f"Total travel time: {total_minutes} minutes")
        print(f"Fare: ₹{fare}")
        return

    # transfer case
    _, la, lb, transfer_point = best_plan
    layout_src, parking_src, ln_src, _ = get_station_meta(lines_data, src)
    print(f"Start at {src} ({pretty_line(ln_src)}), layout - {layout_src}, Parking - {parking_src}")

    # first leg next train
    stations_a = [s['name'] for s in lines_data[la]['stations']]
    idx_src = stations_a.index(src); idx_transfer = stations_a.index(transfer_point)
    towards_end_a = idx_transfer > idx_src
    next_arr_src = next_train_at_station_for_direction(lines_data[la]['stations'], src, start_min, towards_end_a)
    if next_arr_src is None:
        print("Next metro at: No service")
        return
    print(f"Next metro at {min_to_hhmm(next_arr_src)}")
    

    # arrival at transfer (minutes using offsets)
    offsets_a = lines_data[la]['offsets_from_start']
    travel_offset_a = abs(offsets_a.get(transfer_point, 0.0) - offsets_a.get(src, 0.0))
    arrival_transfer_time = next_arr_src + travel_offset_a + DWELL_TIME
    layout_tf, parking_tf, ln_tf, _ = get_station_meta(lines_data, transfer_point)
    print(f"Arrive at {transfer_point} at {min_to_hhmm(arrival_transfer_time)}, layout - {layout_tf}, Parking - {parking_tf}")

    # transfer print
    print(f"Transfer to {pretty_line(lb)}")
    ready_for_line2 = arrival_transfer_time + INTERCHANGE_TIME

    # next train on second line
    stations_b = [s['name'] for s in lines_data[lb]['stations']]
    idx_transfer_b = stations_b.index(transfer_point); idx_dest_b = stations_b.index(best_path[-1])
    towards_end_b = idx_dest_b > idx_transfer_b
    next_arr_b = next_train_at_station_for_direction(lines_data[lb]['stations'], transfer_point, ready_for_line2, towards_end_b)
    if next_arr_b is None:
        print("Next connecting metro: No service")
        return
    print(f"Next {pretty_line(lb)} metro departs at {min_to_hhmm(next_arr_b)}, layout - {layout_tf}, Parking - {parking_tf}")

    # arrival at destination
    offsets_b = lines_data[lb]['offsets_from_start']
    travel_offset_b = abs(offsets_b.get(best_path[-1], 0.0) - offsets_b.get(transfer_point, 0.0))
    arrival_dest_time = next_arr_b + travel_offset_b + DWELL_TIME


    layout_dst, parking_dst, ln_dst, _ = get_station_meta(lines_data, best_path[-1])
    print(f"Arrive at {best_path[-1]} at {min_to_hhmm(arrival_dest_time)}, layout - {layout_dst}, Parking - {parking_dst}")

    # compute distance: sum legs' distances
    dist_a = compute_distance_on_line(lines_data, la, src, transfer_point)
    dist_b = compute_distance_on_line(lines_data, lb, transfer_point, best_path[-1])
    total_dist = dist_a + dist_b
    print(f"Total distance: {total_dist:.2f} km")

    fare = fare_by_distance_km(total_dist)
    total_minutes = int(round(arrival_dest_time - start_min))
    print(f"Total travel time: {total_minutes} minutes")
    print(f"Fare: ₹{fare}")
    return

# -------------------- interactive main --------------------
def main_ride():
    lines_data, station_index = parse_metro_file2(METRO_FILE)
    print("Using metro data file:", METRO_FILE)
    src = input("Source: ").strip()
    dst = input("Destination: ").strip()
    t = input("Time of travel (HH:MM In 24 Hour Format): ").strip()
    plan_journey_compact(lines_data, station_index, src, dst, t)




# ----- Main menu -----
def main():
    while True:
        print("\nSelect an option:")
        print("1) Metro Timings Module")
        print("2) Ride Journey Planner")
        print("0) Exit")
        choice = input("Enter choice (0/1/2): ").strip()
        if choice == '1':
            metro_timing_module()
        elif choice == '2':
            ride_journey_planner()
        elif choice == '0':
            print("Goodbye.")
            break
        else:
            print("Invalid choice. Try again.")

if __name__ == "__main__":
    main()



