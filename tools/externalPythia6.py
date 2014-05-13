#!/usr/bin/env python

"""
.. module:: externalPythia6
   :synopsis: Wrapper for pythia6.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

import setPath
from smodels.tools.externalTool import ExternalTool
import tempfile
import os
import shutil
import commands
from smodels import SModelS
import urllib
import tarfile
import logging

logger = logging.getLogger(__name__)


class ExternalPythia6(ExternalTool):
    """
    An instance of this class represents the installation of pythia6.
    
    """
    def __init__(self,
                 config_file="<install>/etc/pythia.card",
                 executable_path="<install>/tools/external/pythia6/pythia_lhe",
                 src_path="<install>/pythia6/", verbose=False):
        """ 
        :param config_file: location of the config file, full path; copy this
        file and provide tools to change its content and to provide a template
        :param executable_path: location of executable, full path (pythia_lhe)
        
        """
        self.name = "pythia6"
        self.executable_path = self.absPath(executable_path)
        self.src_path = self.absPath(src_path)
        self.verbose = False
        self.tempdir = tempfile.mkdtemp()
        self.cfgfile = self.checkFileExists(config_file)
        self.reset()


    def reset(self):
        """
        Copy the original config file again.
        
        """
        shutil.copy(self.cfgfile, self.tempdir + "/temp.cfg")


    def checkFileExists(self, inputFile):
        """
        Check if file exists, raise an IOError if it does not.
        
        :returns: absolute file name if file exists.
        
        """
        nFile = self.absPath(inputFile)
        if not os.path.exists(nFile):
            raise IOError("config file %s does not exist" % nFile)
        return nFile


    def tempDirectory(self):
        """
        Return the temporary directory name.
        
        """
        return self.tempdir


    def unlink(self, unlinkdir=True):
        """
        Remove temporary files.
        
        :param unlinkdir: remove temp directory completely
        
        """
        logger.debug("Unlinking " + self.tempdir)
        for inputFile in ["fort.61", "fort.68"]:
            if os.path.exists(self.tempdir + "/" + inputFile):
                os.unlink(self.tempdir + "/" + inputFile)
        if unlinkdir:
            for inputFile in ["temp.cfg"]:
                os.unlink(self.tempdir + "/" + inputFile)
            if os.path.exists(self.tempdir):
                os.rmdir(self.tempdir)


    def replaceInCfgFile(self, replacements={"NEVENTS": 10000, "SQRTS":8000}):
        """
        Replace strings in the config file by other strings, similar to
        setParameter.

        This is introduced as a simple mechanism to make changes to the
        parameter file.
        
        :param replacements: dictionary of strings and values; the strings will
                             be replaced with the values; the dictionary keys 
                             must be strings present in the config file
        
        """
        f = open(self.tempdir + "/temp.cfg")
        lines = f.readlines()
        f.close()
        f = open(self.tempdir + "/temp.cfg", "w")
        for line in lines:
            for (key, value) in replacements.items():
                line = line.replace(key, str(value))
            f.write(line)
        f.close()


    def setParameter(self, param="MSTP(163)", value=6):
        """
        Modifies the config file, similar to .replaceInCfgFile.
        
        It will set param to value, overwriting possible old values.
        
        """
        f = open(self.tempdir + "/temp.cfg")
        lines = f.readlines()
        f.close()
        f = open(self.tempdir + "/temp.cfg", "w")
        for line in lines:  # # copy all but lines with "param"
            if not param in line:
                f.write(line)
        f.write("%s=%s\n" % (param, str(value)))
        f.close()


    def run(self, slhafile, cfgfile=None):
        """
        Run Pythia.
        
        :param slhafile: SLHA file
        :param cfgfile: optionally supply a new config file; if not supplied,
                        use the one supplied at construction time; 
                        this config file will not be touched or copied;  
                        it will be taken as is
        :returns: stdout and stderr, or error message
        
        """
        slha = self.checkFileExists(slhafile)
        cfg = self.tempdir + "/temp.cfg"
        if cfgfile != None:
            cfg = self.absPath(cfgfile)
            logger.debug("running with " + str(cfg))
        shutil.copy(slha, self.tempdir + "/fort.61")
        cmd = "cd %s ; %s < %s" % \
             (self.tempdir, self.executable_path, cfg)
        logger.debug("Now running " + str(cmd))
        Out = commands.getoutput(cmd)
        self.unlink(unlinkdir=False)
        return Out


    def compile(self):
        """
        Compile pythia_lhe.
        
        """
        logger.info("Trying to compile pythia:")
        cmd = "cd %s; make" % self.src_path
        out = commands.getoutput(cmd)
        logger.info(out)


    def fetch(self, verbose=True):
        """
        Fetch and unpack tarball.
        
        """
        tempfile = "/tmp/pythia.tar.gz"
        f = open(tempfile, "w")
        if verbose:
            logger.info("Fetching tarball...")
        url = "http://smodels.hephy.at/externaltools/pythia/pythia.tar.gz"
        r = urllib.urlopen(url)
        l = r.readlines()
        for line in l:
            f.write(line)
        r.close()
        f.close()
        if verbose:
            logger.info("... done.")
            logger.info("Untarring...")
        tar = tarfile.open(tempfile)
        for item in tar:
            tar.extract(item, self.src_path)
        if verbose:
            logger.info("... done.")


    def checkInstallation(self):
        """
        Check if installation of tool is correct by looking for executable and
        running it.
        
        """
        if not os.path.exists(self.executable_path):
            logger.error("executable '%s' not found", self.executable_path)
            return False
        if not os.access(self.executable_path, os.X_OK):
            logger.error("%s is not executable", self.executable)
            return False
        inputFile = "/inputFiles/slha/andrePT4.slha"
        slhafile = SModelS.installDirectory() + inputFile
        try:
            out = self.run(slhafile, "<install>/etc/pythia_test.card")
            out = out.split("\n")

            out.pop()
            val = (" ********* Fraction of events that fail fragmentation "
                   "cuts =  0.00000 *********")
            lines = {-1 : val}
            for (nr, line) in lines.items():
                if out[nr].find(line) == -1:
                    logger.error("Expected >>>%s<<< found >>>%s<<<", line,
                                 out[nr])
                    return False
        except Exception, e:  # TODO: which exception?
            logger.error("Something is wrong with the setup: exception %s", e)
        return True


if __name__ == "__main__":
    tool = ExternalPythia6()
    print("installed: " + str(tool.installDirectory()))
    def ok(B):
        """
        TODO: write docstring
        
        """
        if B:
            return "ok"
        return "error"
    td_exists = ok(os.path.exists(tool.tempDirectory()))
    print("temporary directory: %s: %s" % (str(tool.tempDirectory()),
                                           td_exists))
    print("check: " + ok(tool.checkInstallation()))
    tool.replaceInCfgFile({"NEVENTS": 1, "SQRTS":8000})
    tool.setParameter("MSTP(163)", "6")
    print("run:")
    slhafile = SModelS.installDirectory() + "/inputFiles/slha/andrePT4.slha"
    out = tool.run(slhafile)
    tool.unlink()
