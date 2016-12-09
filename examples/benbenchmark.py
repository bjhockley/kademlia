from twisted.internet import reactor
from twisted.internet import defer
from twisted.internet import task
from kademlia.network import Server
from kademlia.log import Logger
import time
import copy
import sys
import signal
from twisted.python import log

log.startLogging(sys.stdout)

# time PYTHONPATH=. python examples/benbenchmark.py

class BenchmarkClient(object):
    def __init__(self, server, loops):
        self.verified_values = 0
        self.key_vals_to_store = [("a key %d" % i, "some value %s" % i) for i in range(0, loops)]
        self.failed_value_names = []
        self.server = server
        self.loops = loops
        self.log = Logger(system=self)


    @defer.inlineCallbacks
    def store_many(self, kv_list):
        """Stores all value v against key k for k, v in kv_list """
        self.log.debug("Attempting to store %s (key, val) pairs" % len(kv_list))
        dfrs = []
        for k, v in kv_list:
            dfrs.append(self.write_key_val(k, v))
        dl =  defer.DeferredList(dfrs, consumeErrors=True)
        res = yield dl
        writes_dispatched = len([succeeded  for succeeded, result in res if succeeded])
        defer.returnValue(writes_dispatched)

    @defer.inlineCallbacks
    def read_and_verify_many(self, kv_list):
        """Attempts to read all v stored against key k for k, v in kv_list - and
        keeps score if expected values are missing."""
        self.log.debug("Attempting to read and verify %s (key, val) pairs" % len(kv_list))
        dfrs = []
        self.verified_values = 0
        self.failed_value_names = []
        for k, v in kv_list:
            dfrs.append(self.read_key_val(k, v))
        dl =  defer.DeferredList(dfrs, consumeErrors=True)
        res = yield dl
        read_requests_dispatched = len([succeeded  for succeeded, result in res if succeeded])
        defer.returnValue(read_requests_dispatched)

    @defer.inlineCallbacks
    def retry_writes_and_reads(self):
        for retry in range(1, 6):
            yield self._sleep(6)
            self.log.debug("***************** Retrying failures ******************")
            self.log.debug("Retry %s: Failed to retrieve previously stored values for %s items: %s " % (retry, len(self.failed_value_names), self.failed_value_names))
            # self.log.debug("***************** Pinging ******************")
            # Ugly ugly hack
            #pingres = yield self.server.protocol.ping(('127.0.0.1', 8468), self.server.protocol.sourceNode.id)
            # self.log.debug("ping sent... : %s " % str(pingres))
            # bootstrapres = yield self.server.bootstrap([('127.0.0.1', 8468)])
            # self.log.debug("bootstrap sent... : %s " % str(bootstrapres))

            yield self._sleep(6)
            self.log.debug("***************** Retrying writes which failed verification ******************")
            failed_value_names_copy = copy.copy(self.failed_value_names)
            writes_dispatched = yield self.store_many(failed_value_names_copy)
            self.log.debug("Successfully dispatched %s (repeat)  write requests" % writes_dispatched)

            yield self._sleep(5)
            self.log.debug("***************** Retrying read ******************")
            read_requests_dispatched = yield self.read_and_verify_many(failed_value_names_copy)

            self.log.debug("Successfully dispatched %s (repeated) read requests" % read_requests_dispatched)
            self.log.debug("***************** Retrying summary ******************")
            self.log.debug("After write/read retry cycle %s, still failed to retrieve previously stored values for %s items: %s " % (retry, len(self.failed_value_names), self.failed_value_names))

            #self.log.debug("Fetching dump....")
            #dumpres = yield self.server.dump()
            #self.log.debug("Finally, dump result is : %s" %(dumpres,))

    @defer.inlineCallbacks
    def benchmark(self, _result):
        bw = time.time()
        writes_dispatched = yield self.store_many(self.key_vals_to_store)
        aw = time.time()
        self.log.debug("Successfully dispatched %s write requests" % writes_dispatched)

        read_requests_dispatched = yield self.read_and_verify_many(self.key_vals_to_store)
        ar = time.time()
        self.log.debug("Successfully dispatched %s read requests" % read_requests_dispatched)
        self.log.debug("%s of %s writes dispatched; took %s seconds = %s ops/sec" % (writes_dispatched, self.loops, aw - bw,  self.loops / (1.0 * aw - bw)  ))
        self.log.debug("%s of %s reads dispatched; took %s seconds = %s ops/sec  (verified values: %s; failed values %s)" % (read_requests_dispatched, self.loops, ar - aw, self.loops / (1.0 * ar - aw), self.verified_values, len(self.failed_value_names)))

        if self.failed_value_names:
            yield self.retry_writes_and_reads()
        else:
            self.log.debug("All values verified successfully")
        self.log.debug("In the end %s values stored on local node" % len(self.server.storage.data))

        reactor.stop()

    @defer.inlineCallbacks
    def write_key_val(self, key, val):
        yield self.server.set(key, val)


    @defer.inlineCallbacks
    def read_key_val(self, key, expected_value):
        result = yield self.server.get(key)
        if result == expected_value:
            self.verified_values = self.verified_values + 1
        else:
            self.log.debug( "Unexpected value read(k='%s'): got v='%s'; expected='%s'" % (key, result, expected_value))
            self.failed_value_names.append((key, expected_value))
        defer.returnValue(result)

    @defer.inlineCallbacks
    def _sleep(self, seconds):
        yield task.deferLater(reactor, seconds, lambda: True)


if __name__ == '__main__':
    n_transactions = 5
    if len(sys.argv) > 1:
        n_transactions = int(sys.argv[1])


    def signal_handler(signal, frame):
        print('You pressed Ctrl+C!')
        reactor.callFromThread(reactor.stop)
    signal.signal(signal.SIGINT, signal_handler)
    server = Server()
    client = BenchmarkClient(server, n_transactions)
    server.listen(5678)
    server.bootstrap([('127.0.0.1', 8468)], fixed_supernode_addrs=[('127.0.0.1', 8468)]).addCallback(client.benchmark)
    reactor.run()


