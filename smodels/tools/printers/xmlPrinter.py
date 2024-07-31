"""
.. module:: xmlPrinter
   :synopsis: Class for describing a printer in XML format

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

from __future__ import print_function
import sys
import os
import copy
from smodels.decomposition.topologyDict import TopologyDict
from smodels.matching.theoryPrediction import TheoryPredictionList,TheoryPrediction,TheoryPredictionsCombiner
from smodels.tools.ioObjects import OutputStatus
from smodels.tools.coverage import Uncovered
from smodels.base.physicsUnits import GeV, fb, TeV
from smodels.base.smodelsLogging import logger
from smodels.tools.printers.pythonPrinter import PyPrinter
import numpy as np
from collections import OrderedDict
from xml.dom import minidom
from xml.etree import ElementTree
import unum
import time


class XmlPrinter(PyPrinter):
    """
    Printer class to handle the printing of one single XML output
    """

    def __init__(self, output='stdout', filename=None, outputFormat='current'):
        PyPrinter.__init__(self, output, filename, outputFormat)
        self.name = "xml"
        self.printingOrder = [OutputStatus, TopologyDict,
                              TheoryPredictionList, TheoryPredictionsCombiner,
                              TheoryPrediction, Uncovered]
        self.toPrint = [None]*len(self.printingOrder)

    def setOutPutFile(self, filename, overwrite=True, silent=False):
        """
        Set the basename for the text printer. The output filename will be
        filename.xml.
        :param filename: Base filename
        :param overwrite: If True and the file already exists, it will be removed.
        :param silent: dont comment removing old files
        """

        self.filename = filename + '.xml'
        if overwrite and os.path.isfile(self.filename):
            if not silent:
                logger.warning("Removing old output file " + self.filename)
            os.remove(self.filename)

    def convertToElement(self, pyObj, parent, tag=""):
        """
        Convert a python object (list,dict,string,...)
        to a nested XML element tree.
        :param pyObj: python object (list,dict,string...)
        :param parent: XML Element parent
        :param tag: tag for the daughter element
        """

        tag = tag.replace(" ", "_").replace("(", "").replace(")", "")
        if not isinstance(pyObj, list) and not isinstance(pyObj, dict):
            parent.text = str(pyObj).lstrip().rstrip()
        elif isinstance(pyObj, dict):
            for key, val in sorted(pyObj.items()):
                key = key.replace(" ", "_").replace("(", "").replace(")", "")
                newElement = ElementTree.Element(key)
                self.convertToElement(val, newElement, tag=key)
                parent.append(newElement)
        elif isinstance(pyObj, list):
            parent.tag += '_List'
            for val in pyObj:
                newElement = ElementTree.Element(tag)
                self.convertToElement(val, newElement, tag)
                parent.append(newElement)

    def flush(self):
        """
        Get the python dictionaries generated by the object formatting
        to the defined output and convert to XML
        """

        outputDict = {}
        for obj in self.toPrint:
            if obj is None:
                continue
            output = self._formatObj(obj)  # Convert to python dictionaries
            if not output:
                continue  # Skip empty output
            outputDict.update(output)

        root = None
        # Convert from python dictionaries to xml:
        if outputDict:
            root = ElementTree.Element('smodelsOutput')
            self.convertToElement(outputDict, root)
            rough_xml = ElementTree.tostring(root, 'utf-8')
            nice_xml = minidom.parseString(
                rough_xml).toprettyxml(indent="    ")
            if self.output == 'stdout':
                sys.stdout.write(nice_xml)
            elif self.output == 'file':
                if not self.filename:
                    logger.error('Filename not defined for printer')
                    return False
                with open(self.filename, "a") as outfile:
                    outfile.write(nice_xml)
                    outfile.close()

        self.toPrint = [None]*len(self.printingOrder)
        return root
