import math


class Graph:
    def __init__(self):
        self.nodes = {}   # name -> (x, y) canvas coords
        self.coords_geo = {}  # name -> (lat, lon) real coords
        self.dist = {}    # (u, v) -> km

    def add_node(self, name, x, y, lat=0.0, lon=0.0):
        self.nodes[name] = (x, y)
        self.coords_geo[name] = (lat, lon)

    def add_edge(self, u, v, km):
        self.dist[(u, v)] = km
        self.dist[(v, u)] = km

    def neighbors(self, node):
        return [v for (u, v) in self.dist if u == node]

    def get_distance(self, u, v):
        return self.dist.get((u, v), float('inf'))

    def euclidean_heuristic(self, a, b):
        """Canvas-space straight-line distance as A* heuristic."""
        x1, y1 = self.nodes[a]
        x2, y2 = self.nodes[b]
        pixel_dist = math.hypot(x2 - x1, y2 - y1)
        # Scale: roughly 3 pixels ≈ 1 km in our coordinate system
        return pixel_dist / 3.0


def build_india_graph():
    g = Graph()

    city_data = {
        "Mumbai":    (120, 400, 19.08, 72.88),
        "Delhi":     (310, 140, 28.61, 77.21),
        "Bengaluru": (320, 510, 12.97, 77.59),
        "Kolkata":   (580, 290, 22.57, 88.36),
        "Chennai":   (430, 530, 13.08, 80.27),
        "Hyderabad": (360, 400, 17.38, 78.49),
        "Pune":      (170, 440, 18.52, 73.86),
        "Ahmedabad": (210, 290, 23.03, 72.59),
        "Jaipur":    (280, 230, 26.91, 75.79),
        "Nagpur":    (370, 330, 21.15, 79.09),
        "Lucknow":   (410, 200, 26.85, 80.95),
        "Bhopal":    (330, 280, 23.26, 77.40),
    }

    for city, (x, y, lat, lon) in city_data.items():
        g.add_node(city, x, y, lat, lon)

    edges = [
        ("Mumbai", "Pune", 150),
        ("Mumbai", "Ahmedabad", 524),
        ("Mumbai", "Nagpur", 830),
        ("Mumbai", "Hyderabad", 710),
        ("Mumbai", "Bengaluru", 981),
        ("Delhi", "Jaipur", 281),
        ("Delhi", "Lucknow", 555),
        ("Delhi", "Ahmedabad", 943),
        ("Delhi", "Bhopal", 770),
        ("Delhi", "Kolkata", 1453),
        ("Bengaluru", "Chennai", 346),
        ("Bengaluru", "Hyderabad", 570),
        ("Bengaluru", "Pune", 840),
        ("Kolkata", "Hyderabad", 1192),
        ("Kolkata", "Bhopal", 1200),
        ("Kolkata", "Lucknow", 992),
        ("Hyderabad", "Chennai", 626),
        ("Hyderabad", "Nagpur", 497),
        ("Hyderabad", "Bhopal", 688),
        ("Pune", "Hyderabad", 560),
        ("Ahmedabad", "Jaipur", 660),
        ("Ahmedabad", "Bhopal", 552),
        ("Jaipur", "Lucknow", 592),
        ("Jaipur", "Bhopal", 614),
        ("Nagpur", "Bhopal", 357),
        ("Nagpur", "Hyderabad", 497),
        ("Nagpur", "Kolkata", 1050),
        ("Lucknow", "Bhopal", 650),
        ("Lucknow", "Kolkata", 992),
        ("Chennai", "Kolkata", 1659),
    ]

    for u, v, d in edges:
        g.add_edge(u, v, d)

    return g