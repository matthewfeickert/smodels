"""This Package is intended to contain everything related to theory:

   * cross section calculation code
   * sms decomposition code (LHE-based, SLHA-based)
   * some more tools, e.g. for reading/writing slha files, or particle names
   
"""
import os
from tools import loggingConfiguration
logger = loggingConfiguration.createLogger  (__name__ )
