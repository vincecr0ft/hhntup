from rootpy.tree.filtering import EventFilter

from math import *
import math

from .. import utils
from ..units import GeV
from .. import datasets
from . import track_counting
from .. import tauid
from ..tauid import IDLOOSE, IDMEDIUM, IDTIGHT
from . import log; log = log[__name__]

class TauVeto(EventFilter):
    """
    taken from 
    https://svnweb.cern.ch/trac/atlasphys/browser/Physics/Higgs/HSG4/software/leplep/MVA_8TeV/Preselection/trunk/Common/analysis.C 
    lines 2564-2646
    """
    def __init__(self, year, **kwargs):
        self.year=year
        super(TauVeto, self).__init__(**kwargs)

    def passes(self,event):
        for tau in event.taus:
            if tau.author not in (1,3):
                continue
            if not tau.JetBDTSigMedium:
                continue
            if not (abs(tau.eta<2.47) and tau.numTrack>0 and abs(tau.track_eta[0])<2.47):
                continue
            if tau.Et>20*GeV:
                continue
            if tau.numTrack not in (1,3):
                continue
            if abs(tau.charge-1.) > 1e-3:
                continue
            if not (tau.numTrack==1 and tau.EleBDTMedium) or tau.numTrack>1:
                continue
            if tau.muonVeto:
                continue
            return False
        return True
    #need to implement Overlap? 2583

class Triggers(EventFilter):
    """
    See lowest unprescaled triggers here:
    https://twiki.cern.ch/twiki/bin/viewauth/Atlas/LowestUnprescaled#Taus_electron_muon_MET
    """
    def __init__(self, year, tree, datatype, passthrough=False, **kwargs):
        if (not passthrough) and datatype == datasets.EMBED:
            raise ValueError("Cannot apply trigger on embedding samples")
        if year == 2011:
            if datatype == datasets.MC:
                self.passes = self.passes_11_mc
            else:
                self.passes = self.passes_11_data
        elif year == 2012:
            if datatype == datasets.MC:
                self.passes = self.passes_12_mc
            else:
                self.passes = self.passes_12_data
        else:
            raise ValueError("No triggers defined for year %d" % year)
        self.tree = tree
        super(Triggers, self).__init__(passthrough=passthrough, **kwargs)

    def passes_11_mc(self, event):
        try:
            if 177986 <= self.tree.RunNumber <= 187815: # Periods B-K
                self.tree.trigger = event.EF_tau29_medium1_tau20_medium1 == 1
                return True
            elif 188902 <= self.tree.RunNumber <= 191933: # Periods L-M
                self.tree.trigger = event.EF_tau29T_medium1_tau20T_medium1 == 1
                return True
        except AttributeError, e:
            print "Missing trigger for run %i: %s" % (self.tree.RunNumber, e)
            raise e
        raise ValueError("No trigger condition defined for run %s" %
                         self.tree.RunNumber)

    def passes_11_data(self, event):
        try:
            if 177986 <= self.tree.RunNumber <= 187815: # Periods B-K
                return event.EF_tau29_medium1_tau20_medium1
            elif 188902 <= self.tree.RunNumber <= 191933: # Periods L-M
                return event.EF_tau29T_medium1_tau20T_medium1
        except AttributeError, e:
            print "Missing trigger for run %i: %s" % (self.tree.RunNumber, e)
            raise e
        raise ValueError("No trigger condition defined for run %s" %
                         self.tree.RunNumber)

    def passes_12_mc(self, event):
        try:
            self.tree.trigger = event.EF_tau29Ti_medium1_tau20Ti_medium1 == 1
            return True
        except AttributeError, e:
            print "Missing trigger for run %i: %s" % (self.tree.RunNumber, e)
            raise e
        # TODO use tau27Ti_m1_tau18Ti_m1_L2loose for period E
        # need emulaion, SFs for this

    def passes_12_data(self, event):
        try:
            return event.EF_tau29Ti_medium1_tau20Ti_medium1
        except AttributeError, e:
            print "Missing trigger for run %i: %s" % (self.tree.RunNumber, e)
            raise e
        # TODO use tau27Ti_m1_tau18Ti_m1_L2loose for period E
        # need emulaion, SFs for this


class TauFakeRateScaleFactors(EventFilter):

    def __init__(self, year, datatype, tree,
                 tes_up=False, tes_down=False,
                 passthrough=False, **kwargs):
        self.tes_up = tes_up
        self.tes_down = tes_down
        log.info("TauFakeRateScaleFactors: TES UP {0}".format(tes_up))
        log.info("TauFakeRateScaleFactors: TES DOWN {0}".format(tes_down))
        if not passthrough:
            self.year = year % 1000
            self.datatype = datatype
            self.tree = tree
            if self.year == 11:
                from externaltools.bundle_2011 import TauFakeRates
                from ROOT import TauFakeRates as TFR
                fakerate_table = TauFakeRates.get_resource(
                        'FakeRateScaleFactor.txt')
                self.fakerate_tool = TFR.FakeRateScaler(fakerate_table)
                self.passes = self.passes_2011
                log.info("will apply 2011 fake rate scale factors")
            elif self.year == 12:
                from externaltools.bundle_2012 import TauFakeRates
                from ROOT import TauFakeRates as TFR
                self.fakerate_tool = TFR.FakeRateScaler()
                self.fakerate_tool.initialise(TauFakeRates.RESOURCE_PATH)
                self.fakerate_ns = TFR
                self.passes = self.passes_2012
                log.info("will apply 2012 fake rate scale factors")
            else:
                raise ValueError("No fakerates defined for year %d" % year)
        super(TauFakeRateScaleFactors, self).__init__(
            passthrough=passthrough, **kwargs)

    def get_id_2011(self, tau):
        # 2011 fake rates are inclusive
        if tau.id == IDLOOSE:
            return 'Loose'
        elif tau.id == IDMEDIUM:
            return 'Medium'
        elif tau.id == IDTIGHT:
            return 'Tight'
        raise ValueError("tau is not loose, medium, or tight")

    def get_id_2012(self, tau):
        # 2012 fake rates are exclusive
        if tau.JetBDTSigTight:
            return self.fakerate_ns.TIGHT
        elif tau.JetBDTSigMedium:
            return self.fakerate_ns.MEDIUM
        elif tau.JetBDTSigLoose:
            return self.fakerate_ns.LOOSE
        raise ValueError("tau is not loose, medium, or tight")

    def passes_2011(self, event):
        assert len(event.taus) == 2
        assert event.taus[0].pt >= event.taus[1].pt

        if self.tree.RunNumber >= 188902:
            trig = "EF_tau%dT_medium1"
        else:
            trig = "EF_tau%d_medium1"

        for tau, thresh in zip(event.taus, (29, 20)):

            # fakerate only applies to taus that don't match truth
            if tau.matched:
                continue

            wpflag = self.get_id_2011(tau)

            sf = self.fakerate_tool.getScaleFactor(
                tau.pt, wpflag,
                trig % thresh)
            tau.fakerate_sf = sf
            tau.fakerate_sf_high = (sf +
                self.fakerate_tool.getScaleFactorUncertainty(
                    tau.pt, wpflag,
                    trig % thresh, True))
            tau.fakerate_sf_low = (sf -
                self.fakerate_tool.getScaleFactorUncertainty(
                    tau.pt, wpflag,
                    trig % thresh, False))
        return True

    def passes_2012(self, event):
        assert len(event.taus) == 2
        assert event.taus[0].pt >= event.taus[1].pt

        for tau, trigger in zip(event.taus, [self.fakerate_ns.TAU29Ti, self.fakerate_ns.TAU20Ti]):
            # fakerate only applies to taus that don't match truth
            if tau.matched:
                continue
            # Get the reco SF
            sf_reco = self.fakerate_tool.getRecoSF(
                tau.pt, tau.numTrack, self.tree.RunNumber)
            tau.fakerate_sf_reco = sf_reco
            # NOTE: no uncertainty on this SF?
            # KG: yes there are, but getRecoSF didn't get updated to access them.
            # It's small so we will ignore it
            tau.fakerate_sf_reco_high = sf_reco
            tau.fakerate_sf_reco_low = sf_reco

            wpflag = self.get_id_2012(tau)

            tes_up = self.tes_up
            tes_down = self.tes_down

            # using LOOSE lepton veto
            sf_numer = self.fakerate_tool.getEffData(
                tau.pt, tau.numTrack, self.tree.RunNumber,
                wpflag, self.fakerate_ns.LOOSE, trigger)

            sf_numer_up = self.fakerate_tool.getEffDataUncertainty(
                tau.pt, tau.numTrack, self.tree.RunNumber,
                wpflag, self.fakerate_ns.LOOSE, trigger, True)

            sf_numer_dn = self.fakerate_tool.getEffDataUncertainty(
                tau.pt, tau.numTrack, self.tree.RunNumber,
                wpflag, self.fakerate_ns.LOOSE, trigger, False)

            if self.datatype == datasets.MC:
                sf_denom = self.fakerate_tool.getEffMC(
                    tau.pt, tau.numTrack, self.tree.RunNumber,
                    wpflag, self.fakerate_ns.LOOSE, trigger, tes_down, tes_up)

                sf_denom_up = self.fakerate_tool.getEffMCUncertainty(
                    tau.pt, tau.numTrack, self.tree.RunNumber,
                    wpflag, self.fakerate_ns.LOOSE, trigger, True, tes_down, tes_up)

                sf_denom_dn = self.fakerate_tool.getEffMCUncertainty(
                    tau.pt, tau.numTrack, self.tree.RunNumber,
                    wpflag, self.fakerate_ns.LOOSE, trigger, False, tes_down, tes_up)

            else: # embedding: no trigger in denominator
                sf_denom = self.fakerate_tool.getEffData(
                    tau.pt, tau.numTrack, self.tree.RunNumber,
                    wpflag, self.fakerate_ns.LOOSE,
                    self.fakerate_ns.TRIGGERNONE)

                sf_denom_up = self.fakerate_tool.getEffDataUncertainty(
                    tau.pt, tau.numTrack, self.tree.RunNumber,
                    wpflag, self.fakerate_ns.LOOSE,
                    self.fakerate_ns.TRIGGERNONE, True)

                sf_denom_dn = self.fakerate_tool.getEffDataUncertainty(
                    tau.pt, tau.numTrack, self.tree.RunNumber,
                    wpflag, self.fakerate_ns.LOOSE,
                    self.fakerate_ns.TRIGGERNONE, False)

            #log.info("data eff: %f, mc eff %f, wp %s, pt %f, ntrack %d, run: %d, trigger: %d" % (
            #    sf_data, sf_mc, wp, tau.pt, tau.numTrack, self.tree.RunNumber,
            #    tau.trigger_match_thresh))

            if sf_numer == 0 or sf_denom == 0:
                log.warning("fake rate bug: efficiency == 0, using sf of 0")
                sf = 0.
                sf_high = 0.
                sf_low = 0.

            else:
                sf = sf_numer / sf_denom

                sf_up = sf * math.sqrt(
                    (sf_denom_up / sf_denom)**2 +
                    (sf_numer_up / sf_numer)**2)

                sf_dn = sf * math.sqrt(
                    (sf_denom_dn / sf_denom)**2 +
                    (sf_numer_dn / sf_numer)**2)

                sf_high = sf + sf_up
                sf_low = sf - sf_dn

            if sf_low < 0:
                sf_low = 0.

            tau.fakerate_sf = sf
            # uncertainty
            tau.fakerate_sf_high = sf_high
            tau.fakerate_sf_low = sf_low
            #log.info("sf: %f, high: %f, low: %f" % (sf, sf_high, sf_low))
        return True
