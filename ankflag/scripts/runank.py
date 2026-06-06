import os, sys
import numpy as np
import time as tm
import argparse as ap
import ankflag.data as ad
from pyfiglet import Figlet
from ankflag.utils.convertfits import *
from ankflag.utils.inputs import *
from ankflag.utils.plottingfns import *
from ankflag.utils.ankdata import init_ankflag_data
from ankflag.utils.udocker_utils import initialize_ankflag_container, run_ankflag

# This script is written by Apurba bera
# Formatted and udocker contanierisation is done by Devojyoti Kansabanik

def cli():
    parser = ap.ArgumentParser(
        description="aNKflag command line interface"
    )
    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )
    # =====================
    # init command
    # =====================
    init_parser = subparsers.add_parser(
        "init",
        help="Initialize aNKflag configuration"
    )
    init_parser.add_argument(
        "--datadir",
        help="Directory to save aNKflag container",
        type=str,
        default="",
    )

    # =====================
    # run command
    # =====================
    run_parser = subparsers.add_parser(
        "run",
        help="Run aNKflag"
    )

    # Essential parameters
    basic_args = run_parser.add_argument_group(
        "###################\nEssential parameters\n###################"
    )
    basic_args.add_argument(
        "infilename",
        help="Input FITS file",
        type=str,
    )
    basic_args.add_argument(
        "outfilename",
        help="Output FITS file",
        type=str,
    )
    basic_args.add_argument(
        "--scratchdir",
        help="Scratch directory",
        type=str,
        default=None,
    )
    basic_args.add_argument(
        "--npol",
        help="Number of polarisation",
        type=int,
        default=2,
    )
    basic_args.add_argument(
        "--nant",
        help="Number of antennas",
        type=int,
        default=30,
    )

    # Flagging control parameters
    flag_args = run_parser.add_argument_group(
        "###################\nFlagging control parameters\n###################"
    )
    flag_args.add_argument(
        "--flagmode",
        help="Mode of flagging (baseline, uvbin)",
        type=str,
        default=None,
    )
    flag_args.add_argument(
        "--target_type",
        help="Target source type (calch0, calbp, normal, uvsub)",
        type=str,
        default=None,
    )
    flag_args.add_argument(
        "--rfifreqfile",
        help="File with RFI frequencies",
        type=str,
        default=None,
    )
    flag_args.add_argument(
        "--flagautocorr",
        help="Flag autocorrelations",
        action="store_true",
    )
    

    # Advanced parameters
    adv_args = run_parser.add_argument_group(
        "###################\nAdvanced control parameters\n###################"
    )
    adv_args.add_argument(
        "--parfile",
        help="Custom YAML file with aNKflag specific input params",
        type=str,
        default=None,
    )
    adv_args.add_argument(
        "--verbose",
        help="Verbose output",
        action="store_true",
    )
    adv_args.add_argument(
        "--logfile",
        help="Name of logfile",
        type=str,
        default="logfile.txt",
    )
    adv_args.add_argument(
        "--nthreads",
        help="Number of threads",
        type=int,
        default=1,
    )
    adv_args.add_argument(
        "--clearscratch",
        help="Clear scratch directory?",
        action="store_true",
    )

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        return 1
        
    args = parser.parse_args()
    f = Figlet(font="big")
    print(f.renderText("aNKflag"))
    
    if args.command == "init":
        print("Running initialization of aNKflag...")
        init_ankflag_data(datadir=args.datadir,update=False)
        initialize_ankflag_container(name="ankflag", update=True)
        return 0
    elif args.command == "run":
        print(f"Running aNKflag on: {args.infilename}")
        # 	--------------------------------------
        #   Read and verify input parameters
        # 	--------------------------------------
        if args.parfile == None:
            datadir = os.path.dirname(ad.__file__)
            parfile = f"{datadir}/ank.yml"
            print(f"Using default input YAML file: {parfile}")
        else:
            parfile = args.parfile
            print(f"Using custom input YAML file: {parfile}")
        flagparams = getparsyaml(parfile, showparams=False)

        if args.scratchdir == None:
            scratchdir = f"{os.getcwd()}/ankscratch/"
        else:
            scratchdir = f"{args.scratchdir.rstrip('/')}/"
        os.makedirs(scratchdir, exist_ok=True)
        if args.clearscratch:
            print("Clearing scratch directory....")
            os.system(f"rm -rf {scratchdir}/*")

        if os.path.exists(args.infilename):
            infilefits = args.infilename
        else:
            print("Provide a real file")
            return 1

        if args.outfilename == None:
            print("Provide a filename")
            return 1
        else:
            outfilefits = args.outfilename

        if not (args.flagmode == "uvbin" or args.flagmode == "baseline"):
            print("Provide from these two flagging mode: uvbin or baseline")
        else:
            print(f"Flagging in {args.flagmode} mode.")

        if args.npol!=2 and args.npol!=4:
            print(f"Number of polarisations should be either 2 or 4, not {args.npol}.")
            return 1
            
        if args.target_type in tartypes:
            print("Target type: ", args.target_type)
            partype = partypes[tartypes.index(args.target_type)]
            if partype in flagparams:
                print("Using parameters: ", partype)
                flagparams["Npols"]=args.npol
                flagparams["N_ants"]=args.nant
                if args.verbose:
                    print("Flagging commands: ")
                    print(*flagparams[partype], sep="\n")
            else:
                print(partype, "is not provided...")
                return 1
        else:
            print("Only supported target types are ", *tartypes, sep=" ")
            return 1

        if (args.target_type == "calch0") or (args.target_type == "calbp"):
            uugrids = flagparams["UgridCal"]
            vvgrids = flagparams["VgridCal"]
        else:
            uugrids = flagparams["UgridTar"]
            vvgrids = flagparams["VgridTar"]

        #   ------------------------------------------
        # 	Convert parameters to aNKflag secret codes
        #   ------------------------------------------
        covertparams(
            flagparams,
            partype,
            scratchdir + "/flagpars.pars",
            args,
            uugrids=uugrids,
            vvgrids=vvgrids,
        )

        # 	------------------------------------------------
        # 	Convert FITS to aNKflag compatible binary files
        # 	------------------------------------------------

        start0 = tm.time()

        if args.flagautocorr:
            # 	Preflag autocorrelations
            infile = fits.open(infilefits)
            data = infile[0].data
            nauto = flagautocorr(flagparams["N_ants"], data)
            infile.writeto(
                scratchdir + "/scratchfits.fits", output_verify="warn", overwrite=True
            )
            infile.close()

        if ConvertFITS:
            if args.flagautocorr:
                infile = fits.open(scratchdir + "/scratchfits.fits")
            else:
                infile = fits.open(infilefits)
            data = infile[0].data

            if (args.rfifreqfile != None) and os.path.exists(args.rfifreqfile):
                # 	-----------	Flagging hopeless channels	---------------------------
                print("Identifying bad channels from ", args.rfifreqfile)
            else:
                print("No bad channel list found... continuing...")

            if args.flagmode == "uvbin":
                uvfitstobinary(
                    data,
                    scratchdir,
                    uugrids,
                    vvgrids,
                    flagparams,
                    verbose=args.verbose,
                )

            elif args.flagmode == "baseline":
                baselinestobinary(
                    flagparams["N_ants"],
                    data,
                    scratchdir,
                    flagparams["ScanBrkSec"],
                    flagparams,
                    verbose=args.verbose,
                )
            else:
                print("Unknown flagging mode !!! ........")

            infile.close()
            print("Convertion done in %d seconds" % (tm.time() - start0))

        # 	----------------------------
        # 	Actual flagging is done here
        # 	----------------------------

        start1 = tm.time()

        if DoFlag:
            status = run_ankflag(
                scratchdir,
                args.logfile,
                args.npol,
                container_name="ankflag",
                check_container=False,
                verbose=args.verbose,
            )
            print("Flagging done in %d seconds" % (tm.time() - start1))

        # 	---------------------------------
        # 	Convert back binary files to FITS
        # 	---------------------------------
        if ReadBack:
            if args.flagautocorr:
                infile2 = fits.open(scratchdir + "/scratchfits.fits")
            else:
                infile2 = fits.open(infilefits)
            data2 = infile2[0].data

            if args.flagmode == "uvbin":
                bintofits = uvfitsfrombinary(
                    data2, scratchdir, uugrids, vvgrids, flagparams
                )

            elif args.flagmode == "baseline":
                baselinesfrombinary(
                    flagparams["N_ants"], data2, scratchdir, flagparams, verbose=args.verbose,
                )

            # 	Write the output FITS --------------
            if WriteOut:
                print("Writing output FITS...")
                infile2.writeto(outfilefits, output_verify="warn", overwrite=True)

            infile2.close()
            print("Everything done in %d seconds" % (tm.time() - start0))

        if args.clearscratch:
            print("Clearing scratch directory....")
            os.system(f"rm -rf {scratchdir}/*")
        return 0
        
