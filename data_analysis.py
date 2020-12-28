import csv
import sys
import os
import ast
import re

# prints error message_string and exits with code 1
def error(message_string):
    print("data_analysis.py error: " + message_string, file = sys.stderr)
    exit(1)

# 'self.data' contains nested dictionaries with all data in the 'data' directory. it has the form "self.data[experiment_num][file_name][data_metric]=data_entry"
class all_data:
    def __init__(self):
        # parse through "data" directory and organize its file contents in a dictionary
        self.data = {} # e.g. self.data[experiment_0] = {resulaj_0.csv: {trial_stats}}
        self.parse_data_dir()
        self.parse_csv_files()

    def parse_data_dir(self):
        if not os.path.exists("data/"):
            error("no 'data/' directory in cwd")
        else:
            os.chdir("data/")

        for dir in os.listdir():
            if not os.path.isdir(dir):
                error("all files in 'data/' should be experiment directories: e.g. experiment_0")
            else:
                self.data[dir] = {}
            for file in os.listdir(dir):
                if not os.path.isfile(os.path.join(dir, file)):
                    error("all files in " + os.path.join("data", dir) +"should be csv files: e.g. resulaj_0")
                else:
                    self.data[dir][file] = {}

    def parse_csv_files(self):
        csv.field_size_limit(10000000)

        for experiment in self.data:
            for file in self.data[experiment]:
                # open csv file
                with open(os.path.join(experiment, file), 'r') as csv_file:
                    csv_reader = csv.reader(csv_file, lineterminator = '\n')

                    self.data[experiment][file]['trial'] = file[-5]
                    for row in csv_reader:
                        if(not row):
                            continue
                        if re.match("Trial*", row[0]):
                            continue
                        elif row[0] == "cursor_positions" or row[0] == "dot_positions":
                            self.data[experiment][file][row[0]] = ast.literal_eval(row[1])
                        else:
                            self.data[experiment][file][row[0]] = row[1]

def main():

    csv_file = all_data()


if __name__=='__main__':
    main()
