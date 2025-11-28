import os
import portalocker
import networkx as nx
from hashlib import sha512
from pyvis.network import Network # type: ignore
from django.conf import settings
from django.db.models import Max
from django.utils.dateformat import format
from .models import Station, Line

graphs = {}

def calculate_route(start: Station, stop: Station) -> tuple[Station, ...]:
    if start == stop:
        return (start, )
    try:
        graph = nx.node_link_graph(graphs[get_map_url()])
        pk_path = nx.shortest_path(graph, start.pk, stop.pk)
        stations = Station.objects.in_bulk(pk_path)
        return tuple([stations[pk] for pk in pk_path])
    except nx.NetworkXNoPath:
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
                    G.add_edge(station.pk, neighbour.pk, color=color, width=8, smooth=True) # type: ignore
        net = Network(height='1000px', width='100%', notebook=True)
        net.from_nx(G)
        net.save_graph(path)
        return G

    maps_dir = os.path.join(settings.MEDIA_ROOT, 'maps')
    os.makedirs(maps_dir, exist_ok=True)
    filename = f'{_get_hash()}.html'
    path = os.path.join(maps_dir, filename)
    url = f'{settings.MEDIA_URL}maps/{filename}'
    if not os.path.exists(path):
        try:
            with portalocker.Lock(path, mode='w', timeout=60):
                graphs[url] = nx.node_link_data(_create_map(path=path))
        except portalocker.exceptions.LockException:
            return '/stations/'
    return url
