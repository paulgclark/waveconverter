# waveconverter_proto
(c) Factoria Labs 2016
WaveConverter is a Python application, built on GTK+ 3. The GUI has been
implemented via Glade. A sqlite database has been implemented via
sqlalchemy. Finally, waveform plotting uses matplotlib.

To install pre-requisites for execution:
sudo apt-get install python-sqlalchemy

sudo apt-get install libgtk-3-dev

sudo apt-get isntall python-matplotlib

If you are contributing to development, you will also need glade:
sudo apt-get install glade


To execute a test using an attached input I-Q file:
cd <install path>/src
./packet_decode.py -q ../input_files/chevy_unlock_00_c315p1M_s400k.dat  -o ../output_files/test.log -s 400000 -c 315100000 -v -g -p -1

This will pre-load the appropriate protocol and input file. Clicking the Demod button
will then produce a baseband waveform. Clicking the Decode button will then produce
decoded data.
