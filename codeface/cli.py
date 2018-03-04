## This file is part of Codeface. Codeface is free software: you can
## redistribute it and/or modify it under the terms of the GNU General Public
## License as published by the Free Software Foundation, version 2.
##
## This program is distributed in the hope that it will be useful, but WITHOUT
## ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
## FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
## details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
##
## Copyright 2013 by Siemens AG, Wolfgang Mauerer <wolfgang.mauerer@siemens.com>
## All Rights Reserved.
'''
Command-line interface driver for the codeface package

Provides

'''
import os
import argparse
import unittest
import subprocess
from pkg_resources import resource_filename

from glob import glob

from codeface.logger import set_log_level, start_logfile, log
from codeface.configuration import Configuration
from codeface.util import execute_command
from codeface.project import (project_analyse, mailinglist_analyse, sociotechnical_analyse,
                              techsmell_analyse)
import codeface.smells_runner as smells

def get_parser():
    parser = argparse.ArgumentParser(prog='codeface',
                description='Program for Social Data Analysis')
    parser.add_argument('-l', '--loglevel', help='Choose the logging level',
                choices=['debug', 'devinfo', 'info', 'warning', 'error'],
                default='info')
    parser.add_argument('-f', '--logfile', help='Save all debug logging into the'
                ' given log file')
    parser.add_argument('-j', '--jobs', default=1,
                help='Number of cores to use in parallel')

    sub_parser = parser.add_subparsers(help='select action')
    test_parser = sub_parser.add_parser('test', help='Run tests')
    test_parser.set_defaults(func=cmd_test)
    test_parser.add_argument('-c', '--config', help="Codeface configuration file",
                default='codeface_testing.conf')
    test_parser.add_argument('-p', '--pattern', default="*",
                help='run only tests matching the given pattern')
    test_parser.add_argument('-u', '--unit', action='store_true',
                help='run only unit tests')

    run_parser = sub_parser.add_parser('run', help='Run analysis')
    run_parser.set_defaults(func=cmd_run)
    run_parser.add_argument('-c', '--config', help="Codeface configuration file",
                default='codeface.conf')
    run_parser.add_argument(
        '--tagging',
        help="Overrides the tagging configuration within the CLI. "
             "When used this parameter overrides the configured tagging, "
             "default is fallback to configuration value",
        default='default')
    run_parser.add_argument('-p', '--project', help="Project configuration file",
                required=True)
    run_parser.add_argument('resdir',
                        help="Directory to store analysis results in")
    run_parser.add_argument('gitdir',
                        help="Directory for git repositories")
    run_parser.add_argument('--no-report', action="store_true",
                        help="Skip LaTeX report generation (and dot compilation)")
    run_parser.add_argument('--recreate', action="store_true",
                        help="Force a delete of the project in the database")
    run_parser.add_argument('--profile-r', action="store_true",
                        help="Compute an execution time profile for R code")
    run_parser.add_argument(
        '--reuse-vcs-analysis', action='store_true', dest="reuse_db",
        help="Re-use an already existing vcs-analysis.db file. "
             "This flag is useful to continue a previously failed analysis"
             " or for debugging purposes.")

    ml_parser = sub_parser.add_parser('ml', help='Run mailing list analysis')
    ml_parser.set_defaults(func=cmd_ml)
    ml_parser.add_argument('-c', '--config', help="Codeface configuration file",
                default='codeface.conf')
    ml_parser.add_argument('-p', '--project', help="Project configuration file",
                required=True)
    ml_parser.add_argument('-m', '--mailinglist', help="Only run on the "
                "specified mailing list (can be specified multiple times)",
                default=[], action="append")
    ml_parser.add_argument('--use-corpus', action="store_true",
                           help="Re-use the corpus file that have been generated before")
    ml_parser.add_argument('resdir',
                        help="Directory to store analysis results in")
    ml_parser.add_argument('mldir',
                        help="Directory for mailing lists")
    
    st_parser = sub_parser.add_parser('st', help='Run socio-technical analysis')
    st_parser.set_defaults(func=cmd_st)
    st_parser.add_argument('-c', '--config', help="Codeface configuration file",
                default='codeface.conf')
    st_parser.add_argument('-p', '--project', help="Project configuration file",
                required=True)
    st_parser.add_argument('resdir',
                        help="Directory with communication and collaboration analysis results")

    dyn_parser = sub_parser.add_parser('dynamic', help='Start R server for a dynamic graph')
    dyn_parser.set_defaults(func=cmd_dynamic)
    dyn_parser.add_argument('-c', '--config', help="Codeface configuration file",
                default='codeface.conf')
    dyn_parser.add_argument('graph', help="graph to show", default=None, nargs='?')
    dyn_parser.add_argument('-l', '--list', action="store_true", help="list available graphs")
    dyn_parser.add_argument('-p', '--port', default="8100", help="Pass this to R as port to listen on")

    smells_parser = sub_parser.add_parser('smells',
                                         description="Start a complete analisys using default "
                                         "values of known projects. For additional help please see "
                                         "http://www.google.com/")
    smells_parser.set_defaults(func=cmd_smells)

    tsa_parser = sub_parser.add_parser('tsa', description="Start tech smell analysis")
    tsa_parser.set_defaults(func=cmd_tsa)
    tsa_parser.add_argument('resdir', help="Directory to store analysis results in")
    tsa_parser.add_argument('gitdir', help="Directory for git repositories")
    tsa_parser.add_argument('-c', '--config', help="Codeface configuration file",
                            default='codeface.conf')
    tsa_parser.add_argument('-p', '--project', help="Project configuration file", required=True)

    return parser

def cmd_smells(args):

    (cf_conf, prj_args, ml_args, st_args,
     tsa_args) = smells.prepare_reqs(os.path.basename(os.getcwd()), os.getcwd(), log)

    execute_command(['killall', 'node'], True)
    id_service = subprocess.Popen(["node", cf_conf.codeface_dir + '/../id_service/id_service.js',
                                   cf_conf.codeface_conf_file], stdout=subprocess.PIPE)

    if smells.get_status(cf_conf.status_file, smells.PROJECT_ANALIZED) is False:
        cmd_run(prj_args)
        smells.set_status_done(cf_conf.status_file, smells.PROJECT_ANALIZED)

    if smells.get_status(cf_conf.status_file, smells.ML_ANALIZED) is False:
        cmd_ml(ml_args)
        smells.set_status_done(cf_conf.status_file, smells.ML_ANALIZED)

    if smells.get_status(cf_conf.status_file, smells.SOCIOTECH_ANALIZED) is False:
        cmd_st(st_args)
        smells.set_status_done(cf_conf.status_file, smells.SOCIOTECH_ANALIZED)

    if smells.get_status(cf_conf.status_file, smells.TECHSMELL_ANALIZED) is False:
        cmd_tsa(tsa_args)
        smells.set_status_done(cf_conf.status_file, smells.TECHSMELL_ANALIZED)

    id_service.terminate()

    return 0

def cmd_run(args):
    '''Dispatch the ``run`` command.'''
    # First make all the args absolute
    resdir, gitdir = map(os.path.abspath, (args.resdir, args.gitdir))
    codeface_conf, project_conf = map(os.path.abspath, (args.config, args.project))
    logfile = args.logfile
    if logfile:
        logfile = os.path.abspath(logfile)
    project_analyse(resdir, gitdir, codeface_conf, project_conf,
                    args.no_report, args.loglevel, logfile, args.recreate,
                    args.profile_r, args.jobs, args.tagging, args.reuse_db)
    return 0

def cmd_ml(args):
    '''Dispatch the ``ml`` command.'''
    # First make all the args absolute
    resdir, mldir = map(os.path.abspath, (args.resdir, args.mldir))
    codeface_conf, project_conf = map(os.path.abspath, (args.config, args.project))
    logfile = args.logfile
    if logfile:
        logfile = os.path.abspath(logfile)
    mailinglist_analyse(resdir, mldir, codeface_conf, project_conf,
                        args.loglevel, logfile, args.jobs, args.mailinglist,
                        args.use_corpus)
    return 0

def cmd_st(args):
    '''Dispatch the ``st`` command.'''
    # First make all the args absolute
    resdir = os.path.abspath(args.resdir)
    codeface_conf, project_conf = map(os.path.abspath, (args.config, args.project))
    logfile = args.logfile
    if logfile:
        logfile = os.path.abspath(logfile)
    sociotechnical_analyse(resdir, codeface_conf, project_conf,
                           args.loglevel, logfile, args.jobs)
    return 0

def cmd_tsa(args):
    '''Dispatch the ``tsa`` command.'''

    tsa_dir = os.path.dirname(os.path.abspath(__file__)) + '/../tsa'
    # First make all the args absolute
    resdir, gitdir, tsadir = map(os.path.abspath, (args.resdir, args.gitdir, tsa_dir))
    codeface_conf, project_conf = map(os.path.abspath, (args.config, args.project))
    logfile = args.logfile
    if logfile:
        logfile = os.path.abspath(logfile)
    techsmell_analyse(resdir, gitdir, tsadir, codeface_conf, project_conf, args.loglevel,
                      logfile, args.jobs)
    return 0

def cmd_dynamic(args):
    dyn_directory = resource_filename(__name__, "R/shiny/apps")

    if args.graph is None and not(args.list):
        log.critical("No dynamic graph given!")

    if args.list or args.graph is None:
        print('List of possible dynamic graphs:')
        for s in sorted(os.listdir(dyn_directory)):
            if os.path.isdir(os.path.join(dyn_directory, s)):
                print(" * " + s)
        return 1

    cwd = os.path.join(dyn_directory, args.graph)
    cfg = os.path.abspath(args.config)
    if not os.path.exists(cwd):
        log.critical('Path "{}" not found!'.format(cwd))
        return 1
    Rcode = "library(shiny); runApp(host='0.0.0.0', port={})".format(args.port)
    cmd = ["Rscript", "-e", Rcode, "-c", cfg]
    execute_command(cmd, direct_io=True, cwd=cwd)

def cmd_test(args):
    '''Sub-command handler for the ``test`` command.'''
    unit_only=args.unit
    pattern=args.pattern
    config_file=os.path.abspath(args.config)
    del args
    test_path = os.path.join(os.path.dirname(__file__), 'test')
    print('\n===== running unittests =====\n')
    tests = unittest.TestLoader().discover(os.path.join(test_path, 'unit'),
        pattern='test_{}.py'.format(pattern), top_level_dir=test_path)
    unit_result = unittest.TextTestRunner(verbosity=1).run(tests)
    unit_success = not (unit_result.failures or unit_result.errors)
    if unit_only:
        if unit_success:
            print('\n===== unit tests succeeded :) =====')
        else:
            print('\n===== unit tests failed :( =====')
        return 0 if unit_success else 1
    print('\n===== running integration tests =====\n')
    tests = unittest.TestLoader().discover(os.path.join(test_path, 'integration'),
        pattern='test_{}.py'.format(pattern), top_level_dir=test_path)
    # Set the testing configuration file as member variable
    # for all integration tests, since we need the DB and REST configurations
    def set_config(suite):
        if isinstance(suite, unittest.TestSuite):
            for test in suite:
                set_config(test)
        suite.config_file = config_file
    set_config(tests)
    int_result = unittest.TextTestRunner(verbosity=2).run(tests)
    int_success = not (int_result.failures or int_result.errors)
    if unit_success and int_success:
            print('\n===== all tests succeeded :) =====')
    else:
            print('\n===== some tests failed :( =====')
    return 0 if unit_success and int_success else 1

def run(argv):
    parser = get_parser()
    # Note: The first argument of argv is the name of the command
    args = parser.parse_args(argv[1:])
    set_log_level(args.loglevel)
    if args.logfile:
        start_logfile(args.logfile, 'debug')
    return args.func(args)

def main():
    import sys
    return run(sys.argv)
