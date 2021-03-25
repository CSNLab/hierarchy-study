#!/usr/bin/env python

import sys, os
sys.path.append(os.getcwd() + '/pygaze')
from psychopy_util import *
from config import *
from eyetribe import EyeTribeTracker


def show_one_trial(param, trial_index):
    # START RECORDING
    if trial_index != 'prac':
        tracker.start_recording()
    # 0 anchor face
    if trial_index != 'prac':
        tracker.log('Trial #%d face starts' % trial_index)
    presenter.draw_stimuli_for_duration(images[param['anchor']], FACE_TIME)
    if trial_index != 'prac':
        tracker.log('Trial #%d face ends' % trial_index)
    # 1 fixation
    presenter.show_fixation(FIXATION_TIME)
    # 2 number
    num_stim = visual.TextStim(presenter.window, str(param['distance']), height=1, color=DIR_COLORS[param['direction']])
    if trial_index != 'prac':
        tracker.log('Trial #%d number starts' % trial_index)
    presenter.draw_stimuli_for_duration(num_stim, NUMBER_TIME)
    if trial_index != 'prac':
        tracker.log('Trial #%d number ends' % trial_index)
    # 3 fixation (mental navigation)
    if trial_index != 'prac':
        tracker.log('Trial #%d navigation starts' % trial_index)
    presenter.show_fixation(BLANK_TIME)
    if trial_index != 'prac':
        tracker.log('Trial #%d navigation ends' % trial_index)
    # 4.0 options
    correct_option = param['anchor'] + param['distance'] if param['direction'] == DIRECTIONS[0] else \
                     param['anchor'] - param['distance']
    options = []
    # 4.1 randomly pick 3 other images adjacent to the answer
    abs_dist = 1  # absolute value of distance
    while len(options) < NUM_OPTIONS - 1:
        dist_candidates = [-abs_dist, abs_dist]
        while len(dist_candidates) > 0:
            dist = random.choice(dist_candidates)
            dist_candidates.remove(dist)
            option = correct_option + dist
            if (option not in options) and (option >= 0) and (option < len(images)) and (option != param['anchor']):
                options.append(option)
                if len(options) == NUM_OPTIONS - 1:
                    break
        abs_dist += 1
    random.shuffle(options)
    options.insert(param['answer_index'], correct_option)
    option_stims = [images[index] for index in options]
    for option, position in zip(option_stims, img_positions):
        option.pos = position
        option.size = option_img_size
    # 5.0 create feedback stimuli
    correct_feedback = visual.ImageStim(presenter.window, FEEDBACK_RIGHT)
    correct_bg = visual.Rect(presenter.window, width=2.1, height=2.1, fillColor=GREEN)
    incorrect_feedback = visual.ImageStim(presenter.window, FEEDBACK_WRONG)
    incorrect_bg = visual.Rect(presenter.window, width=2.1, height=2.1, fillColor=RED)
    resp_feedback = ([incorrect_bg, incorrect_feedback], [correct_bg, correct_feedback])
    no_resp_feedback = visual.TextStim(presenter.window, FEEDBACK_SLOW)
    # 4&5 show options, get response, show feedback
    highlight.size = (option_img_size[0] * 1.1, option_img_size[1] * 1.1)
    if trial_index != 'prac':
        tracker.log('Trial #%d options starts' % trial_index)
    response = presenter.select_from_stimuli(option_stims, options, RESPONSE_KEYS, SELECTION_TIME, 0, highlight,
                                             lambda x: x == correct_option, None, resp_feedback, no_resp_feedback,
                                             FEEDBACK_TIME)
    if trial_index != 'prac':
        tracker.log('Trial #%d options ends' % trial_index)
        tracker.stop_recording()
    # 4.2 recover central positions
    for option in option_stims:
        option.pos = presenter.CENTRAL_POS
        option.size = None
    # 6 interval between trials
    presenter.show_fixation(random.choice(TRIAL_INTERVALS))
    # return
    param['options'] = options
    if response is None:
        param['response'] = None
    else:
        param.update(response)
    param['trial_index'] = trial_index
    return param


def generate_trials():
    # generate unique combinations
    unique_trials = []
    practices = []
    for anchor in range(NUM_FACES):
        for dist in range(1, NUM_FACES):
            trials = unique_trials \
                if (anchor in ANCHOR_INDEXES) and (dist >= MIN_DISTANCE) and (dist <= MAX_DISTANCE) \
                else practices
            if anchor - dist >= 0:
                trials.append({
                    'anchor': anchor,
                    'direction': DIRECTIONS[1],  # up
                    'distance': dist,
                })
            if anchor + dist < NUM_FACES:
                trials.append({
                    'anchor': anchor,
                    'direction': DIRECTIONS[0],  # down
                    'distance': dist,
                })
    trials = [list(unique_trials) for i in range(NUM_RUNS * 2)]
    for prac in practices:
        prac['answer_index'] = random.randrange(4)
    ans_indexes = [[i for _ in range(len(unique_trials) / 4 / 2) for i in range(4)],
                   [i for _ in range(len(unique_trials) / 4 / 2) for i in range(4)]]  # up & down trials
    for run in trials:
        random.shuffle(ans_indexes[0])
        random.shuffle(ans_indexes[1])
        counters = [0, 0]
        for trial in run:
            direction = DIRECTIONS.index(trial['direction'])  # 0 or 1
            trial['answer_index'] = ans_indexes[direction][counters[direction]]
            counters[direction] += 1
        random.shuffle(run)
    if section != 'prac':
        trials = trials[NUM_RUNS * section : NUM_RUNS * (section + 1)]
    return trials, practices


def validation(items):
    # check empty field
    for key in items.keys():
        if items[key] is None or len(items[key]) == 0:
            return False, str(key) + ' cannot be empty.'
    # check age
    try:
        if int(items['Age']) <= 0:
            raise ValueError
    except ValueError:
        return False, 'Age must be a positive integer'
    # everything is okay
    return True, ''


def get_positions(window):
    # calculate 4 image positions so that the distances from them to the screen center are the same
    x0, y0 = window.size
    x = float(OPTION_IMG_DIST) / x0
    y = float(OPTION_IMG_DIST) / y0
    return (0, y), (0, -y), (-x, 0), (x, 0)


def get_option_img_size(window):
    # calculate the option image sizes so that they maintain a 1:1 height-width ratio and wouldn't overlap
    x0, y0 = window.size
    return OPTION_IMG_HEIGHT * y0 / x0, OPTION_IMG_HEIGHT


def show_key_mapping():
    texts = [visual.TextStim(presenter.window, key.upper(), pos=pos, color=BLACK, height=0.2)
             for key, pos in zip(RESPONSE_KEYS, img_positions)]
    presenter.show_instructions(INSTR_3, TOP_INSTR_POS, example_images + texts, next_instr_pos=(0, -0.9))


def navigation():
    if sinfo['Section'] == 'Instr':
        presenter.show_instructions(INSTR_0)
        presenter.show_instructions(color_instr)
        presenter.show_instructions(INSTR_1)
        presenter.show_instructions(INSTR_2, TOP_INSTR_POS, example_images, next_instr_pos=(0, -0.9))
        show_key_mapping()

        # practices
        presenter.show_instructions(INSTR_PRACTICE)
        global practices
        practices = random.sample(practices, NUM_PRACTICE_TRIALS)
        for trial in practices:
            presenter.show_instructions(color_instr)
            data = show_one_trial(trial.copy(), trial_index='prac')
            data['practice'] = True
            dataLogger.write_data(data)
        presenter.show_instructions(INSTR_4)

    else:
        # show trials
        total_correct_counter = 0
        trial_counter = 0
        for run in trials:
            # instructions
            presenter.show_instructions('Block #' + str(trials.index(run) + 1) + '\n\nRemember: ' + color_instr)
            # start run
            correct_counter = 0
            for trial in run:
                trial_counter += 1
                data = show_one_trial(trial.copy(), trial_counter)
                if data['response'] is not None and data['correct']:
                    correct_counter += 1
                dataLogger.write_data(data)
                if trial_counter >= MAX_NUM_TRIALS:
                    break
            total_correct_counter += correct_counter
            presenter.show_instructions('You earned ' + str(correct_counter) + ' point(s) out of ' + str(len(run)) +
                                        ' points possible in this block')
            if trial_counter >= MAX_NUM_TRIALS:
                break
        # end
        presenter.show_instructions(INSTR_END[section], next_instr_text=None)
        accuracy = float(total_correct_counter) / len(trials) / len(trials[0])  # overall accuracy
        print('accuracy', accuracy)
        dataLogger.write_data({'overall_accuracy': accuracy})


if __name__ == '__main__':
    # subject ID dialog
    sinfo = {'ID': '',
             'Gender': ['Female', 'Male'],
             'Age': '',
             'Section': ['Instr', '1', '2'],
             'Screen': ['Exp', 'Test']}
    show_form_dialog(sinfo, validation, order=['ID', 'Gender', 'Age', 'Section', 'Screen'])
    sid = int(sinfo['ID'])
    img_prefix = sinfo['Gender'][0]
    section = 'prac' if sinfo['Section'] == 'Instr' else int(sinfo['Section']) - 1

    # create data file
    postfix = 'prac' if sinfo['Section'] == 'Instr' else sinfo['Section']
    dataLogger = DataHandler(DATA_FOLDER, str(sid) + '_eye_%s.txt' % postfix)
    if not os.path.isdir('log'):
        os.mkdir('log')
    # save info from the dialog box
    dataLogger.write_data({
        k: str(sinfo[k]) for k in sinfo.keys()
    })
    # create window
    presenter = Presenter(fullscreen=(sinfo['Screen'] == 'Exp'))
    option_img_size = get_option_img_size(presenter.window)
    img_positions = get_positions(presenter.window)
    dataLogger.write_data(str(info.RunTimeInfo(win=presenter.window, refreshTest=None, verbose=False)))
    # load images
    example_images = presenter.load_all_images(IMG_FOLDER, '.png', img_prefix='usericon')
    for img, pos in zip(example_images, img_positions):
        img.pos = pos
    images = presenter.load_all_images(IMG_FOLDER, '.jpg', img_prefix)
    highlight = visual.ImageStim(presenter.window, image=IMG_FOLDER + 'highlight.png')
    # randomize trials
    trials, practices = generate_trials()
    # randomize images
    random.seed(sid)
    random.shuffle(images)  # status high -> low
    dataLogger.write_data({i: stim._imName for i, stim in enumerate(images)})
    # randomize colors
    DIR_COLORS = {DIRECTIONS[0]: DIR_COLORS[0], DIRECTIONS[1]: DIR_COLORS[1]} if random.randrange(2) == 0 else \
                 {DIRECTIONS[0]: DIR_COLORS[1], DIRECTIONS[1]: DIR_COLORS[0]}
    dataLogger.write_data({direc: COLOR_NAMES[DIR_COLORS[direc]] for direc in DIR_COLORS.keys()})
    color_instr = INSTR_COLOR.format(down_color=COLOR_NAMES[DIR_COLORS[DIRECTIONS[0]]],
                                     up_color=COLOR_NAMES[DIR_COLORS[DIRECTIONS[1]]])

    # eye tribe setup
    if sinfo['Section'] != 'Instr':
        tracker = EyeTribeTracker(presenter, SCREEN_SIZE, SCREEN_DIST,
                                  logfile='log/%d_tracker_%s' % (sid, sinfo['Section']))
        tracker.show_calibration()
    # show everything
    navigation()
