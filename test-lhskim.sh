#!/bin/bash

grid-batch --dataset data_muhad --metadata datasets.cfg --student LHSkim /global/mtm/data/D3PD/DATA/Muon_test
grid-batch --dataset data_ehad --metadata datasets.cfg --student LHSkim /global/mtm/data/D3PD/DATA/Electron_test
grid-batch --dataset Ztautau_lephad --metadata datasets.cfg --student LHSkim /global/mtm/data/D3PD/MC/testSkim
