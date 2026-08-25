\# Demo notes — Person 3, GPS + Route Matching



\## What my module does (one sentence)

Takes a hazard detection from the camera and answers three questions:

how far away is it, is it in front of us, and is it actually on our route.



\## The key moment — hazard H3

Around t=63s the model detects a pothole 45 m off to the side.

It is real, it is a pothole, and it is directly ahead of us.

The system stays silent.



That is the point: it's on the service road, not on our planned route.

Distance alone would have warned the driver. Route matching is what

stops the system crying wolf every time it sees a pothole on the next

street over.



Show: the H3 rows in run\_demo.py output — ahead=True, on\_route=False, no warning.



\## "Where's the real GPS?"

Simulated vehicle driving a known route at a known speed, with hazards at

known positions. Everything downstream of that is real geometry — the

projection onto the route polyline, the along-route distance, the

cross-track corridor test.



The only mocked part is the position source. Swapping to live GPS means

replacing one method (VehicleSimulator.state\_at\_ms) — nothing else changes.



\## How it works, if asked

Instead of comparing raw lat/lon, every point gets projected onto the route

and described by two numbers: how far along the route it is, and how far off

it is. on\_route is then a corridor test, ahead is a comparison of positions

along the route, and distance is the distance the driver will actually drive

— not a straight line through buildings.



\## Numbers I should have ready

\- Route length: 2,441 m

\- Speed: 40 km/h

\- Corridor width: 25 m

\- 5 planted hazards, 4 on route, 1 off

