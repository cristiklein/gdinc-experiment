from __future__ import division, print_function

from collections import defaultdict

import logging
import math
import random
import select
import socket
from sys import stderr
import libvirt
import shlex
import time

#
# Configuration
#
CAPACITY = 30 # cores
UDP_IP = "192.168.122.1"
UDP_PORT = 2712
REPRICING_INTERVAL = 1440 # seconds
    # i.e., every 24 minutes, i.e., every 24 hours of uncompressed trace

#
# Helper methods
#
def now():
        return time.time()

def saturate(x, low, high):
    return min(max(x, low), high)

#
# Business logic
#
class ServiceProvider:
    hypervisorConnection = None
    
    def __init__(self, name, addr, sock):
        self.name = name

        # Capacities (see paper)
        self.c_b = 1
        self.c_d = 1
        self.c_i = 1

        # Prices (see paper)
        self.p_b = 0
        self.p_d = 0
        self.nextPriceChangeAt = None

        # Actually billed
        self.totalBilled = 0

        # Which VM and how to communicate to it
        self.addr = addr
        self.sock = sock
        try:
            if ServiceProvider.hypervisorConnection is None:
                ServiceProvider.hypervisorConnection = libvirt.open('xen:///')
            self.vm = ServiceProvider.hypervisorConnection.lookupByName(name)
        except libvirt.libvirtError as e:
            logging.error("Error communicating with hypervisor '%s'; "
                "capacity for %s will not be enforced", e, name)
            self.vm = None

    def __str__(self):
        return self.name

    def send(self, data):
        self.sock.sendto(data, self.addr)

    def setCapacity(self, capacity): 
        if capacity < 0.1:
            capacity = 0.1
        ncpus = int(math.ceil(capacity))
        cap = int(capacity * 100)

        if self.vm:
            self.vm.setVcpus(ncpus)
            self.vm.setSchedulerParameters(
                { libvirt.VIR_DOMAIN_SCHEDULER_CAP: cap })

class InfrastructureProvider:
    def __init__(self, capacity, sock):
        self.capacity = capacity
        self.p_b = None
        self.p_d = None
        self.serviceProviders = dict()

        self.sock = sock

    def handleMessage(self, name, data, addr):
        # New SP, add to list
        if name not in self.serviceProviders:
            self.serviceProviders[name] = ServiceProvider(name=name, addr=addr, sock=self.sock)

        sp = self.serviceProviders[name]
        req = dict(token.split('=') for token in shlex.split(data))
        logging.debug("received request from %s: %s", sp, req)

        if 'c_b' in req and 'c_d' in req:
            try:
                sp.c_b = saturate(float(req['c_b']), 1, self.capacity)
                sp.c_d = saturate(float(req['c_d']), sp.c_b, self.capacity)
                sp.c_b = saturate(sp.c_b, 1, sp.c_d)

                logging.debug('> %s: c_b=%f c_d=%f', sp, sp.c_b, sp.c_d)
                sp.setCapacity(sp.c_d)

                # Ensure c_i <= c_d
                if getattr(req, 'c_i', sp.c_i) > sp.c_d:
                    req['c_i'] = sp.c_d
            except ValueError:
                logging.error('> invalid c_b or c_d')
        if 'c_i' in req:
            try:
                sp.c_i = min(float(req['c_i']), sp.c_d) # SP is never granted more than c_d
                logging.debug('> %s: c_i=%f', name, sp.c_i)
            except ValueError:
                logging.error('> invalid c_i')

    def doControl(self):
        logging.debug('controlling BEGIN')
        logging.debug('> known SPs: %s', self.serviceProviders.keys())

        self.updateBilling()
        self.updateSpotPrices()
        self.updateOfferedPrices()

        logging.debug('controlling END')

    def updateBilling(self):
        logging.debug('> updating billing')
        for name, sp in self.serviceProviders.items():
            # SP always pays for base capacity, but only
            # for what it consumes of dynamic capacity
            sp.totalBilled += \
                    sp.c_b * sp.p_b + \
                    max(sp.c_i - sp.c_b, 0) * sp.p_d
            logging.debug('> > %s: %s', name, sp.totalBilled)

    def updateSpotPrices(self):
        reserved_capacity = sum([ sp.c_b for sp in self.serviceProviders.values()])
        allocated_capacity = sum([ sp.c_d for sp in self.serviceProviders.values()])

        # TODO: Devise a valid method to compute base and dynamic spot prices
        core_cap = 2926
        self.p_b = 0.05/(12*core_cap)
        self.p_d = 0.07/(12*core_cap)

        logging.debug('> updating spot prices: reserved_capacity=%s allocated_capacity=%s p_b=%s p_d=%s',
            reserved_capacity, allocated_capacity, self.p_b, self.p_d)

    def updateOfferedPrices(self):
        logging.debug('> updating offered prices')
        for name, sp in self.serviceProviders.items():
            if sp.nextPriceChangeAt <= now():
                # SP's negotiation period expired
                # Sync prices offered to SP from spot infrastructure prices
                sp.p_b = self.p_b
                sp.p_d = self.p_d
                logging.debug('> > %s: p_b=%s p_d=%s', name, sp.p_b, sp.p_d)
                sp.nextPriceChangeAt = now() + REPRICING_INTERVAL

                sp.send('p_b=%s p_d=%s\n' % (sp.p_b, sp.p_d))

def main():
    logging.basicConfig(format='%(asctime)s.%(msecs).06d %(message)s', datefmt='%s', level=logging.DEBUG)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    poll = select.poll()
    poll.register(sock, select.POLLIN)

    infrastructureProvider = InfrastructureProvider(capacity=CAPACITY, sock=sock)

    nextControlAt = math.ceil(now() + 0.001)
    while True:
        waitFor = nextControlAt - now()
        events = None
        if waitFor > 0:
            events = poll.poll(waitFor * 1000)

        if events:
            data, addr = sock.recvfrom(1024)
            try:
                ip_addr, port = addr
                name = socket.gethostbyaddr(ip_addr)[0]
                infrastructureProvider.handleMessage(name=name, data=data,
                        addr=addr)
            except socket.herror as e:
                logging.error("Caught '{0}', message from '{1}' data '{2}'".
                    format(e, ip_addr, data.strip()))

        if now() >= nextControlAt:
            nextControlAt += 1
            infrastructureProvider.doControl()

if __name__ == '__main__':
    main()
