1. Download and install [audiomulch](http://www.audiomulch.com/) (license required).

2. Download and install [loopmidi](http://www.tobias-erichsen.de/software/loopmidi.html). This will be used to create virtual Midi ports.

3. Open loopmidi and create a new virtual midi port. If previous virtual midi ports have been created, your system might need a reboot to ensure they are cleared.

4. Open audiomulch and go to View --> Parameter Control --> Metasurface. Create a MIDI mapping for each of `Snapshot Number`, `Interpolate_X`, `Interpolate_Y`. Make sure to use a different note for each of the three mappings.
Now you can send MIDI messages from anywhwere to control these three parameters outside audiomulch.

