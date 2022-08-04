#!/usr/bin/env python3

"""
.. module:: testReweighting
   :synopsis: Tests the function of coverage
.. moduleauthor:: Alicia Wongel <alicia.wongel@gmail.com>
"""
import sys
sys.path.insert(0,"../")
import unittest
from smodels.tools.coverage import Uncovered
from smodels.theory.theorySMS import TheorySMS
from smodels.theory.topologyDict import TopologyDict
from smodels.tools.physicsUnits import GeV, TeV, fb
from smodels.theory.crossSection import XSectionList, XSection, XSectionInfo
from smodels.share.models import SMparticles, mssm
from smodels.experiment.reweighting import reweightFactorFor
from smodels.theory.particle import Particle
from smodels.theory.particleNode import ParticleNode
from smodels.share.models.mssm import BSMList
from smodels.share.models.SMparticles import SMList
from smodels.theory.model import Model
from unitTestHelpers import theorySMSFromString as fromString
import random

slhafile = './testFiles/slha/lightEWinos.slha'

model = Model( BSMparticles=BSMList, SMparticles=SMList)
model.updateParticles(inputFile=slhafile,erasePrompt=['spin'])


n1 = model.getParticle(label='N1')
n1.totalwidth = 0.*GeV
st1 = model.getParticle(label='st_1')
st1.totalwidth = 2.*GeV
st2 = model.getParticle(label='st_2')
st2.totalwidth = 10**(-15)*GeV
gluino = model.getParticle(label='gluino')
gluino.totalwidth = 1.*10**(-30)*GeV


#Default definitions for the uncovered topology categories/groups:
##Element filters for each group:
##(it should be a function which takes an Element object as input
##and returns True if the element belongs to the group and False otherwise)
filters = {'missing (prompt)': lambda sms: not ('prompt' in sms.coveredBy),
                  'missing (displaced)': lambda sms: not ('displaced' in sms.coveredBy),
                  # 'missing (long cascade)' : lambda el: (not el.coveredBy) and el._getLength() > 3,
                  'missing (all)': lambda sms: (not sms.coveredBy),
                  'outsideGrid (all)': lambda sms: (sms.coveredBy and not sms.testedBy)}



##Weight factors for each group:
##(it should be a function which takes an Element object as input
##and returns the reweighting factor to be applied to the element weight. It is relevant if only
##the fraction of the weight going into prompt or displaced decays is required)
factors = {}
for key in filters:
    if 'prompt' in key.lower():
        factors[key] = lambda el: reweightFactorFor(el, 'prompt')
    elif 'displaced' in key.lower():
        factors[key] = lambda el: reweightFactorFor(el, 'displaced')
    else:
        # If not specified assumed all fractions
        factors[key] = lambda el: reweightFactorFor(el, 'prompt') + reweightFactorFor(el, 'displaced')


class CoverageTest(unittest.TestCase):

    def testUncovered(self):

        w1 = XSectionList()
        w1.xSections.append(XSection())
        w1.xSections[0].info = XSectionInfo()
        w1.xSections[0].info.sqrts = 8.*TeV
        w1.xSections[0].info.label = '8 TeV'
        w1.xSections[0].info.order = 0
        w1.xSections[0].value = 10.*fb


        topolist = TopologyDict()

        # prompt
        sms1 = fromString("(PV > st_1(1),st_1(2)), (st_1(1) > b,t+,N1), (st_1(2) > b,t+,N1)",
                          model=model,prodXSec=w1,maxWeight=w1.getMaxXsec())

        # long-lived
        sms2 = fromString("(PV > gluino,st_1(1)), (st_1(1) > b,t+,N1)",
                          model=model,prodXSec=w1,maxWeight=w1.getMaxXsec())
        # prompt and displaced
        sms3 = fromString("(PV > st_2(1),st_1(2)), (st_2(1) > st_1(3),t+), (st_1(3) > b,t+,N1), (st_1(2) > b,t+,N1)",
                          model=model,prodXSec=w1,maxWeight=w1.getMaxXsec())


        topolist.addSMS(sms1)
        topolist.addSMS(sms2)
        topolist.addSMS(sms3)
        topolist.setSMSIds()
        uncovered = Uncovered(topolist,groupFilters=filters,groupFactors=factors)

        prompt = uncovered.getGroup('missing (prompt)')
        displaced = uncovered.getGroup('missing (displaced)')

        self.assertEqual(len(displaced.finalStateSMS), 1)
        self.assertEqual(len(prompt.finalStateSMS), 3)

        self.assertAlmostEqual(displaced.finalStateSMS[0].missingX, 9.96109334317542,places=4)
        self.assertAlmostEqual(prompt.finalStateSMS[0].missingX, 10.,3)
        self.assertAlmostEqual(prompt.finalStateSMS[1].missingX, 10.,3)
        self.assertAlmostEqual(prompt.finalStateSMS[2].missingX, 0.03890665682,3)


    def testUncoveredTree(self):

        p1 = Particle(Z2parity=-1, label='p1', pdg=10001, mass=100.*GeV,
              eCharge=0., colordim=1, totalwidth=0*GeV)
        p2 = Particle(Z2parity=-1, label='p2', pdg=10002, mass=200.*GeV,
              eCharge=0., colordim=1, totalwidth=1e-15*GeV)
        pv = Particle(isSM=True, label='PV', pdg=0)

        model = Model(BSMList=[p1,p2], SMList= [pv])

        xsecA = XSectionList()
        xsecA.xSections.append(XSection())
        xsecA.xSections[0].info = XSectionInfo()
        xsecA.xSections[0].info.sqrts = 13.*TeV
        xsecA.xSections[0].info.label = '13 TeV'
        xsecA.xSections[0].info.order = 0
        xsecA.xSections[0].value = 10.*fb

        xsecB = XSectionList()
        xsecB.xSections.append(XSection())
        xsecB.xSections[0].info = XSectionInfo()
        xsecB.xSections[0].info.sqrts = 13.*TeV
        xsecB.xSections[0].info.label = '13 TeV'
        xsecB.xSections[0].info.order = 0
        xsecB.xSections[0].value = 5.*fb

        xsec = XSectionList()
        xsec.xSections.append(XSection())
        xsec.xSections[0].info = XSectionInfo()
        xsec.xSections[0].value = 15.*fb
        xsec.xSections[0].info.sqrts = 13.*TeV
        xsec.xSections[0].info.label = 'wA+wB'
        xsec.xSections[0].info.order = 0

        #SMS family-tree: A0->A1+B1, A1->A2
        #Mother A
        smsA = fromString('(PV > p1,p1)',prodXSec=xsecA,
                          maxWeight=xsecA.getMaxXsec())
        smsA.label = 'A0'
        smsA.testedBy = ['prompt','displaced']
        smsA.coveredBy = ['prompt','displaced']
        smsA.ancestors = [smsA]

        #Daughters:
        smsA1 = fromString('(PV > p1,p1)',prodXSec=xsecA,
                          maxWeight=xsecA.getMaxXsec())
        smsA1.label = 'A1'
        smsA1.testedBy = []
        smsA1.coveredBy = []
        smsA1.ancestors = [smsA1,smsA]

        smsB1 = fromString('(PV > p1,p1)',prodXSec=xsecA,
                          maxWeight=xsecA.getMaxXsec())
        smsB1.label = 'B1'
        smsB1.testedBy = []
        smsB1.coveredBy = []
        smsB1.ancestors = [smsB1,smsA]

        smsA2 = fromString('(PV > p1,p1)',prodXSec=xsecA,
                          maxWeight=xsecA.getMaxXsec())
        smsA2.label = 'A2'
        smsA2.testedBy = []
        smsA2.coveredBy = []
        smsA2.ancestors = [smsA2,smsA1]

        #Element family-tree: a0->a1+b1
        #Mother B
        smsa = TheorySMS()
        smsa.label = 'a0'
        smsa.testedBy = []
        smsa.coveredBy = []
        smsa.weightList = xsecB
        smsa.ancestors = [smsa]
        #Daughters:
        smsa1 = TheorySMS()
        smsa1.label = 'a1'
        smsa1.testedBy = []
        smsa1.coveredBy = []
        smsa1.weightList = xsecB
        smsa1.ancestors = [smsa1,smsa]
        smsb1 = TheorySMS()
        smsb1.label = 'b1'
        smsb1.testedBy = []
        smsb1.coveredBy = []
        smsb1.weightList = xsecB
        smsb1.ancestors = [smsb1,smsa]


        #Merged element = (A2+b1)
        smsCombined = TheorySMS()
        smsCombined.label = 'A2+b1'
        smsCombined.testedBy = []
        smsCombined.coveredBy = []
        smsCombined.weightList = xsec
        smsCombined.ancestors = [smsCombined,smsA2,smsb1]

        topoList = TopologyDict()
        smsList = [smsA,smsA1,smsA2,smsB1,smsa,smsb1,smsa1,smsCombined]
        #Set odd particles (important for sorting the smsements)
        for sms in [smsA,smsA1,smsA2,smsCombined]:
            sms.add_node(pv)
            sms.add_node(p1)
            sms.add_node(p2)
            sms.add_edge(0,1)  # pv > p1
            sms.add_edge(0,2)  # pv > p2

        smsB1.add_nodes_from([p2,p1,p1])
        smsB1.add_edges_from([(0,1),(0,2)(1,3),])  # pv > p2, pv > p1, p2 >p1

        smsa1.add_nodes_from([p2,p1,p1])
        smsa1.add_edges_from([(0,2),(0,1)(1,3),])  # pv > p1, pv > p2, p2 >

        branches[1].oddParticles = [p2,p1]
        smsb1.branches[1].oddParticles = [p2,p1]
        smsa.branches[0].oddParticles = [p2,p2,p1]

        #make sure the ordering in elList is not important:
        random.shuffle(elList)
        topoList.topos[0].elementList = elList[:]
        topoList._setElementIds()

        #Test if the family tree is being retrieved correctly and in the correct ordering (mother before grandmother,...):
        elListAncestors = {'A0' : [], 'A1' : ['A0'], 'A2' : ['A1','A0'], 'B1' : ['A0'],'A2+b1' : ['A2','b1','A1','a0','A0'],
                           'b1' : ['a0'], 'a1' : ['a0'] , 'a0' : []}
        for el in elList:
            ancestors = [mom.label for mom in el.getAncestors()]
            self.assertEqual(ancestors,elListAncestors[el.label])
        # A2+b1--> b1 is not tested, A2 is tested because its grandmother is tested
        missingTopos = Uncovered(topoList).getGroup('missing (all)')
        self.assertEqual(len(missingTopos.generalElements),1) #Only elCombined should appear (it is smaller than a1)
        self.assertAlmostEqual(missingTopos.generalElements[0].missingX,5.) #Only the fraction of the cross-section from elB is not missing
        self.assertEqual(len(missingTopos.generalElements[0]._contributingElements),1) #Only elCombined should appear
        self.assertTrue(missingTopos.generalElements[0]._contributingElements[0] is elCombined)

if __name__ == "__main__":
    unittest.main()
