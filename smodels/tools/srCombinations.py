#!/usr/bin/env python3

"""
.. module:: srCombinations
   :synopsis: a module to contain the logic around combinations of signal regions
              within a single analysis, be they SL-based or pyhf-based.

.. moduleauthor:: Wolfgang Waltenberger <wolfgang.waltenberger@gmail.com>

"""

from smodels.tools.simplifiedLikelihoods import LikelihoodComputer, Data, UpperLimitComputer
from smodels.tools.smodelsLogging import logger
from smodels.theory.exceptions import SModelSTheoryError as SModelSError
import numpy as np
from smodels.tools.statsTools import StatsComputer

def getCombinedUpperLimitFor(dataset, nsig, expected=False, deltas_rel=0.2):
    """
    Get combined upper limit. If covariances are given in globalInfo then
    simplified likelihood is used, else if json files are given pyhf
    cimbination is performed.

    :param nsig: list of signal events in each signal region/dataset. The list
                    should obey the ordering in globalInfo.datasetOrder.
    :param expected: return expected, not observed value
    :param deltas_rel: relative uncertainty in signal (float). Default value is 20%.

    :returns: upper limit on sigma*eff
    """

    if dataset.type == "simplified":
        cov = dataset.globalInfo.covariance
        if type(cov) != list:
            raise SModelSError("covariance field has wrong type: %s" % type(cov))
        if len(cov) < 1:
            raise SModelSError("covariance matrix has length %d." % len(cov))

        computer = StatsComputer ( dataset, nsig, deltas_rel = deltas_rel,
               marginalize = dataset._marginalize )
        ret = computer.poi_upper_limit ( expected = expected, limit_on_xsec = True )
        logger.debug("SL upper limit : {}".format(ret))
        return ret
    elif dataset.type == "pyhf":
        logger.debug("Using pyhf")
        if all([s == 0 for s in nsig]):
            logger.warning("All signals are empty")
            return None
        ulcomputer = _getPyhfComputer(dataset, nsig)
        ret = ulcomputer.getUpperLimitOnSigmaTimesEff(expected=expected)
        logger.debug("pyhf upper limit : {}".format(ret))
        return ret
    else:
        logger.error(
            "no covariance matrix or json file given in globalInfo.txt for %s"
            % dataset.globalInfo.id
        )
        raise SModelSError(
            "no covariance matrix or json file given in globalInfo.txt for %s"
            % dataset.globalInfo.id
        )


def getCombinedLikelihood(
    dataset, nsig, marginalize=False, deltas_rel=0.2, expected=False, mu=1.0
):
    """compute only lBSM
    :param nsig: predicted signal (list)
    :param deltas_rel: relative uncertainty in signal (float). Default value is 20%.
    :param expected: compute expected, not observed likelihood. if "posteriori",
                     compute expected posteriori.
    :param mu: signal strength parameter mu
    """
    if dataset.type == "pyhf":
        # Getting the path to the json files
        # Loading the jsonFiles
        ulcomputer = _getPyhfComputer(dataset, nsig, False)
        index = ulcomputer.getBestCombinationIndex()
        lbsm = ulcomputer.likelihood(mu=mu, workspace_index=index, expected=expected)
        return lbsm
    lbsm = getCombinedSimplifiedLikelihood(
        dataset, nsig, marginalize, deltas_rel, expected=expected, mu=mu )
    return lbsm

def getCombinedPyhfStatistics(
    dataset, nsig, marginalize, deltas_rel, nll=False, expected=False, 
    allowNegativeSignals=False
):
        # Getting the path to the json files
        # Loading the jsonFiles
        computer = StatsComputer ( dataset, nsig, deltas_rel = deltas_rel,
               marginalize = dataset._marginalize, normalize = False )
        ulcomputer = _getPyhfComputer(dataset, nsig, False)
        lbsm = computer.likelihood(poi_test=1.0, expected=expected, return_nll = False )
        ret = computer.maximize_likelihood ( expected = expected, allowNegativeSignals =allowNegativeSignals )
        lmax = ret["llhd"]
        muhat = ret["muhat"]
        sigma_mu = ret["sigma_mu"]
        lsm = computer.likelihood(poi_test=0.0, expected=expected, return_nll=False )
        return { "lbsm": lbsm, "lmax": ret["llhd"], "lsm": lsm, "muhat": ret["muhat"],
                 "sigma_mu": ret["sigma_mu"] }

def getCombinedStatistics(
    dataset, nsig, marginalize=False, deltas_rel=0.2, expected=False, allowNegativeSignals=False
):
    """compute lBSM, lmax, and LSM in a single run
    :param nsig: predicted signal (list)
    :param deltas_rel: relative uncertainty in signal (float). Default value is 20%.
    :param expected: compute expected values, not observed
    """
    if dataset.type == "pyhf":
        return getCombinedPyhfStatistics ( dataset, nsig, marginalize, deltas_rel,
            deltas_rel, expected=expected, allowNegativeSignals=allowNegativeSignals)
    cslm = getCombinedSimplifiedStatistics( dataset, nsig, marginalize,
        deltas_rel, expected=expected, allowNegativeSignals=allowNegativeSignals,
    )
    return cslm

_pyhfcomputers = {}

def _getPyhfComputer(dataset, nsig, normalize=True):
    """create the pyhf ul computer object
    :param normalize: if true, normalize nsig
    :returns: pyhf upper limit computer, and combinations of signal regions
    """
    idt = dataset.globalInfo.id + str(nsig)
    if idt in _pyhfcomputers:
        return _pyhfcomputers[idt]
    # Getting the path to the json files
    jsonFiles = [js for js in dataset.globalInfo.jsonFiles]
    jsons = dataset.globalInfo.jsons.copy()
    # datasets = [ds.getID() for ds in dataset._datasets]
    datasets = [ds.getID() for ds in dataset.origdatasets]
    total = sum(nsig)
    # if total == 0.0:  # all signals zero? can divide by anything!
    #     total = 1.0
    if normalize and total != 0.:
        nsig = [
            s / total for s in nsig
        ]  # Normalising signals to get an upper limit on the events count
    # Filtering the json files by looking at the available datasets
    for jsName in dataset.globalInfo.jsonFiles:
        if all([ds not in dataset.globalInfo.jsonFiles[jsName] for ds in datasets]):
            # No datasets found for this json combination
            jsIndex = jsonFiles.index(jsName)
            jsonFiles.pop(jsIndex)
            jsons.pop(jsIndex)
            continue
        if not all([ds in datasets for ds in dataset.globalInfo.jsonFiles[jsName]]):
            # Some SRs are missing for this json combination
            logger.error( "Wrong json definition in globalInfo.jsonFiles for json : %s" % jsName)
    logger.debug("list of datasets: {}".format(datasets))
    logger.debug("jsonFiles after filtering: {}".format(jsonFiles))
    # Constructing the list of signals with subsignals matching each json
    nsignals = list()
    for jsName in jsonFiles:
        subSig = list()
        for srName in dataset.globalInfo.jsonFiles[jsName]:
            try:
                index = datasets.index(srName)
            except ValueError:
                line = (
                    f"{srName} signal region provided in globalInfo is not in the list of datasets, {jsName}:{','.join(datasets)}"
                )
                raise ValueError(line)
            sig = nsig[index]
            subSig.append(sig)
        nsignals.append(subSig)
    # Loading the jsonFiles, unless we already have them (because we pickled)
    from smodels.tools.pyhfInterface import PyhfData, PyhfUpperLimitComputer

    data = PyhfData(nsignals, jsons, total, jsonFiles)
    if data.errorFlag:
        return None
    if hasattr(dataset.globalInfo, "includeCRs"):
        includeCRs = dataset.globalInfo.includeCRs
    else:
        includeCRs = False
    ulcomputer = PyhfUpperLimitComputer(data, includeCRs=includeCRs,
                                        lumi=dataset.getLumi() )
    # _pyhfcomputers[idt] = ulcomputer
    return ulcomputer


def getCombinedSimplifiedLikelihood(
    dataset, nsig, marginalize=False, deltas_rel=0.2, expected=False, mu=1.0
):
    """
    Computes the combined simplified likelihood to observe nobs events, given a
    predicted signal "nsig", with nsig being a vector with one entry per
    dataset.  nsig has to obey the datasetOrder. Deltas is the error on
    the signal.
    :param nsig: predicted signal (list)
    :param deltas_rel: relative uncertainty in signal (float). Default value is 20%.
    :param expected: compute expected likelihood, not observed
    :param mu: signal strength parameter mu
    :returns: likelihood to observe nobs events (float)
    """
    for k, v in enumerate(nsig):
        nsig[k] = v * mu

    if dataset.type != "simplified":
        logger.error(
            "Asked for combined simplified likelihood, but no covariance given: %s" % dataset.type
        )
        return None
    if len(dataset.origdatasets) == 1:
        if isinstance(nsig, list):
            nsig = nsig[0]
        return dataset.origdatasets[0].likelihood(nsig, marginalize=marginalize)
    bg = [x.dataInfo.expectedBG for x in dataset.origdatasets]
    nobs = [x.dataInfo.observedN for x in dataset.origdatasets]
    cov = dataset.globalInfo.covariance
    computer = LikelihoodComputer(Data(nobs, bg, cov, None, nsig, deltas_rel=deltas_rel))
    computer.transform ( expected )
    return computer.likelihood(1., marginalize=marginalize)

def getCombinedSimplifiedStatistics(
    dataset, nsig, marginalize, deltas_rel, nll=False, expected=False, allowNegativeSignals=False
):
    """compute likelihood at maximum, for simplified likelihoods only"""
    if dataset.type != "simplified":
        return {"lmax": -1.0, "muhat": None, "sigma_mu": None}
    nobs = [x.dataInfo.observedN for x in dataset.origdatasets]
    bg = [x.dataInfo.expectedBG for x in dataset.origdatasets]
    bg = [x.dataInfo.expectedBG for x in dataset.origdatasets]
    cov = dataset.globalInfo.covariance
    if type(nsig) in [list, tuple]:
        nsig = np.array(nsig)
    computer = LikelihoodComputer(Data(nobs, bg, cov, None, nsig, deltas_rel=deltas_rel))
    computer.transform ( expected )
    ret = computer.findMuHat(allowNegativeSignals=allowNegativeSignals, extended_output=True)
    lbsm = computer.likelihood ( 1., marginalize = marginalize )
    lsm = computer.likelihood ( 0., marginalize = marginalize )
    lmax = ret["lmax"]
    if lsm > lmax:
        muhat = ret["muhat"]
        logger.debug(f"lsm={lsm:.2g} > lmax({muhat:.2g})={lmax:.2g}: will correct")
        ret["lmax"] = lsm
        ret["muhat"] = 0.0
    if lbsm > lmax:
        muhat = ret["muhat"]
        logger.debug(f"lbsm={lbsm:.2g} > lmax({muhat:.2g})={lmax:.2g}: will correct")
        ret["lmax"] = lbsm
        ret["muhat"] = 1.0
    ret["lbsm"] = lbsm
    ret["lsm"] = lsm
    return ret
