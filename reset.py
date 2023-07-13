# this script should reset the waveshare display for off periods etc.
# takes about 10 seconds to run

import sys

sys.path.append('lib')
from waveshare_epd import epd7in5_V2
epd = epd7in5_V2.EPD()

print("Resetting screen...")

epd.init()
epd.Clear()
epd.sleep()

print("Done!")