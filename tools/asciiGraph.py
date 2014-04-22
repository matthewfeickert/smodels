#!/usr/bin/env python

"""
.. module:: asciiGraphs
   :synopsis: Contains a simple routine to draw ASCII-art Feynman-like graphs.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

from __future__ import print_function
import sys
import logging

logger = logging.getLogger(__name__) # pylint: disable-msg=C0103


def _printParticle(label):
    """
    Rename particles for the asciidraw routine.
    
    """
    if label == "jet":
        label = "q"
    label = label + "     "
    return label[:2]

def _drawBranch(branch, upwards, labels, htmlFormat, border, l):
    """
    Draw a single branch.
    
    """
    lines = ["   ", "----"]
    labels = "   "
    if border and upwards:
        lines = [" |    ", " | ----"]
        labels = " |    "
    if border and not upwards:
        lines = [" |    ", " | ----"]
        labels = " |    "

    for insertions in branch.particles:
        if len(insertions) == 0:
            lines[0] += " "
            lines[1] += "*"
            continue
        lines[1] += "*----"
        if len(insertions) == 1:
            labels += " " + _printParticle(insertions[0]) + "  "
            lines[0] += " |   "
        if len(insertions) == 2:
            labels += _printParticle(insertions[0]) + " " + \
                    _printParticle(insertions[1])
            if upwards:
                lines[0] += "\\ /  "
            else:
                lines[0] += "/ \\  "
        if len(insertions) > 2:
            logger.error("n > 3 for n-body decay not yet implemented.")
            sys.exit(0)

    order = [0, 1]
    if not upwards: order = [1, 0]
    html = "<br>"
    lengthdiff = l - len(lines[0])/5
    if border:
        if l == 2:
            lines[0] += " "
            lines[1] += " "
            labels += " "
        labels += " " + " "*(5*lengthdiff) + " |"
        lines[0] += " "*(5*lengthdiff + 0) + "  |"
        lines[1] += " "*(5*lengthdiff + 0) + " |"
    if border and upwards:
        print(" /" + "-"*(4*l + 4) + "\\")
    if htmlFormat:
        print(html)
    if upwards and labels:
        print(labels)
    if htmlFormat:
        print(html)
    for i in order:
        print(lines[i])
    if htmlFormat:
        print(html)
    if not upwards and labels:
        print(labels)
    if htmlFormat:
        print(html)
    if border and not upwards:
        print(" \\" + "-"*(4*l + 4) + "/")

def asciidraw(element, labels=True, html=False, border=False):
    """
    Draw a simple ASCII graph on the screen.
    
    """
    l = []
    for (ct, branch) in enumerate(element.branches):
        l.append(int( str(branch).count("[")))
    for (ct, branch) in enumerate(element.branches):
        _drawBranch(branch, upwards=(ct == 0), labels=labels, htmlFormat=html,
                    border=border, l=max(l))

if __name__ == "__main__":
    import setPath # pylint: disable-msg=W0611
    import argparse
    import types
    import SModelS
    from theory import lheReader
    from theory import lheDecomposer
    from theory import crossSection

    argparser = argparse.ArgumentParser( # pylint: disable-msg=C0103
            description = "simple tool that is meant to draw lessagraphs, as "
                          "an ascii plot") 
    argparser.add_argument('-T', nargs='?', help = "Tx name, will look up lhe "
            "file in ../regression/Tx_1.lhe. Will be overriden by the '--lhe' "
            "argument", type=types.StringType, default='T1')
    argparser.add_argument('-l', '--lhe', nargs='?', help = "lhe file name, "
            "supplied directly. Takes precedence over '-T' argument.", 
            type=types.StringType, default='')
    argparser.add_argument('-b', '--border', help="draw a border around the "
            "graph", action='store_true')
    args = argparser.parse_args() # pylint: disable-msg=C0103

    filename = ("%sinputFiles/lhe/%s_1.lhe" # pylint: disable-msg=C0103
                % (SModelS.installDirectory(), args.T))
    if args.lhe != "":
        filename = args.lhe # pylint: disable-msg=C0103

    reader = lheReader.LheReader(filename) # pylint: disable-msg=C0103
    Event = reader.next() # pylint: disable-msg=C0103
    element = lheDecomposer.elementFromEvent(Event, # pylint: disable-msg=C0103
                                             crossSection.XSectionList())
    asciidraw(element, border=args.border)                    
