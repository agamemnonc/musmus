import mido


__all__ = ['Transmitter']


class Transmitter(object):
    def __init__(self, midi_port, note_x=60, note_y=61, note_snap=62):

        self.midi_port = midi_port
        self.note_x = note_x
        self.note_y = note_y
        self.note_snap = note_snap

        self.port = mido.open_output(self.midi_port)

    def midi_mapping(self):
        for note, function in zip(
               [self.note_x, self.note_y, self.note_snap],
               ['X', 'Y', 'Snap number']):
            wait = input("Triger {} midi mapping key.".format(function))
            msg = mido.Message('note_on', note=note, velocity=1)
            self._send_msg(msg)

    def set_position(self, x, y):
        for velocity, note in zip([x, y], [self.note_x, self.note_y]):
            msg = mido.Message('note_on', note=note, velocity=velocity)
            self._send_msg(msg)

    def set_snap(self, snap):
        """snap: 1-based indexing"""
        msg = mido.Message('note_on', note=self.note_snap, velocity=snap-1)
        self._send_msg(msg)

    def _send_msg(self, msg):
        self.port.send(msg)

    def stop(self):
        self.port.close()

    def __del__(self):
        self.stop()
