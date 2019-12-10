# musmus
Muscle-controlled music performance. musmus stands for **mus**cle **mus**ic.

Check out the [instructions](instructions.md) for installation and use guidelines.

Here is a minimal working example that scans the available MIDI ports and selects the first available MIDI port to establish a connection to AudioMulch. It then guides the user through the MIDI mapping procedure. Finally, it triggers a snapshot and sets the (x,y) position on the Metasurface before closing the connection.

```python
import mido

from musmus.transmitter import Transmitter

port = mido.get_output_names()[1]

t = Transmitter(port, channel=1)
t.midi_mapping()
t.set_snap(1)
t.set_xy(1000, 1000)
t.stop()
```

## Requirements
* [PyQt5](https://wiki.python.org/moin/PyQt)
* [axopy](https://github.com/intellsensing/axopy)
* [pydaqs](https://github.com/intellsensing/pydaqs)
* [mido](https://github.com/mido/mido)
* [python-rtmidi](https://pypi.org/project/python-rtmidi/)

## Notes
* Tested only on Windows using Python 3.8.
