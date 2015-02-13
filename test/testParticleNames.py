#!/usr/bin/env python

"""
.. module:: testParticleNames
   :synopsis: Tests ParticleNames.elementsInStr

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""
import unittest

class InStrTest(unittest.TestCase):
    def testInStr(self):
        instring="[[['t+'],['W-']],[['t+'],['W-']]]+[[['t-'],['W+']],[['t-'],['W+']]]+[[['t+'],['W-']],[['t-'],['W+']]]"
        from smodels.theory import particleNames
        out= particleNames.elementsInStr( instring )
        self.assertEqual ( out, ['[[[t+],[W-]],[[t+],[W-]]]', '[[[t-],[W+]],[[t-],[W+]]]', '[[[t+],[W-]],[[t-],[W+]]]'] )

if __name__ == "__main__":
    unittest.main()
