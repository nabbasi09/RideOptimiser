from collections import deque
from datetime import datetime


class Booking:
    _counter = 0

    def __init__(self, pickup, dropoff, preference, num_passengers=1):
        Booking._counter += 1
        self.booking_id = f"RD{Booking._counter:04d}"
        self.pickup = pickup
        self.dropoff = dropoff
        self.preference = preference
        self.num_passengers = num_passengers
        self.timestamp = datetime.now()
        self.assigned_driver = None
        self.fare = 0
        self.rating = 0
        self.status = "pending"

    def __repr__(self):
        return f"Booking({self.booking_id}, {self.pickup}→{self.dropoff})"


class BookingQueue:
    def __init__(self):
        self._queue = deque()
        self.active_bookings = []
        self.completed_bookings = []

    def enqueue(self, booking):
        self._queue.append(booking)

    def dequeue(self):
        if self._queue:
            return self._queue.popleft()
        return None

    def has_pending(self):
        return len(self._queue) > 0

    def pending_count(self):
        return len(self._queue)

    def active_count(self):
        return len(self.active_bookings)

    def complete(self, booking, fare, driver_name):
        booking.fare = fare
        booking.status = "completed"
        booking.assigned_driver = driver_name
        if booking in self.active_bookings:
            self.active_bookings.remove(booking)
        self.completed_bookings.append(booking)


class SurgePricing:
    """
    Demand-based surge: increases with active rides and decreases over time.
    """
    TIERS = [
        (0, 1, 1.0,  "🟢 Normal",    "#4CAF50"),
        (2, 3, 1.3,  "🟡 Moderate",  "#FFD700"),
        (4, 5, 1.6,  "🟠 High",      "#FFA500"),
        (6, 99, 2.0, "🔴 Surge x2!", "#FF4444"),
    ]

    def __init__(self):
        self.active_rides = 0
        self.rush_hour = False

    def get_multiplier(self):
        base = 1.0
        for lo, hi, mult, _, _ in self.TIERS:
            if lo <= self.active_rides <= hi:
                base = mult
                break
        if self.rush_hour:
            base = min(base * 1.25, 2.5)
        return round(base, 2)

    def get_label(self):
        for lo, hi, _, label, color in self.TIERS:
            if lo <= self.active_rides <= hi:
                if self.rush_hour:
                    return f"🔴 RUSH + {label.split()[1] if len(label.split()) > 1 else 'surge'}", "#FF4444"
                return label, color
        return "🟢 Normal", "#4CAF50"

    def ride_started(self):
        self.active_rides += 1

    def ride_ended(self):
        self.active_rides = max(0, self.active_rides - 1)