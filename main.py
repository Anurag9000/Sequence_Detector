import sys

def build_transitions(pattern: str, allow_overlap: bool = True):
    """Return (transitions, plen) for a single pattern using a KMP-like automaton."""
    seq = [ch for ch in pattern.strip()]
    plen = len(seq)

    def nxt(state_len, bit):
        temp = seq[:state_len] + [bit]
        limit = min(len(temp), plen)
        for size in range(limit, -1, -1):
            suffix = temp[-size:] if size > 0 else []
            prefix = seq[:size]
            if suffix == prefix:
                return size
        return 0

    transitions = {}
    for st in range(plen + 1):
        transitions[st] = {'0': nxt(st, '0'), '1': nxt(st, '1')}

    if not allow_overlap and plen >= 1:
        # After accepting, take transitions as if from S0 → “non-overlap”
        transitions[plen]['0'] = transitions[0]['0']
        transitions[plen]['1'] = transitions[0]['1']

    return transitions, plen

class StreamMultiDetector:
    """
    Tracks multiple patterns at once.
    - Precomputes a DFA per pattern.
    - On each input bit, updates states and counts.
    """
    def __init__(self, patterns, allow_overlap=True):
        self.patterns = patterns
        self.allow_overlap = allow_overlap
        self.tables = []
        self.plens = []
        for p in patterns:
            t, L = build_transitions(p, allow_overlap=allow_overlap)
            self.tables.append(t)
            self.plens.append(L)
        self.states = [0]*len(patterns)
        self.counts = [0]*len(patterns)

    def step(self, bit: str):
        if bit not in ('0','1'):
            raise ValueError("Bit must be '0' or '1'")
        for i in range(len(self.patterns)):
            t = self.tables[i]
            st = self.states[i]
            nxt = t[st][bit]
            self.states[i] = nxt
            if nxt == self.plens[i]:
                self.counts[i] += 1

    def snapshot(self):
        """Return (counts list) and (state list) for display."""
        return list(self.counts), list(self.states)

def prompt_patterns():
    print("Enter binary sequences to detect (one per line). Empty line to finish.")
    pats = []
    while True:
        line = input("> ").strip()
        if line == "":
            break
        if not line or any(c not in "01" for c in line):
            print("  (must be non-empty and only 0/1)")
            continue
        pats.append(line)
    if not pats:
        print("No patterns provided; exiting.")
        sys.exit(0)
    return pats

def prompt_overlap():
    print("\nMatching mode:")
    print("  1) Overlapping")
    print("  2) Non-overlapping")
    while True:
        choice = input("Enter 1 or 2: ").strip()
        if choice == "1":
            return True
        if choice == "2":
            return False
        print("Invalid choice. Please enter 1 or 2.")

def pretty_counts(patterns, counts):
    parts = []
    for p, c in zip(patterns, counts):
        parts.append(f"{p}:{c}")
    return " | ".join(parts)

def main():
    print("=== Multi Sequence Detector ===")
    patterns = prompt_patterns()
    allow_overlap = prompt_overlap()
    print("\nLoaded patterns:")
    for i, p in enumerate(patterns):
        print(f"  [{i}] {p} (len={len(p)})")
    print(f"Mode: {'overlap' if allow_overlap else 'non-overlap'}\n")

    det = StreamMultiDetector(patterns, allow_overlap=allow_overlap)

    print("Stream bits live. Enter:")
    print("  - single bit 0/1")
    print("  - multiple bits like 010110")
    print("  - 'show' to print counts")
    print("  - 'reset' to zero the stream state and counts")
    print("  - empty line to quit\n")

    while True:
        s = input("bit(s)> ").strip()
        if s == "":
            break
        if s.lower() == "show":
            counts, _ = det.snapshot()
            print("counts:", pretty_counts(patterns, counts))
            continue
        if s.lower() == "reset":
            det = StreamMultiDetector(patterns, allow_overlap=allow_overlap)
            print("State and counts reset.")
            continue
        # allow batch like "0100111"
        if any(ch not in "01" for ch in s):
            print("Only '0'/'1', 'show', 'reset', or empty to quit.")
            continue
        for ch in s:
            det.step(ch)
            counts, _ = det.snapshot()
            print(pretty_counts(patterns, counts))
    print("Bye.")

if __name__ == "__main__":
    main()
