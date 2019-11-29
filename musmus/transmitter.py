import mido


__all__ = ['Transmitter']


class Transmitter(object):
    def __init__(
            self,
            midi_port,
            channel=1,
            control_x=0,
            control_y=1,
            control_snap=2):

        self.midi_port = midi_port
        self.channel = channel
        self.control_x = control_x
        self.control_y = control_y
        self.control_snap = control_snap

        self._init()

    def _init(self):
        self.port_ = mido.open_output(self.midi_port)
        # Midi port numbering uses 1-based indexing
        self.channel_ = self.channel - 1

    def midi_mapping(self):
        for cback, param_name in zip(
               [self.set_x, self.set_y, self.set_snap],
               ['Interpolate_X', 'Interpolate_Y', 'Snapshot number']):
            wait = input("Click {} midi mapping key".format(param_name))
            # Callback function with arbitrary value
            cback(1)

    def set_x(self, x):
        self._set_position(axis='x', pos=x)

    def set_y(self, y):
        self._set_position(axis='y', pos=y)

    def set_xy(self, x, y):
        self.set_x(x)
        self.set_y(y)

    def set_snap(self, snap):
        """snap: 1-based indexing"""
        msg = self._make_msg(self.control_snap, snap - 1)
        self._send_msg(msg)

    def _make_msg(self, control, value):
        msg = mido.Message(
            'control_change',
            channel=self.channel_,
            control=control,
            value=value)

        return msg

    def _set_position(self, axis, pos):
        if axis == 'x':
            control = self.control_x
        elif axis == 'y':
            control = self.control_y
        else:
            raise ValueError('Only x and y axes are supported.')

        msg = self._make_msg(control, pos)
        self._send_msg(msg)

    def _send_msg(self, msg):
        self.port_.send(msg)

    def stop(self):
        self.port_.close()

    def __del__(self):
        self.stop()
