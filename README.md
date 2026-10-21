*This project has been created as part of the 42 curriculum by lusampai.*

# Fly-in

## Description

Fly-in routes a fleet of drones from a start zone to an end zone through a
network of connected zones, in the **fewest possible simulation turns**.

The network is read from a map file. Zones have a type (`normal`, `priority`,
`restricted`, `blocked`) and a capacity, and connections have a capacity too.
All the drones move simultaneously, turn by turn, and the program prints one
line per turn with the movements of that turn.

The program does four things:

1. **Parses** the map file and reports any error with its line number.
2. **Plans** the route of every drone so that no capacity is ever exceeded.
3. **Validates** the plan against every rule of the subject before printing.
4. **Displays** the simulation in the terminal, with colors.

Main features:

- Parser with clear errors (line and cause) for every rule of the format.
- Planner that handles restricted zones (2 turns), priority zones, blocked
  zones, zone capacities and connection capacities.
- Detection of maps that are valid but have no path to the end zone.
- Independent validator that checks every plan before it is shown.
- Colored terminal output, disabled automatically when the output is not a
  terminal.
- Pure Python, no graph library, fully typed and object-oriented.

## Instructions

### Requirements

- Python 3.10 or later.
- `flake8` and `mypy` for the linting rules (installed by `make install`).

### Installation

```bash
make install
```

It is recommended to do it inside a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
make install
```

### Running

```bash
make run MAP=maps/easy/01_linear_path.txt
```

which is the same as:

```bash
python3 main.py maps/easy/01_linear_path.txt
```

### Makefile rules

| Rule | What it does |
|---|---|
| `make install` | Installs the dependencies with `pip`. |
| `make run MAP=<file>` | Runs the simulation on a map file. |
| `make debug MAP=<file>` | Runs the program under the Python debugger (`pdb`). |
| `make clean` | Removes `__pycache__`, `.mypy_cache` and `.pytest_cache`. |
| `make lint` | Runs `flake8` and `mypy` with the flags required by the subject. |
| `make lint-strict` | Runs `flake8` and `mypy --strict`. |

### Output streams and exit codes

- **stdout** contains only the simulation lines, in the exact format of the
  subject. Redirecting it to a file gives a clean log.
- **stderr** contains the messages for humans: errors and the final summary
  (`Done: 4 turns, 2 drones delivered`).

| Exit code | Meaning |
|---|---|
| 0 | The simulation ran correctly. |
| 1 | Wrong usage, invalid map, or valid map with no path to the end zone. |
| 2 | Internal error (for example, a computed plan that fails validation). |

## Input format

```
nb_drones: 5

start_hub: hub 0 0 [color=green]
end_hub: goal 10 10 [color=yellow]
hub: roof1 3 4 [zone=restricted color=red]
hub: corridorA 4 3 [zone=priority color=green max_drones=2]
connection: hub-roof1
connection: corridorA-tunnelB [max_link_capacity=2]
```

The parser follows the subject and fixes the points the subject leaves open.
These are the rules it enforces:

- Comment lines start with `#`. A `#` in the middle of a line is **not** a
  comment, it is part of the line.
- The first useful line must be `nb_drones: <positive integer>`.
- There must be exactly one `start_hub` and one `end_hub`.
- A zone is `name x y [metadata]`, with integer coordinates (negative values
  are valid). The metadata block is optional, and an empty block `[]` is
  accepted.
- Zone names cannot contain `-`, whitespace, `[` or `]`. The dash is the
  separator of a connection, and the brackets delimit the metadata.
- Zone metadata keys: `zone` (`normal`, `blocked`, `restricted`, `priority`),
  `color` (any single word) and `max_drones` (positive integer). The keys may
  appear in any order. `max_drones` is ignored on the start and end zones.
- Connections are `name1-name2 [max_link_capacity=<positive integer>]`. They
  must link zones that are **already defined**. The same connection cannot
  appear twice (`a-b` and `b-a` are the same), and a zone cannot be connected
  to itself.
- Integers accept an optional leading `-` followed by digits only (`+4` and
  `1_0` are rejected).
- An unknown metadata key, a repeated key or a malformed block is an error.
- Every error stops the program with a message like
  `Error: line 3: Unknown zone type 'banana'. Valid types: normal, blocked, restricted, priority`.

A map that is syntactically valid but has no path from the start to the end
(for example because a blocked zone cuts the graph) is **not** a parsing error.
The program reports `Error: No path from 's' to 'e'` and exits with code 1.

## Output format

One line per turn. Each line lists the drones that moved during that turn, as
`D<id>-<zone>`. A drone that is crossing a connection towards a restricted zone
is shown as `D<id>-<origin>-<destination>`, and appears again as
`D<id>-<destination>` in the next turn, when it arrives.

Drones that do not move are omitted. A turn in which nobody moves is printed as
an empty line, because it still counts as a turn. The output ends when the
last drone arrives, so there are never empty lines at the end.

## Algorithm and implementation strategy

### The model

The map is loaded into a `Network`: a dictionary of zones, a dictionary of
connections indexed by the **unordered pair** of their zones (so `a-b` and
`b-a` are the same connection), and an adjacency list. Blocked zones stay in
the network, but `neighbours()` never returns them, so no algorithm can enter
them by mistake.

A **plan** stores, for each drone, its **state at every turn**. A state is
either the name of a zone, or the name of a connection while the drone is in
flight towards a restricted zone. Since zone names cannot contain a dash, a
connection name (`a-b`) can never be confused with a zone name. The output
lines are obtained by comparing the state of each drone at turn `t` with its
state at turn `t-1`.

### Shortest path for one drone (`Pathfinder`)

A Dijkstra search (with `heapq`) where the cost of a step is the number of
turns needed to enter the destination zone: 1 for `normal` and `priority`, 2
for `restricted`. The cost is a tuple `(turns, -priority zones)`, so among
paths with the same number of turns, the one crossing more priority zones is
preferred. This is also how the subject's "priority zones should be preferred"
is implemented: priority never makes a path longer in turns, it only breaks
ties.

This search gives the duration of a drone flying alone, and it detects maps
with no solution.

### Planning all the drones (`Planner`)

The drones are planned **one after the other**. Each drone searches for the
route that makes it arrive **as early as possible**, taking into account
everything the previous drones have already reserved. After the search, the
drone reserves its own route.

The search is a Dijkstra over pairs **(zone, turn)**, so waiting is just one
more kind of move. From `(zone, t)` a drone can:

| Move | Condition | Arrives at |
|---|---|---|
| wait | the zone has room at turn `t+1` | `(zone, t+1)` |
| go to a normal or priority zone | the connection has room at `t+1` and the destination zone has room at `t+1` | `(destination, t+1)` |
| go to a restricted zone | the connection has room at `t+1` and the destination zone has room at **`t+2`** | `(destination, t+2)` |

A drone in flight cannot wait on the connection, so the room in the
destination zone is checked, and reserved, **at the moment the drone leaves**.

Because every drone plans around the reservations of the previous ones, the
final plan never has conflicts or deadlocks, by construction.

### Reservation table (`ReservationTable`)

Two dictionaries: how many drones are in each zone at the end of each turn,
and how many drones use each connection during each turn. Start and end zones
have no limit. The rules mirror the subject:

- A space freed by a drone leaving a zone is available to another drone in the
  **same turn**, so a single-file column of drones advances one step per turn.
- A restricted connection is freed in the turn the drone arrives, so the next
  drone may start crossing in that same turn.
- The capacity of a connection is shared by both directions.

### Why a plan always exists

The search is limited to `(nb_drones + 1) × T` turns, where `T` is the duration
of one drone flying alone. This horizon is always enough: whatever the previous
drones have reserved, the next drone can wait in the start zone (which has no
capacity limit) until all the previous drones have arrived, and then follow the
shortest path alone.

### Validation (`Validator`)

Before printing, every plan is checked by a separate class that does not share
the planning logic. It checks, for every drone and turn:

- every drone starts in the start zone and ends in the end zone;
- every transition is legal: waiting, moving to a neighbouring zone through an
  existing connection, never entering a blocked zone, entering a restricted
  zone only through the two-turn flight, and **arriving** at the destination
  right after the flight;
- no zone holds more than `max_drones` drones at the end of a turn;
- no connection is used by more than `max_link_capacity` drones during a turn;
- a drone that reached the end zone never leaves it.

If a plan fails the validation, the program does not print it: it reports an
internal error (exit code 2).

### Complexity

Let `Z` be the number of zones, `E` the connections, `N` the drones, `T` the
number of turns and `H` the search horizon.

- **Parser**: linear in the size of the file.
- **Pathfinder**: `O((Z + E) log Z)` time and `O(Z)` memory.
- **Planner**: each drone explores at most `Z × H` pairs, each with at most
  `degree + 1` moves, with a `log` for the heap. The search stops at the first
  arrival, so it usually explores far fewer. The planner does not cache paths:
  the best route of a drone depends on what the previous drones reserved, so
  each drone is searched again. Only the single-drone shortest path is computed
  once, to obtain the horizon.
- **Memory**: the plan stores one state per drone and per turn, `O(N × T)`,
  and the reservation table stores one entry per occupied zone and turn.
- **Validator and simulation**: `O(N × T)`.

### Results on the maps of the subject

| Map | Drones | Turns | Optimum | Time |
|---|---|---|---|---|
| easy / linear path | 2 | 4 | 4 | 0.06 s |
| easy / simple fork | 4 | 4 | 4 | 0.04 s |
| easy / basic capacity | 4 | 4 | 4 | 0.04 s |
| medium / dead end trap | 5 | 8 | 8 | 0.04 s |
| medium / circular loop | 6 | 10 | 10 | 0.04 s |
| medium / priority puzzle | 5 | 6 | 6 | 0.06 s |
| hard / maze nightmare | 8 | 13 | 13 | 0.06 s |
| hard / capacity hell | 12 | 16 | 16 | 0.06 s |
| hard / ultimate challenge | 15 | 26 | 26 | 0.06 s |
| challenger / the impossible dream | 25 | **43** | 43 | 0.14 s |

Times are for the whole program (parsing, planning, validation and output).

### Limitations

- The planner is **greedy**: each drone takes the best route for itself,
  without looking at the whole fleet. It reaches the optimum on every map of
  the subject, but there is no proof that it does so on every possible map.
- The time grows faster than linearly with the number of drones, because the
  plan stores the waiting time of every drone and each search starts from turn
  0. With the first map and a growing number of drones, the whole program takes
  about 0.8 s with 500 drones and about 3 s with 1000 drones. It handles any
  number of drones, but thousands of drones take a long time.

## Visual representation

The simulation is shown with **colored terminal output**:

- Every movement is colored with the `color` of the **destination zone**. For a
  drone in flight towards a restricted zone, the color is the one of the zone it
  is going to reach.
- The color names of the map file are translated to ANSI escape codes by the
  `Palette` class (`red`, `blue`, `green`, `orange`, `gold`, `crimson`,
  `darkred`, `purple`, `lime`, and so on). The lookup ignores case.
- The subject accepts any single word as a color, so an **unknown color name is
  displayed without color** instead of being an error. For example, the
  challenger map uses `rainbow`, which has no ANSI equivalent.
- Colors are used only when stdout is a terminal and the `NO_COLOR` environment
  variable is not set. When the output is redirected to a file or a pipe, it
  contains no escape codes.
- The human summary goes to stderr, so it never mixes with the simulation
  lines.

Following a color from line to line makes it easy to see which drone is in
which zone, when several drones share a corridor, and when a drone is crossing
a restricted zone.

## Example

Input (the example map of the subject):

```
nb_drones: 5

start_hub: hub 0 0 [color=green]
end_hub: goal 10 10 [color=yellow]
hub: roof1 3 4 [zone=restricted color=red]
hub: roof2 6 2 [zone=normal color=blue]
hub: corridorA 4 3 [zone=priority color=green max_drones=2]
hub: tunnelB 7 4 [zone=normal color=red]
hub: obstacleX 5 5 [zone=blocked color=gray]
connection: hub-roof1
connection: hub-corridorA
connection: roof1-roof2
connection: roof2-goal
connection: corridorA-tunnelB [max_link_capacity=2]
connection: tunnelB-goal
```

Output (stdout):

```
D1-corridorA D3-hub-roof1
D1-tunnelB D2-corridorA D3-roof1 D5-hub-roof1
D1-goal D2-tunnelB D3-roof2 D4-corridorA D5-roof1
D2-goal D3-goal D4-tunnelB D5-roof2
D4-goal D5-goal
```

Summary (stderr): `Done: 5 turns, 5 drones delivered`.

How to read it:

- `D3-hub-roof1` in the first line means that D3 is crossing the connection
  `hub-roof1` towards the restricted zone `roof1`. It arrives in the next line
  (`D3-roof1`). D5 cannot start crossing before turn 2, because the connection
  has capacity 1 and is only freed when D3 arrives.
- D1, D2 and D4 use the priority corridor `corridorA` (capacity 2) and then
  `tunnelB`, one behind the other. The five drones arrive in 5 turns using
  both routes at the same time.

Errors are reported with the line of the map file:

```
$ python3 main.py bad_map.txt
Error: line 3: Unknown zone type 'banana'. Valid types: normal, blocked, restricted, priority

$ python3 main.py map_without_path.txt
Error: No path from 's' to 'e'
```

## Project structure

```
.
├── main.py              Entry point: parse, plan, validate, display
├── Makefile             install, run, debug, clean, lint, lint-strict
├── requirements.txt     Development dependencies
├── maps/                Maps of the subject and invalid maps for error handling
└── flyin/
    ├── zone.py          Zone and ZoneType (movement cost of each type)
    ├── connection.py    Connection between two zones
    ├── network.py       The graph: zones, connections, neighbours
    ├── errors.py        ParseError and UnsolvableError
    ├── parser.py        MapParser: map file to Network, with line errors
    ├── pathfinder.py    Dijkstra shortest path for one drone
    ├── reservations.py  ReservationTable: what the planned drones occupy
    ├── planner.py       Planner: earliest-arrival search over (zone, turn)
    ├── plan.py          Plan: the state of every drone at every turn
    ├── validator.py     Validator: checks a plan against the rules
    ├── simulation.py    Simulation: replays a plan turn by turn
    ├── renderer.py      TerminalRenderer: prints the simulation
    └── colors.py        Palette: color names to ANSI codes
```

## Design decisions

Points that the subject leaves open, and the choice made:

1. A `#` in the middle of a line is not a comment.
2. An empty metadata block `[]` means no metadata.
3. Integers accept only an optional `-` and ASCII digits.
4. An unknown metadata key is an error.
5. Zone names cannot contain `-`, whitespace, `[` or `]`.
6. `max_drones` is ignored on the start and end zones, even if its value is
   invalid.
7. A second `start_hub` or `end_hub` is an error.
8. A connection from a zone to itself is rejected.
9. The capacity of a connection is shared by both directions.
10. A drone that reached the end zone cannot leave it.
11. The name of a connection in flight follows the direction of travel
    (`origin-destination`), whatever the order used in the map file.
12. A turn in which nobody moves is printed as an empty line.
13. `priority` zones only break ties between paths with the same number of
    turns.
14. Drones are planned in order (`D1`, `D2`, ...), each one with the earliest
    arrival the previous reservations allow.
15. Only the exact simulation lines go to stdout. Everything else goes to
    stderr.
16. Colors are used only when stdout is a terminal and `NO_COLOR` is not set.
    An unknown color name is not colored.

## Testing

No test programs are included in this repository, as the subject asks for them
not to be submitted. The program protects itself instead: every plan is
checked by the `Validator` before it is printed, and a plan that breaks any
rule is never shown.

During development the program was run on all the maps of the subject, on
invalid maps (one for each parsing rule), on maps with no solution, and on
randomly generated maps, and the printed output was also checked by a separate
script that replays the text of the simulation and applies the rules of the
subject again.

## Resources

### References

- E. W. Dijkstra, *A note on two problems in connexion with graphs*,
  Numerische Mathematik 1, 1959.
- D. Silver, *Cooperative Pathfinding*, AIIDE 2005. The idea of planning the
  agents one after the other with a reservation table, over (position, time).
- R. Stern et al., *Multi-Agent Pathfinding: Definitions, Variants, and
  Benchmarks*, SoCS 2019.
- Python documentation: [`heapq`](https://docs.python.org/3/library/heapq.html),
  [`dataclasses`](https://docs.python.org/3/library/dataclasses.html),
  [`enum`](https://docs.python.org/3/library/enum.html) and
  [`typing`](https://docs.python.org/3/library/typing.html).
- [PEP 257](https://peps.python.org/pep-0257/) (docstrings) and
  [PEP 484](https://peps.python.org/pep-0484/) (type hints).
- [flake8](https://flake8.pycqa.org) and [mypy](https://mypy.readthedocs.io).
- [ANSI escape code](https://en.wikipedia.org/wiki/ANSI_escape_code) and the
  [NO_COLOR](https://no-color.org) convention.

### Use of AI

I used an AI assistant (Claude, by Anthropic) throughout the project, mainly as
a tutor and a reviewer:

- **Learning**: explanations of graph concepts, Dijkstra, time-expanded
  search, reservation tables, and of Python features such as `dataclasses`,
  `Enum`, `str.partition`, `heapq` and ANSI escape codes.
- **Design**: discussion of the architecture (parser, model, plan, validator,
  planner, renderer), of the representation of a plan, and of how to read the
  rules of the subject.
- **Code**: the models and the parser were written step by step with the
  guidance and the review of the assistant. Some modules (the validator, the
  planner, the reservation table, the simulation and the renderer) were
  drafted with the help of the assistant, and then read, tested and adapted by
  me.
- **Verification**: the assistant helped to review the code for bugs, and to
  build checks that are not part of this repository: a separate script that
  replays the printed output, random map generation, and a comparison with an
  exhaustive search on small maps.

Everything produced with the assistant was read, run against the maps of the
subject, and checked with `flake8` and `mypy`. I can explain every part of the
code.