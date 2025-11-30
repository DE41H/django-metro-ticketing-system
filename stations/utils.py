import os
import portalocker
import networkx as nx
from hashlib import sha512
from pyvis.network import Network
from django.conf import settings
from django.db.models import Max
from django.utils.dateformat import format
from .models import Station, Line

maps_dir = os.path.join(settings.MEDIA_ROOT, 'maps')
os.makedirs(maps_dir, exist_ok=True)

def calculate_route(start: Station, stop: Station) -> tuple[Station, ...]:
    if start == stop:
        return (start, )
    filename = get_map_url().replace(f'{settings.MEDIA_URL}maps/', '').replace('.html', '.gexf')
    gexf_path = os.path.join(maps_dir, filename)
    try:
        with portalocker.Lock(gexf_path, mode='r', timeout=10):
            graph = nx.read_gexf(path=gexf_path)
            pk_path = nx.shortest_path(graph, start.pk, stop.pk)
            stations = Station.objects.in_bulk(pk_path)
            return tuple([stations[pk] for pk in pk_path])
    except (nx.NetworkXNoPath, portalocker.exceptions.LockException, FileNotFoundError):
        return ()

def get_map_url() -> str:
    def _get_hash() -> str:
        latest_station_update = Station.objects.all().aggregate(Max('updated_at'))['updated_at__max']
        latest_line_update = Line.objects.all().aggregate(Max('updated_at'))['updated_at__max']
        updates = [u for u in [latest_station_update, latest_line_update] if u]
        if not updates:
            return sha512(b"EMPTY_MAP").hexdigest()
        latest_update = max(updates)
        string = format(latest_update, 'MAP_CONFIG:%Y-%m-%d H:i:s.u').encode('utf-8')
        hash_data = sha512(string).hexdigest()
        return hash_data
    
    def _create_map(path: str) -> nx.DiGraph[str]:
        G: nx.DiGraph[str] = nx.DiGraph()
        all_stations = Station.objects.prefetch_related('lines', 'neighbours')
        for station in all_stations:
            lines = ', '.join([line.name for line in station.lines.all()])
            G.add_node(station.pk, label=station.name, title=f'Lines: {lines}', shape='dot', size=12, font={'size': 30, 'vadjust': 5})
        for station in all_stations:
            for neighbour in station.neighbours.all():
                station_lines = set(station.lines.all())
                neighbour_lines = set(neighbour.lines.all())
                lines = station_lines.intersection(neighbour_lines)
                line = next((l for l in lines), None)
                if line and line.is_running:
                    color = line.color
                    G.add_edge(station.pk, neighbour.pk, color=color, width=8, smooth=True)
        net = Network(height='1000px', width='100%', notebook=False, directed=True, cdn_resources='remote')
        net.from_nx(G)
        net.save_graph(path)
        nx.write_gexf(G, path.replace('.html', '.gexf'))
        return G
    
    hash_key = f'{_get_hash()}'
    gexf_path = os.path.join(maps_dir, f'{hash_key}.gexf')
    html_path = os.path.join(maps_dir, f'{hash_key}.html')
    if not os.path.exists(gexf_path) or not os.path.exists(html_path):
        try:
            with portalocker.Lock(gexf_path, mode='w', timeout=30):
                _create_map(path=html_path)
        except portalocker.exceptions.LockException:
            return '/stations/'
    return f'{settings.MEDIA_URL}maps/{hash_key}.html'
