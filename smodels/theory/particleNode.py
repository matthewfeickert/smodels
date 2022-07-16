"""
.. module:: tree
   :synopsis: Classes used to construct trees (root directed graphs) describing
              simplified model topologies.

.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""


from smodels.theory.exceptions import SModelSTheoryError as SModelSError
from smodels.theory.particle import Particle
from smodels.tools.inclusiveObjects import InclusiveValue

# Define a common inclusive particle object
# to be used with the inclusive node
IncluviseParticle = Particle(label='Inclusive')


class ParticleNode(object):
    """
    Simple wrapper for creating graphs with Particle objects.
    It is necessary because the same particle can appear multiple
    times within a tree, so
    Particle objects can not be directly used as nodes
    (since the same particle can not appear as distinct nodes)

    :ivar particle: Stores the Particle object
    """

    def __init__(self, particle,
                 isFinalState=False,
                 isInclusive=False, inclusiveList=False):

        self.particle = particle

        # Flag to tag nodes which should not be decayed
        self.isFinalState = isFinalState

        # Flag to identify as non-inclusive node:
        self.isInclusive = isInclusive

        # Flag to identify as non-inclusive node:
        self.inclusiveList = inclusiveList

    def __hash__(self):
        return object.__hash__(self)

    def __cmp__(self, other):
        """
        Node comparison based on compareTo method

        :return: 0 if nodes are equal, 1 if self > other, -1 otherwise
        """

        return self.compareTo(other)

    def __lt__(self, other):
        return self.__cmp__(other) == -1

    def __gt__(self, other):
        return self.__cmp__(other) == 1

    def __eq__(self, other):
        return self.__cmp__(other) == 0

    def __ne__(self, other):
        return self.__cmp__(other) != 0

    def __str__(self):

        label = str(self.particle)
        if self.inclusiveList:
            label = '*'+label
        return label

    def __repr__(self):

        return self.__str__()

    def __getattr__(self, attr):
        """
        Returns the attribute from particle.

        :parameter attr: Attribute string

        :return: Attribute from self.particle
        """

        return getattr(self.particle, attr)

    def __getstate__(self):
        """
        Since getattr is defined, we must defined getstate
        for pickling/unpickling.
        """

        attrDict = self.__dict__

        return attrDict

    def __setstate__(self, state):
        """
        Since getattr is defined, we must defined getstate
        for pickling/unpickling.
        """

        self.__dict__.update(state)

    def __add__(self, other):
        """
        Adds two nodes. The properties of self are kept, except
        for the particle, which are added with other.

        :param other: ParticleNode object

        :return: a copy of self with the particle combined with other.particle
        """

        newNode = self.copy()
        newNode.particle = self.particle + other.particle

        return newNode

    def compareTo(self, other):
        """
        Compare nodes accoring to  particles.

        :param other: ParticleNode or InclusiveParticleNode object

        :return: 1 if self > other, -1 if self < other and 0 if self == other
        """

        if other.isInclusive:
            return -other.compareTo(self)
        if not isinstance(other, ParticleNode):
            raise SModelSError("Can not compare node to %s" % type(other))

        cmp = self.particle.__cmp__(other.particle)

        return cmp

    def equalTo(self, other):
        """
        Compare nodes accoring to their particle.

        :param other: ParticleNode or InclusiveParticleNode object

        :return: True if nodes are equal, false otherwise
        """

        return (self.compareTo(other) == 0)

    def copy(self):
        """
        Makes a shallow copy of itself. The particle attribute
        shares the same object with the original copy.
        :return: ParticleNode object
        """

        newNode = ParticleNode(particle=self.particle,
                               isInclusive=self.isInclusive,
                               isFinalState=self.isFinalState)

        return newNode


class InclusiveParticleNode(ParticleNode):
    """
    An inclusive ParticleNode class. It will return True when compared to any other ParticleNode object or InclusiveParticleNode object.

    :ivar particle: IncluviseParticle (dummy)
    :ivar finalStates: Allowed final states (final state nodes)
    """

    def __init__(self, particle=IncluviseParticle,
                 finalStates=[]):

        ParticleNode.__init__(self, particle=particle,
                              isFinalState=True,
                              isInclusive=True)

        # Store the final states for the inclusive node
        self.finalStates = sorted(finalStates)

    def compareTo(self, other):
        """
        Dummy method. Always return 0, since it will always match any node.

        :param other: ParticleNode or InclusiveParticleNode object

        :return: 0
        """

        return 0

    def equalFinalStates(self,otherFinalStates):
        """
        Compares only the finalStates of self to otherFinalStates.
        All the final states in other have to match at least one final
        state in self.

        :param otherFinalStates: List of particle objects

        :return: True if all the particles in otherFinalStates match
                 at least one particle in self.finalStates.
        """

        fsOther = otherFinalStates
        for fs in fsOther:
            if not any(fs == fsB for fsB in self.finalStates):
                return False

        return True


    def copy(self):
        """
        Makes a shallow copy of itself. The particle attribute
        shares the same object with the original copy.
        :return: ParticleNode object
        """

        newNode = InclusiveParticleNode(particle=self.particle,
                                        finalStates=self.finalStates[:])

        return newNode

    def longStr(self):
        """
        Returns a string representation of self containing
        its final states.

        :return: String
        """

        nodeStr = str(self)
        if self.finalStates:
            fStates = [str(ptc) for ptc in self.finalStates]
            nodeStr += '\n(%s)' % (','.join(fStates))
        return nodeStr

    def __getattr__(self, attr):
        """
        Returns None if does not contain the attribute.

        :parameter attr: Attribute string

        :return: Attribute value or None
        """

        if attr not in self.__dict__:
            return None
