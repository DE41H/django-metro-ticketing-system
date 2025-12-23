import os
import portalocker
import networkx as nx
from hashlib import sha512
from pyvis.network import Network
from django.conf import settings
from django.db.models import Max
from django.utils.dateformat import format
from .models import Station, Line

CACHE = {}

maps_dir = os.path.join(settings.MEDIA_ROOT, 'maps')
html_path = os.path.join(maps_dir, f'graph.html')
os.makedirs(maps_dir, exist_ok=True)

def calculate_route(start: Station, stop: Station) -> tuple[Station, ...]:
    try:
        graph = _create_map()
        pk_path = nx.shortest_path(graph, start.pk, stop.pk)
        stations = Station.objects.in_bulk(pk_path)
        return tuple([stations[pk] for pk in pk_path])
    except (nx.NetworkXNoPath, portalocker.exceptions.LockException, FileNotFoundError):
        return ()

def get_map_url() -> str:
    if not os.path.exists(html_path):
        try:
            with portalocker.Lock(html_path, mode='w', timeout=30):
                _create_map()
        except portalocker.exceptions.LockException:
            return '/stations/list/'
    return f'{settings.MEDIA_URL}maps/graph.html'

def _is_updated() -> bool:
    updated_stations = Station.objects.filter(updated=True)
    updated_lines = Line.objects.filter(updated=True)
    if not updated_lines.exists() and not updated_stations.exists():
        return False
    updated_stations.update(updated=False)
    updated_lines.update(updated=False)
    return True

def _create_map() -> nx.DiGraph:
    if not _is_updated():
        return CACHE['graph']
    G: nx.DiGraph = nx.DiGraph()
    all_stations = Station.objects.prefetch_related('lines', 'neighbours', 'neighbours__lines')
    all_station_lines = {}
    groups = ('Isolated Stations', 'Terminal Stations', 'Standard Stations', 'Interchange Hubs')
    for station in all_stations:
        all_station_lines[station.pk] = set(station.lines.all())
        count = len(station.neighbours.all())
        if count > 3:
            count = 3
        group = groups[count]
        lines = ', '.join([line.name for line in all_station_lines[station.pk]])
        G.add_node(station.pk, label=station.name, title=f'Lines: {lines}', shape='dot', size=12, font={'size': 30, 'vadjust': 5}, group=group)
    for station in all_stations:
        for neighbour in station.neighbours.all():
            lines = all_station_lines[station.pk] & all_station_lines[neighbour.pk]
            line = next((l for l in lines if l.is_running), None)
            if line:
                if G.has_edge(neighbour.pk, station.pk):
                    G[neighbour.pk][station.pk]['arrows'] = 'to;from'
                else:
                    color = line.color
                    G.add_edge(station.pk, neighbour.pk, color=color, width=8, smooth=True, arrows='to')
    net = Network(height='1000px', width='100%', notebook=False, directed=True, cdn_resources='remote', select_menu=True)
    net.from_nx(G)
    net.force_atlas_2based(
        gravity=-50, 
        central_gravity=0.01, 
        spring_length=200,
        spring_strength=0.08
    )
    net.toggle_physics(True)
    net.save_graph(f'{html_path}.tmp.html')
    os.replace(f'{html_path}.tmp.html', html_path)
    return G
