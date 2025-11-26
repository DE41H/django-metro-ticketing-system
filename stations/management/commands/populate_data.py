# stations/management/commands/populate_data.py

from django.core.management.base import BaseCommand
from django.db import transaction, IntegrityError
from stations.models import Station, Line
import csv
from io import StringIO

# --------------------- Embedded Data ---------------------
# (Paste your full STATIONS_CSV, LINES_CSV, and COLOR_MAP here)
STATIONS_CSV = """uid,name,neighbours
1,AIIMS,29|52
2,Adarsh Nagar,67|8
..."""
LINES_CSV = """name,stations
Red Line,187|58|...
Yellow Line,176|172|...
..."""
COLOR_MAP = {
    'Red Line': '#FF0000', 'Yellow Line': '#FFFF00', 'Blue Line': '#0000FF',
    'Green Line': '#008000', 'Violet Line': '#EE82EE', 'Pink Line': '#FF69B4',
    'Magenta Line': '#FF00FF', 'Grey Line': '#808080', 'Airport Express': '#FFA500'
}

def run_populate_logic():
    # Step 1: Prepare mappings and temporary storage
    uid_to_name_map = {}
    name_to_station_object = {}
    raw_line_data = []
    raw_station_m2m_data = {}

    # Step 2: Parse the stations CSV
    print("[Step] Parsing stations.csv...")
    lines = [line.strip() for line in STATIONS_CSV.strip().split('\n') if line.strip()]
    for line in lines[1:]:  # skip header
        try:
            if '"' in line:
                row = next(csv.reader(StringIO(line)))
            else:
                row = [item.strip() for item in line.split(',')]
            if len(row) < 3:
                continue
            uid = int(row[0])
            name = row[1]
            neighbours_raw = row[2]
            uid_to_name_map[uid] = name
            raw_station_m2m_data[name] = [int(n) for n in neighbours_raw.split('|') if n]
        except Exception as e:
            print(f"[Warn] Skipping malformed station row: {line} -- {e}")
            continue

    # Step 3: Create Station objects (bulk, failsafe)
    stations_to_create = [Station(pk=name, name=name) for name in uid_to_name_map.values()]
    Station.objects.bulk_create(stations_to_create)
    for station in Station.objects.filter(pk__in=uid_to_name_map.values()):
        name_to_station_object[station.pk] = station
    print(f"[Info] Created {len(name_to_station_object)} stations.")

    # Step 4: Parse LINES_CSV and create Line objects
    lines_to_create = []
    lines_data = [line.strip() for line in LINES_CSV.strip().split('\n') if line.strip()][1:]
    for line in lines_data:
        try:
            parts = [part.strip() for part in line.split(',', 1)]
            if len(parts) < 2:
                continue
            name = parts[0]
            raw_stations = [int(s) for s in parts[1].split('|') if s]
            line_obj = Line(pk=name, name=name, color=COLOR_MAP.get(name, '#000000'))
            lines_to_create.append(line_obj)
            raw_line_data.append({'line_object': line_obj, 'station_uids': raw_stations})
        except Exception as e:
            print(f"[Warn] Skipping malformed line row: {line} -- {e}")
            continue
    Line.objects.bulk_create(lines_to_create)
    name_to_line_object = {line.name: line for line in lines_to_create}
    print(f"[Info] Created {len(name_to_line_object)} lines.")

    # Step 5: Set Line-to-Station relationships
    for item in raw_line_data:
        line_obj = name_to_line_object.get(item['line_object'].pk)
        station_names = [uid_to_name_map.get(uid) for uid in item['station_uids'] if uid in uid_to_name_map]
        station_objs = [name_to_station_object[n] for n in station_names if n in name_to_station_object]
        if line_obj and station_objs:
            line_obj.stations.set(station_objs)
    print("[Info] Set line-to-station relationships.")

    # Step 6: Set Station-to-Station neighbour M2M relationships
    for station_name, neighbour_uids in raw_station_m2m_data.items():
        station_obj = name_to_station_object.get(station_name)
        if not station_obj:
            continue
        neighbour_names = [uid_to_name_map.get(nuid) for nuid in neighbour_uids if nuid in uid_to_name_map]
        neighbour_objs = [name_to_station_object.get(name) for name in neighbour_names if name in name_to_station_object]
        neighbour_objs = [obj for obj in neighbour_objs if obj]
        station_obj.neighbours.set(neighbour_objs)
    print("[Info] Set station neighbour relationships.")
    print("[Success] Data population complete.")

class Command(BaseCommand):
    help = "Populates the database with initial metro station and line data, safely and robustly."

    @transaction.atomic
    def handle(self, *args, **options):
        # Robust existence checks before any writes
        station_count = Station.objects.count()
        line_count = Line.objects.count()
        if station_count > 0 or line_count > 0:
            self.stdout.write(self.style.WARNING(
                f"Population skipped: Station records ({station_count}), Line records ({line_count}) already exist."
            ))
            return

        try:
            self.stdout.write(self.style.NOTICE("Starting population of metro database..."))
            run_populate_logic()
            self.stdout.write(self.style.SUCCESS("Database populated successfully."))
        except IntegrityError as e:
            self.stderr.write(f"[ERROR] Integrity error during population: {e}")
            raise
        except Exception as e:
            self.stderr.write(f"[ERROR] Unexpected error: {e}")
            raise
