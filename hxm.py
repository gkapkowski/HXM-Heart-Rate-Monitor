# -*- coding: utf-8 -*-
# HXM BT message decoding adapted from HXM Tracker by Jari Multisilta
#  http://www.my-maemo.com/software/applications.php?name=HXM_Tracker&faq=38&fldAuto=1293

from struct import unpack
import bluetooth
import logging
import time
import sys
import time

DEVICE_NAME = "HXM"
log = logging.getLogger("hxm")

class HXM(object):
    MAX_RETRIES = 3
    PROTOCOL = '<BBHccHccBBBHHHHHHHHHHHHHHHHHHHHBBHBB'
    FIELD_NAMES = ['msg_id', 
                 'dlc', 
                 'firmware_id', 
                 'firmware_vesrion_a',
                 'firmware_vesrion_b', 
                 'hardware_id', 
                 'hardware_version_a',
                 'hardware_version_b',
                 'battery', 
                 'heart_rate', 
                 'heart_beat_number', 
                 'heart_beat_1', 
                 'heart_beat_2', 
                 'heart_beat_3',
                 'heart_beat_4', 
                 'heart_beat_5', 
                 'heart_beat_6', 
                 'heart_beat_7', 
                 'heart_beat_8', 
                 'heart_beat_9',
                 'heart_beat_10', 
                 'heart_beat_11', 
                 'heart_beat_12', 
                 'heart_beat_13', 
                 'heart_beat_14', 
                 'heart_beat_15',
                 'reserved_1', 
                 'reserved_2', 
                 'reserved_3', 
                 'distance', 
                 'speed', 
                 'strides', 
                 'reserved_4', 
                 'reserved_5', 
                 'crc', 
                 'etx']
    _stop = False
    
    def __init__(self, addr):
        self.addr = addr
        
    def discover(self):
        tries = 0
        while tries < self.MAX_RETRIES and not self._stop:
            tries += 1
            log.info("Scanning bluetooth devices... (try {i} of {max})".format(i=tries,
                                                                               max=self.MAX_RETRIES))

            for addr, name in bluetooth.discover_devices(lookup_names=True):
                log.info("Found device: %s (%s)" % (name, addr))
                if name is not None and name.startswith(DEVICE_NAME):
                    return addr

    def connect(self):
        """Connect to HXM, return socket or None on failure."""

        socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        
        if not self.addr:
            self.addr = self.discover()
            
        if self.addr is None:
            log.info("No usable BT devices found")
            return None

        log.debug("Connecting to BT address: %s" % self.addr)
        socket.connect((self.addr, 1))
        return socket
    
    def decode_data(self, data):
        if len(data) == 59:
            return dict(zip(self.FIELD_NAMES, unpack(self.PROTOCOL, data)))
        
        log.info("Could not decode data: {data}".format(data=data))

    def listen(self, socket, results_receiver):
        while not self._stop:
            data = socket.recv(60)
            results_receiver(self.decode_data(data))

    def run(self, results_receiver=None):
        socket = None
        while not self._stop:
            try:
                if socket is None:
                    time.sleep(1)
                    socket = self.connect()
                else:
                    self.listen(socket, results_receiver)
            except bluetooth.BluetoothError, ex:
                log.exception("Bluetooth error, will try to reconnect")
                socket = None

    def stop(self):
        """ Signal run() to return as soon as possible. """
        self._stop = True


if __name__ == "__main__":
    from optparse import OptionParser
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    
    usage = "usage: %prog [options]"
    parser = OptionParser(usage)
    parser.add_option("-a", "--addr", dest="addr",
                      help="HXM device bluetooth address")
    parser.add_option("-r", "--raw", dest="raw", action='store_true',
                      default=False, help="Print raw data")
    parser.add_option("-f", "--file", dest="file", 
                      help="Save results to file")


    (options, args) = parser.parse_args()
    
    datafile = sys.stdout
    if options.file:
        datafile = open(options.file, 'w')

    def printer(data):
        if data:
            print data['heart_rate']
            if options.raw:
                datafile.write(str(data['heart_rate']))
            else:
                datafile.write("Received HR: {hr}, bat: {bat}".format(hr=data['heart_rate'], 
                                                                      bat=data['battery']))
            datafile.write('\n')
    
    hxm = HXM(options.addr)
    try:
        hxm.run(printer)
    except KeyboardInterrupt:
        datafile.close()
    