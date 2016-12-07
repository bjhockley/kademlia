from twisted.internet import reactor
from twisted.internet import defer
from twisted.python import log
from kademlia.network import Server
import time
import sys

# time PYTHONPATH=. python examples/benbenchmark.py


@defer.inlineCallbacks
def benchmark(_result, loops):
    bw = time.time()
    dfrs = []
    for i in range(0, loops):
        #yield write_key_val("a key", "some value")
        dfrs.append(write_key_val("a key %d" % i, "some value"))
    dl = defer.DeferredList(dfrs, consumeErrors=True)
    res = yield dl
    aw = time.time()

    print "write result:", res
    write_succs = len([succeeded  for succeeded, result in res if succeeded])


    dfrs = []
    for i in range(0, loops):
        #read_val = yield read_key_val("a key")
        dfrs.append(read_key_val("a key %d" % i))
    dl =  defer.DeferredList(dfrs, consumeErrors=True)
    res = yield dl
    ar = time.time()

    print "read result:", res
    read_succs = len([succeeded  for succeeded, result in res if succeeded])


    print "%s of %s writes succeeded took %s seconds = %s ops/sec" % (write_succs, loops, aw - bw,  loops / (1.0 * aw - bw)  )
    print "%s of %s reads succeeded and took %s seconds = %s ops/sec" % (read_succs, loops, ar - aw, loops / (1.0 * ar - aw)  )

    #print "Key result:", read_val
    reactor.stop()

@defer.inlineCallbacks
def write_key_val(key, val):
    yield server.set(key, val)


@defer.inlineCallbacks
def read_key_val(key):
    result = yield server.get(key)
    defer.returnValue(result)



server = Server()
server.listen(5678)
server.bootstrap([('127.0.0.1', 8468)]).addCallback(benchmark, 500)

reactor.run()


