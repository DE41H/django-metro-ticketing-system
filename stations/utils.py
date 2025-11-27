import os
import networkx as nx
from collections import deque
from hashlib import sha512
from pyvis.network import Network # type: ignore
from django.conf import settings
from django.db.models import Value, CharField, F
from django.db.models.functions import Concat, Cast
from .models import Station, Line

def calculate_route(start: Station, stop: Station) -> list[Station]:
    if start == stop:
        return [start]
    stations = {s.pk: s for s in Station.objects.all().prefetch_related('lines', 'neighbours')}
    queue = deque([start])
    parents: dict[Station, Station|None] = {start: None}
    visited = {start}
    while queue:
        current = queue.popleft()
        for neighbour in current.neighbours.all():
            line = Line.objects.filter(stations__name=current.name, is_running=True).filter(stations__name=neighbour.name, is_running=True).distinct().exists()
            if neighbour not in visited and line: # type: ignore
                visited.add(neighbour)
                parents[neighbour] = current
                if neighbour == stop:
                    return get_path(parents=parents, start=start, stop=stop)
    return []

def get_path(parents: dict[Station, Station|None], start: Station, stop: Station) -> list[Station]:
    path = []
    current = stop
    while current is not None:
        path.append(current)
        current = parents.get(current)
    return path[::-1]

def create_map(path: str) -> None:
    G: nx.Graph[str] = nx.Graph()
    all_stations = Station.objects.prefetch_related('lines', 'neighbours')
    for station in all_stations:
        lines = ', '.join([line.name for line in station.lines.all()])
        G.add_node(station.name, label=station.name, title=f'Lines: {lines}', size=15, font={'size': 30, 'vadjust': 5})
    for station in Station.objects.all():
        for neighbour in station.neighbours.all():
            if not G.has_edge(station.pk, neighbour.pk):
                line = Line.objects.filter(stations__name=station.name).filter(stations__name=neighbour.name).distinct().first()
                G.add_edge(station.pk, neighbour.pk, color=line.color) # type: ignore
    net = Network(height='1000px', width='100%', notebook=True)
    net.from_nx(G)
    net.save_graph(path)

def get_map_url() -> str:
    maps_dir = os.path.join(settings.MEDIA_ROOT, 'maps')
    os.makedirs(maps_dir, exist_ok=True)
    filename = f'{get_hash()}.html'
    path = os.path.join(maps_dir, filename)
    if not os.path.exists(path):
        create_map(path=path)
    return f'{settings.MEDIA_URL}maps/{filename}'

def get_hash() -> str:
    lines_qs = Line.objects.annotate(
        config_string=Concat(
            Value('LINE_CONF:'), F('name'), Value('|'), F('color'),
            Value('|'), Cast(F('is_running'), CharField()),
            Value('|'), Cast(F('allow_ticket_purchase'), CharField()),
            output_field=CharField()
        )
    ).values_list('config_string', flat=True)
    stations_qs = Station.objects.annotate(
        config_string=Concat(
            Value('STATION_CONF:'), F('name'), Value('|'), F('footfall'),
            output_field=CharField()
        )
    ).values_list('config_string', flat=True)
    station_lines_qs = Station.objects.prefetch_related('lines').annotate(
        config_string=Concat(
            Value('LINE_CONN:'), F('name'), Value('|'), F('lines__name'),
            output_field=CharField()
        )
    ).values_list('config_string', flat=True)
    station_neighbors_qs = Station.objects.prefetch_related('neighbours').annotate(
        config_string=Concat(
            Value('NEIGHBOR_CONN:'), F('name'), Value('|'), F('neighbours__name'),
            output_field=CharField()
        )
    ).values_list('config_string', flat=True)
    all_config_strings = sorted(list(lines_qs) + list(stations_qs) + list(station_lines_qs) + list(station_neighbors_qs))
    combined_data = '|'.join(all_config_strings).encode('utf-8')
    hash_data = sha512(combined_data).hexdigest()
    return hash_data
