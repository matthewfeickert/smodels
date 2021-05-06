#!/usr/bin/env python3
 
"""
.. module:: testInteractivePlots
   :synopsis: Tests the interactive plot tool
 
.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>
 
"""
 
import sys,os,shutil
sys.path.insert(0,"../")
import unittest
from smodels.tools.interactivePlots import main
try:
    from types import SimpleNamespace
except ImportError: ## doesnt exist in python2
    class SimpleNamespace:
        pass


class RunInteractivePlotSTest(unittest.TestCase):
    
    # this test corresponds to calling
    # ../smodelsTools.py interactive-plots -f ./testFiles/scanExample/smodels-output.tar.gz -s testFiles/scanExample/slhas.tar.gz -p iplots_parameters.py
    def testInteractivePlots(self):
        slhaFolder = './testFiles/scanExample/slhas.tar.gz'
        smodelsFolder = './testFiles/scanExample/smodels-output.tar.gz'
        parametersFile = './iplots_parameters.py'
        outFolder = './plots_test'
        
        defaultFolder = './plots_test_default'
        
        if os.path.isdir(outFolder):
            shutil.rmtree(outFolder)

        parser = SimpleNamespace()
        parser.smodelsFolder = smodelsFolder
        parser.slhaFolder  =  slhaFolder
        parser.parameters = parametersFile
        parser.outputFolder = outFolder
        parser.verbosity = 'error'
        parser.npoints = -1
        parser.modelFile='../smodels/share/models/mssm.py'

        run = main(parser)
        
        self.assertEqual(run,outFolder)        
        self.assertEqual(sorted(os.listdir(outFolder)), sorted(os.listdir(defaultFolder)))

#         if os.path.isdir(outFolder):
#             shutil.rmtree(outFolder)
#         if os.path.exists("all_data_frame.txt"):
#             os.unlink("all_data_frame.txt")


if __name__ == "__main__":
    unittest.main()
