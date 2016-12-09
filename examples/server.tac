from twisted.application import service, internet
from twisted.python.log import ILogObserver
from twisted.internet import reactor, task, defer

import sys, os
sys.path.append(os.path.dirname(__file__))
from kademlia.network import Server
from kademlia import log

application = service.Application("kademlia")
application.setComponent(ILogObserver, log.FileLogObserver(sys.stdout, log.INFO).emit)

if os.path.isfile('cache.pickle'):
    kserver = Server.loadState('cache.pickle')
else:
    kserver = Server()
    kserver.bootstrap([("127.0.0.1", 5678)], fixed_supernode_addrs=[('127.0.0.1', 5678)])
kserver.saveStateRegularly('cache.pickle', 10)

server = internet.UDPServer(8468, kserver.protocol)
server.setServiceParent(application)

@defer.inlineCallbacks
def graceful_shutdown():
    print "Shutting down ..."
    print ("In the end %s values stored on local node" % len(kserver.storage.data))
    yield defer.succeed(True)

reactor.addSystemEventTrigger('before', 'shutdown', graceful_shutdown)


