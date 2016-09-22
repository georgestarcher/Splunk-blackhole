#!/usr/bin/python
#--------------------------------------------------------------------------------
import sys
import os
import os.path
import pprint
import logging
import datetime
import time
import subprocess
import StringIO

SPLUNK_URL = 'https://192.168.96.1:8089'
SPLUNK_USER = 'admin'
SPLUNK_PASSWORD = 'abc123'
SPLUNK_APP = 'search'
SPLUNK_COLLECTION='blackhole'


sys.path.append(os.path.realpath(os.path.dirname(os.path.realpath(sys.argv[0]))+'/../lib'))
import simple_kvstore 


# create logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# add formatter to ch
ch.setFormatter(formatter)
# add ch to logger
logger.addHandler(ch)

logging.getLogger('requests.packages.urllib3.connectionpool').setLevel(logging.ERROR)
logging.getLogger('urllib3.connectionpool').setLevel(logging.ERROR)

def get_kv_connection(url=SPLUNK_URL,app=SPLUNK_APP,collection=SPLUNK_COLLECTION,login=SPLUNK_USER,password=SPLUNK_PASSWORD,json_cls=None):
    return simple_kvstore.KV(url,app,collection,login='admin',password='abc123')

# This is very quagga specific, using vtysh and assumptions.
# Future revs should make this part pluggable for other
# types of devices and/or API'ing opportunities.  
def addBlackhole(cidr):
    if cidr is None:
        return 1
    # else

    devnull=open('/dev/null','w')
    cmds=[
            'vtysh',
            '-c',
            'configure terminal',
            '-c',
            'ip route %s null0' % cidr,
            '-c',
            'exit',
            '-c',
            'write mem'
            ]
    return subprocess.call(cmds,stdout=devnull,stderr=devnull)

def removeBlackhole(cidr):
    if cidr is None:
        return 1
    # else

    devnull=open('/dev/null','w')
    cmds=[
            'vtysh',
            '-c',
            'configure terminal',
            '-c',
            'no ip route %s null0' % cidr,
            '-c',
            'exit',
            '-c',
            'write mem'
            ]
    return subprocess.call(cmds,stdout=devnull,stderr=devnull)

def checkRouteExists(cidr):
    if cidr is None:
        return False

    devnull=open('/dev/null','w')
    cmds=[
            'vtysh',
            '-c',
            'show ip route static'
        ]


    q=subprocess.check_output(cmds,stderr=devnull,universal_newlines=True)
    f=StringIO.StringIO(q)
    for line in f:
        if line[0]=="S":
            if line.split()[1]==cidr:
                return True

    return False


#-------------- MAIN ENTRY ------------------------------

collection = get_kv_connection()

for r in collection.get():
    if 'blackhole' in r and 'cidr' in r:
        if r.get('blackhole',True) and not checkRouteExists(r.get('cidr',None)):
            rc=addBlackhole(r.get('cidr',None))
            if rc == 0:
                logger.info("Add blackhole for %s successful.  Requestor=%s at=%d" % (r.get('cidr'),r.get('username'),r.get('time')))
            else:
                logger.error("Add blackhole for %s failed rc=%d.  Requestor=%s at=%d" % (r.get('cidr'),rc,r.get('username'),r.get('time')))

        elif not r.get('blackhole',True) and checkRouteExists(r.get('cidr',None)):
            rc=removeBlackhole(r.get('cidr',None))
            if rc == 0:
                logger.info("Remove blackhole for %s successful.  Requestor=%s at=%d" % (r.get('cidr'),r.get('username'),r.get('time')))
            else:
                logger.error("Remove blackhole for %s failed rc=%d.  Requestor=%s at=%d" % (r.get('cidr'),rc,r.get('username'),r.get('time')))


