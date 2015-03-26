#!/usr/bin/env python

"""
.. module:: runSModelS
   :synopsis: Main code for running SModelS.
   
"""

import sys, os, logging
import argparse
from ConfigParser import SafeConfigParser
from smodels.tools.physicsUnits import GeV, fb
from smodels.tools import ioObjects, missingTopologies
from smodels.experiment.databaseObjects import Database
from smodels.theory import slhaDecomposer, lheDecomposer
from smodels.theory.theoryPrediction import theoryPredictionsFor
from smodels.installation import installDirectory
log = logging.getLogger(__name__)


def main(inputFile, parameterFile, outputFile):
    """
    Provides a command line interface to basic SModelS functionalities.
    
    :param inputFile: input file name (either a SLHA or LHE file)
    :param parameterFile: File containing the input parameters (default = /etc/parameters_default.ini)
    :param outputFile: Output file to write a summary of results
    
    """

    """
    Read and check input file
    =========================
    """
    parser = SafeConfigParser()
    parser.read(parameterFile)

    """ Minimum value of cross-section for an element to be considered eligible for decomposition.
        Too small sigmacut leads to too large decomposition time. """
    sigmacut = parser.getfloat("parameters", "sigmacut") * fb

    """ Minimum value for considering two states non-degenerate (only used for mass compression) """
    minmassgap = parser.getfloat("parameters", "minmassgap") * GeV

    if os.path.exists(outputFile):
        log.warning("Removing old output file in " + outputFile)
    outfile = open(outputFile, 'w')
    outfile.close()

    inputType = parser.get("options", "inputType").lower()
    if inputType != 'slha' and inputType != 'lhe':
        log.error("Unknown input type (must be SLHA or LHE): %s" % inputType)
        return

    """ Check input file for errors """
    inputStatus = ioObjects.FileStatus()
    if parser.getboolean("options", "checkInput"):
        inputStatus.checkFile(inputType, inputFile, sigmacut)

    """ Check database location """
    try:
        databasePath = parser.get("path", "databasePath")
        database = Database(databasePath)
        databaseVersion = database.databaseVersion
    except:
        log.error("Database not found in %s" % os.path.realpath(databasePath))
        databaseVersion = None
        return

    """ Initialize output status and exit if there were errors in the input """
    outputStatus = ioObjects.OutputStatus(inputStatus.status, inputFile, dict(parser.items("parameters")), databaseVersion, outputFile)
    if outputStatus.status < 0: return

    """
    Decompose input file
    ====================
    """
    try:
        """ Decompose input SLHA file, store the output elements in smstoplist """
        if inputType == 'slha':
            smstoplist = slhaDecomposer.decompose(inputFile, sigmacut, doCompress=parser.getboolean("options", "doCompress"),
                         doInvisible=parser.getboolean("options", "doInvisible"), minmassgap=minmassgap)
        else:
            smstoplist = lheDecomposer.decompose(inputFile, doCompress=parser.getboolean("options", "doCompress"),
                         doInvisible=parser.getboolean("options", "doInvisible"), minmassgap=minmassgap)
    except:
        """ Update status to fail, print error message and exit """
        outputStatus.updateStatus(-1)
        return

    """ Print Decomposition output.
        If no topologies with sigma > sigmacut are found, update status, write output file, stop running """
    if not smstoplist:
        outputStatus.updateStatus(-3)
        return

    outLevel = 0
    if parser.getboolean("stdout", "printDecomp"):
        outLevel = 1
        outLevel += parser.getboolean("stdout", "addElmentInfo")
    smstoplist.printout(outputLevel=outLevel)


    """
    Load analysis database
    ======================
    """
    
    """ In case that a list of analyses or txnames are given, retrieve list """
    analyses = parser.get("database", "analyses").split(",")
    txnames = parser.get("database", "txnames").split(",")
    
    """ Load analyses """    
    listOfExpRes = database.getExpResults(analysisIDs=analyses,txnames=txnames) 

    """ Print list of analyses loaded """
    if parser.getboolean("stdout", "printAnalyses"):
        print("=======================\n == List of Analyses   ====\n ================")
        for expResult in listOfExpRes: print(expResult)


    """
    Compute theory predictions and anlalyses constraints
    ====================================================
    """

    """ Define result list that collects all theoryPrediction objects.
        Variables set to define printing options. """
    results = ioObjects.ResultList(bestresultonly=not parser.getboolean("file", "expandedSummary"),
                                   describeTopo=parser.getboolean("file", "addConstraintInfo"))

    """ Get theory prediction for each analysis and print basic output """
    for expResult in listOfExpRes:
        theorypredictions = theoryPredictionsFor(expResult, smstoplist)
        if not theorypredictions: continue
        print(expResult)
        if parser.getboolean("stdout", "printResults"):
            print "================================================================================"
            theorypredictions.printout()
        print "................................................................................"

        """ Create a list of results, to determine the best result """
        for theoryprediction in theorypredictions:
            results.addResult(theoryprediction, maxcond=parser.getfloat("parameters", "maxcond"))

    """ If there is no best result, this means that there are no matching experimental results for the point """
    if results.isEmpty():
        """ no experimental constraints found """
        outputStatus.updateStatus(0)
    else:
        outputStatus.updateStatus(1)

    """ Write output file """
    outputStatus.printout("file", outputFile)
    """ Add experimental constraints if found """
    if outputStatus.status == 1:
        results.printout("file", outputFile)

    sqrts = max([xsec.info.sqrts for xsec in smstoplist.getTotalWeight()])
    if parser.getboolean("options", "findMissingTopos"):
        """ Look for missing topologies, add them to the output file """
        missingtopos = missingTopologies.MissingTopoList(sqrts)
        missingtopos.findMissingTopos(smstoplist, listOfExpRes, minmassgap, parser.getboolean("options", "doCompress"),
                         doInvisible=parser.getboolean("options", "doInvisible"))
        missingtopos.printout("file", outputFile)


if __name__ == "__main__":
    """ Set default input and output files """
    parameterFile = "%s/etc/parameters_default.ini" % installDirectory()
    outputFile = "summary.txt"

    """ Get the name of input slha file and parameter file """
    argparser = argparse.ArgumentParser()
    argparser.add_argument('-f', '--filename', help='name of SLHA or LHE input file, necessary input', required=True)
    argparser.add_argument('-p', '--parameterFile',
                            help='name of parameter file, optional argument, if not set, use all parameters from etc/parameters_default.ini',
                            default=parameterFile)
    argparser.add_argument('-o', '--outputFile', help='name of output file, optional argument, default is: ' + outputFile,
                           default=outputFile)
    args = argparser.parse_args()

    main(args.filename, args.parameterFile, args.outputFile)
