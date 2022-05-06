"""
.. module:: element
   :synopsis: Module holding the Element class and its methods.

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

from smodels.theory.graphTools import stringToTree, getCanonName, treeToString, compareNodes, drawTree, getTreeRoot, sortTree, addTrees
from smodels.theory import crossSection
from smodels.theory.exceptions import SModelSTheoryError as SModelSError
from smodels.theory.particle import Particle
from networkx import DiGraph, bfs_successors


class Element(object):
    """
    An instance of this class represents an element.
    This class possesses a pair of branches and the element weight
    (cross-section * BR).
    """

    def __init__(self, info=None, finalState=None, intermediateState=None, model=None):
        """
        Initializes the element. If info is defined, tries to generate
        the element using it.

        :parameter info: string describing the element in bracket notation
                         (e.g. [[[e+],[jet]],[[e-],[jet]]]) or process notation
                         (e.g (PV > gluino(1),gluino(2)), (gluino(1) > u,u~,N1), (gluino(2) > d,d~,N1))
                         OR a tree (DiGraph object)

        :parameter finalState: list containing the final state labels for each branch
                         (e.g. ['MET', 'HSCP'] or ['MET','MET']). Only needed for the bracket notation
                         input.
        :parameter intermediateState: nested list containing intermediate state labels
                                      for each branch  (e.g. [['gluino'], ['gluino']]). Only
                                      needed for the bracket notation input.

        :parameter model: The model (Model object) to be used when converting particle labels to
                          particle objects (only used if info, finalState or intermediateState != None).
        """
        self.tree = DiGraph()
        self.weight = crossSection.XSectionList()  # gives the weight for all decays promptly
        self.decayLabels = []
        self.motherElements = [self]  # The motheElements includes self to keep track of merged elements
        self.elID = 0
        self.coveredBy = set()
        self.testedBy = set()

        if info:
            if isinstance(info, str):
                try:
                    self.tree = stringToTree(info, finalState=finalState,
                                             intermediateState=intermediateState,
                                             model=model)
                except (SModelSError, TypeError):
                    raise SModelSError("Can not create element from input %s" % info)
            elif isinstance(info, DiGraph):
                self.tree = info.copy()  # Makes a shallow copy of the original tree
            else:
                raise SModelSError("Can not create element from input type %s" % type(info))

        self.setCanonName()
        self.sort()

    def setCanonName(self):
        """
        Compute and store the canonical name for the tree
        topology. The canonical name can be used to compare and sort topologies.
        The name is stored in self.tree.canonName
        """

        canonName = getCanonName(self.tree)
        self.tree.graph['canonName'] = canonName

    def sort(self):
        """
        Sort the tree according to the canonName and then particle. For each node,
        all the daughters are sorted according to their canonName.
        """

        # If canon names have not been defined, compute them:
        if 'canonName' not in self.tree.graph:
            self.setCanonName()

        self.tree = sortTree(self.tree)

    def compareTo(self, other, sortOther=False):
        """
        Compares the element with other.
        Uses the topology name (Tree canonincal name) to identify isomorphic topologies (trees).
        If trees are not isomorphic, compare topologies using the topology name.
        Else  check if nodes (particles) are equal. For nodes with the same canonName
        and the same parent, compare against all permutations.
        If the canonical names match, but the particle differs, returns the particle
        comparison.

        :param other:  element to be compared (Element object)
        :param sortOther: if True and the elements match,
                          also returns a copy of other, but with its tree sorted
                          according to the way it matched self.
                          If True, but elements do not match, return None.

        :return: -1 if self < other, 0 if self == other, +1, if self > other.
        """

        if not isinstance(other, Element):
            return -1

        # make sure the topology names have been computed:
        if 'canonName' not in self.tree.graph:
            self.setCanonName()
        if 'canonName' not in other.tree.graph:
            other.setCanonName()

        # Recursively compare the nodes:
        cmp, newTree = compareNodes(self.tree, other.tree,
                                    getTreeRoot(self.tree), getTreeRoot(other.tree))

        if sortOther:
            if cmp == 0:  # Elements matched, return copy of other with tree sorted
                otherNew = other.copy()
                otherNew.tree = newTree
            else:
                otherNew = None
            return cmp, otherNew
        else:
            return cmp

    def __eq__(self, other):
        return self.compareTo(other) == 0

    def __lt__(self, other):
        return self.compareTo(other) < 0

    def __gt__(self, other):
        return self.compareTo(other) > 0

    def __hash__(self):
        return object.__hash__(self)

    def __getattr__(self, attr):
        """
        If the attribute has not been defined for the element
        try to fetch it from its branches.
        :param attr: Attribute name

        :return: Attribute value
        """

        # If calling another special method, return default (required for pickling)
        if attr.startswith('__') and attr.endswith('__'):
            return object.__getattr__(attr)

        try:
            val = [getattr(node, attr) if str(node) != 'PV' else None
                   for node in self.tree.nodes()]
            return val
        except AttributeError:
            raise AttributeError("Neither element nor particles have attribute ``%s''" % attr)

    def __str__(self):
        """
        Create the element to a string.

        :returns: string representation of the element
        """

        return treeToString(self.tree)

    def __repr__(self):

        return self.__str__()

    def __add__(self, other):
        """
        Adds two elements. Should only be used if the elements
        have the same topologies. The element weights are added and their
        odd and even particles are combined.
        """

        if not isinstance(other, Element):
            raise TypeError("Can not add an Element object to %s" % type(other))
        elif self.getCanonName() != other.getCanonName():
            raise SModelSError("Can not add elements with distinct topologies")

        newEl = self.__class__(info=self.tree)
        newEl.motherElements = self.motherElements[:] + other.motherElements[:]
        newEl.weight = self.weight + other.weight
        newEl.tree = addTrees(self.tree, other.tree)
        newEl.sort()

        return newEl

    def __radd__(self, other):
        """
        Adds two elements. Only elements with the same
        topology can be combined.
        """

        return self.__add__(other)

    def __iadd__(self, other):
        """
        Combine two elements. Should only be used if the elements
        have the same topologies. The element weights are added and their
        odd and even particles are combined.
        """

        if not isinstance(other, Element):
            raise TypeError("Can not add an Element object to %s" % type(other))
        elif self.getCanonName() != other.getCanonName():
            raise SModelSError("Can not add elements with distinct topologies")

        self.motherElements += other.motherElements[:]
        self.weight += other.weight
        self.tree = addTrees(self.tree, other.tree)

        return self

    def drawTree(self, particleColor='lightcoral',
                 smColor='skyblue',
                 pvColor='darkgray',
                 nodeScale=4, labelAttr=None, attrUnit=None):
        """
        Draws Tree using matplotlib.

        :param tree: tree to be drawn
        :param particleColor: color for particle nodes
        :param smColor: color used for particles which have the _isSM attribute set to True
        :param pvColor: color for primary vertex
        :param nodeScale: scale size for nodes
        :param labelAttr: attribute to be used as label. If None, will use the string representation
                          of the node object.
        :param attrUnit: Unum object with the unit to be removed from label attribute (if applicable)

        """

        return drawTree(self.tree, particleColor=particleColor,
                        smColor=smColor,
                        pvColor=pvColor, nodeScale=nodeScale,
                        labelAttr=labelAttr, attrUnit=attrUnit)

    def copy(self):
        """
        Create a copy of self.
        Faster than deepcopy.

        :returns: copy of element (Element object)
        """

        # Allows for derived classes (like inclusive classes)
        newel = self.__class__(info=self.tree.copy())
        newel.weight = self.weight.copy()
        newel.motherElements = self.motherElements[:]
        newel.elID = self.elID
        return newel

    def getFinalStates(self):
        """
        Get the list of particles which have not decayed (within the element)

        :returns: list of ParticleNode objects
        """

        finalStates = []
        for node in self.tree.nodes():
            if not list(self.tree.successors(node)):
                finalStates.append(node)

        return finalStates

    def _getAncestorsDict(self, igen=0):
        """
        Returns a dictionary with all the ancestors
        of the element. The dictionary keys are integers
        labeling the generation (number of generations away from self)
        and the values are a list of Element objects (ancestors) for that generation.
        igen is used as the counter for the initial generation.
        The output is also stored in self._ancestorsDict for future use.

        :param igen: Auxiliary integer indicating to which generation self belongs.

        :return: Dictionary with generation index as key and ancestors as values
                 (e.g. {igen+1 : [mother1, mother2], igen+2 : [grandmother1,..],...})
        """

        ancestorsDict = {igen+1: []}
        for mother in self.motherElements:
            if mother is self:
                continue
            ancestorsDict[igen+1].append(mother)
            for jgen, elList in mother._getAncestorsDict(igen+1).items():
                if jgen not in ancestorsDict:
                    ancestorsDict[jgen] = []
                ancestorsDict[jgen] += elList

        # Store the result
        self._ancestorsDict = dict([[key, val] for key, val in ancestorsDict.items()])

        return self._ancestorsDict

    def getAncestors(self):
        """
        Get a list of all the ancestors of the element.
        The list is ordered so the mothers appear first, then the grandmother,
        then the grandgrandmothers,...

        :return: A list of Element objects containing all the ancestors sorted by generation.
        """

        # Check if the ancestors have already been obtained (performance gain)
        if not hasattr(self, '_ancestorsDict'):
            self._getAncestorsDict()

        orderedAncestors = []
        for jgen in sorted(self._ancestorsDict.keys()):
            orderedAncestors += self._ancestorsDict[jgen]

        return orderedAncestors

    def isRelatedTo(self, other):
        """
        Checks if the element has any common ancestors with other or one
        is an ancestor of the other.
        Returns True if self and other have at least one ancestor in common
        or are the same element, otherwise returns False.

        :return: True/False
        """

        ancestorsA = set([id(self)] + [id(el) for el in self.getAncestors()])
        ancestorsB = set([id(other)] + [id(el) for el in other.getAncestors()])

        if ancestorsA.intersection(ancestorsB):
            return True
        else:
            return False

    def getCanonName(self):
        """
        Get element topology info from branch topology info.

        :returns: dictionary containing vertices and number of final states information
        """
        if 'canonName' not in self.tree.graph:
            self.setCanonName()
        return self.tree.graph['canonName']

    def setTestedBy(self, resultType):
        """
        Tag the element, all its daughter and all its mothers
        as tested by the type of result specified.
        It also recursively tags all granddaughters, grandmothers,...

        :param resultType: String describing the type of result (e.g. 'prompt', 'displaced')
        """

        self.testedBy.add(resultType)
        for ancestor in self.getAncestors():
            ancestor.testedBy.add(resultType)

    def setCoveredBy(self, resultType):
        """
        Tag the element, all its daughter and all its mothers
        as covered by the type of result specified.
        It also recursively tags all granddaughters, grandmothers,...

        :param resultType: String describing the type of result (e.g. 'prompt', 'displaced')
        """

        self.coveredBy.add(resultType)
        for mother in self.getAncestors():
            mother.coveredBy.add(resultType)

    def compressElement(self, doCompress, doInvisible, minmassgap):
        """
        Keep compressing the original element and the derived ones till they
        can be compressed no more.

        :parameter doCompress: if True, perform mass compression
        :parameter doInvisible: if True, perform invisible compression
        :parameter minmassgap: value (in GeV) of the maximum
                               mass difference for compression
                               (if mass difference < minmassgap, perform mass compression)
        :returns: list with the compressed elements (Element objects)
        """

        if not doCompress and not doInvisible:
            return []

        added = True
        newElements = [self]
        # Keep compressing the new topologies generated so far until no new
        # compressions can happen:
        while added:
            added = False
            # Check for mass compressed topologies
            if doCompress:
                for element in newElements:
                    newel = element.massCompress(minmassgap)
                    # Avoids double counting
                    # (elements sharing the same parent are removed during clustering)
                    if newel and not any(newel == el for el in newElements[:]):
                        newElements.append(newel)
                        added = True

            # Check for invisible compressed topologies (look for effective
            # LSP, such as LSP + neutrino = LSP')
            if doInvisible:
                for element in newElements:
                    newel = element.invisibleCompress()
                    # Avoids double counting
                    # (elements sharing the same parent are removed during clustering)
                    if newel and not any(newel == el for el in newElements[:]):
                        newElements.append(newel)
                        added = True

        newElements.pop(0)  # Remove original element
        return newElements

    def massCompress(self, minmassgap):
        """
        Perform mass compression.

        :parameter minmassgap: value (in GeV) of the maximum
                               mass difference for compression
                               (if mass difference < minmassgap -> perform mass compression)
        :returns: compressed copy of the element, if two masses in this
                  element are degenerate; None, if compression is not possible;
        """

        newelement = self.copy()
        newelement.motherElements = [self]
        checkCompression = True
        # Check for compression until tree can no longer be compressed
        previousName = self.getCanonName()

        while checkCompression:
            tree = newelement.tree
            root = getTreeRoot(tree)
            # Loop over nodes:
            for mom, daughters in bfs_successors(tree, root):
                if mom == root:  # Skip primary vertex
                    continue
                if not mom.particle.isPrompt():  # Skip long-lived
                    continue
                bsmDaughter = []
                smDaughters = []
                for d in daughters:
                    # Split daughters into final states SM and others (BSM)
                    if hasattr(d, '_isSM') and d._isSM and not list(tree.successors(d)):
                        smDaughters.append(d)
                    else:
                        bsmDaughter.append(d)

                # Skip decays to multiple BSM particles or to SM particles only
                if len(bsmDaughter) != 1:
                    continue
                bsmDaughter = bsmDaughter[0]

                # Check mass difference:
                massDiff = mom.mass - bsmDaughter.mass
                if massDiff > minmassgap:
                    continue

                # Get grandmother:
                gMom = list(tree.predecessors(mom))
                if len(gMom) != 1:
                    raise SModelSError('Found multiple parents for %s when compressing element. Something went wrong.' % mom)

                gMom = gMom[0]
                # Remove mother and all SM daughters and mom:
                tree.remove_nodes_from(smDaughters+[mom])

                # Attach BSM daughter to grandmother:
                tree.add_edge(gMom, bsmDaughter)

                # For safety break loop since tree structure changed
                break

            # Recompute the canonical name and
            newelement.setCanonName()
            # If iteration has not changed element, break loop
            name = newelement.getCanonName()
            if name == previousName:
                checkCompression = False
            else:
                checkCompression = True
                previousName = name
        newelement.sort()

        # If element was not compressed, return None
        if newelement.getCanonName() == self.getCanonName():
            return None
        else:
            return newelement

    def invisibleCompress(self):
        """
        Perform invisible compression.

        :returns: compressed copy of the element, if element ends with invisible
                  particles; None, if compression is not possible
        """

        newelement = self.copy()
        newelement.motherElements = [self]
        checkCompression = True
        # Check for compression until tree can no longer be compressed
        previousName = self.getCanonName()

        while checkCompression:
            tree = newelement.tree
            root = getTreeRoot(tree)
            # Loop over nodes:
            for mom, daughters in bfs_successors(tree, root):
                if mom == root:  # Skip primary vertex
                    continue
                # Skip node if its daughters are not stable
                if any(list(tree.successors(d)) for d in daughters):
                    continue
                # Check if all daughters can be considered MET
                neutralDaughters = all(d.particle.isMET() for d in daughters)
                # Check if the mother is MET or prompt:
                neutralMom = (mom.isMET() or mom.isPrompt())

                # If mother and daughters are neutral, remove daughters
                if (not neutralDaughters) or (not neutralMom):
                    continue

                tree.remove_nodes_from(daughters)
                # Replace mom particle by invisible (generic) particle
                invParticle = Particle(label='inv', mass=mom.mass,
                                       eCharge=0, colordim=1,
                                       _isInvisible=True,
                                       totalwidth=mom.totalwidth,
                                       pdg=mom.pdg, _isSM=mom._isSM)
                mom.particle = invParticle

                # For safety break loop since tree structure changed
                break

            # Recompute the canonical name and
            newelement.setCanonName()
            # If iteration has not changed element, break loop
            name = newelement.getCanonName()
            if name == previousName:
                checkCompression = False
            else:
                checkCompression = True
                previousName = name
        newelement.sort()

        # If element was not compressed, return None
        if newelement.getCanonName() == self.getCanonName():
            return None
        else:
            return newelement

    def hasTopInList(self, elementList):
        """
        Check if the element topology matches any of the topologies in the
        element list.

        :parameter elementList: list of elements (Element objects)
        :returns: True, if element topology has a match in the list, False otherwise.
        """
        if not isinstance(elementList, list) or len(elementList) == 0:
            return False
        for element in elementList:
            if type(element) != type(self):
                continue
            if self.getCanonName() == element.getCanonName():
                return True
        return False
