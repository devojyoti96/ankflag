import sys
import gc
import numpy as np
from astropy.io import fits
import matplotlib.pyplot as plt

# This script is written by Apurba Bera
# Formating done by Devojyoti Kansabanik


def uvfitstobinary(
    data,
    scratchdir,
    ugrids,
    vgrids,
    flagparams,
    savefig=False,
    figname="uvgrid.png",
    showgui=False,
    verbose=False,
):
    """
    Function to convert UVFITS file to binary files and write in scratch direcotory
    """
    ngroups = len(data)
    recids = np.arange(ngroups)
    print("Converting fits to binary...")
    if verbose:
        print(f"Total no of records	= {ngroups}")
    uvwarr = np.transpose(
        np.array(
            [
                data.par(flagparams["Ukey"]),
                data.par(flagparams["Vkey"]),
                data.par(flagparams["Wkey"]),
            ]
        )
    )
    usorted = np.argsort(uvwarr[:, 0])
    uvwarrus = uvwarr[usorted]
    recdataus = data[usorted]
    recidus = recids[usorted]
    del uvwarr, recids, data
    gc.collect()
    uvbins = []
    ustart = 0
    uglen = 1 + int(ngroups / ugrids)
    if savefig:
        fig = plt.figure(figsize=(6, 6))
        ax = fig.add_axes([0.1, 0.1, 0.85, 0.85])
    for ug in range(0, ugrids):
        ustop = ustart + uglen
        if ustop > (ngroups + 1):
            ustop = ngroups + 1
        ugridarr = uvwarrus[ustart:ustop]
        ugsize = len(ugridarr)
        vsorted = np.argsort(ugridarr[:, 1])
        ugarrvs = ugridarr[vsorted]
        urecdata = recdataus[ustart:ustop]
        urecvs = urecdata[vsorted]
        urecid = recidus[ustart:ustop]
        urecidvs = urecid[vsorted]
        vstart = 0
        vglen = 1 + int(ugsize / vgrids)
        for vg in range(0, vgrids):
            vstop = vstart + vglen
            if vstop > (ugsize + 1):
                vstop = ugsize + 1
            vgridarr = ugarrvs[vstart:vstop]
            vgsize = len(vgridarr)
            vrecdata = urecvs[vstart:vstop]
            vrecid = urecidvs[vstart:vstop]
            uvbins.append([ug, vg, vrecdata, vrecid])
            del vrecdata, vrecid
            gc.collect()
            colsel = "b."
            if (ug + vg) % 2:
                colsel = "r."
            if savefig:
                plt.plot(vgridarr[:, 0], vgridarr[:, 1], colsel, markersize=0.5)
            vstart = vstop
        ustart = ustop
    if savefig:
        plt.xlabel("U")
        plt.ylabel("V")
        plt.savefig(figname, dpi=300)
        if showgui:
            plt.show()
        plt.close()
    uvbinstats = []
    for ug in range(0, ugrids):
        for vg in range(0, vgrids):
            datauvg = uvbins[ug * vgrids + vg]
            datarray = datauvg[2].data
            uvbinstats.append([ug, vg, 1, len(datarray), len(datarray[0, 0, 0, 0])])
            bindetails = [
                datauvg[3],
                datauvg[2].par(flagparams["Ukey"]),
                datauvg[2].par(flagparams["Vkey"]),
                datauvg[2].par(flagparams["Wkey"]),
                datauvg[2].par("BASELINE"),
            ]
            bindetails = np.array(bindetails)
            bindetails = np.transpose(bindetails)
            np.savetxt(
                scratchdir + "uvbindetails_%d_%d_0.txt" % (ug, vg),
                bindetails,
                fmt="%d	%e	%e	%e	%d",
            )
            fname = open(scratchdir + "uvbin_%d_%d_0.array" % (ug, vg), "wb")
            for p in range(0, flagparams["Npols"]):
                for d in range(0, 3):
                    fname.write(
                        datarray[:, 0, 0, 0, :, p, d].astype("float32").tobytes()
                    )
            fname.close()
    uvbinstats = np.array(uvbinstats)
    np.savetxt(scratchdir + "uvbin_status.txt", uvbinstats, fmt="%4d	%4d	%4d	%4d	%4d")
    del uvbins, datauvg, datarray
    gc.collect()
    return


def uvfitsfrombinary(data, scratchdir, ugrids, vgrids, flagparams):
    """
    Function to convert binary files from the scratch directory to UVFITS file
    """
    print("Converting binary to uvfits...")
    for ug in range(0, ugrids):
        for vg in range(0, vgrids):
            bindetails = np.loadtxt(scratchdir + "uvbindetails_%d_%d_0.txt" % (ug, vg))
            recids = bindetails[:, 0].astype("int32")
            baselines = bindetails[:, 4]
            temparr = np.fromfile(
                scratchdir + "uvbin_%d_%d_0_f.array" % (ug, vg),
                dtype="float32",
                count=-1,
                sep="",
            )

            if (
                (len(temparr) % len(recids))
                or (len(temparr) % flagparams["Npols"])
                or (len(temparr) % 3)
            ):
                print("Length Mismatch !!!!!!! ....... exiting...")
                return 1
            nchan = int(len(temparr) / (flagparams["Npols"] * 3 * len(recids)))
            temparr = np.reshape(temparr, (flagparams["Npols"], 3, len(recids), nchan))
            for p in range(0, flagparams["Npols"]):
                for d in range(0, 3):
                    for l in range(0, len(recids)):
                        np.copyto(
                            data.data[recids[l], 0, 0, 0, :, p, d], temparr[p, d, l]
                        )
    return 0


def baselinestobinary(ANTS, data, scratchdir, breaktimesec, flagparams, verbose=False):
    """
    Function to convert baselines to binary files and write in scratch direcotory
    """
    blid = []
    for a in range(1, ANTS):
        for b in range(a + 1, ANTS + 1):
            blid.append([a, b, 256 * a + b])
    blid = np.array(blid)
    nbase = len(blid)
    nvis = len(data)
    if verbose:
        print(f"Writing Total baselines = {nbase}, Visibilities = {nvis}")
    datepars = []
    for ipar in range(0, len(data.parnames)):
        if data.parnames[ipar] == "DATE":
            datepars.append(ipar)

    if len(datepars) > 2:
        print("More than two DATE parameters !!! EXITING ...")
        return 1
    mjdates = data.par(datepars[1]) + data.par(datepars[0])
    breaks = []
    scanlens = []
    prebrk = -1
    for dt in range(0, len(mjdates) - 2):
        if (mjdates[dt + 1] - mjdates[dt]) * 86400.0 > breaktimesec:
            breaks.append(dt)
            scanlens.append(dt - prebrk)
            prebrk = dt
    breaks.append(len(mjdates) - 1)
    scanlens.append(len(mjdates) - 1 - prebrk)
    breaks = np.array(breaks)
    scanlens = np.array(scanlens)
    totscans = len(breaks)
    if verbose:
        print(f"Found total {totscans} scans")
    scandetails = np.transpose(np.concatenate((np.array([totscans]), breaks), axis=0))
    np.savetxt(scratchdir + "scandetails.txt", scandetails, fmt="%ld")
    blstatus = []
    scstart = 0
    scend = 0
    for scan in range(0, totscans):
        scend = breaks[scan] + 1
        if verbose:
            print(
                "Scan %d / %d		Visibilities	%ld - %ld"
                % (scan, totscans, scstart, scend)
            )
        scdata = data[scstart:scend]
        if verbose:
            print("Total visibilities	= %ld" % len(scdata))
        for bline in range(0, nbase):
            bl = blid[bline]
            bindx = np.where(scdata.par("BASELINE") == bl[2])[0]
            bdata = scdata[bindx]
            if len(bdata) == 0:
                blstatus.append([bl[0], bl[1], 0, 0, 0, scan])
                continue
            bindetails = [
                bindx,
                bdata.par(flagparams["Ukey"]),
                bdata.par(flagparams["Vkey"]),
                bdata.par(flagparams["Wkey"]),
                bdata.par("BASELINE"),
                scan * np.ones(bindx.shape, dtype=int),
            ]
            bindetails = np.array(bindetails)
            bindetails = np.transpose(bindetails)
            np.savetxt(
                scratchdir + "baselinedetails_%d_%d_%d.txt" % (bl[0], bl[1], scan),
                bindetails,
                fmt="%d	%e	%e	%e	%d	%d",
            )
            bldata = bdata.data
            blstatus.append(
                [bl[0], bl[1], 1, len(bldata), len(bldata[0, 0, 0, 0]), scan]
            )
            fname = open(
                scratchdir + "baseline_%d_%d_%d.array" % (bl[0], bl[1], scan), "wb"
            )
            for p in range(0, flagparams["Npols"]):
                tfdata = bldata[:, 0, 0, 0, :, p, :]  # 	Time frequency data
                lent = len(tfdata)
                for d in range(0, 3):
                    for r in range(0, lent):
                        fname.write(tfdata[r, :, d].astype("float32").tobytes())
            fname.close()
        scstart = scend
    blstatus = np.array(blstatus)
    np.savetxt(
        scratchdir + "baseline_status.txt", blstatus, fmt="%4d	%4d	%4d	%4d	%4d	%4d"
    )
    return 0


def baselinesfrombinary(ANTS, data, scratchdir, flagparams, verbose=False):
    """
    Function to convert baselines from binary files in scratch direcotory to UVFITS
    """
    blid = []
    for a in range(1, ANTS):
        for b in range(a + 1, ANTS + 1):
            blid.append([a, b, 256 * a + b])
    blid = np.array(blid)
    nbase = len(blid)
    nvis = len(data)

    scanbreaks = np.loadtxt(scratchdir + "scandetails.txt", dtype=int, ndmin=1)

    nscan = scanbreaks[0]
    scanbreaks = scanbreaks[1:]

    blstatus = np.loadtxt(scratchdir + "baseline_status.txt", dtype=int)
    baselineflag = np.loadtxt(scratchdir + "badbase.list", dtype=int)
    if verbose:
        print("Reading Total baselines = %d	Scans = %d" % (nbase, nscan))
    scanstart = 0
    for scan in range(0, nscan):
        if scan > 0:
            scanstart = scanbreaks[scan - 1] + 1
        if scan < (nscan - 1):
            scanend = scanbreaks[scan] + 1
        else:
            scanend = nvis + 1
        scdata = data[scanstart:scanend]
        for bline in range(0, nbase):
            bl = blid[bline]
            if blstatus[scan * nbase + bline, 2] == 0:
                continue

            bindetails = np.loadtxt(
                scratchdir + "baselinedetails_%d_%d_%d.txt" % (bl[0], bl[1], scan)
            )
            if len(bindetails.shape) == 1:
                bindetails = np.array([bindetails])
            if len(bindetails.shape) < 1:
                if verbose:
                    print(
                        "Blanck details for baseline	%d %d	scan %d ... CONTINUING !!!"
                        % (bl[0], bl[1], scan)
                    )
                continue
            recids = bindetails[:, 0].astype("int32")
            baselines = bindetails[:, 4]
            temparr = np.fromfile(
                scratchdir + "baseline_%d_%d_%d_f.array" % (bl[0], bl[1], scan),
                dtype="float32",
                count=-1,
                sep="",
            )
            if (
                (len(temparr) % len(recids))
                or (len(temparr) % flagparams["Npols"])
                or (len(temparr) % 3)
            ):
                print("Length Mismatch !!!!!!! ....... exiting...")
                return 1
            nchan = int(len(temparr) / (flagparams["Npols"] * 3 * len(recids)))
            temparr = np.reshape(temparr, (flagparams["Npols"], 3, len(recids), nchan))
            temp00 = np.zeros(np.shape(temparr), dtype="float32")
            for p in range(0, flagparams["Npols"]):
                for d in range(2, 3):
                    if baselineflag[scan * nbase + bline, 3] or baselineflag[scan * nbase + bline, 4]:
                        for l in range(0, len(recids)):
                            np.copyto(
                                scdata.data[recids[l], 0, 0, 0, :, p, d],
                                temparr[p, d, l],
                            )
                    else:
                        for l in range(0, len(recids)):
                            np.copyto(
                                scdata.data[recids[l], 0, 0, 0, :, p, d],
                                temp00[p, d, l],
                            )
            del temp00
            del temparr
    return 0


def flagautocorr(ANTS, data):
    """
    Function to flag auto-correlations if present
    """
    blid = []
    for a in range(1, ANTS + 1):
        blid.append([a, a, 256 * a + a])
    blid = np.array(blid)
    nbase = len(blid)
    nvis = len(data)
    print("Flagging %d auto-correlations..." % nbase)
    for bline in range(0, len(data.par("BASELINE"))):
        if np.isin(data.par("BASELINE")[bline], blid):
            data[bline].data[:, :, :, :, :, 2] = 0
    print ("Auto-correlation flagging is done.")
    return nbase


def flagchanlist(data, hopelesschans):
    """
    Function to flag a list of channels in all baselines
    """
    nhopeless = len(hopelesschans)
    if nhopeless > 0:
        print("Flagging %d hopeless channels" % nhopeless)
        nchan = data.data.shape[4]
        for hc in hopelesschans:
            if hc < nchan:
                data.data[:, :, :, :, hc, :, :] = 0
    else:
        print("No bad channels to flag")
    return nhopeless


def returnbadbaselines(bl, data):
    """
    Function to find out completely flagged baselines
    """
    baseflagged = 1
    bdata = data[data.par("BASELINE") == bl[2]]
    if len(bdata) == 0:
        baseflagged = 1
        return baseflagged
    bldata = bdata.data
    for p in range(0, npols):
        tfdata = bldata[:, 0, 0, 0, :, p, :]  # 	Time frequency data
        tfw = tfdata[:, :, 2]  # 	Weight
        if len(tfw[tfw > 0.0]) > 0:
            baseflagged = 0
    return baseflagged
