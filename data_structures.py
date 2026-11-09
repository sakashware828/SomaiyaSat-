# Data structures for SomaiyaSat scheduler (KJS-SRS-01)
# 1. Min-heap (priority queue)   2. Hash map (dict)
# 3. Circular buffer (log)       4. State machine


#  1 + 2. MIN-HEAP WITH HASH MAP
# heap = list of packets. pos = dict {packet_id: index in list}
# Packet = [priority, id, mode, size]

class MinHeap:
    def __init__(self):
        self.a = []        # heap array
        self.pos = {}      # hash map: id -> index

    def swap(self, i, j):
        self.a[i], self.a[j] = self.a[j], self.a[i]
        self.pos[self.a[i][1]] = i
        self.pos[self.a[j][1]] = j

    def sift_up(self, i):                     # O(log n)
        while i > 0:
            parent = (i - 1) // 2
            if self.a[i] < self.a[parent]:
                self.swap(i, parent)
                i = parent
            else:
                break

    def sift_down(self, i):                   # O(log n)
        n = len(self.a)
        while True:
            left = 2 * i + 1
            right = 2 * i + 2
            small = i
            if left < n and self.a[left] < self.a[small]:
                small = left
            if right < n and self.a[right] < self.a[small]:
                small = right
            if small == i:
                break
            self.swap(i, small)
            i = small

    def push(self, packet):                   # O(log n)
        self.a.append(packet)
        self.pos[packet[1]] = len(self.a) - 1
        self.sift_up(len(self.a) - 1)

    def peek(self):                           # O(1)
        return self.a[0] if self.a else None

    def pop(self):                            # O(log n)
        top = self.a[0]
        self.remove(top[1])
        return top

    def remove(self, pid):                    # O(log n), found in O(1) by hash map
        i = self.pos.pop(pid)
        last = self.a.pop()
        if i < len(self.a):
            self.a[i] = last
            self.pos[last[1]] = i
            self.sift_up(i)
            self.sift_down(i)

    def update_priority(self, pid, new_p):    # O(log n)  dynamic reordering
        i = self.pos[pid]
        old_p = self.a[i][0]
        self.a[i][0] = new_p
        if new_p < old_p:
            self.sift_up(i)
        else:
            self.sift_down(i)

    def rebuild(self, new_priority_fn):       # O(n)  heapify after conditions change
        for p in self.a:
            p[0] = new_priority_fn(p)
        for i in range(len(self.a) // 2 - 1, -1, -1):
            self.sift_down(i)

    def __len__(self):
        return len(self.a)


#  3. CIRCULAR BUFFER (decision log)
# fixed size, newest entry overwrites the oldest

class RingLog:
    def __init__(self, size):
        self.buf = [None] * size
        self.size = size
        self.head = 0
        self.count = 0

    def add(self, text):                      # O(1)
        self.buf[self.head] = text
        self.head = (self.head + 1) % self.size
        if self.count < self.size:
            self.count += 1

    def latest_first(self):
        out = []
        for i in range(self.count):
            out.append(self.buf[(self.head - 1 - i) % self.size])
        return out


#  4. FINITE STATE MACHINE
# table: state -> {event: next_state}

TRANSITIONS = {
    "STOWED":        {"separation_switch": "SEPARATED"},
    "SEPARATED":     {"timer_done": "COMMISSIONING"},
    "COMMISSIONING": {"beacon_ack": "NOMINAL"},
    "NOMINAL":       {"low_power": "SAFE"},
    "SAFE":          {"power_ok": "NOMINAL"},
}

class StateMachine:
    def __init__(self):
        self.state = "STOWED"

    def fire(self, event):                    # O(1)
        nxt = TRANSITIONS[self.state].get(event)
        if nxt is None:
            return False                      # illegal event is ignored
        self.state = nxt
        return True


#  DEMO
if __name__ == "__main__":
    PRIORITY = {"TTC": 0, "SSTV": 1, "CODEC2": 2, "M17": 2}

    h = MinHeap()
    packets = [("M17", 1500), ("SSTV", 9000), ("TTC", 150), ("CODEC2", 900)]
    for n, (mode, size) in enumerate(packets, start=1):
        h.push([PRIORITY[mode], n, mode, size])

    print("Send order:", end=" ")
    order = []
    while len(h):
        order.append(h.pop()[2])
    print(order)                              # ['TTC', 'SSTV', 'M17', 'CODEC2']  (same priority = first come first served)

    # dynamic reordering: promote packet 1 (M17) to top priority
    for n, (mode, size) in enumerate(packets, start=1):
        h.push([PRIORITY[mode], n, mode, size])
    h.update_priority(1, -1)
    print("After update_priority(M17 -> -1):", h.peek()[2])

    log = RingLog(3)
    for t in ["a", "b", "c", "d"]:
        log.add(t)
    print("Ring log (size 3):", log.latest_first())   # ['d', 'c', 'b']

    sm = StateMachine()
    for ev in ["separation_switch", "timer_done", "beacon_ack", "beacon_ack"]:
        print(ev, "->", sm.fire(ev), sm.state)
