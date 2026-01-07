import os
import time
import portalocker
import networkx as nx
from pyvis.network import Network
from django.conf import settings
from .models import Station, Line

CACHE = {}

MAPS_DIR = os.path.join(settings.MEDIA_ROOT, 'maps')
os.makedirs(MAPS_DIR, exist_ok=True)
HTML_PATH = os.path.join(MAPS_DIR, f'graph.html')

def calculate_route(start: Station, stop: Station) -> tuple[Station, ...]:
    try:
        graph = _get_graph()
        pk_path = nx.shortest_path(graph, start.pk, stop.pk)
        stations = Station.objects.in_bulk(pk_path)
        return tuple([stations[pk] for pk in pk_path if pk in stations])
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return ()

def get_map_url() -> str:
    if not os.path.exists(HTML_PATH) or _is_updated():
        try:
            with portalocker.Lock(HTML_PATH, mode='a', timeout=30):
                if not os.path.exists(HTML_PATH) or _is_updated():
                    _save_graph()
                    _reset_updated()
        except portalocker.exceptions.LockException:
            return '/stations/list/'
    timestamp = int(time.time())
    return f'{settings.MEDIA_URL}maps/graph.html?v={timestamp}'

def _is_updated() -> bool:
    updated_stations = Station.objects.filter(updated=True)
    updated_lines = Line.objects.filter(updated=True)
    if not updated_lines.exists() and not updated_stations.exists():
        return False
    return True

def _reset_updated() -> None:
    Station.objects.filter(updated=True).update(updated=False)
    Line.objects.filter(updated=True).update(updated=False)

def _get_graph() -> nx.DiGraph:
    if 'graph' in CACHE and not _is_updated():
        return CACHE['graph']
    graph = _create_graph()
    CACHE['graph'] = graph
    return graph

def _create_graph() -> nx.DiGraph:
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
                color = line.color
                G.add_edge(station.pk, neighbour.pk, color=color, width=8, smooth=True)
                if G.has_edge(neighbour.pk, station.pk):
                    G[neighbour.pk][station.pk]['arrows'] = 'to;from'
                    G[station.pk][neighbour.pk]['hidden'] = True
                else:
                    G[station.pk][neighbour.pk]['arrows'] = 'to'
                    G[station.pk][neighbour.pk]['hidden'] = False
    G.remove_nodes_from(list(nx.isolates(G)))
    return G

def _save_graph():
    G = _get_graph()
    net = Network(height='1000px', width='100%', notebook=False, directed=True, cdn_resources='remote', select_menu=True)
    net.from_nx(G)
    net.force_atlas_2based(
        gravity=-50, 
        central_gravity=0.01, 
        spring_length=200,
        spring_strength=0.08
    )
    net.toggle_physics(True)
    net.save_graph(f'{HTML_PATH}.tmp.html')
    os.replace(f'{HTML_PATH}.tmp.html', HTML_PATH)
