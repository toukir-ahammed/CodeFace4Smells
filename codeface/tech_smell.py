#! /usr/bin/env python
import string
from os.path import join as pathjoin
from progressbar import ProgressBar, Percentage, Bar
from codeface.dbmanager import DBManager
from codeface.util import execute_command

def doTechSmellAnalysis(conf, resdir, repo, tsadir):

    dbm = DBManager(conf)
    project_id = dbm.getProjectID(conf["project"], conf["tagging"])
    releases = dbm.get_project_release_end(project_id)
    widgets = ['Pass 1/2: ', Percentage(), ' ', Bar()]
    pbar = ProgressBar(widgets=widgets, maxval=len(releases)).start()

    git_cmd = []
    git_cmd.append("git")
    git_cmd.append("rev-parse")
    git_cmd.append("--abbrev-ref")
    git_cmd.append("HEAD")
    git_latest_ver_raw = execute_command(git_cmd, direct_io=False, cwd=repo)
    git_latest_version = string.replace(git_latest_ver_raw, "\n", "")
    i = 0

    for release in releases:

        git_cmd = []
        git_cmd.append("git")
        git_cmd.append("checkout")
        git_cmd.append(release[1]) # commit hash
        execute_command(git_cmd, direct_io=False, cwd=repo)

        csv_file_name = pathjoin(resdir, "release_" + str(release[0]) + ".csv") #releaseId
        tsa_cmd = []
        tsa_cmd.append("java")
        tsa_cmd.append("-jar")
        tsa_cmd.append(tsadir + "/RunCodeSmellDetection.jar")
        tsa_cmd.append(repo)
        tsa_cmd.append(csv_file_name)
        stdout = execute_command(tsa_cmd, ignore_errors=True, direct_io=False, cwd=repo)

        i = i + 1
        pbar.update(i)

    git_cmd = []
    git_cmd.append("git")
    git_cmd.append("checkout")
    git_cmd.append(git_latest_version) # back to latest
    execute_command(git_cmd, direct_io=False, cwd=repo)

    pbar.finish()
