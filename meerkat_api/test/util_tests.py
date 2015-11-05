"""
util unit tests
"""
import unittest

from meerkat_api import util
from meerkat_abacus import model

class UtilTests(unittest.TestCase):

    def test_is_child(self):
        """ test is child"""
        locations = {1: model.Locations(name="Demo"),
                     2: model.Locations(name="Region 1",
                                        parent_location=1),
                     3: model.Locations(name="Region 2",
                                        parent_location=1),
                     4: model.Locations(name="District 1",
                                        parent_location=2),
                     5: model.Locations(name="District 2",
                                        parent_location=3),
                     6: model.Locations(name="Clinic 1",
                                        parent_location=4),
                     7: model.Locations(name="Clinic 2",
                                        parent_location=5)
                     }
        assert util.is_child(1, 3, locations)
        assert util.is_child(2, 4, locations)
        assert util.is_child(1, 7, locations)
        assert util.is_child(3, 7, locations)
        assert util.is_child("3", "7", locations)
        assert not util.is_child(3, 6, locations)
        assert not util.is_child(2, 5, locations)

    
        



        
