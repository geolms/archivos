import struct
from time import strftime
import datetime as dt
import sys

import matplotlib as mpl
mpl.rcParams['figure.subplot.left'] = 0.06
mpl.rcParams['figure.subplot.right'] = 0.95
mpl.rcParams['figure.subplot.bottom'] = 0.09
mpl.rcParams['figure.subplot.top'] = 0.95
mpl.rcParams['agg.path.chunksize'] = 20000

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

mask = 7

bits = 16
vref = 2500.0
ztime = 3*60*60
med_ok = 0

file = open(sys.argv[1],"rb")

format = struct.unpack("B", file.read(1))[0]
print "file format:", format

if format >= 3:
  uidl = struct.unpack("I", file.read(4))[0]
  uidlm = struct.unpack("I", file.read(4))[0]
  uidhm = struct.unpack("I", file.read(4))[0]
  uidh = struct.unpack("I", file.read(4))[0]
  print "id:%d.%d.%d.%d"%(uidl, uidlm, uidhm, uidh)

nbyte = struct.unpack("B", file.read(1))[0]
gain = (nbyte >> 4) & 0xF
gain = 2.0**gain
average = nbyte & 0xF
print "gain:", gain
print "average:", average

tick_useg = struct.unpack("I", file.read(4))[0]
print "tick_useg:", tick_useg

type = struct.unpack("B", file.read(1))[0]
print "type:", type

time_begin = struct.unpack("I", file.read(4))[0]
print "time_begin: %02u:%02u:%02u" % (time_begin/(60*60), (time_begin%(60*60))/60, time_begin%60)
time_end = struct.unpack("I", file.read(4))[0]
print "time_end: %02u:%02u:%02u" % (time_end/(60*60), (time_end%(60*60))/60, time_end%60)

vbat = struct.unpack("f", file.read(4))[0]
print "vbat:", vbat

rtc_clock = struct.unpack("I", file.read(4))[0]
print "rtc_begin: %s"%(dt.datetime.fromtimestamp(rtc_clock+ztime).strftime('%H:%M:%S %Y-%m-%d'))

adc_play_cnt = struct.unpack("I", file.read(4))[0]
print "adc_play_cnt:", adc_play_cnt

error_start = struct.unpack("I", file.read(4))[0]
print "error_start:", error_start

dtime = tick_useg*adc_play_cnt/1000000.0

print "dtime:", dtime

time = rtc_clock%(24*60*60)

utime = tick_useg/1000000.0

x = []
y = []
z = []
t = np.arange(0, dtime, tick_useg/1000000.0)

alpha = 0
beta = 1.0
#beta = 1.0/0.8057
offset_x = 0.0
offset_y = 0.0
offset_z = 0.0
gain = 1.0

words = ""
ok = True
Ndata = adc_play_cnt
for i in xrange(Ndata):
  word = file.read(6)

  words += word
  if len(words) > 20:
    words = words[-20:]

  if len(word) == 6:
    sample = struct.unpack("HHH", word)
    x.append(1*(offset_x+vref*((sample[0]/2.0**bits)-0.5)*beta/gain+alpha))
    y.append(1*(offset_y+vref*((sample[1]/2.0**bits)-0.5)*beta/gain+alpha))
    z.append(1*(offset_z+vref*((sample[2]/2.0**bits)-0.5)*beta/gain+alpha))
    if (Ndata - i) < 10:
      print sample[0], sample[1], sample[2]
  else:
    ok = False
    break

if ok:
  word = file.read(20)
  words += word
if len(words) > 20:
  words = words[-20:]

data = struct.unpack("IIIif", words)
print "buffer_errors:", data[0]
print "adc_errors:", data[1]
print "rtc_end: %s" % (dt.datetime.fromtimestamp(data[2]+ztime).strftime('%H:%M:%S %Y-%m-%d'))
print "adc_play_cnt:", data[3]
print "vbat:", data[4]
print "length:", len(x)
print "med:", sum(x)/len(x), sum(y)/len(y), sum(z)/len(z)
if (mask & 0b100) > 0:
  line, = plt.plot(t[0:len(x)], np.array(x)-med_ok*sum(x)/len(x), 'r')
if (mask & 0b010) > 0:
  line, = plt.plot(t[0:len(y)], np.array(y)-med_ok*sum(y)/len(y), 'b')
if (mask & 0b001) > 0:
  line, = plt.plot(t[0:len(z)], np.array(z)-med_ok*sum(z)/len(z), 'g')
plt.xlabel('time (s)')
plt.ylabel('mV')
file.close()
plt.show()
