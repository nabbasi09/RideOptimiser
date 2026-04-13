from enum import Enum, auto


class DriverState(Enum):
    IDLE = auto()
    EN_ROUTE_TO_PICKUP = auto()
    AT_PICKUP = auto()
    EN_ROUTE_TO_DROPOFF = auto()
    COMPLETED = auto()


class Driver:
    def __init__(self, name, home_city, color="#2ECC71"):
        self.name = name
        self.city = home_city          # current city
        self.home_city = home_city
        self.color = color
        self.state = DriverState.IDLE
        self.rating = 4.8
        self.trips_completed = 0
        self.total_earnings = 0

        # Animation state
        self.path = []
        self.path_index = 0
        self.target_pickup = None
        self.target_dropoff = None

        # Canvas marker IDs
        self.canvas_ids = []

    # ------------------------------------------------------------------
    def assign_ride(self, pickup, dropoff):
        self.target_pickup = pickup
        self.target_dropoff = dropoff
        self.state = DriverState.EN_ROUTE_TO_PICKUP

    def arrived_at_pickup(self):
        self.city = self.target_pickup
        self.state = DriverState.AT_PICKUP

    def depart_to_dropoff(self):
        self.state = DriverState.EN_ROUTE_TO_DROPOFF

    def complete_ride(self, fare):
        self.city = self.target_dropoff
        self.state = DriverState.COMPLETED
        self.trips_completed += 1
        self.total_earnings += fare
        self.target_pickup = None
        self.target_dropoff = None
        self.path = []
        self.path_index = 0

    def reset_to_idle(self):
        self.state = DriverState.IDLE

    # ------------------------------------------------------------------
    @property
    def is_available(self):
        return self.state == DriverState.IDLE

    @property
    def status_text(self):
        return {
            DriverState.IDLE: "🟢 Available",
            DriverState.EN_ROUTE_TO_PICKUP: f"🟡 Heading to {self.target_pickup}",
            DriverState.AT_PICKUP: f"🟠 At {self.target_pickup}",
            DriverState.EN_ROUTE_TO_DROPOFF: f"🔵 Driving to {self.target_dropoff}",
            DriverState.COMPLETED: "✅ Ride done",
        }[self.state]

    def __repr__(self):
        return f"Driver({self.name}, {self.city}, {self.state.name})"


def create_default_drivers():
    return [
        Driver("Arjun Singh",  "Mumbai",    "#E74C3C"),
        Driver("Priya Sharma", "Delhi",     "#3498DB"),
        Driver("Ravi Kumar",   "Bengaluru", "#F39C12"),
        Driver("Neha Patel",   "Ahmedabad", "#9B59B6"),
    ]