from cursor_info import cursor
from psychopy import gui
import csv
import os
import sys

summary = []
positions = []

class data:
    def __init__ (self, window):
        self.cursor = cursor(window)
    def init_file(self):
        input = gui.Dlg()
        input.addField("Subject:")
        input.addField("Trial Type:")
        input.show()
        subj = input.data[0]
        trial_type = input.data[1]
        self.file = subj + "_trial_"+ trial_type + ".csv"
    def check_file(self):
        file_exists = os.path.exists(self.file)
        if file_exists:
            sys.exit("Filename " + self.file + " already exists.")
    def trial_summary(self, trial_num, coherence, direction, choice, reaction):
        result = "Incorrect"
        if direction == choice:
            result = "Correct"
        csvfile = open(self.file, 'a', newline='')
        writer = csv.writer(csvfile, delimiter=",")
        writer.writerow([trial_num, "Coh: " + str(coherence), "Dir: " + str(direction), "Choice: " + str(choice), result, "Rxn Time: " + str(reaction)])
        csvfile.close()
    def pos_summary(self):
        csvfile = open(self.file, 'a', newline='')
        writer = csv.writer(csvfile, delimiter=",")
        writer.writerow(self.cursor.get_pos())
        csvfile.close()