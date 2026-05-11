class Protocol:
    def __init__(self, name, packet_color, range_m, reliability, latency_ms):
        self.name = name
        self.packet_color = packet_color
        self.range_m = range_m
        self.reliability = reliability
        self.latency_ms = latency_ms

PROTOCOLS = {
    "DSRC": Protocol("DSRC", (0, 242, 255), 300, 0.82, 20.0),
    "C-V2X": Protocol("C-V2X", (57, 255, 20), 500, 0.92, 10.0),
    "5G-V2X": Protocol("5G-V2X", (188, 19, 254), 800, 0.99, 2.0)
}
