from twisted.internet import reactor
import sys, os, signal
sys.path.append(os.path.dirname(__file__))
from kademlia.network import Server
from kademlia.log import Logger
from twisted.python import log
log.startLogging(sys.stdout)


# Run this with:
# reset; clear; rm ./cache.pickle ; PYTHONPATH=. python examples/server.py  8881 8882 8883
# reset; clear; rm ./cache.pickle ; PYTHONPATH=. python examples/server.py  8883 8882 8881
# reset; clear; rm ./cache.pickle ; PYTHONPATH=. python examples/server.py  8882 8881 8883

if __name__ == '__main__':
    n_transactions = 5
    if len(sys.argv) > 1:
        n_transactions = int(sys.argv[1])

    server = Server()
    klog = Logger(system=server)
    def signal_handler(signal, frame):
        klog.debug('You pressed Ctrl+C!')
        klog.debug ("In the end %s values stored on this server" % len(server.storage.data))
        reactor.callFromThread(reactor.stop)
    signal.signal(signal.SIGINT, signal_handler)
    #client = BenchmarkClient(server, n_transactions)

    strports = sys.argv[1:] if len(sys.argv) >3 else [ "8468", "8469" ]

    ports = [int(port) for port in strports]
    local_port = ports[0]
    bootstrap_addrs = [("127.0.0.1", port ) for port in ports[1:]]

    server.listen(local_port)
    server.bootstrap(bootstrap_addrs, fixed_supernode_addrs=bootstrap_addrs)#.addCallback(client.benchmark)
    reactor.run()

