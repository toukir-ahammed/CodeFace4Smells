import csv
import os

def get_project_conf(project_name):
    codeface_dir = os.path.dirname(os.path.abspath(__file__))

    with open(codeface_dir + '/../known-projects/db.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if (row['Project'].lower() == project_name.lower()):
                return row['Project'], row['Repo'], row['Gmane Mailing list']

    raise KeyError("{} not found in the konw projects database.".format(project_name))
