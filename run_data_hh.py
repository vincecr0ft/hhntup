#!/usr/bin/env python

import os
import cluster

from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument('--year', type=int, choices=(11, 12), default=11)
parser.add_argument('--nproc', type=int, default=3)
parser.add_argument('--nsplit', type=int, default=30)
parser.add_argument('--queue', default='short')
parser.add_argument('--nice', type=int, default=10)
parser.add_argument('--dry', action='store_true', default=False)
parser.add_argument('--output-path', default='ntuples/hadhad_running')
parser.add_argument('splits', nargs='*', type=int)
args = parser.parse_args()

setup = cluster.get_setup('setup.noel.sfu.txt')

output_path = os.path.join(args.output_path, 'HHProcessor')

CWD = os.getcwd()
CMD = ("%s && ./run --output-path %s "
       "-s HHProcessor.py -n %d --db datasets_hh "
       "--nice %d --split %d:%%d data%d-JetTauEtmiss") % (
               setup, output_path, args.nproc,
               args.nice, args.nsplit, args.year)

for i in xrange(args.nsplit):
    if args.splits and (i + 1) not in args.splits:
        continue
    cmd = "cd %s && %s" % (CWD, CMD % (i + 1))
    output = 'HHProcessor.data%d-JetTauEtmiss_%d.root' % (args.year, i + 1)
    if os.path.exists(os.path.join(output_path, output)):
        print "%s already exists. please delete it and resubmit" % output
        continue
    cluster.qsub(
        cmd,
        ncpus=args.nproc,
        name='HHProcessor.data%d_%d' % (args.year, i + 1),
        stderr_path=output_path,
        stdout_path=output_path,
        queue=args.queue,
        dry_run=args.dry)
