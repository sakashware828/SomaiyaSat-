# SomaiyaSat data scheduler (KJS-SRS-01)
# Uses a priority queue (min-heap made by hand) to decide which data to send first.
# Priority: TTC (0) -> SSTV (1) -> voice CODEC2/M17 (2). Smaller number = sent first.

import random

priority = {"TTC": 0, "SSTV": 1, "CODEC2": 2, "M17": 2}


#  min heap (stored in a list)
# each item is (priority, order_number, mode, size)
heap = []

def push(item):
    heap.append(item)
    i = len(heap) - 1
    while i > 0:
        parent = (i - 1) // 2
        if heap[i] < heap[parent]:
            heap[i], heap[parent] = heap[parent], heap[i]
            i = parent
        else:
            break

def pop():
    top = heap[0]
    last = heap.pop()
    if len(heap) > 0:
        heap[0] = last
        i = 0
        while True:
            left = 2 * i + 1
            right = 2 * i + 2
            small = i
            if left < len(heap) and heap[left] < heap[small]:
                small = left
            if right < len(heap) and heap[right] < heap[small]:
                small = right
            if small == i:
                break
            heap[i], heap[small] = heap[small], heap[i]
            i = small
    return top


#  satellite settings
battery = 4.0          # Wh
battery_max = 5.0
counter = 0            # keeps first-come-first-served inside same priority
max_buffer = 30        # satellite memory is limited
dropped = 0            # how many packets were thrown away


def add_packet(mode, size):
    global counter, dropped
    if len(heap) >= max_buffer:
        # buffer full: remove the lowest priority packet to make room
        worst = max(heap)
        if priority[mode] >= worst[0]:
            dropped += 1
            return
        heap.remove(worst)
        dropped += 1
        # rebuild heap after removing from the middle
        old = heap[:]
        heap.clear()
        for x in old:
            push(x)
    counter += 1
    push((priority[mode], counter, mode, size))


def reorder_for_conditions(link):
    # change priorities when battery is low or link is bad, then rebuild heap
    old = heap[:]
    heap.clear()
    for p, c, mode, size in old:
        new_p = p
        if mode != "TTC":
            if battery < 1.5 and mode in ("CODEC2", "M17"):
                new_p = p + 3          # save power, voice can wait
            if link < 0.4 and mode == "SSTV":
                new_p = p + 2          # image is big, wasteful on bad link
        push((new_p, c, mode, size))


def run_pass(pass_time, link):
    global battery
    bitrate = 9600 * link              # bits per second after link loss
    time_left = pass_time
    sent = {"TTC": 0, "SSTV": 0, "CODEC2": 0, "M17": 0}
    skipped = []

    reorder_for_conditions(link)

    while len(heap) > 0 and time_left > 0:
        item = pop()
        mode = item[2]
        size = item[3]
        airtime = size * 8 / bitrate
        energy = airtime * 1.2 / 3600  # 1.2 W transmitter

        if airtime > time_left:
            skipped.append(item)       # does not fit in this pass
            continue
        if mode != "TTC" and battery - energy < 0.75:
            skipped.append(item)       # keep reserve battery for TTC
            continue

        time_left -= airtime
        battery -= energy
        sent[mode] += 1

    for item in skipped:               # put unsent packets back
        push(item)

    # after the pass: bus uses power, solar panels charge
    battery = battery - 0.55 + 0.9
    if battery > battery_max:
        battery = battery_max
    return sent


#  simple deployment state machine
state = "STOWED"
steps = [("STOWED", "separation_switch", "SEPARATED"),
         ("SEPARATED", "timer_done", "COMMISSIONING"),
         ("COMMISSIONING", "beacon_ack", "NOMINAL")]

for old_state, event, new_state in steps:
    if state == old_state:
        print("State:", state, "->", new_state, "(", event, ")")
        state = new_state


#  simulation
random.seed(5)
sizes = {"TTC": (100, 200), "SSTV": (6000, 14000), "CODEC2": (800, 2500), "M17": (1000, 3000)}

print()
print(f"{'Pass':<6}{'Link':<7}{'Battery':<10}{'TTC':<5}{'SSTV':<6}{'CODEC2':<8}{'M17':<5}{'Left':<6}{'Dropped'}")
print("-" * 60)
for n in range(1, 7):
    dropped = 0
    for i in range(random.randint(25, 40)):
        mode = random.choice(["TTC", "SSTV", "CODEC2", "M17", "M17"])
        add_packet(mode, random.randint(sizes[mode][0], sizes[mode][1]))
    link = round(random.uniform(0.25, 1.0), 2)
    r = run_pass(random.choice([200, 300, 400]), link)
    print(f"{n:<6}{link:<7}{battery:<10.2f}{r['TTC']:<5}{r['SSTV']:<6}{r['CODEC2']:<8}{r['M17']:<5}{len(heap):<6}{dropped}")
