import os
from data_utilities import *


DATA_FOLDER = 'data/'
CSV_FILENAME = 'learning_data.csv'
START_WITH_SUBJECT = 130

all_data = []
for datafile in os.listdir(DATA_FOLDER):
    if not datafile.endswith('.txt') or not datafile[0].isdigit():
        continue
    if int(datafile[:3]) < START_WITH_SUBJECT:
        continue
    sdata = load_json(DATA_FOLDER + datafile, multiple_obj=True)
    training, test = [datafile[:-4], 'train (16)'], [datafile[:-4], 'test (8)']
    for trial in sdata:
        if 'block' in trial:
            block_type = trial['block']
            data_list = training if 'train' in block_type else test
            correct = int(trial['correct'])
            if block_type == 'practice':
                continue
            try:
                data_list[int(block_type.split('_')[0]) + 2] += correct
            except IndexError:
                data_list.append(correct)
    all_data.append(training)
    all_data.append(test)


with open(CSV_FILENAME, 'w') as outfile:
    writer = csv.writer(outfile, delimiter=',')
    writer.writerow(['id', 'block_type'] + ['block_' + str(i) for i in range(16)])
    for line in all_data:
        writer.writerow(line)
