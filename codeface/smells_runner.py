#! /usr/bin/env python

# This file is part of Codeface. Codeface is free software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, version 2.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# Copyright 2013 by Siemens AG
# All Rights Reserved.

import os
import json
import time
import string
import nntplib
import multiprocessing

from argparse import Namespace
from email.utils import parsedate
from datetime import datetime, date, timedelta


import yaml

from codeface.util import execute_command
# from codeface.cli import cmd_run
from codeface.kownProjectsManager import get_project_conf

CONF_FILE = "confFile"
REPO_DOWNLOADED = "repoDownloaded"
ML_DOWNLOADED = "mlDownloaded"
PROJECT_ANALIZED = "projectAnalized"
ML_ANALIZED = "mlAnalized"
SOCIOTECH_ANALIZED = "sociotechAnalized"
TECHSMELL_ANALIZED = "techsmellAnalized"

def get_status(status_file, key):
    with open(status_file) as sfile:
        status = json.load(sfile)

    return status.get(key, False)

def _set_status(status_file, key, new_status):
    with open(status_file) as sfile:
        status = json.load(sfile)
    status[key] = new_status
    with open(status_file, 'w') as outfile:
        json.dump(status, outfile)

def set_status_done(status_file, key):
    _set_status(status_file, key, True)

def _init(project_name, project_dir):
    # init class variables
    _, repo, mail_list = get_project_conf(project_name)
    codeface_dir = os.path.dirname(os.path.abspath(__file__))
    codeface_conf_file = codeface_dir + '/../codeface.conf'
    codeface_base_conf = codeface_dir + '/../conf/baseConf.conf'
    project_name = project_name
    # project_dir = project_dir
    project_conf_file = project_dir + '/' + project_name + '.conf'
    project_results_dir = project_dir + '/results'
    conf = {'project': ''}
    repo_folder = project_dir + "/" + project_name + "-repo/"
    ml_mbox = mail_list + ".mbox"
    ml_temp_mbox = project_name + "-ml-temp.mbox"
    cores = multiprocessing.cpu_count()

    status_file = project_dir + '/' + project_name + '-operation-log.json.log'
    if os.path.isfile(status_file) is False:
        with open(status_file, 'w') as outfile:
            json.dump({
                CONF_FILE: False,
                REPO_DOWNLOADED: False,
                ML_DOWNLOADED: False,
                PROJECT_ANALIZED: False,
                ML_ANALIZED: False,
                SOCIOTECH_ANALIZED: False,
                TECHSMELL_ANALIZED: False
                }, outfile)

    return (codeface_dir, codeface_conf_file, codeface_base_conf, project_conf_file,
            project_results_dir, conf, cores, status_file, repo, repo_folder, mail_list,
            ml_mbox, ml_temp_mbox)

def prepare_reqs(project_name, project_dir, console):
    (codeface_dir, codeface_conf_file, codeface_base_conf, project_conf_file, project_results_dir,
     conf, cores, status_file, repo, repo_folder, mail_list,
     ml_mbox, ml_temp_mbox) = _init(project_name, project_dir)

    cf_conf = Namespace()
    setattr(cf_conf, 'codeface_dir', codeface_dir)
    setattr(cf_conf, 'codeface_conf_file', codeface_conf_file)
    setattr(cf_conf, 'status_file', status_file)

    if os.path.isdir(project_results_dir) is False:
        os.mkdir(project_results_dir)

    if get_status(status_file, CONF_FILE) is False:
        _process_configuration(project_name, project_conf_file, codeface_base_conf,
                               conf, status_file, repo_folder, mail_list, console)
        set_status_done(status_file, CONF_FILE)

    if get_status(status_file, REPO_DOWNLOADED) is False:
        execute_command(['git', 'clone', repo, repo_folder], direct_io=True)
        set_status_done(status_file, REPO_DOWNLOADED)

    if get_status(status_file, ML_DOWNLOADED) is False:
        ml_start_date = date.today() - 3 * timedelta(days=365)
        exe = codeface_dir + "/R/ml/download.r"
        cmd = []
        cmd.append(exe)
        cmd.append(mail_list)
        cmd.append(str(_get_nntp_infos(mail_list,
                                       ml_start_date.year, ml_start_date.month, ml_start_date.day
                                      )))
        cmd.append(ml_temp_mbox)

        execute_command(cmd, direct_io=True, cwd=project_dir)
        _clean_ml(ml_temp_mbox, ml_mbox)
        os.remove(ml_temp_mbox)
        set_status_done(status_file, ML_DOWNLOADED)


    prj_args = Namespace()
    setattr(prj_args, 'resdir', project_results_dir)
    setattr(prj_args, 'gitdir', repo_folder)
    setattr(prj_args, 'config', codeface_conf_file)
    setattr(prj_args, 'project', project_conf_file)
    setattr(prj_args, 'no_report', False)
    setattr(prj_args, 'loglevel', 'info')
    setattr(prj_args, 'logfile', None)
    setattr(prj_args, 'recreate', False)
    setattr(prj_args, 'profile_r', False)
    setattr(prj_args, 'jobs', cores)
    setattr(prj_args, 'tagging', 'default')
    setattr(prj_args, 'reuse_db', False)

    ml_args = Namespace()
    setattr(ml_args, 'resdir', project_results_dir)
    setattr(ml_args, 'mldir', project_dir)
    setattr(ml_args, 'config', codeface_conf_file)
    setattr(ml_args, 'project', project_conf_file)
    setattr(ml_args, 'loglevel', 'info')
    setattr(ml_args, 'logfile', None)
    setattr(ml_args, 'jobs', 1)
    setattr(ml_args, 'mailinglist', None)
    setattr(ml_args, 'use_corpus', False)

    st_args = Namespace()
    setattr(st_args, 'resdir', project_results_dir)
    setattr(st_args, 'config', codeface_conf_file)
    setattr(st_args, 'project', project_conf_file)
    setattr(st_args, 'loglevel', 'info')
    setattr(st_args, 'logfile', None)
    setattr(st_args, 'jobs', cores)

    tsa_args = Namespace()
    setattr(tsa_args, 'resdir', project_results_dir)
    setattr(tsa_args, 'gitdir', repo_folder)
    setattr(tsa_args, 'config', codeface_conf_file)
    setattr(tsa_args, 'project', project_conf_file)
    setattr(tsa_args, 'loglevel', 'info')
    setattr(tsa_args, 'logfile', None)
    setattr(tsa_args, 'jobs', cores)

    return cf_conf, prj_args, ml_args, st_args, tsa_args



def _process_configuration(project_name, project_conf_file, codeface_base_conf, conf, status_file,
                           repo_folder, mail_list, console):
    if os.path.isfile(project_conf_file) is False:
        try:
            base_conf = yaml.load(open(codeface_base_conf))
            conf.update(base_conf)
        except IOError:
            console.exception("Could not open configuration file '{}'")
            raise
        except yaml.YAMLError:
            console.exception("Could not parse configuration file '{}'")
            raise

        conf["project"] = project_name
        conf["repo"] = repo_folder
        conf["mailinglists"][0]["name"] = mail_list
        conf["description"] = project_name + " project"

        yaml.dump(conf, open(project_conf_file, 'w'))

    # self.conf = Configuration.load(self.codeface_dir + '/../codeface.conf',
    #                                self.project_conf_file)

def _get_nntp_infos(mail_list, year, month, day):

    def fn(item):
        email_date = item[1].replace('"', ' ')
        datetime_object = parsedate(email_date)
        return time.mktime(datetime_object)


    news_server = nntplib.NNTP('news.gmane.org')
    _, _, first, last, _ = news_server.group(mail_list)
    _, subs = news_server.xhdr('date', first + '-' + last)

    rrr = map(fn, subs)
    max_val = max([x for x in rrr if x < time.mktime(datetime(year, month, day).timetuple())])
    max_idx = rrr.index(max_val)

    news_server.quit()

    return len(rrr) - max_idx

def _clean_ml(source, destination):
    prev = ""
    target = open(destination, 'w')
    for line in open(source):
        prev = filter(lambda x: x in string.printable, prev)
        target.write(prev)
        prev = line
    target.write(prev)
    target.close()
