# geo_route — Person 3: GPS + Route Matching

Turns one YOLO detection into the geospatial object the rest of the pipeline needs.

```
ROAD VIDEO → YOLO → [ LOCATION → ROUTE MATCHING → DISTANCE ] → RISK ENGINE → WARNING → STREAMLIT
                            this module
```

No dependencies. Standard library only — `python run_demo.py` works on a fresh clone.

## Quick start

```bash
cd geo_route
python run_demo.py     # watch distance_m count down, ahead flip, on_route reject H3
python test_geo.py     # 5 sanity checks, all must pass
```

`run_demo.py` writes `sample_geo_output.json` so Person 5 and Person 6 can build
against real-shaped data now, without waiting on the video pipeline.

## The API — one function

```python
from geo_route.locate import locate_detection

geo = locate_detection(detection)   # detection = one dict from Person 1
# {"latitude": 12.9720415, "longitude": 77.5973313,
#  "distance_m": 150, "ahead": True, "on_route": True}
```

That is exactly the five contract fields, nothing else. Pass `include_debug=True`
to also get a `_debug` key (vehicle state, matched hazard id, cross-track distance)
for tuning and for the Streamlit map — but never send `_debug` downstream to Person 5.

For a stream, reuse one locator instead of the convenience function:

```python
from geo_route.locate import GeoLocator
locator = GeoLocator()
geos = locator.locate_many(detections)
```

## How it works

Everything is expressed in **route coordinates** rather than raw lat/lon. Each point
gets two numbers by projecting it onto the planned route polyline:

- `s` — metres **along** the route from the start
- `d` — metres **off** the route (cross-track)

The three contract fields then fall straight out:

| field | rule |
|---|---|
| `on_route` | `d <= 25 m` (corridor around the planned A→B polyline) and not past the destination |
| `ahead` | `s_hazard > s_vehicle` (with a 5 m buffer). For off-route hazards, falls back to a bearing test against vehicle heading |
| `distance_m` | along-route distance `s_hazard − s_vehicle` when on route — that's the distance the driver will actually travel. Straight-line haversine when off route |

**Vehicle position** (`gps_sim.py`): drives the route at a constant 40 km/h. Its only
input is `t_ms`, milliseconds since the start of the video — the field Person 1 already
emits. Detections and GPS therefore share one clock with no extra plumbing. Replacing
this with a real GPS feed later means rewriting `state_at_ms()` and nothing else.

**Hazard position** (`locate.py`): two modes, chosen automatically.

- **Mode A `planted`** (default, used for the demo) — the detection is matched to a
  known hazard in the simulated ground-truth map lying just ahead of the vehicle.
  Deterministic, so the golden demo gives identical numbers every run.
- **Mode B `projected`** (fallback) — if nothing matches, range is estimated from the
  bbox with a crude flat-road pinhole model and projected along the vehicle heading.
  This is **not** real camera-to-GPS projection (out of scope) — it exists purely so an
  unexpected detection can never return null mid-demo.

## Tuning for the golden demo

Everything adjustable lives in `config.py`. Move a hazard by editing `s_m`, not by
hunting for a plausible lat/lon.

- `ROUTE_WAYPOINTS` — the planned route (A→B)
- `PLANTED_HAZARDS` — ground-truth hazards, positioned as (metres along route, lateral offset)
- `VEHICLE_SPEED_KMPH`, `VIDEO_START_UTC` — the vehicle/video clock anchor
- `ROUTE_CORRIDOR_M` — how wide "on my route" is (default 25 m)

**Keep hazard H3.** It sits 45 m off the route on a notional parallel service road, and
it's the one case that proves `on_route` is real logic rather than hardcoded `true`.
It's worth showing a judge explicitly: *nearby is not the same as on my route.*

## Notes for the rest of the team

**Person 1 / Person 2 — timestamp alignment.** I key off `timestamp_ms` (ms since video
start) and `VIDEO_START_UTC` in `config.py` is the shared anchor. `frame_timestamp` in
ISO form is also accepted, and `bbox` is accepted as either `[x1,y1,x2,y2]` or
`{"x1":…}`, so a rename upstream won't break the pipeline. As agreed, no timing logic is
built against `shared/sample_detections.json` — its timestamps are placeholder-spaced.
Field shapes only.

**Person 5 — risk engine.** You get `distance_m`, `ahead`, `on_route`. `distance_m` is
rounded to whole metres and is always positive; use `ahead` for direction, don't infer it
from the sign. `severity` and `confidence` stay yours and Person 1's — I don't touch them.

**Person 4 — backend.** `GeoLocator.locate()` is a pure function with no I/O, safe to
call inside a FastAPI request handler. `latitude`/`longitude` are the hazard's position,
ready for a PostGIS point.

**Person 6 — frontend.** `VehicleSimulator.track(duration_ms)` returns the full GPS trace
for the map view, and `build_hazard_map(route)` gives every hazard's lat/lon for markers.

## Files

| file | what's in it |
|---|---|
| `config.py` | every tunable constant — route, hazards, speed, thresholds |
| `geo_utils.py` | haversine, bearing, local flat-earth projection, point-to-segment |
| `route.py` | the route polyline: arc length, projection, heading, offsets |
| `gps_sim.py` | simulated vehicle driving the route on the video clock |
| `hazards.py` | builds the ground-truth hazard map from config |
| `locate.py` | **the deliverable** — detection → contract output |
| `run_demo.py` | runnable demo + writes `sample_geo_output.json` |
| `test_geo.py` | 5 plain-assert sanity checks |
