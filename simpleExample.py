#!/usr/bin/env python

"""
.. module:: simpleExample
   :synopsis: Basic use case for the SModelS framework.

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

from __future__ import print_function
import sys
sys.path.append("../")
## from smodels import SModelS
from smodels.theory import slhaDecomposer
## from theory import lheDecomposer
from smodels.tools.physicsUnits import addunit
from smodels.experiment import smsAnalysisFactory
from smodels.theory.theoryPrediction import theoryPredictionFor
## import logging

def main():
    """
    Main program. Displays basic use case.

    """
    slhafile = 'inputFiles/slha/andrePT4.slha'
    # lhefile = 'inputFiles/lhe/ued_1.lhe'

    # Decompose model (SLHA or LHE input):
    sigmacut = addunit(0.1, 'fb')
    mingap = addunit(5., 'GeV')

    smstoplist = slhaDecomposer.decompose(slhafile, sigmacut, doCompress=True,
                                          doInvisible=True, minmassgap=mingap)
    # smstoplist = lheDecomposer.decompose(lhefile, doCompress=True,
    #                                      doInvisible=True, minmassgap=mingap)

    # Print decomposition summary
    smstoplist.printout()

    # Load analyses
    listofanalyses = smsAnalysisFactory.load()

    # Get theory prediction for each analysis and print basic output
    for analysis in listofanalyses:
        theorypredictions = theoryPredictionFor(analysis, smstoplist)
        if not theorypredictions:
            continue
        print(analysis.label)
        theorypredictions.printout()


if __name__ == '__main__':
    main()
