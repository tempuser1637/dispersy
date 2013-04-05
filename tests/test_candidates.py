import unittest
from time import time

from ..dispersy import Dispersy
from ..callback import Callback
from ..debugcommunity import DebugCommunity
from ..crypto import ec_generate_key, ec_to_public_bin, ec_to_private_bin
from ..tool.tracker import TrackerCommunity

class TestCandidates(unittest.TestCase):

    def setUp(self):
        self.c = Callback()
        self.d = Dispersy(self.c, u".", u":memory:")
        ec = ec_generate_key(u"low")
        self.mm = self.d.get_member(ec_to_public_bin(ec), ec_to_private_bin(ec))
        
    def tearDown(self):
        self.d.stop()
        self.c.stop()
        
    def test_yield_introduce_candidates(self):
        self.__test_introduce(DebugCommunity.create_community)
            
    def test_tracker_yield_introduce_candidates(self):
        communities, candidates = self.__test_introduce(TrackerCommunity.create_community)
        
        #trackers should not prefer either stumbled or walked candidates, i.e. it should not return
        #candidate 1 more than once/in the wrong position
        now = time()
        c = communities[0]
        
        candidates[0].walk(c, now, 10.5)
        candidates[0].walk_response(c)
        
        expected = [("127.0.0.1", 5), ("127.0.0.1", 1), ("127.0.0.1", 2), ("127.0.0.1", 3), ("127.0.0.1", 4)]
        got = []

        for candidate in candidates:
            candidate.stumble(c, now)

            candidate = c.dispersy_yield_introduce_candidates(candidate).next()
            got.append(candidate.lan_address if candidate else None)
        
        self.assertEquals(expected, got)
        
    def __test_introduce(self, community_create_method):
        c = community_create_method(self.mm)
        candidates = []
        for i in range(5):
            address = ("127.0.0.1", i+1)
            candidate = c.create_candidate(address, False, address, address, u"unknown")
            candidates.append(candidate)
        
        now = time()
        expected = [None, ("127.0.0.1", 1), ("127.0.0.1", 2), ("127.0.0.1", 3), ("127.0.0.1", 4)]
        got = []

        for candidate in candidates:
            candidate.stumble(c, now)

            candidate = c.dispersy_yield_introduce_candidates(candidate).next()
            got.append(candidate.lan_address if candidate else None)
        
        self.assertEquals(expected, got)
        
        #ordering should not interfere between communities
        expected = [None, ("127.0.0.1", 5), ("127.0.0.1", 4), ("127.0.0.1", 3), ("127.0.0.1", 2)]
        got = []

        c2 = community_create_method(self.mm)        
        for candidate in reversed(candidates):
            candidate.stumble(c2, now)
            
            candidate = c2.dispersy_yield_introduce_candidates(candidate).next()
            got.append(candidate.lan_address if candidate else None)
        
        self.assertEquals(expected, got)
        return [c,c2], candidates
    
    def test_merge_candidates(self):
        c = DebugCommunity.create_community(self.d, self.mm)
        
        #let's make a list of all possible combinations which should be merged into one candidate
        candidates = []
        candidates.append(c.create_candidate(("1.1.1.1", 1), False, ("192.168.0.1", 1), ("1.1.1.1", 1), u"unknown"))
        candidates.append(c.create_candidate(("1.1.1.1", 2), False, ("192.168.0.1", 1), ("1.1.1.1", 2), u"symmetric-NAT"))
        candidates.append(c.create_candidate(("1.1.1.1", 3), False, ("192.168.0.1", 1), ("1.1.1.1", 3), u"symmetric-NAT"))
        candidates.append(c.create_candidate(("1.1.1.1", 4), False, ("192.168.0.1", 1), ("1.1.1.1", 4), u"unknown"))
        
        self.d._filter_duplicate_candidate(candidates[0])
        
        expected = [candidates[0].wan_address]
        
        got = []
        for candidate in self.d._candidates.itervalues():
            got.append(candidate.wan_address)
        
        self.assertEquals(expected, got)
