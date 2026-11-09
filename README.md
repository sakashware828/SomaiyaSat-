# SomaiyaSat Mission Scheduler

An onboard data scheduler for a sub-1 W PocketQube satellite (SomaiyaSat / SomaiyaPod), built using **data structures**.
Use case: **KJS-SRS-01**

**Live demo:** https://YOUR-USERNAME.github.io/YOUR-REPO-NAME

## What it does

A satellite only has a few minutes of contact with the ground station on each pass, so it must decide what to send first. This project simulates that decision.

Packets wait in a priority queue and are sent in this order:

1. **TT&C** (telemetry and housekeeping)
2. **SSTV** (images)
3. **Codec2 / M17** (voice)

The scheduler reacts to conditions:

- Low battery (below 1.5 Wh): voice is delayed
- Poor link (below 0.4): SSTV images are delayed
- Battery reserve of 0.75 Wh is always kept for TT&C
- Buffer holds 30 packets; when full, the lowest-priority packet is dropped
- Watchdog forces a TT&C beacon if none was sent for 2 passes
- SAFE mode sends TT&C only

## Data structures used

All written from scratch (no `heapq` or built-in priority queue).

| Data structure | Used for | Time complexity |
|---|---|---|
| Binary min-heap | Priority queue | push, pop, remove, update: O(log n) |
| Hash map (dict) | Packet ID to heap position | O(1) |
| Circular buffer | Decision log | O(1) |
| Finite state machine | Deployment states and SAFE mode | O(1) |
| Greedy algorithm | Choosing what to send in a pass | O(k log n) |

## Files

| File | Description |
|---|---|
| `index.html` | Interactive website (open in any browser) |
| `data_structures.py` | Standalone data structure code with a demo |
| `satellite_scheduler_simple.py` | Full scheduler simulation in Python |

## How to run

**Website:** open `index.html` in a browser, or use the live demo link above.

1. Press **Advance deployment** three times to reach NOMINAL
2. Press **Add 10 packets**
3. Press **Run ground pass** and watch TT&C go out first
4. Try **Drain battery** or lower the link quality, then run another pass

**Python:**

```
python data_structures.py
python satellite_scheduler_simple.py
```

Requires Python 3. No extra libraries needed.

## Author

YOUR NAME · Roll No. YOUR ROLL NUMBER · K. J. Somaiya
