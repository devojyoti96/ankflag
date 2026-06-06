import numpy as np
import yaml as ym
import argparse as ap

# 	Control parameters for debugging only

ConvertFITS = True  # 	Convert FITS to binary ?
DoFlag = True  # 	Do flagging ?
ReadBack = True  # 	Read back baselines ?
WriteOut = True  # 	Write output ?

# 	List of optiopns used for internal processes

exmode = ["baseline", "uvbin"]
flagwhat = ["vis_ind", "chan_ind", "rec_ind", "vis_block", "chan_block", "rec_block"]
flagon = ["mean", "rms", "mean_rms"]
statused = ["median", "mean"]
datype = ["re", "im", "am", "ph"]
blkorder = ["ascending", "", "descending"]
tartypes = ["calch0", "calbp", "normal", "uvsub"]
partypes = ["FlgCalCh0", "FlgCalBp", "FlgNorm", "FlgUvsub"]


class SmartDefaultsHelpFormatter(ap.ArgumentDefaultsHelpFormatter):
    def _get_help_string(self, action):
        # Don't show default for boolean flags
        if isinstance(action, ap._StoreTrueAction) or isinstance(
            action, ap._StoreFalseAction
        ):
            return action.help
        return super()._get_help_string(action)
        
        
def getparsyaml(infile, showparams=False):
    """
    Read parameters from the input YAML file
    """
    with open(infile, "r") as infl:
        flagparams = ym.load(infl, Loader=ym.SafeLoader)
        if showparams:
            print("Inputs provided -- ")
            print(ym.dump(flagparams, sort_keys=False))
    return flagparams


def covertparams(flagparams, partype, flagparfile, argus, uugrids, vvgrids):
    """
    Convert parameters to aNKflag secret codes
    Write encoded parameters in flagparfile
    """
    print("Total flagging rounds = %d" % len(flagparams[partype]))
    flagparfile = open(flagparfile, "w")
    flagparfile.write(
        "%d	%d	%d	%d	%d	"
        % (
            flagparams["N_ants"],
            exmode.index(argus.flagmode),
            uugrids,
            flagon.index(flagparams["ScanFlMean"][0]) + 1,
            vvgrids,
        )
    )
    flagparfile.write(
        "%f	%f	%d	%d	%d	%f	%f\n"
        % (
            float(flagparams["ScanFlMean"][1]),
            float(flagparams["ScanFlMean"][2]),
            len(flagparams[partype]),
            argus.nthreads,
            WriteOut,
            float(flagparams["BlockPow"]),
            float(flagparams["ScanFlMean"][3]),
        )
    )
    for flpar in flagparams[partype]:
        flagparfile.write(
            "%d	%d	%d	%d	%d	"
            % (
                flagwhat.index(flpar["what"]),
                flagon.index(flpar["flagon"]) + 1,
                statused.index(flpar["stat"]),
                datype.index(flpar["data"]),
                -(blkorder.index("ascending") - 1),
            )
        )
        fitorder = int(flpar["fitorder"]) if ("fitorder" in flpar) else 0
        minfrac = float(flpar["minfrac"]) if ("minfrac" in flpar) else 0.1
        chan_block = int(flpar["chan_block"]) if ("chan_block" in flpar) else 1
        rec_block = int(flpar["rec_block"]) if ("rec_block" in flpar) else 1
        chan_max_frac = (
            float(flpar["chan_max_frac"]) if ("chan_max_frac" in flpar) else 0.1
        )
        rec_max_frac = (
            float(flpar["rec_max_frac"]) if ("rec_max_frac" in flpar) else 0.1
        )
        flagparfile.write(
            "%f	%f	%d	%d	%d	%f	%f\n"
            % (
                float(flpar["tol"]),
                minfrac,
                fitorder + 1,
                chan_block,
                rec_block,
                chan_max_frac,
                rec_max_frac,
            )
        )
    flagparfile.close()
    return 0
