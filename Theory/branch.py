"""
.. module:: Theory.branch
   :synopsis: missing
        
.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>
        
"""

from ParticleNames import PtcDic, Reven, simParticles, elementsInStr
from Tools.PhysicsUnits import addunit
import logging

logger = logging.getLogger(__name__)


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
                logging.error("Wrong input string "+info)
                return False                
            else:
                branch = branch[0]
                vertices = elementsInStr(branch[1:-1])
                for vertex in vertices:
                    ptcs = vertex[1:-1].split(',')
                    #Syntax check:
                    for ptc in ptcs:
                        if not ptc in Reven.values() and not PtcDic.has_key(ptc):
                            logger.error("Unknown particle "+ptc)
                            return False
                    self.particles.append(ptcs)
                    
                        
    def __str__ ( self ):
        """
        The canonical SModels description of the Branch.
        
        """
        st = str(self.particles).replace("'","")
        st = st.replace(" ","")
        return st
                
    def __eq__ ( self, other ):
        return self.isEqual ( other )
    
    def __ne__ ( self, other ):
        return not self.isEqual ( other )


    def isEqual ( self, other, useDict=True):
        if type (other) != type(self):
            return False
        if not simParticles(self.particles,other.particles,useDict):
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

    
    def addDecay(self,BR,Massdic):
        """
        Generates a new branch adding a 1-step cascade decay described by
        the BR object, with particle masses given by Massdic.
        
        """        
        import ParticleNames
        newBranch = self.copy()
        newparticles = []
        newmass = []
        newBranch.daughterID = None

        for partID in BR.ids:
            if partID in ParticleNames.Reven:   # Add R-even particles to final state
                newparticles.append(ParticleNames.Reven[partID])
            else:
                newmass.append(Massdic[partID]) # Add masses of non R-even particles to mass vector
                newBranch.daughterID = partID

        if len(newmass) > 1:
            logger.warning("[addDecay] multiple R-odd particles in the final state:",BR)
            return False
       
        if newparticles:
            newBranch.particles.append(newparticles)
        if newmass:
            newBranch.masses.append(newmass[0])
        newBranch.maxWeight = self.maxWeight*BR.br
                
        return newBranch
    
    def decayDaughter(self,BRdic,Massdic):
        """
        Generates a list of all new branches generated by the 1-step cascade
        decay of the current branch daughter.
        
        """        
        if not self.daughterID:
            return []   # Do nothing if there is no R-odd daughter (relevant for RPV decays of the LSP)
        BRs = BRdic[self.daughterID]    # List of possible decays (BRs) for R-odd daughter in branch
        if len(BRs) == 0:
            return []   # Daughter is stable, there are no new branches
        newBranches = []
        for br in BRs:
            newBranches.append(self.addDecay(br,Massdic))   # Generate a new branch for each possible decay        
        return newBranches

    def getLength(self):
        """
        Returns the branch length (= number of R-odd masses).
        
        """        
        return len(self.masses)
    

def decayBranches(branchList,BRdic,Massdic,sigcut=addunit(0.,'fb')):
    """
    Decay all branches from branchList until all R-odd particles have
    decayed.
    
    :param branchList: list of Branch() objects containing the initial mothers
    :param BRdic: branching ratio dictionary for all particles appearing in the
    decays
    :param Massdic: mass dictionary for all particles appearing in the decays
    :param sigcut: minimum sigma*BR to be generated, by default sigcut = 0.
    (all branches are kept)
    
    """    
    finalBranchList = [] 
    while branchList:   
        newBranchList = []  # Store branches after adding one step cascade decay             
        for branch in branchList:            
            if branch.maxWeight < sigcut:
                continue    # Remove the branches above sigcut and with length > topmax            
            newBranches = branch.decayDaughter(BRdic,Massdic)   # Add all possible decays of the R-odd daughter to the original branch (if any)
            if newBranches:
                newBranchList.extend(newBranches)   # New branches were generated, add them for next iteration
            else:
                finalBranchList.append(branch)  # All particles have already decayed, store final branch
        branchList = newBranchList  # Use new branches (if any) for next iteration step        
    return finalBranchList
