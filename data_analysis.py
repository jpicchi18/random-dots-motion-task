import csv
import sys
import os
import ast
import re
y=np.array([1,1,2,1,-2])
x=np.array([0,1,2,3,4])
integral_threshhold = -10
# create new column in dataframe that holds coords for integration
df[“integral”] = -1
df[“is_COM”] = 0
# enumerate over all participants
# for name in df.name.unique():
#   entries = df[df[‘name’] == name] # change later
x_dim, y_dim = df.shape
# get x_coord of start position (varies due to screen size)
start_position = 863
# loop over cursor position dicts
for i in range(x_dim):
  # find which side they selected (target 1 = left, target 2 = right)
  target_selected = ‘left’
  if (int(df.iloc[i, 6]) == 2):
    target_selected = ‘right’
  cursor_pos = ast.literal_eval(df.iloc[i, 5])
  x_coords = []
  y_coords = []
  # loop over cursor coordinates in the dictionary
  first = True
  for key in sorted(cursor_pos):
    if first:
      first = False
      start_position = cursor_pos[key][0]
      continue
    x_coord = cursor_pos[key][0] - start_position
    y_coord = cursor_pos[key][1]
    # set x_coord to 0 if it is on the side of the selected targets
    if (target_selected == ‘left’ and x_coord < 0) or (target_selected == ‘right’ and x_coord > 0):
      x_coord = 0
    # switch coords and append coords to list
    x_coords.append(y_coord)
    y_coords.append(np.abs(x_coord))
  # print(y_coords)
  # compute integral and store
  df.at[i, “integral”] = scipy.integrate.trapz(y_coords, x_coords)
  if (df.iloc[i, 18]) < integral_threshhold:
    df.at[i, “is_COM”] = 1
















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
            print('bye')
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
