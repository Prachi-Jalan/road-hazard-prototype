"""
geo_route/gps_sim.py — simulated vehicle GPS.

The vehicle drives the planned route at a constant speed. The ONLY input is
`t_ms`: milliseconds since the start of the video. That is deliberate — it is
exactly the field Person 1 already emits (`timestamp_ms`), so detections and
GPS share one clock with no extra plumbing.

    t_ms  ->  s = start_s + speed * t   ->  (lat, lon, heading) on the route

Swapping this for a real GPS feed later means replacing `state_at_ms()` only;
nothing downstream changes.
"""

from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone

try:
    from .config import VEHICLE_SPEED_KMPH, VEHICLE_START_S_M, VIDEO_START_UTC
    from .route import Route
except ImportError:
    from config import VEHICLE_SPEED_KMPH, VEHICLE_START_S_M, VIDEO_START_UTC
    from route import Route


@dataclass
class VehicleState:
    t_ms: int
    latitude: float
    longitude: float
    heading_deg: float
    s_m: float             # distance travelled along the route
    speed_mps: float
    utc: str               # wall-clock time, for logs and the backend

    def as_dict(self):
        return asdict(self)


class VehicleSimulator:
    def __init__(self, route: Route, speed_kmph=VEHICLE_SPEED_KMPH,
                 start_s_m=VEHICLE_START_S_M, video_start_utc=VIDEO_START_UTC):
        self.route = route
        self.speed_mps = speed_kmph / 3.6
        self.start_s_m = start_s_m
        self.video_start = datetime.fromisoformat(
            video_start_utc.replace("Z", "+00:00")
        ).astimezone(timezone.utc)

    def state_at_ms(self, t_ms) -> VehicleState:
        """Where the vehicle is `t_ms` milliseconds into the video."""
        t_ms = int(t_ms)
        s = self.start_s_m + self.speed_mps * (t_ms / 1000.0)
        s = max(0.0, min(s, self.route.length_m))
        lat, lon, heading = self.route.position_at_s(s)
        utc = (self.video_start + timedelta(milliseconds=t_ms)).isoformat(
            timespec="milliseconds"
        ).replace("+00:00", "Z")
        return VehicleState(
            t_ms=t_ms,
            latitude=round(lat, 7),
            longitude=round(lon, 7),
            heading_deg=round(heading, 2),
            s_m=round(s, 2),
            speed_mps=round(self.speed_mps, 2),
            utc=utc,
        )

    def track(self, duration_ms, step_ms=1000):
        """Full simulated GPS trace — handy for Person 6's map view."""
        return [self.state_at_ms(t) for t in range(0, int(duration_ms) + 1, step_ms)]
