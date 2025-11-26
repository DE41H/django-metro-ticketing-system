import os
from django.core.management.base import BaseCommand
from django.db import transaction, IntegrityError
from stations.models import Station, Line
import csv

COLOR_MAP = {
    "Red Line": "#FF0000",
    "Yellow Line": "#FFFF00",
    "Blue Line": "#0000FF",
    "Green Line": "#008000",
    "Violet Line": "#EE82EE",
    "Pink Line": "#FF69B4",
    "Magenta Line": "#FF00FF",
    "Grey Line": "#808080",
    "Airport Express": "#FFA500",
}

def parse_stations_csv(stations_file_path):
    uid_to_name_map = {}
    raw_station_m2m_data = {}
    stations_to_create = []

    with open(stations_file_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                uid = int(row["uid"])
                name = row["name"].strip()
                neighbours = row["neighbours"].split('|') if row["neighbours"] else []
                neighbours = [int(n) for n in neighbours if n]
                uid_to_name_map[uid] = name
                raw_station_m2m_data[uid] = neighbours
                stations_to_create.append(Station(pk=uid, name=name))
            except Exception as e:
                print(f"[Warn] Skipping malformed station row: {row} -- {e}")
                continue
    return stations_to_create, uid_to_name_map, raw_station_m2m_data

def parse_lines_csv(lines_file_path):
    lines_to_create = []
    raw_line_data = []

    with open(lines_file_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                name = row["name"].strip()
                raw_stations = row["stations"].split('|') if row["stations"] else []
                raw_stations = [int(s) for s in raw_stations if s]
                line_obj = Line(pk=name, name=name, color=COLOR_MAP.get(name, "#000000"))
                lines_to_create.append(line_obj)
                raw_line_data.append({"line_object": line_obj, "station_uids": raw_stations})
            except Exception as e:
                print(f"[Warn] Skipping malformed line row: {row} -- {e}")
                continue
    return lines_to_create, raw_line_data

def run_populate_logic(stations_file_path, lines_file_path):
    print("[Step] Parsing stations.csv...")
    stations_to_create, uid_to_name_map, raw_station_m2m_data = parse_stations_csv(stations_file_path)
    Station.objects.bulk_create(stations_to_create)
    name_to_station_object = {station.pk: station for station in Station.objects.filter(pk__in=uid_to_name_map.keys())}
    print(f"[Info] Created {len(name_to_station_object)} stations.")

    print("[Step] Parsing lines.csv...")
    lines_to_create, raw_line_data = parse_lines_csv(lines_file_path)
    Line.objects.bulk_create(lines_to_create)
    name_to_line_object = {line.name: line for line in lines_to_create}
    print(f"[Info] Created {len(name_to_line_object)} lines.")

    # Set line-to-station relationships
    for item in raw_line_data:
        line_obj = name_to_line_object.get(item["line_object"].pk)
        station_objs = [name_to_station_object.get(uid) for uid in item["station_uids"] if uid in name_to_station_object]
        station_objs = [obj for obj in station_objs if obj]
        if line_obj and station_objs:
            line_obj.stations.set(station_objs)
    print("[Info] Set line-to-station relationships.")

    # Set station neighbours relationships
    for uid, neighbour_uids in raw_station_m2m_data.items():
        station_obj = name_to_station_object.get(uid)
        neighbour_objs = [name_to_station_object.get(nuid) for nuid in neighbour_uids if nuid in name_to_station_object]
        neighbour_objs = [obj for obj in neighbour_objs if obj]
        if station_obj and neighbour_objs:
            station_obj.neighbours.set(neighbour_objs)
    print("[Info] Set station neighbour relationships.")
    print("[Success] Data population complete.")

class Command(BaseCommand):
    help = "Populates the database with initial metro station and line data, safely and robustly."

    @transaction.atomic
    def handle(self, *args, **options):
        stations_file_path = os.path.join(os.path.dirname(__file__), "stations.csv")
        lines_file_path = os.path.join(os.path.dirname(__file__), "lines.csv")

        if not os.path.exists(stations_file_path) or not os.path.exists(lines_file_path):
            self.stderr.write("[ERROR] stations.csv or lines.csv not found in the command directory.")
            return

        station_count = Station.objects.count()
        line_count = Line.objects.count()
        if station_count > 0 or line_count > 0:
            self.stdout.write(self.style.WARNING(
                f"Population skipped: Station records ({station_count}), Line records ({line_count}) already exist."
            ))
            return

        try:
            self.stdout.write(self.style.NOTICE("Starting population of metro database..."))
            run_populate_logic(stations_file_path, lines_file_path)
            self.stdout.write(self.style.SUCCESS("Database populated successfully."))
        except IntegrityError as e:
            self.stderr.write(f"[ERROR] Integrity error during population: {e}")
            raise
        except Exception as e:
            self.stderr.write(f"[ERROR] Unexpected error: {e}")
            raise
