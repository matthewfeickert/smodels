"""
.. module:: theory.branch
   :synopsis: missing
        
.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>
        
"""

from .particleNames import PtcDic, Reven, simParticles, elementsInStr
from tools.physicsUnits import addunit
from . import logger

class Branch(object):
    """
    An instance of this class represents a branch.
    
    """
    def __init__(self, info=None):
        """A branch-element can be constructed from a string S (e.g.,
        ('[b,b],[W]').
        
        """
        self.masses = []
        self.particles = []
        self.momID = None
        self.daughterID = None
        self.maxWeight = None
        if type(info)==type(str()):
            branch = elementsInStr(info)
            if not branch or len(branch) > 1:
                logger.error("Wrong input string " + info)
                return False                
            else:
                branch = branch[0]
                vertices = elementsInStr(branch[1:-1])
                for vertex in vertices:
                    ptcs = vertex[1:-1].split(',')
                    #Syntax check:
                    for ptc in ptcs:
                        if not ptc in Reven.values() \
                                and not ptc in PtcDic:
                            logger.error("Unknown particle " + ptc)
                            return False
                    self.particles.append(ptcs)
                    
                        
    def __str__(self):
        """
        The canonical SModels description of the Branch.
        
        """
        st = str(self.particles).replace("'", "")
        st = st.replace(" ", "")
        return st
                
                
    def __eq__(self, other):
        return self.isEqual(other)
    
    
    def __ne__(self, other):
        return not self.isEqual(other)


    def isEqual(self, other, useDict=True):
        """
        missing
        
        """
        if type (other) != type(self):
            return False
        if not simParticles(self.particles, other.particles, useDict):
            return False
        if self.masses != other.masses:
            return False
        return True
    
    
    def copy(self):
        """
        Generates an independent copy of itself. Faster than deepcopy.
        
        """        
        newbranch = Branch()
        newbranch.masses = self.masses[:]
        newbranch.particles = self.particles[:]
        newbranch.momID = self.momID
        newbranch.daughterID = self.daughterID
        if not self.maxWeight is None:
            newbranch.maxWeight = self.maxWeight.copy()
        return newbranch     

    
    def addDecay(self, br, massDictionary):
        """
        Generates a new branch adding a 1-step cascade decay described by
        the br object, with particle masses given by massDictionary.
        
        """
        newBranch = self.copy()
        newparticles = []
        newmass = []
        newBranch.daughterID = None

        for partID in br.ids:
            # Add R-even particles to final state
            if partID in Reven:
                newparticles.append(Reven[partID])
            else:
                # Add masses of non R-even particles to mass vector
                newmass.append(massDictionary[partID])
                newBranch.daughterID = partID

        if len(newmass) > 1:
            logger.warning("Multiple R-odd particles in the final state: %s" % br)
            return False
       
        if newparticles:
            newBranch.particles.append(newparticles)
        if newmass:
            newBranch.masses.append(newmass[0])        
        if not self.maxWeight is None: newBranch.maxWeight = self.maxWeight*br.br
                
        return newBranch
    
    
    def decayDaughter(self, brDictionary, massDictionary):
        """
        Generates a list of all new branches generated by the 1-step cascade
        decay of the current branch daughter.
        
        """
        if not self.daughterID:
            # Do nothing if there is no R-odd daughter (relevant for RPV decays
            # of the LSP)
            return []
        # List of possible decays (brs) for R-odd daughter in branch
        brs = brDictionary[self.daughterID]
        if len(brs) == 0:
            # Daughter is stable, there are no new branches
            return []
        newBranches = []
        for br in brs:
            # Generate a new branch for each possible decay
            newBranches.append(self.addDecay(br, massDictionary))
        return newBranches


    def getLength(self):
        """
        Returns the branch length (= number of R-odd masses).
        
        """        
        return len(self.masses)
    

def decayBranches(branchList, brDictionary, massDictionary,
                  sigcut=addunit(0., 'fb')):
    """
    Decay all branches from branchList until all R-odd particles have
    decayed.
    
    :param branchList: list of Branch() objects containing the initial mothers
    :param brDictionary: branching ratio dictionary for all particles appearing in the
    decays
    :param massDictionary: mass dictionary for all particles appearing in the decays
    :param sigcut: minimum sigma*BR to be generated, by default sigcut = 0.
    (all branches are kept)
    
    """
    
    finalBranchList = []
    while branchList:
        # Store branches after adding one step cascade decay
        newBranchList = []
        for inbranch in branchList:      
            if sigcut.asNumber() > 0. and inbranch.maxWeight < sigcut:
                # Remove the branches above sigcut and with length > topmax
                continue
            # Add all possible decays of the R-odd daughter to the original
            # branch (if any)
            newBranches = inbranch.decayDaughter(brDictionary, massDictionary)
            if newBranches:
                # New branches were generated, add them for next iteration
                newBranchList.extend(newBranches)
            else:
                # All particles have already decayed, store final branch
                finalBranchList.append(inbranch)
        # Use new branches (if any) for next iteration step
        branchList = newBranchList  
    return finalBranchList
