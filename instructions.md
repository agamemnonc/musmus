1. Download and install [AudioMulch](http://www.audiomulch.com/) (license required).

2. Download and install [loopMIDI](http://www.tobias-erichsen.de/software/loopmidi.html). This will be used to create virtual MIDI ports.

3. Open loopMIDI and create a new virtual MIDI port. If previous virtual MIDI ports have been created, your system might need a reboot to ensure they are cleared.

4. Open AudioMulch and go to View --> Parameter Control --> Metasurface. Create a MIDI mapping for each of `Snapshot Number`, `Interpolate_X`, `Interpolate_Y`. Make sure to use a different note for each of the three mappings.
Now you can send MIDI messages from anywhwere to control these three parameters outside AudioMulch.
<br/>*Important note*: The `midi_mapping()` method of `Transmitter` class automatically performs a mapping, however once the procedure is completed, the user is required to change the control type for `Interpolate_X` and `Interpolate_Y` in AudioMulch to `14 bit Control Change`. For information on how 14-bit CC messages work in AudioMulch, refer to [post](http://www.audiomulch.com/comment/1980#comment-1980).