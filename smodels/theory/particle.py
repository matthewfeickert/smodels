"""
.. module:: particle
   :synopsis: Defines the particle class and particle list class, their methods and related functions

.. moduleauthor:: Alicia Wongel <alicia.wongel@gmail.com>
.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>
"""

import copy,itertools,weakref

class Particle(object):
    """
    An instance of this class represents a single particle. 
    The properties are: label, pdg, mass, electric charge, color charge, width 
    """
    
    _instances = set()

    def __init__(self, **kwargs):
        """         
        Initializes the particle.
        Assigns an ID to the isntance using the class Particle._instance
        list. Reset the comparison dictionary.
        
        Possible properties for arguments.
        Z2parity: int, +1 or -1
        label: str, e.g. 'e-'
        pdg: number in pdg
        mass: mass of the particle
        echarge: electric charge as multiples of the unit charge
        colordim: color dimension of the particle 
        spin: spin of the particle
        totalwidth: total width
        """  
        
        for attr,value in kwargs.items():
            setattr(self,attr,value)
        self.id = Particle.getID()
        self._comp = {self.id : 0}            
        Particle._instances.add(weakref.ref(self))
        
    def __getstate__(self):
        """
        Override getstate method. Required for pickling.
        """  
        return self.__dict__

    def __setstate__(self, state):
        """
        Override setstate method. Required for pickling.
        It makes sure the instance is added to the list Particle._instances,
        its ID is properly set and the comp dictionary is reset.
        """
        
        self.__init__(**state)
        
    def __hash__(self):
        """
        Return the object address. Required for using weakref
        """
        return id(self)
    
    def __del__(self):
        """
        If the instance is deleted, make sure to remove all references to
        it from the comparison dictionary of other Particle or MultiParticle instances.
        """
        
        for obj in Particle.getinstances():            
            obj._comp.pop(self.id,None)
        del self
        
    @classmethod
    def getParticle(cls,**kwargs):        
        for obj in Particle.getinstances():
            if not isinstance(obj,Particle):
                continue
            if any(not hasattr(obj, attr) for attr in kwargs):
                continue
            if any(getattr(obj, attr) != value for attr,value in kwargs.items()):
                continue
            return obj
        return Particle(**kwargs)
        
    @classmethod
    def getinstances(cls):
        dead = set()
        for ref in Particle._instances:
            obj = ref()
            if obj is not None:
                yield obj
            else:
                dead.add(ref)
        Particle._instances -= dead
        
    @classmethod
    def getID(cls):
        #lastID = highest id so far or 0, if there are no instances of the class
        lastID = max([obj.id for obj in Particle.getinstances()]+[-1])
        return lastID+1
            

    def __cmp__(self,other):
        """
        Compares particle with other.
        The comparison is based on the particle properties.
        
        :param other:  particle to be compared (Particle or MultiParticle object)
        
        :return: -1 if particle < other, 1 if particle > other and 0 if particle == other
        """    
        
        if not isinstance(other,(MultiParticle,Particle)):
            raise ValueError

        #First check if we have already compared to this object        
        if other.id in self._comp:
            return self._comp[other.id]
        elif self.id in other._comp:
            return -other._comp[self.id]

        cmpProp = self.cmpProperties(other) #Objects have not been compared yet.
        self._comp[other.id] = cmpProp
        other._comp[self.id] = -cmpProp
        return cmpProp

    def __lt__( self, p2 ):
        return self.__cmp__(p2) == -1

    def __gt__( self, p2 ):
        return self.__cmp__(p2) == 1

    def __eq__( self, p2 ):
        return self.__cmp__(p2) == 0
        
    def __ne__( self, p2 ):
        return self.__cmp__(p2) != 0

    def __str__(self): 
        if hasattr(self, 'label'):
            return self.label
        else: return ''
        
    def __repr__(self):
        return self.__str__()        
    
    def __add__(self, other):
        """
        Define addition of two Particle objects
        or a Particle object and a MultiParticle object.
        The result is a MultiParticle object containing
        both particles.
        """

        if not isinstance(other,(MultiParticle,Particle)):
            raise TypeError("Can only add particle objects")
        elif isinstance(other,MultiParticle):
            return other.__add__(self)
        elif self.contains(other):
            return self
        elif other.contains(self):
            return other
        else:
            combined = MultiParticle(label = 'multiple', particles= [self,other])
            return combined

    def __radd__(self,other):
        return self.__add__(other)

    def __iadd__(self,other):
        return self.__add__(other)


    def describe(self):
        return str(self.__dict__)

    def eqProperties(self,other, 
                     properties = ['Z2parity','spin','colordim','eCharge','mass','totalwidth']):
        """
        Check if particle has the same properties (default is spin, colordim and eCharge)
        as other. Only compares the attributes which have been defined in both objects.
        
        :param other: a Particle or MultiParticle object
        :param properties: list with properties to be compared. Default is spin, colordim and eCharge
        
        :return: True if all properties are the same, False otherwise.
        """
        
        if self.cmpProperties(other, properties=properties) == 0:
            return True
        else:
            return False
            
    def cmpProperties(self,other, 
                      properties = ['Z2parity','spin','colordim','eCharge','mass','totalwidth']):
        """
        Compare properties (default is spin, colordim and eCharge).
        Return 0 if properties are equal, -1 if self < other and 1 if self > other.
        Only compares the attributes which have been defined in both objects.
        The comparison is made in hierarchical order, following the order
        defined by the properties list.
        
        :param other: a Particle or MultiParticle object
        :param properties: list with properties to be compared. Default is spin, colordim and eCharge
        
        :return: 0 if properties are equal, -1 if self < other and 1 if self > other.
        """

        if isinstance(other,(MultiParticle)):
            return -1*other.cmpProperties(self,properties=properties)
        
        for prop in properties:
            if not hasattr(self,prop) or not hasattr(other,prop):
                continue
            x = getattr(self,prop)
            y = getattr(other,prop)
            if x == y:
                continue
            if x > y:
                return 1
            else:
                return -1
            
        return 0

    def copy(self):
        """
        Make a copy of self (using deepcopy)
        
        :return: A Particle object identical to self
        """

        return copy.deepcopy(self)

    def chargeConjugate(self,label=None):
        """
        Returns the charge conjugate particle (flips the sign of eCharge).        
        If it has a pdg property also flips its sign.
        If label is None, the charge conjugate name is defined as the original name plus "~" or
        if the original name ends in "+" ("-"), it is replaced by "-" ("+")

        :parameter label: If defined, defines the label of the charge conjugated particle.

        :return: the charge conjugate particle (Particle object)
        """
        
        pConjugate = self.copy()
        pConjugate.id = Particle.getID()
        pConjugate._comp = {pConjugate.id : 0}
                    
        if hasattr(pConjugate, 'pdg') and pConjugate.pdg:
            pConjugate.pdg *= -1       
        if hasattr(pConjugate, 'eCharge') and pConjugate.eCharge:
            pConjugate.eCharge *= -1    
        if hasattr(pConjugate, 'label'):                
            if pConjugate.label[-1] == "+":
                pConjugate.label = pConjugate.label[:-1] + "-"
            elif pConjugate.label[-1] == "-":
                pConjugate.label = pConjugate.label[:-1] + "+"
            elif pConjugate.label[-1] == "~":
                pConjugate.label = pConjugate.label[:-1]
            else:
                pConjugate.label += "~"            
        
        if not label is None:
            pConjugate.label = label
            
        return pConjugate

    def isNeutral(self):
        """
        Return True if the particle is electrically charged and color neutral.
        If these properties have not been defined, return True.
        
        :return: True/False
        """
        
        if hasattr(self,'eCharge') and self.eCharge != 0:
            return False
        if hasattr(self,'colordim') and self.colordim != 1:
            return False
        
        return True
    
    def isMET(self):
        """
        Checks if the particle can be considered as MET.
        If the isMET attribute has not been defined, it will return True/False is isNeutral() = True/False.
        Else it will return the isMET attribute.
        
        :return: True/False
        """
        
        if hasattr(self,'_isMET'):
            return self._isMET
        else:
            return self.isNeutral()

    def isPrompt(self):
        """
        Checks if the particle decays promptly (e.g. totalwidth = inf).

        :return: True/False
        """

        return self.totalwidth.asNumber() == float('inf')

    def isStable(self):
        """
        Checks if the particle is stable (e.g. totalwidth = 0).

        :return: True/False
        """

        return self.totalwidth.asNumber() == 0.
    
    def contains(self,particle):
        """
        If particle is a Particle object check if self and particle are the same object.

        :param particle: Particle or MultiParticle object

        :return: True/False
        """

        if self is particle:
            return True
        else:
            return False    


class MultiParticle(Particle):

    """ An instance of this class represents a list of particle object to allow for inclusive expresions such as jet. 
        The properties are: label, pdg, mass, electric charge, color charge, width 
    """
    
    def __init__(self, label, particles, **kwargs):

        """ 
        Initializes the particle list.
        """        
        self.label = label
        self.particles = particles
        Particle.__init__(self,**kwargs)
        self._comp = dict([[self.id,0]] + [[ptc.id,0] for ptc in particles])
        
    def __del__(self):
        """
        If the instance is deleted, make sure to remove all references to
        it from the comparison dictionary of other Particle or MultiParticle instances.
        """
        for obj in Particle.getinstances():            
            obj._comp.pop(self.id,None)
        del self
        
    @classmethod
    def getMultiParticle(cls,*args,**kwargs):
        attrDict = {}
        posArg = ['label','particles']
        for i,v in enumerate(args):
            attrDict[posArg[i]] = v
        attrDict.update(kwargs)
        particles = sorted(attrDict.pop('particles'))
        label = attrDict.pop('label')
        for obj in Particle.getinstances():
            if not isinstance(obj,MultiParticle):
                continue
            if any(not hasattr(obj, attr) for attr in attrDict):
                continue            
            pListB = sorted(obj.particles)
            if len(particles) != len(pListB):
                continue            
            if any(pA is not pListB[i] for i,pA in enumerate(particles)):
                continue
            if any(getattr(obj, attr) != value for attr,value in attrDict.items()):
                continue
            return obj
        return MultiParticle(label=label,particles=particles,**attrDict)
        
        
    def __getattribute__(self,attr):
        """
        If MultiParticle does not have attribute, return a list
        if the attributes of each particle in self.particles.
        If not all particles have the attribute, it will raise an exception.
        If all particles share a common attribute, a single value
        will be returned.
         
        :parameter attr: Attribute string
         
        :return: Attribute or list with the attribute values in self.particles
        """

        #Try to get the attribute directly
        try:
            return Particle.__getattribute__(self,attr)
        except:
            pass
        
        #If not found, try to fetch it from its particles
        try:
            values = [getattr(particle,attr) for particle in self.particles]
            if all(type(x) == type(values[0]) for x in values):
                if all(x == values[0] for x in values):
                    return values[0]
            return values
        except:
            raise AttributeError
            
    def cmpProperties(self,other, 
                      properties = ['Z2parity','spin','colordim','eCharge','mass','totalwidth']):
        """
        Compares the properties in self with the ones in other.
        If other is a Particle object, checks if any of the particles in self matches
        other.
        If other is a MultiParticle object, checks if any particle in self matches
        any particle in other.
        If self and other are equal returns 0,
        else returns the result of comparing the first particle of self with other.
        
        :param other: a Particle or MultiParticle object
        :param properties: list with properties to be compared. Default is spin, colordim and eCharge
        
        :return: 0 if properties are equal, -1 if self < other and 1 if self > other.
        """
        
        #Check if any of its particles matches other
        if isinstance(other,Particle):
            otherParticles = [other]
        elif isinstance(other,MultiParticle):
            otherParticles = other.particles
            
        for otherParticle in otherParticles:
            if any(p.cmpProperties(otherParticle,properties) == 0 for p in self.particles):
                return 0
 
        cmpv = self.particles[0].cmpProperties(otherParticles[0],properties)
        return cmpv

    def __add__(self, other):
        """
        Define addition of two Particle objects
        or a Particle object and a MultiParticle object.
        The result is a MultiParticle object containing
        both particles.
        """

        if not isinstance(other,(MultiParticle,Particle)):
            raise TypeError("Can not add a Particle object to %s" %type(other))
        elif other is self or self.contains(other): #Check if other is self or a subset of self
            return self
        #Check if self is a subset of other
        if other.contains(self):
            return other        
        elif isinstance(other,MultiParticle):
            addParticles = [ptc for ptc in other.particles if not self.contains(ptc)] 
        elif isinstance(other,Particle):
            addParticles = [other]

        combinedParticles = self.particles[:] + addParticles[:]
        combined = MultiParticle(label = 'multiple', particles = combinedParticles)

        return combined
    
    def __radd__(self,other):
        return self.__add__(other)
    
    def __iadd__(self,other):
        
        if isinstance(other,MultiParticle):
            self.particles += [ptc for ptc in other.particles if not self.contains(ptc)]
        elif isinstance(other,Particle):
            if not self.contains(other):
                self.particles.append(other)
        #Since the multiparticle changed, reset comparison tracking:
        self._comp = {self.id : 0}
        for ptc in self.particles:
            self._comp[ptc.id] = 0

        return self

    def getPdgs(self):
        """
        pdgs appearing in MultiParticle
        :return: list of pgds of particles in the MultiParticle
        """
        
        pdgs = [particle.pdg for particle in self.particles]
        
        return pdgs
        
    def getLabels(self):
        """
        labels appearing in MultiParticle
        :return: list of labels of particles in the MultiParticle
        """
        
        labels = [particle.label for particle in self.particles]
        
        return labels
    
    def isNeutral(self):
        """
        Return True if ALL particles in particle list are neutral.
        
        :return: True/False
        """
        
        neutral = all(particle.isNeutral() for particle in self.particles)
        return neutral

    def isMET(self):
        """
        Checks if all the particles in self can be considered as MET.
        
        :return: True/False
        """
        
        met = all(particle.isMET() for particle in self.particles)
        return met

    def contains(self,particle):
        """
        Check if MultiParticle contains the Particle object or MultiParticle object.

        :param particle: Particle or MultiParticle object

        :return: True/False
        """

        if not isinstance(particle,(Particle,MultiParticle)):
            raise False
        elif isinstance(particle,MultiParticle):
            checkParticles = particle.particles
        else:
            checkParticles = [particle]

        for otherParticle in checkParticles:
            hasParticle = False
            for p in self.particles:
                if p.contains(otherParticle):
                    hasParticle = True
            if not hasParticle:
                return False

        return True
    
    
class ParticleList(object):
    """
    Simple class to store a list of particles.
    """
    
    _instances = set()

    def __init__(self,particles=[],**kwargs):

        self.particles = particles[:]
        self.id = ParticleList.getID()
        self._comp = {self.id : 0}
        ParticleList._instances.add(weakref.ref(self))

    def __setstate__(self,state):
        """
        Override setstate method. Required for pickling.
        It makes sure the instance is added to the list of instances,
        its ID is properly set and the comp dictionary is reset.
        """
        
        self.__init__(**state)
        
    def __hash__(self):
        return id(self)   
    
    def __del__(self):
        for obj in ParticleList.getinstances():            
            obj._comp.pop(self.id,None)
        del self
    
    @classmethod
    def getVertex(cls,particles):
        pList = sorted(particles)
        for obj in ParticleList.getinstances():
            if len(obj) != len(pList):
                continue
            if all(ptc is obj.particles[iptc] for iptc,ptc in enumerate(pList)):
                return obj
        return ParticleList(pList)

    @classmethod
    def getinstances(cls):
        dead = set()
        for ref in ParticleList._instances:
            obj = ref()
            if obj is not None:
                yield obj
            else:
                dead.add(ref)
        ParticleList._instances -= dead
        
    @classmethod
    def getID(cls):
        #lastID = highest id so far or 0, if there are no instances of the class
        lastID = max([obj.id for obj in ParticleList.getinstances()]+[-1])
        return lastID+1
        
    def __cmp__(self,other):
        """
        Compares two particle lists irrespective of the particle ordering.
        
        :param other:  particle list to be compared (ParticleList object)
        
        :return: -1 if self < other, 1 if self > other, 0 is self == other 
        """    
        
        if not isinstance(other,ParticleList):
            raise ValueError

        #First check if we have already compared to this object
        if other.id in self._comp:
            return self._comp[other.id]
        
        if len(self) != len(other):
            comp = len(self) > len(other)
            if comp:
                comp = 1
            else:
                comp = -1
            self._comp[other.id] = comp
            other._comp[self.id] = comp
            return comp
        
        #Compare even final states irrespective of ordering:
        for particles in itertools.permutations(self.particles):
            particles = list(particles)
            if particles == other.particles:
                self._comp[other.id] = 0
                other._comp[self.id] = 0
                return 0
        
        comp = self.particles > other.particles
        if comp:
            comp = 1
        else:
            comp = -1
        self._comp[other.id] = comp
        other._comp[self.id] = -comp
            
        return comp

    def __lt__( self, p2 ):
        return self.__cmp__(p2) == -1

    def __gt__( self, p2 ):
        return self.__cmp__(p2) == 1

    def __eq__( self, p2 ):
        return self.__cmp__(p2) == 0
        
    def __ne__( self, p2 ):
        return self.__cmp__(p2) != 0

    def __iter__(self):
        return iter(self.particles)

    def __getitem__(self, i):
        return self.particles[i]
    
    def __setitem__(self, i, value):
        self.particles[i] = value

    def __len__(self):
        return len(self.particles)
    
    def __str__(self):
        return str([str(ptc) for ptc in self.particles]) 
        
    def __repr__(self):
        return self.__str__()        
