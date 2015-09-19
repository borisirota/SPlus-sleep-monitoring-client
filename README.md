This code developed based on analyzing of S+ Resmed Andorid app and sniffing of bluetooth communication with device.

**This script was developed and tested on windows 8.1 x64**

## Requirements

* python 2.7
* pybluez for python (and all it's requirementes)
* gnuplot 5.0.1 (if you want to show live graph)

## Instructions
	
Pair the computer with the S+ bluetooth device.  
SPlus_client.py will connect to device by hard coded ADDRESS.  
You can uncomment the auto discover code to work with your specific device.  
SPlus_client.py will show ENV and BIO data and will dump plot.dat and plot2.dat files to the same dir.

You can run "gnuplot show_gnuplot.dem" to show live graph.