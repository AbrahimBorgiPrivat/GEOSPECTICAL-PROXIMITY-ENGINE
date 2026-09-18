# Denmark OSRM setup

This directory contains the Denmark-specific OSRM setup, including the Denmark map data, generated routing data, build script, and Docker Compose services for foot, car, and bicycle routing.

Run `docker compose up` from this directory to start the local OSRM services.

The services expose routed distances and travel durations. The proximity algorithm
can use either metric through `distance_unit="metres"` or
`distance_unit="duration"`; the selected OSRM profile determines the default
movement speed used for geographic candidate screening in duration mode.
