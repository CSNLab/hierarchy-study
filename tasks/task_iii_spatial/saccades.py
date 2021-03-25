#!/usr/bin/env python

# (4 TRs + 398 seconds/run1 + 7 TRs) + (4 TRs + 385 seconds/run2 + 7 TRs)

from psychopy_util import *
from saccades_config import *
import random
import pickle


def random_position(direction, step_num):
    if direction == 0:  # up
        return (0 + random.uniform(-small_jitters[0], small_jitters[0]),
                step_num * step_distances[1] + random.uniform(-large_jitters[1], large_jitters[1]))
    if direction == 1:  # down
        return (0 + random.uniform(-small_jitters[0], small_jitters[0]),
                -step_num * step_distances[1] + random.uniform(-large_jitters[1], large_jitters[1]))
    if direction == 2:  # right
        return (step_num * step_distances[0] + random.uniform(-large_jitters[0], large_jitters[0]),
                0 + random.uniform(-small_jitters[1], small_jitters[1]))
    if direction == 3:  # left
        return (-step_num * step_distances[0] + random.uniform(-large_jitters[0], large_jitters[0]),
                0 + random.uniform(-small_jitters[1], small_jitters[1]))


def show_one_trial(step_time, iti, direction, positions):
    infoLogger.logger.info('Starting saccade, direction ' + str(direction))
    # saccades
    for step in range(NUM_STEPS_PER_TRIAL):
        presenter.show_fixation(duration=step_time, pos=positions[step])
    # ITI part 1
    infoLogger.logger.info('End of saccade, starting a ' + str(iti) + '-second ITI')
    presenter.show_fixation(duration=ITI_PART1, pos=positions[-1], wait_trigger=True)
    # ITI part 2
    presenter.show_fixation(duration=iti - ITI_PART1, wait_trigger=True)
    infoLogger.logger.info('End of ITI')


def validation(items):
    # check empty field
    for key in items.keys():
        if items[key] is None or len(items[key]) == 0:
            return False, str(key) + ' cannot be empty.'
    # everything is okay
    return True, ''


if __name__ == '__main__':
    # subject ID dialog
    sinfo = {'ID': '', 'Mode': ['Exp', 'Test']}
    show_form_dialog(sinfo, validation, order=['ID', 'Mode'])
    sid = int(sinfo['ID'])

    # create log file
    infoLogger = DataLogger(LOG_FOLDER, str(sid) + '_saccades.log', 'info_logger', logging_info=True)
    # create window
    presenter = Presenter(fullscreen=(sinfo['Mode'] == 'Exp'), info_logger='info_logger', trigger=TRIGGER)
    # lengths in normalized units
    step_distances = presenter.pixel2norm(STEP_DISTANCE)
    small_jitters = presenter.pixel2norm(SMALL_JITTER_MAX)
    large_jitters = presenter.pixel2norm(LARGE_JITTER_MAX)

    # get trial sequences
    with open('saccades_design.pkl', 'rb') as infile:
        run_seqs = [pickle.load(infile), pickle.load(infile)]
    run_seqs[0][-1]['iti'] = ITI_PART1 + AFTER_RUN_TRIGGERS
    run_seqs[1][-1]['iti'] = ITI_PART1 + AFTER_RUN_TRIGGERS
    assert(len(run_seqs) == NUM_RUNS)
    # add random positions to trial sequences
    for seq in run_seqs:
        for trial in seq:
            trial['pos'] = []
            for step in range(1, NUM_STEPS_PER_TRIAL + 1):
                trial['pos'].append(random_position(direction=trial['stim'], step_num=step))

    # show trials
    for r in range(NUM_RUNS):
        seq = run_seqs[r]
        infoLogger.logger.info('Run #' + str(r))
        presenter.show_instructions(INSTR.format(r + 1), next_page_text=NEXT_RUN_INSTR)  # press space here to continue
        presenter.show_instructions(INSTR.format(r + 1), next_page_text=None, duration=1, wait_trigger=True)
        # center fixation
        presenter.show_fixation(duration=INITIAL_STEP_TRIGGERS, wait_trigger=True)
        for t in range(NUM_TRIALS_PER_RUN):
            show_one_trial(step_time=seq[t]['step_time'], iti=seq[t]['iti'],
                           direction=seq[t]['stim'], positions=seq[t]['pos'])
    # end of experiment
    infoLogger.logger.info('End of experiment')
