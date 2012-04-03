#!/usr/bin/env python

import ROOT
from rootpy import routines
from rootpy.plotting import Canvas, Hist
from rootpy.io import openFile
routines.ROOTlogon()


f = openFile("/global/endw/higgs/data/data.root")
t = f.Get("data")
c = Canvas()
c.cd()
mass = Hist(100,20,200)
MMC_mass = Hist(100,20,400)

from numpy import logspace
cuts = list(reversed(1 - (logspace(0,1.05,150) - 1)/10))[2:]
cuts.insert(0,0.)


for i, BDTcut in enumerate(cuts):
    
    print "frame %i"% i
    cut = "(tau1_charge * tau2_charge == -1 ) && tau1_BDTJetScore>%f && tau2_BDTJetScore>%f" % (BDTcut, BDTcut)

    """
    c.Clear()
    mass.Reset()
    t.Draw("Mvis_tau1_tau2/1000", cut, hist=mass)
    mass.SetXTitle("M_{vis}(#tau_{1},#tau_{2}) [GeV]")
    mass.SetYTitle("Events")
    mass.Draw()
    label = routines.makeLabel(0.7,0.8,"BDT > %.2f"% BDTcut, size=25)
    label.Draw()
    c.SaveAs("mass/mass_%04d.eps"% i)
    """

    c.Clear()
    MMC_mass.Reset()
    t.Draw("MMC_mass", cut, hist=MMC_mass)
    MMC_mass.SetXTitle("M(#tau_{1},#tau_{2}) [GeV]")
    MMC_mass.SetYTitle("Events")
    MMC_mass.Draw()
    label = routines.makeLabel(0.7,0.8,"BDT > %.2f"% BDTcut, size=25)
    label.Draw()
    c.SaveAs("mass/MMC_mass_%04d.eps"% i)

    """
    c.Clear()
    tracks.Reset()
    t.Draw("tau1_numTrack", cut, hist=tracks)
    tracks.SetXTitle("Number of Tracks")
    tracks.SetYTitle("#tau Candidates")
    tracks.Draw()
    label = routines.makeLabel(0.7,0.8,"BDT > %.2f"% BDTcut, size=25)
    label.Draw()
    c.SaveAs("tracks_%04d.png"% i)
    """

"""
h = Hist(50,80,300)
t.Draw("Mvis_tau1_tau2/1000", cut, hist=h)
h.SetXTitle("M_{vis}(#tau_{1},#tau_{2}) [GeV]")
h.Draw()
c.SaveAs("massroi.png")

from rootpy import root2matplotlib as r2m
from matplotlib import pyplot as plt

plt.figure()
r2m.errorbar(h)
plt.savefig("massplot.png")
"""