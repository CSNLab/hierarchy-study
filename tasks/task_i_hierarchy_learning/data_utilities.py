import pickle
import yaml
import csv


def load_json(json_file, multiple_obj=False, pkl_file=None):
    """
    Read a json file as a python object (or a list of python objects)
    :param json_file: string file name
    :param pkl_file: (string file name) optionally save the object as a pickle data file
    :param multiple_obj: (boolean) whether the json file contains multiple objects (must have one object per line)
                         or one object total
    :return: a python object (if multiple_obj is False) or a list of python objects (if multiple_obj is True)
    """
    with open(json_file, 'r') as infile:
        if multiple_obj:
            data = [yaml.safe_load(line) for line in infile]
        else:
            data = yaml.safe_load(infile.read())

    if pkl_file:
        with open(pkl_file, 'w') as outfile:
            pickle.dump(data, outfile)

    return data


def flatten(obj, obj_id=None):
    """
    Flatten a nested list or dictionary to a one-dimensional list.
    :return a list of string names, and a list of corresponding values
    """
    names, values = ([], []) if obj_id is None else (['id'], [obj_id])

    def _flatten(x, name=''):  # recursion
        if type(x) is dict:
            for k in x:
                _flatten(x[k], name + k + '.')
        elif type(x) is list:
            for i, a in enumerate(x):
                _flatten(a, name + str(i) + '.')
        else:
            if x is not None:
                names.append(name[:-1])
                values.append(x)

    _flatten(obj)
    return names, values


def fill_missing_keys(data_list):
    """
    Given a list of data with another list of column names to each row, find the union of column names, and make
    every row of data have an equal length by inserting empty strings at the missing columns.
    Assuming column names are unique and sorted.
    :param data_list: a list of tuples (column_name_list, value_list)
                      e.g. [ (['a', 'b', 'c'], [1, 2, 3]),
                             (['a', 'c', 'd'], [1, 3, 4]) ]
    :return a list of complete column names, and a 2-dimensional list of values
            e.g. ( ['a', 'b', 'c', 'd'],
                   [ [1, 2, 3, ''], [1, '', 3, 4] ] )
    """
    name_lists, data = zip(*data_list)

    # get a complete list of column names
    all_names = list(name_lists[0])
    for row in range(1, len(name_lists)):
        name_list = name_lists[row]  # current name list
        all_col, cur_col = 0, 0  # all_names iterator, current name list iterator
        while cur_col < len(name_list):
            if all_col == len(all_names):
                all_names += name_list[cur_col:]
                break
            if name_list[cur_col] != all_names[all_col]:
                if name_list[cur_col] not in all_names:
                    all_names.insert(all_col, name_list[cur_col])
                else:
                    cur_col -= 1
            cur_col += 1
            all_col += 1

    # fill empty strings
    for row in range(len(name_lists)):
        name_i = 0  # name_list iterator
        data_i = 0  # data[row] iterator
        for i in range(len(all_names)):  # i: all_names iterator
            if name_i < len(name_lists[row]):
                if name_lists[row][name_i] != all_names[i]:
                    data[row].insert(data_i, '')
                else:
                    name_i += 1
                data_i += 1
            else:  # missing the last column
                data[row].append('')
    return all_names, data

# print fill_missing_keys([
#     (['a', 'b', 'c', 'd'], [1, 2, 3, 4]),
#     (['b', 'a', 'c', 'd'], [2, 1, 3, 4])
# ])


def longest_common_substring(s1, s2):
    # adapted from https://en.wikibooks.org/wiki/Algorithm_Implementation/Strings/Longest_common_substring#Python_2
    m = [[0] * (1 + len(s2)) for i in xrange(1 + len(s1))]
    longest, x_longest = 0, 0
    for x in xrange(1, 1 + len(s1)):
        for y in xrange(1, 1 + len(s2)):
            if s1[x - 1] == s2[y - 1]:
                m[x][y] = m[x - 1][y - 1] + 1
                if m[x][y] > longest:
                    longest = m[x][y]
                    x_longest = x
            else:
                m[x][y] = 0
    lcs = s1[x_longest - longest: x_longest]
    for k, c in enumerate(lcs):
        if c.isalnum():
            return lcs[k:]  # start from the first alphanumeric character


def _simple_stack(wide_cols, wide_data, cols, data, start, end, skip_cols, cut_number):
    for col_i in xrange(start, end):
        if col_i not in skip_cols:
            cols.append(wide_cols[col_i])
            for row_i, row in enumerate(wide_data):
                for new_row_i in xrange(row_i * cut_number, (row_i + 1) * cut_number):
                    data[new_row_i].append(row[col_i])


def cut_and_stack(wide_cols, wide_data, cut_start, cut_length, cut_number, skip_cols=()):
    """
    Converts data from wide to long format. The cut range (cut_start, cut_start + cut_length * cut_number) has to be
    continuous after columns in skip_cols are excluded.
    :param wide_cols: (list) original data column names
    :param wide_data: (2D list) original data; each sublist should have the same length as wide_cols
    :param cut_start: (integer) the index indicating where the repetition start. Columns and data will be cut and fold
                      right before this start index
    :param cut_length: (integer) length of each repetition
    :param cut_number: (integer) number of repetitions
    :param skip_cols: (a list of integers) column indexes to be excluded.
    :return: a list of new column names and a list of new data
    """
    cols = []
    n_rows = len(wide_data) * cut_number
    data = [[] for i in xrange(n_rows)]
    skip_cols.sort()
    # get cut_end and a list of skipped columns within the cut range
    cut_end = cut_start + cut_length * cut_number  # if no column skipped in the cut range
    i, j = cut_start, 0
    skip_cols_in_cut = []
    while j < len(skip_cols) and skip_cols[j] < cut_start:  # find first element in skip_col that is > cut_start
        j += 1
    while i < cut_end and j < len(skip_cols):
        if i == skip_cols[j]:
            skip_cols_in_cut.append(i)
            cut_end += 1
            j += 1
        i += 1
    # columns before cut
    _simple_stack(wide_cols, wide_data, cols, data, 0, cut_start, skip_cols, cut_number)
    # cut starts
    second_cut_start = 0
    for row_i, row in enumerate(wide_data):
        skip_i = 0
        for cut in xrange(cut_number):
            for i in xrange(cut_length):
                data_row = row_i * cut_number + cut
                col = cut_start + cut * cut_length + i + skip_i
                while skip_i < len(skip_cols_in_cut) and col == skip_cols_in_cut[skip_i]:  # skip
                    skip_i += 1
                    col += 1
                if cut == 1 and i == 0:
                    second_cut_start = col
                data[data_row].append(row[col])
    # cut ends
    # get column names in cut range
    i, j, col_counter, skip_i, skip_j = cut_start, second_cut_start, 0, 0, 0
    while skip_j < len(skip_cols_in_cut) and skip_cols_in_cut[skip_j] < second_cut_start:
        skip_j += 1
    max_skip_i = int(skip_j)  # make copy
    while col_counter < cut_length:
        while skip_i < max_skip_i and i == skip_cols_in_cut[skip_i]:
            i += 1
            skip_i += 1
        while skip_j < len(skip_cols_in_cut) and j == skip_cols_in_cut[skip_j]:
            j += 1
            skip_j += 1
        name = longest_common_substring(wide_cols[i], wide_cols[j])  # combine first two column names in the cycle
        cols.append(name)
        col_counter += 1
        i += 1
        j += 1
    # columns after cut
    _simple_stack(wide_cols, wide_data, cols, data, cut_end, len(wide_cols), skip_cols, cut_number)
    return cols, data


def list2csv(data, csv_filename, col_names=None):
    """
    Write a 2-dimensional data list to a csv file.
    """
    with open(csv_filename, 'w') as outfile:
        writer = csv.writer(outfile, delimiter=',')
        if col_names:
            writer.writerow(col_names)
        for row in data:
            writer.writerow(row)
