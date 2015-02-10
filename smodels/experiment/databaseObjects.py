"""
.. module:: databaseObjects
   :synopsis: Holds the classes and methods to load the database and create the InfoFile and DataFile
              objects as well as the list of analyses.

.. moduleauthor:: Veronika Magerl <v.magerl@gmx.at>
.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>

"""

import logging, os, sys, glob
from smodels.experiment import infoObject
from smodels.experiment import txnameObject

FORMAT = '%(levelname)s in %(module)s.%(funcName)s() in %(lineno)s: %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

logger.setLevel(level=logging.INFO)


class ExpResult(object):
    """
    Simple object to hols a pair of (InfoFile,DataFile) objects corresponding to an
    experimental result.
    
    :ivar path: path to the result folder
    :ivar info: InfoFile object
    :ivar data: DataFile object
    """
    def __init__(self, path=None):
        if path and os.path.isdir(path):
            self.path = path
            self.info = infoObject.Info(os.path.join(path,"info.txt"))
            self.txnames = []
            for txtfile in glob.iglob(os.path.join(path,"*.txt")):            
                txtFile = open(txtfile,'r')
                data = txtFile.read()
                if not "txname" in data or (not 'upperLimits' in data and not 'efficiencyMap' in data):
                    continue
                       
                self.txnames.append(txnameObject.TxName(txtfile,self.info))
            
    def __str__(self):
        label = self.info.getInfo('id') + ": "
        for txname in self.txnames:
            label += txname.txname+','
        return label[:-1]
            

class DataBase(object):    
    """
    Database object. Holds a collection of InfoFile and DataFile objects containing
    all the metainfo from the info.txt files and the corresponding data from the sms.py
    files.
    
    :ivar base: path to the database (string)
    :ivar expResultList: list of ExpResult objects 
        
    """
    def __init__(self, base=None):
        self._base = self._validateBase(base)
        self._verbosity = 'error'
        self._databaseVersion = self._getDatabaseVersion
        self.expResultList = self._loadExpResults()
        

    @property
    def databaseVersion(self):
        """
        The version of the database, read from the 'version' file.
        """
        return self._databaseVersion
        
    @property
    def base(self):
        """This is the path to the base directory where to find the database.
        
        """
        return self._base
        
    def _validateBase(self, path):
        """Validates the base directory to locate the database. 
        Exits the script if something is wrong with the path.
    
        """
        logger.debug('Try to set the path for the database to: %s' %path)
        path = os.path.realpath(path) + '/'
        if not os.path.exists(path):
            logger.error('%s is no valid path!' %path)
            sys.exit()        
        return path
    
    def __str__(self):
        idList = "Database: "+self.databaseVersion+"\n---------- \n"
        for expRes in self.expResultList:
            idList += expRes.info.getInfo('id')+'\n'
        return idList
        
             
    
    @property
    def _getDatabaseVersion(self):
        """Retrieves the version of the database using the version file.
        """
        try:
            versionFile = open(self._base + '/version')
            content = versionFile.readlines()
            versionFile.close()
            logger.debug('Found version file %s with content %s' \
            %(self._base + '/version', content))
            return content[0].strip()
            
        except IOError:
            logger.error('There is no version file %s' \
            %self._base + '/version')
            return 'unknown version'
        
    @property
    def verbosity(self):
        """Tells the level the logger is set to.
        
        """
        return self._verbosity
        
    @verbosity.setter
    def verbosity(self, level):
        """Set the logger to specified level.
        
        """
        level = self._validateLevel(level)
        self._verbosity = level
        self._setLogLevel(level)
        
    def _validateLevel(self, level):
        """Validates given level for pythons logger module.
        
        """
        if not level.lower() in ['debug', 'info', 'warning', 'error']:
            logger.error('No valid level for verbosity: %s! Browser will ' +
                         'use default setting!' %level)
            return 'error'
        return level.lower()
            
    def _setLogLevel(self, level = 'error'):
        if level == 'debug':
            logger.setLevel(level=logging.DEBUG)
        if level == 'info':
            logger.setLevel(level=logging.INFO)
        if level == 'warning':
            logger.setLevel(level=logging.WARNING)
        if level == 'error':
            pass

    def _loadExpResults(self):
        """
        Checks the database folder and generates a list of ExpResult objects for
        each (info.txt,sms.py) pair.
        
        :return: list of ExpResult objects    
        """
        
        resultsList = []
        for root, dirs, files in os.walk(self._base):
            if not 'info.txt' in files:
                logger.debug("Missing files in %s" % root)
                continue
            else:
                resultsList.append(ExpResult(root))

        if not resultsList: logger.warning("Zero results loaded.")
                
        return resultsList

    def getExpResults(self,analysisIDs=[],txnames=[]):
        """
        Returns a list of ExpResult objects.
        Each object refers to an analysisID (for UL analyses)
        or analysisID+SignalRegion (for EM analyses).
        If analysisIDs is defined, returns only the results matching one of the IDs in the list.
        If txname is defined, returns only the results matching one of the Tx names in the list.
        :param analysisID: list of analysis ids ([CMS-SUS-13-006,...])
        :param txname: list of txnames ([TChiWZ,...])
        :returns: list of ExpResult objects    
        """
        
        
        expResultList = []
        for expResult in self.expResultList:
            ID = expResult.info.getInfo('id')
            #Skip analysis not containing any of the required ids:
            if analysisIDs and not ID in analysisIDs: continue
            newExpResult = ExpResult()
            newExpResult.path = expResult.path
            newExpResult.info = expResult.info            
            newExpResult.txnames = []
            for txname in expResult.txnames:
                if txnames and not txname.txname in txnames:
                    continue
                newExpResult.txnames.append(txname)
            #Skip analysis not containing any of the required txnames:
            if not newExpResult.txnames: continue
            expResultList.append(newExpResult)                        
        return expResultList
        