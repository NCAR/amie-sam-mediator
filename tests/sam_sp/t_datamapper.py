#!/usr/bin/env python
import unittest
import json
from time import sleep
from sam_sp.datamapper import (MAP, map_data,
                               COPY_SRC_OR_ADD_NONE,
                               COPY_SRC_OR_ADD_BLANK,
                               COPY_SRC_IF_SRC_SET,
                               COPY_SRC_IF_SRC_SET_TARG_UNSET)

TEST_SRC_TARG_PAIRS = [
    ('APacket',           'PeopleOrgSearchParms'),
    ('PeopleExternalOrg', 'AMIEOrg'),
    ('APacket',           'choose_or_add_institution'),
    ('APacket',           'PeoplePersonSearchParms'),
    ('APacket',           'choose_or_add_person'),
    ('APacket',           'activate_person'),
    ('APacket',           'choose_or_add_contract'),
    ('APacket',           'choose_area_of_interest'),
    ('APacket',           'choose_or_add_mnemonic_code'),
    ('PeoplePerson',      'AMIEPerson'),
    ('APacket',           'create_project'),
    ('APacket',           'reactivate_project'),
    ('APacket',           'inactivate_project'),
    ('APacket',           'create_account'),
    ('APacket',           'inactivate_account'),
    ('APacket',           'reactivate_account'),
    ('APacket',           'renew_allocation'),
    ('APacket',           'supplement_allocation'),
    ('APacket',           'adjust_allocation'),
    ('APacket',           'extend_allocation'),
    ('APacket',           'modify_user'),
    ('APacket',           'merge_person'),
]

CSOAN_map = None
CSOAN_src_targ = None
CSOAB_map = None
CSOAB_src_targ = None
CSISS_map = None
CSISS_src_targ = None
CSISSTU_map = None
CSISSTU_src_targ = None


def init_tests():
    global TEST_SRC_TARG_PAIRS
    global CSOAN_map
    global CSOAN_src_targ
    global CSOAB_map
    global CSOAB_src_targ
    global CSISS_map
    global CSISS_src_targ
    global CSISSTU_map
    global CSISSTU_src_targ
    for src_targ_pair in TEST_SRC_TARG_PAIRS:
        submap = MAP.get(src_targ_pair,None)
        st_pair = "('" + src_targ_pair[0] + "', '" + src_targ_pair[1] + "')"

        for l2key in submap.keys():
            if l2key == COPY_SRC_OR_ADD_NONE:
                if CSOAN_map is None:
                    CSOAN_map = submap[l2key]
                    CSOAN_src_targ = src_targ_pair
            elif l2key == COPY_SRC_OR_ADD_BLANK:
                if CSOAB_map is None:
                    CSOAB_map = submap[l2key]
                    CSOAB_src_targ = src_targ_pair
            elif l2key == COPY_SRC_IF_SRC_SET:
                if CSISS_map is None:
                    CSISS_map = submap[l2key]
                    CSISS_src_targ = src_targ_pair
            elif l2key == COPY_SRC_IF_SRC_SET_TARG_UNSET:
                if CSISSTU_map is None:
                    CSISSTU_map = submap[l2key]
                    CSISSTU_src_targ = src_targ_pair
            else:
                self.assertTrue(False,
                                msg="unknown key under "+st_pair+": "+l2key)

init_tests()
        
class Test_MAP(unittest.TestCase):

    def test_MAP(self):
        global TEST_SRC_TARG_PAIRS
        global CSOAN_map
        global CSOAB_map
        global CSISS_map
        global CSISSTU_map
        for src_targ_pair in TEST_SRC_TARG_PAIRS:
            submap = MAP.get(src_targ_pair,None)
            st_pair = "('" + src_targ_pair[0] + "', '" + src_targ_pair[1] + "')"
            self.assertIsNotNone(submap,
                                 msg="no " + st_pair + " map");
            
        self.assertIsNotNone(CSOAN_map,
                             msg="current MAP will not support " + \
                             "COPY_SRC_OR_ADD_NONE test");
        
        self.assertIsNotNone(CSOAB_map,
                             msg="current MAP will not support " + \
                             "COPY_SRC_OR_ADD_BLANK test");
        
        self.assertIsNotNone(CSISS_map,
                             msg="current MAP will not support " + \
                             "COPY_SRC_IF_SRC_SET test");
        
        self.assertIsNotNone(CSISSTU_map,
                             msg="current MAP will not support " + \
                             "COPY_SRC_IF_SRC_SET_TARG_UNSET test");

class Test_map_data_unmapped(unittest.TestCase):

    def test_unmapped(self):
        global TEST_SRC_TARG_PAIRS
        test_in = dict()
        test_target = dict()
        test_target['foo'] = None

        for src_targ_pair in TEST_SRC_TARG_PAIRS:
            src = src_targ_pair[0]
            targ = src_targ_pair[1]

            new_target = map_data(src, targ, test_in, test_target)

            self.assertTrue('foo' in new_target,
                            msg="unmapped key not copied when value " + \
                            "None for ('"+src+"', '"+targ+"')")

            test_target['foo'] = 'bar'

            new_target = map_data(src, targ, test_in, test_target)

            self.assertTrue(new_target['foo'] == 'bar',
                            msg="unmapped key not copied when value set " +\
                            "for ('"+src+"', '"+targ+"')")


def setup_test_parms(cls, map, src_targ):
    cls.test_map = map

    cls.src_key = None
    cls.targ_key = None
    for skey in map.keys():
        cls.src_key = skey
        cls.targ_key = cls.test_map[skey]
        break
        
    cls.src = src_targ[0]
    cls.targ = src_targ[1]
    

class Test_COPY_SRC_OR_ADD_NONE(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        global CSOAN_map
        global CSOAN_src_targ
        setup_test_parms(cls, CSOAN_map, CSOAN_src_targ)
        
    def test_CSOAN(self):
        cls = self.__class__

        test_map = cls.test_map
        src_key = cls.src_key
        targ_key = cls.targ_key
        src = cls.src
        targ = cls.targ
        
        test_in = dict()
        test_target = dict()

        new_target = map_data(src, targ, test_in, test_target)

        self.assertIn(targ_key, new_target,
                        msg="CSOAN key is not in output dict when source empty")

        test_in[src_key] = '123'
        new_target = map_data(src, targ,
                              test_in, test_target)
        self.assertEqual(new_target[targ_key], '123',
                         msg="CSOAN keyval not copied when source has value")

        test_target[src_key] = '456'
        new_target = map_data(src, targ,
                              test_in, test_target)
        self.assertEqual(new_target[targ_key], '123',
                         msg="CSOAN keyval not copied when source and target have value")


class Test_COPY_SRC_OR_ADD_BLANK(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        global CSOAB_map
        global CSOAB_src_targ
        setup_test_parms(cls, CSOAB_map, CSOAB_src_targ)
        
        
    def test_CSOAB(self):
        cls = self.__class__

        test_map = cls.test_map
        src_key = cls.src_key
        targ_key = cls.targ_key
        src = cls.src
        targ = cls.targ
        
        test_in = dict()
        test_target = dict()

        new_target = map_data(src, targ, test_in, test_target)
        self.assertEqual(new_target[targ_key], '',
                         msg="CSOAB keyval not blank when source empty")

        test_in[src_key] = '123'
        new_target = map_data(src, targ,
                              test_in, test_target)
        self.assertEqual(new_target[targ_key], '123',
                        msg="CSOAB keyval not copied when source has value")

        test_target[src_key] = '456'
        new_target = map_data(src, targ,
                              test_in, test_target)
        self.assertEqual(new_target[targ_key], '123',
                        msg="CSOAB keyval not copied when source and target have value")

        
class Test_COPY_SRC_IF_SRC_SET_TARG_UNSET(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        global CSISSTU_map
        global CSISSTU_src_targ
        setup_test_parms(cls, CSISSTU_map, CSISSTU_src_targ)

    def test_CSISSTU(self):
        cls = self.__class__

        test_map = cls.test_map
        src_key = cls.src_key
        targ_key = cls.targ_key
        src = cls.src
        targ = cls.targ

        test_in = dict()
        test_in['name'] = None
        test_target = dict()

        new_target = map_data(src, targ,
                              test_in, test_target)

        self.assertNotIn(targ_key, new_target,
                         msg="CSIFSTU key is in output dict when source None")

        test_in[src_key] = ''
        new_target = map_data(src, targ,
                              test_in, test_target)

        self.assertNotIn(targ_key, new_target,
                         msg="CSIFSTU key is in output dict when source ''")

        test_in[src_key] = 'foo'
        new_target = map_data(src, targ,
                              test_in, test_target)

        self.assertEqual(new_target[targ_key], 'foo',
                         msg="CSIFSTU val not copied when source set, target unset")

        test_target[src_key] = 'bar'
        new_target = map_data(src, targ,
                              test_in, test_target)
        self.assertEqual(new_target[targ_key], 'foo',
                         msg="CSISSTU keyval copied when target has value")

        
class Test_COPY_SRC_IF_SRC_SET(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        global CSISS_map
        global CSISS_src_targ
        setup_test_parms(cls, CSISS_map, CSISS_src_targ)

    def test_CSISS(self):
        cls = self.__class__

        test_map = cls.test_map
        src_key = cls.src_key
        targ_key = cls.targ_key
        src = cls.src
        targ = cls.targ

        test_in = dict()
        test_in[src_key] = None
        test_target = dict()

        new_target = map_data(src, targ,
                              test_in, test_target)

        self.assertNotIn(targ_key, new_target,
                         msg="CSIF key is in output dict when source None")

        test_in[src_key] = ''
        new_target = map_data(src, targ,
                              test_in, test_target)

        self.assertNotIn(targ_key, new_target,
                        msg="CSIF key is in output dict when source ''")

        test_in[src_key] = 'foo'
        new_target = map_data(src, targ,
                              test_in, test_target)

        self.assertEqual(new_target[targ_key], 'foo',
                         msg="CSIF value not copied when source set, target unset")

        test_target[src_key] = 'bar'
        new_target = map_data(src, targ,
                              test_in, test_target)

        self.assertEqual(new_target[targ_key], 'foo',
                         msg="CSIF value not copied when source set, target set")

        
if __name__ == '__main__':
    unittest.main()
