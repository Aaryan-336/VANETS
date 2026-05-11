class Vehicle:
    def __init__(self, vid, pos, angle, protocol):
        self.vid = vid
        self.pos = pos
        self.angle = angle
        self.speed = 0
        self.protocol = protocol
        self.signal_wave_radius = 0

    def update(self, pos, angle, speed):
        self.pos = pos
        self.angle = angle
        self.speed = speed