import heapq


def dijkstra_km(graph, start, end):
    """Shortest path by distance in km."""
    if start == end:
        return [start], 0.0
    pq = [(0.0, start, [start])]
    visited = {}
    while pq:
        cost, node, path = heapq.heappop(pq)
        if node in visited and visited[node] <= cost:
            continue
        visited[node] = cost
        if node == end:
            return path, cost
        for nei in graph.neighbors(node):
            edge_km = graph.get_distance(node, nei)
            if edge_km == float('inf'):
                continue
            heapq.heappush(pq, (cost + edge_km, nei, path + [nei]))
    return [], float('inf')


def astar_fastest(graph, start, end, traffic_factor=1.0, avoid_cities=None):
    """
    A* search optimising for travel time.
    Heuristic: straight-line canvas distance converted to hours.
    """
    if start == end:
        return [start], 0.0

    avoid = set(avoid_cities or [])
    speed_kmph = 60.0 / traffic_factor  # effective speed

    def time_cost(u, v):
        km = graph.get_distance(u, v)
        return km / speed_kmph if km != float('inf') else float('inf')

    def heuristic(node):
        h_km = graph.euclidean_heuristic(node, end)
        return h_km / speed_kmph

    open_set = [(heuristic(start), 0.0, start, [start])]
    g_score = {start: 0.0}

    while open_set:
        f, g, node, path = heapq.heappop(open_set)
        if node == end:
            return path, g
        if g > g_score.get(node, float('inf')):
            continue
        for nei in graph.neighbors(node):
            if nei in avoid and nei != end:
                continue
            edge_t = time_cost(node, nei)
            if edge_t == float('inf'):
                continue
            new_g = g + edge_t
            if new_g < g_score.get(nei, float('inf')):
                g_score[nei] = new_g
                f_score = new_g + heuristic(nei)
                heapq.heappush(open_set, (f_score, new_g, nei, path + [nei]))

    return [], float('inf')


def astar_eco(graph, start, end, traffic_factor=1.0):
    """
    Eco-friendly: minimise a blend of distance and estimated fuel use.
    Penalises highway stretches (>500 km legs) with a small extra factor.
    """
    if start == end:
        return [start], 0.0

    def eco_cost(u, v):
        km = graph.get_distance(u, v)
        if km == float('inf'):
            return float('inf')
        # Longer single legs = lower avg speed = worse fuel efficiency
        penalty = 1.15 if km > 500 else 1.0
        return km * penalty

    def heuristic(node):
        return graph.euclidean_heuristic(node, end)

    open_set = [(heuristic(start), 0.0, start, [start])]
    g_score = {start: 0.0}

    while open_set:
        f, g, node, path = heapq.heappop(open_set)
        if node == end:
            return path, g
        if g > g_score.get(node, float('inf')):
            continue
        for nei in graph.neighbors(node):
            cost = eco_cost(node, nei)
            new_g = g + cost
            if new_g < g_score.get(nei, float('inf')):
                g_score[nei] = new_g
                heapq.heappush(open_set, (new_g + heuristic(nei), new_g, nei, path + [nei]))

    return [], float('inf')


def compute_eta_minutes(graph, from_city, to_city, traffic_factor=1.0):
    """ETA in minutes via A*."""
    if from_city == to_city:
        return 0.0
    _, time_h = astar_fastest(graph, from_city, to_city, traffic_factor)
    return time_h * 60.0


def compute_km(graph, from_city, to_city):
    """Distance in km via Dijkstra."""
    if from_city == to_city:
        return 0.0
    _, km = dijkstra_km(graph, from_city, to_city)
    return km


def compute_fare(graph, from_city, to_city, traffic_factor=1.0, surge=1.0, num_passengers=1):
    """
    Fare = base + per-km + per-min + passenger adjustment.
    """
    if from_city == to_city:
        return 50
    km = compute_km(graph, from_city, to_city)
    eta_min = compute_eta_minutes(graph, from_city, to_city, traffic_factor)
    base = 50
    fare = (base + km * 12 + eta_min * 2) * surge
    if num_passengers > 1:
        fare *= (1 + (num_passengers - 1) * 0.15)
    return int(fare)


def get_path(graph, start, end, preference="Fastest", traffic_factor=1.0, avoid_cities=None):
    """Return (path, metric) for the chosen preference."""
    if preference == "Fastest":
        return astar_fastest(graph, start, end, traffic_factor, avoid_cities)
    elif preference == "Eco-friendly":
        return astar_eco(graph, start, end, traffic_factor)
    else:  # Shortest distance / Avoid tolls (same here without real toll data)
        return dijkstra_km(graph, start, end)