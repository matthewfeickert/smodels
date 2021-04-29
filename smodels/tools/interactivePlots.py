"""
.. module:: interactive_plots
   :synopsis: Main module of the interactive plots.

.. moduleauthor:: Humberto Reyes <humberto.reyes-gonzalez@lpsc.in2p3.fr>
.. moduleauthor:: Andre Lessa <lessa.a.p@gmail.com>
.. moduleauthor:: Sabine Kraml <sabine.kraml@gmail.com>

"""

from __future__ import print_function

from smodels.tools.smodelsLogging import logger, setLogLevel
from smodels.theory.exceptions import SModelSTheoryError as SModelSError
import os, glob,pathlib

from smodels.tools import interactivePlotsHelpers as helpers

class PlotMaster(object):
    """
    A class to store the required data and producing the interactive plots
    """

    def __init__(self,smodelsFolder,slhaFolder,parameterFile, indexfile ):
        """
        Initializes the class.

        :parameter smodelsFolder: path to the folder containing the smodels (python) output files
        :parameter slhaFolder: path to the folder containing the SLHA input files
        :parameter parameterFile: path to the file containing the plotting definitions
        """

        
        self.data_dict = []
        self.smodelsFolder = smodelsFolder
        self.slhaFolder = slhaFolder
        self.indexfile = indexfile
        self.parameterFile = parameterFile

        self.slha_hover_information = None
        self.ctau_hover_information = None
        self.BR_hover_information = None
        self.SModelS_hover_information = None
        self.plot_data = None
        self.variable_x = None
        self.variable_y = None
        self.plot_list = None
        self.min_BR = None


        if not os.path.isfile(parameterFile):
            raise SModelSError('Parameters file %s not found' %parameterFile)
        if not os.path.isdir(smodelsFolder):
            raise SModelSError("Folder %s not found" %smodelsFolder)
        if not os.path.isdir(slhaFolder):
            raise SModelSError("Folder %s not found" %slhaFolder)

        self.loadParameters()
        self.initializeDataDict()

    def loadParameters(self):
        """
        Reads the parameters from the plotting parameter file.
        """

        logger.info("Reading parameters from %s ..." %(self.parameterFile))

        parFile = self.parameterFile
        import imp

        try:
            with open(self.parameterFile, 'rb') as fParameters: ## imports parameter file
                parameters = imp.load_module("parameters",fParameters,self.parameterFile,('.py', 'rb', imp.PY_SOURCE))
        # except Exception as e:
        except (IOError,ValueError,ImportError,SyntaxError) as e:
            logger.error("Error loading parameters file %s: %s" % (self.parameterFile,e) )
            raise SModelSError()

        if not hasattr(parameters, 'slha_hover_information'):
            logger.debug("slha_hover_information dictionary was not found in %s. SLHA data will not be included in info box." %parFile)
            self.slha_hover_information = {}
        else:
            self.slha_hover_information = parameters.slha_hover_information

        if not hasattr(parameters, 'ctau_hover_information'):
            logger.debug("ctau_hover_information dictionary was not found in %s. Lifetime data will not be included in info box." %parFile)
            self.ctau_hover_information = {}
        else:
            self.ctau_hover_information = parameters.ctau_hover_information

        if not hasattr(parameters, 'BR_hover_information'):
            logger.debug("BR_hover_information dictionary was not found in %s. Branching ratio data will not be included in info box." %parFile)
            self.BR_hover_information = {}
        else:
            self.BR_hover_information = parameters.BR_hover_information

        if not hasattr(parameters, 'SModelS_hover_information'):
            logger.debug("SModelS_hover_information dictionary was not found in %s. SModelS data will not be included in info box." %parFile)
            self.SModelS_hover_information = {}
        else:
            self.SModelS_hover_information = list(set(parameters.SModelS_hover_information))

        if not hasattr(parameters, 'plot_data'):
            logger.debug("plot_data list was not found in %s. All points will be plotted" %parFile)
            self.plot_data = ['all']
        else:
            self.plot_data = list(set(parameters.plot_data))

        if not hasattr(parameters, 'variable_x'):
            raise SModelSError("variable_x was not found in %s. Please define the variable to be plotted in the x-axis." %parFile)
        else:
            self.variable_x = parameters.variable_x
        if not hasattr(parameters, 'variable_y'):
            raise SModelSError("variable_y was not found in %s. Please define the variable to be plotted in the y-axis." %parFile)
        else:
            self.variable_y = parameters.variable_y
        if not hasattr(parameters, 'plot_list'):
            raise SModelSError("plot_list was not found in %s. Please define the list of plots to be plotted." %parFile)
        else:
            self.plot_list = list(set(parameters.plot_list))

        if not hasattr(parameters,'min_BR'):
            logger.debug("min_BR not found in %s. Will include all decay channels")
            self.min_BR = 'all'
        else:
            self.min_BR = parameters.min_BR

        if not hasattr(parameters,'plot_title'):
            logger.warning("plot_title not defined in %s. Using default title" %parFile)
            self.plot_title = 'interactive-plots'
        else:
            self.plot_title = parameters.plot_title
        


    def initializeDataDict(self):
        """
        Initializes an empty dictionary with the plotting options.
        """
      
        self.data_dict = {}
        self.data_dict['SModelS_status']=[]
        for smodels_names in sorted(self.SModelS_hover_information):
            if smodels_names=='SModelS_status':
                continue
            self.data_dict[smodels_names]=[]
        for plot_name in self.plot_list:
            self.data_dict[plot_name]=[]
        for slha_names in self.slha_hover_information:
            self.data_dict[slha_names]=[]
        if list(self.variable_x.keys())[0] not in self.slha_hover_information.keys():
            for variable in self.variable_x:
                self.data_dict[variable]=[]
        if list(self.variable_y.keys())[0] not in self.slha_hover_information.keys():
            for variable in self.variable_y:
                self.data_dict[variable]=[]
        for ctau in self.ctau_hover_information:
            self.data_dict[ctau]=[]
        for BR in self.BR_hover_information:
            self.data_dict[BR]=[]

        self.data_dict['file'] = []
        

    def fillWith(self,smodelsOutput,slhaData):
        """
        Fill the dictionary (data_dict) with the desired data from
        the smodels output dictionary (smodelsDict) and the pyslha.Doc object
        slhaData
        """
     
        filler=helpers.Filler(self.data_dict,smodelsOutput,slhaData,self.slha_hover_information,self.ctau_hover_information,self.BR_hover_information,self.min_BR)
        #Fill with smodels data if defined
        if smodelsOutput is None:
            for key in self.SModelS_hover_information:
                if key != 'file':
                    self.data_dict[key].append(False)
        else:
            self.data_dict=filler.getSmodelSData()

        self.data_dict=filler.getSlhaData(self.variable_x,self.variable_y)
        
        


    def loadData(self,npoints=-1):
        """
        Reads the data from the smodels and SLHA folders.
        If npoints > 0, it will limit the number of points in the plot to npoints.

        :parameter npoints: Number of points to be plotted (int).
                            If < 0, all points will be used.
        """
        logger.info( f"Reading data folders {self.smodelsFolder} and {self.slhaFolder} ..." )

        n = 0
        
        for f in glob.glob(self.smodelsFolder+'/*'):

            if npoints > 0 and n >= npoints:
                break
            
            smodelsOutput = helpers.importPythonOutput(f)
           
            if not smodelsOutput:
                continue
           
            #Get SLHA file name:
            slhaFile = helpers.getSlhaFile(smodelsOutput)
            slhaFile = os.path.join(self.slhaFolder,os.path.basename(slhaFile))
            #Get SLHA data:
            slhaData = helpers.getSlhaData(slhaFile)
            if not slhaData:
                continue

            #Data read successfully
            self.data_dict['file'].append(f.split('/')[-1])
            outputStatus = helpers.outputStatus(smodelsOutput)
            
            if outputStatus == -1:
                self.fillWith(None,slhaData)
            else:
                self.fillWith(smodelsOutput,slhaData)
            n += 1

        return True

    def makePlots(self,outFolder):
        """
        Uses the data in self.data_dict to produce the plots.

        :parameter outFolder: Path to the output folder.
        """

        if not os.path.isdir(outFolder):
            os.makedirs(outFolder)


        logger.info('Making plots...')

        Plotter=helpers.Plotter(self.data_dict,self.SModelS_hover_information,
               self.slha_hover_information,self.ctau_hover_information,self.BR_hover_information,self.variable_x,self.variable_y,self.plot_list,self.plot_data,self.plot_title,outFolder)

        Plotter.makePlots()


        logger.info('Generation of interactive plots finished. Go to: \n %s/%s \n to see the plots.' % ( outFolder, self.indexfile ) )

        return True






def main(args,indexfile= "index.html" ):
    """
    Create the interactive plots using the input from argparse

    :parameter args: argparser.Namespace object containing the options for makePlots

    Main interface for the interactive-plots.

    :parameter smodelsFolder: Path to the folder containing the SModelS python output
    :parameter slhaFolder: Path to the folder containing the SLHA files corresponding to the SModelS output
    :parameter parameters: Path to the parameter file setting the options for the interactive plots
    :parameter npoints: Number of points used to produce the plot. If -1, all points will be used.
    :parameter verbosity: Verbosity of the output (debug,info,warning,error)
    :parameter indexfile: name of the starting web page (index.html)

    :return: True if the plot creation was successfull
    """




    #First check if the needed directories are there
    #inputdirSlha = os.path(args.slhaFolder)

    if os.path.isdir(args.slhaFolder)==False:
        raise SModelSError("slha directory: "+str(args.slhaFolder)+"' does not exist or is a file")

    if os.path.isdir(args.smodelsFolder)==False:
        raise SModelSError("smodels directory: "+str(args.smodelsFolder)+"' does not exist or is a file")
    if not os.path.exists ( args.outputFolder ):
        os.mkdir ( args.outputFolder )
    if os.path.isdir(args.outputFolder)==False:
        raise SModelSError(f"output directory '{args.outputFolder}' does not exist or is a file")

    if os.path.isfile(args.parameters)==False:
        raise SModelSError("parameter file '"+str(args.parameters)+"' does not exist")


    #Basic checks:
    smodelsFolder = args.smodelsFolder
    slhaFolder = args.slhaFolder
    parFile = args.parameters
    verbosity=args.verbosity
    outputFolder=args.outputFolder
    npoints=args.npoints


    try:
        import plotly
    except ImportError:
        raise SModelSError("Plotly is not installed. To use this tool, please install plotly")

    try:
        import pandas
    except ImportError:
        raise SModelSError("Pandas is not installed. To use this tool, please install pandas")


    setLogLevel(verbosity)



    plotMaster = PlotMaster(smodelsFolder,slhaFolder,parFile, indexfile )
    loadData = plotMaster.loadData(npoints)
    if not loadData:
        raise SModelSError("Error loading data from folders:\n %s\n %s" %(smodelsFolder,slhaFolder))

    plotMaster.makePlots(outputFolder)

    return outputFolder
