#!/usr/bin/env python3
 
"""
.. module:: testRunSModelS
   :synopsis: Tests runSModelS
 
.. moduleauthor:: Ursula Laa <Ursula.Laa@assoc.oeaw.ac.at>
.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>
 
"""
 
import sys,os
sys.path.insert(0,"../")
import unittest
from os.path import join, basename
from smodels.installation import installDirectory as iDir
from databaseLoader import database ## to make sure the db exists
from smodels.tools.runSModelS import run
import redirector
import unum
import shutil
 
from smodels.tools.smodelsLogging import logger, setLogLevel
 
def equalObjs(obj1,obj2,allowedDiff,ignore=[]):
    """
    Compare two objects.
    The numerical values are compared up to the precision defined by allowedDiff.
 
    :param obj1: First python object to be compared
    :param obj2: Second python object to be compared
    :param allowedDiff: Allowed % difference between two numerical values
    :param ignore: List of keys to be ignored
    :return: True/False
    """
    if type(obj1) in [ float, int ] and type ( obj2) in [ float, int ]:
        obj1,obj2=float(obj1),float(obj2)
 
    if type(obj1) != type(obj2):
        logger.warning("Data types differ (%s,%s)" %(type(obj1),type(obj2)))
        return False
 
    if isinstance(obj1,unum.Unum):
        if obj1 == obj2:
            return True
        diff = 2.*abs(obj1-obj2)/abs(obj1+obj2)
        return diff.asNumber() < allowedDiff
    elif isinstance(obj1,float):
        if obj1 == obj2:
            return True
        diff = 2.*abs(obj1-obj2)/abs(obj1+obj2)
        return diff < allowedDiff
    elif isinstance(obj1,str):
        return obj1 == obj2
    elif isinstance(obj1,dict):
        for key in obj1:
            if key in ignore: continue
            if not key in obj2:
                logger.warning("Key %s missing" %key)
                return False
            if not equalObjs(obj1[key],obj2[key],allowedDiff, ignore=ignore ):
                logger.warning( "Dictionaries differ in key ``%s''" % key )
                s1,s2 = str(obj1[key]),str(obj2[key]) 
                if False: # len(s1) + len(s2) > 200:
                    logger.warning ( "The values are too long to print." )
                else:
                    logger.warning( 'The values are: >>%s<< (this run) versus >>%s<< (default)'%\
                                ( s1[:20],s2[:20] ) )
                return False
    elif isinstance(obj1,list):
        if len(obj1) != len(obj2):
            logger.warning('Lists differ in length:\n   %i (this run)\n and\n   %i (default)' %\
                                (len(obj1),len(obj2)))
            return False
        for ival,val in enumerate(obj1):
            if not equalObjs(val,obj2[ival],allowedDiff):
                logger.warning('Lists differ:\n   %s (this run)\n and\n   %s (default)' %\
                                (str(val),str(obj2[ival])))
                return False
    else:
        return obj1 == obj2
 
    return True
 
 
class RunSModelSTest(unittest.TestCase):
    def runMain(self, filename, timeout = 0, suppressStdout=True, development=False,
                 inifile = "testParameters_agg.ini" ):
        to = None
        level = 'debug'
        if suppressStdout:
            level = 'error'
            to = os.devnull
        with redirector.stdout_redirected ( to = to ):
            out = join( iDir(), "test/unitTestOutput" )
            setLogLevel ( level )
            run(filename, parameterFile=join ( iDir(), "test/%s" % inifile ),
                 outputDir= out, db= database, timeout = timeout,
                 development = development)
            sfile = join(iDir(),"test/unitTestOutput/%s.py" % basename(filename))
            return sfile
 
    
    def testCombinedResult(self):
        filename = join ( iDir(), "inputFiles/slha/gluino_squarks.slha" )
        outputfile = self.runMain(filename)
        shutil.copyfile(outputfile,'./output.py')
        from gluino_squarks_default_agg import smodelsOutputDefault
        from output import smodelsOutput
        ignoreFields = ['input file','smodels version', 'ncpus', 'database version']
        smodelsOutputDefault['ExptRes'] = sorted(smodelsOutputDefault['ExptRes'],
                    key=lambda res: [res['theory prediction (fb)'],res['TxNames'],
                    res['AnalysisID'],res['DataSetID']])
        equals = equalObjs(smodelsOutput,smodelsOutputDefault,allowedDiff=0.02,
                           ignore=ignoreFields)
        self.assertTrue(equals)
        if os.path.isfile('./output.py'):
            os.remove('./output.py')
 
if __name__ == "__main__":
    unittest.main()
