#!/usr/bin/env python

from psychopy_util import *
from config import *
import pickle
import dumb_text_input as dt
import copy

# run #12356: 399 trials + 3 feedback = 402 seconds
# run #4: 401 + 3 = 404 seconds


def show_one_trial(param):
    # 0 anchor face
    infoLogger.logger.info('Showing anchor face')
    presenter.draw_stimuli_for_duration(images[param['anchor']], FACE_TRIGGER, wait_trigger=True)
    infoLogger.logger.info('End of anchor face')
    # 1 fixation
    presenter.show_fixation(FIXATION_TIME, wait_trigger=False)
    # 2 number
    num_stim = visual.TextStim(presenter.window, str(param['distance']), height=1, color=DIR_COLORS[param['direction']])
    infoLogger.logger.info('Showing number')
    presenter.draw_stimuli_for_duration(num_stim, NUMBER_TRIGGER, wait_trigger=True)
    infoLogger.logger.info('End of number')
    # 3 fixation (mental navigation)
    presenter.show_fixation(BLANK_TRIGGER, wait_trigger=True)
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
    selection_time = SELECTION_TIME
    highlight.size = (option_img_size[0] * 1.1, option_img_size[1] * 1.1)
    response = presenter.select_from_stimuli(option_stims, options, RESPONSE_KEYS, selection_time, 0, highlight,
                                             lambda x: x == correct_option, None, resp_feedback, no_resp_feedback,
                                             FEEDBACK_TRIGGER, no_resp_feedback_time=FEEDBACK_TRIGGER,
                                             feedback_wait_trigger=True)
    # 4.2 recover central positions
    for option in option_stims:
        option.pos = presenter.CENTRAL_POS
        option.size = None
    # 6 interval between trials
    infoLogger.logger.info('End of trial')
    presenter.show_fixation(param['iti'], wait_trigger=True)
    # return
    param['options'] = options
    if response is None:
        param['response'] = None
    else:
        param.update(response)
    return param


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
    x = 2.0 * OPTION_IMG_DIST / x0
    y = 2.0 * OPTION_IMG_DIST / y0
    return (0, y), (0, -y), (-x, 0), (x, 0)


def get_option_img_size(window):
    # calculate the option image sizes so that they maintain a 1:1 height-width ratio and wouldn't overlap
    x0, y0 = window.size
    return OPTION_IMG_HEIGHT * y0 / x0, OPTION_IMG_HEIGHT


if __name__ == '__main__':
    # subject ID dialog
    sinfo = {'ID': '',
             'Gender': ['Female', 'Male'],
             'Age': '',
             'Screen': ['Exp', 'Test']}
    show_form_dialog(sinfo, validation, order=['ID', 'Gender', 'Age', 'Screen'])
    sid = int(sinfo['ID'])
    img_prefix = sinfo['Gender'][0]

    # create data/log files
    file_postfix = '_scanner'
    infoLogger = DataLogger(LOG_FOLDER, str(sid) + file_postfix + '.log', log_name='info', logging_info=True)
    dataLogger = DataLogger(DATA_FOLDER, str(sid) + file_postfix + '.txt', log_name='data')
    # save info from the dialog box
    dataLogger.write_json({
        k: str(sinfo[k]) for k in sinfo.keys()
    })
    # create window
    presenter = Presenter(fullscreen=(sinfo['Screen'] == 'Exp'), info_logger='info', trigger=TRIGGER)
    option_img_size = get_option_img_size(presenter.window)
    img_positions = get_positions(presenter.window)
    # load images
    example_images = presenter.load_all_images(IMG_FOLDER, '.png', img_prefix='usericon')
    for img, pos in zip(example_images, img_positions):
        img.pos = pos
        img.size = option_img_size
    images = presenter.load_all_images(IMG_FOLDER, '.jpg', img_prefix)
    highlight = visual.ImageStim(presenter.window, image=IMG_FOLDER + 'highlight.png')
    buttonbox_img = visual.ImageStim(presenter.window, image=IMG_FOLDER + 'buttonbox.png')
    # get trials from pickle file
    with open(DESIGN_FILENAME, 'r') as infile:
        trials = pickle.load(infile)
        if len(trials) < NUM_RUNS:
            raise ValueError(DESIGN_FILENAME + ' does not contain enough runs.')
        else:
            trials = trials[:NUM_RUNS]
    # randomize images
    random.seed(sid)
    random.shuffle(images)  # status high -> low
    dataLogger.write_json({i: stim._imName for i, stim in enumerate(images)})
    # randomize colors
    DIR_COLORS = {DIRECTIONS[0]: DIR_COLORS[0], DIRECTIONS[1]: DIR_COLORS[1]} if random.randrange(2) == 0 else \
                 {DIRECTIONS[0]: DIR_COLORS[1], DIRECTIONS[1]: DIR_COLORS[0]}
    dataLogger.write_json({direc: COLOR_NAMES[DIR_COLORS[direc]] for direc in DIR_COLORS.keys()})
    color_instr = INSTR_COLOR.format(down_color=COLOR_NAMES[DIR_COLORS[DIRECTIONS[0]]],
                                     up_color=COLOR_NAMES[DIR_COLORS[DIRECTIONS[1]]])
    # reorder runs
    remainder = sid % NUM_RUNS
    trials = trials[remainder:] + trials[:remainder]

    # show instructions
    infoLogger.logger.info('Starting experiment')
    example_images.insert(0, buttonbox_img)
    presenter.show_instructions(INSTR_KEY, TOP_INSTR_POS, example_images, next_instr_text=None,
                                key_to_continue=[TRIGGER, 'space'])  # wait for either space or trigger

    # show trials
    trial_counter = 0
    total_correct_counter = 0
    for run in trials:
        # instructions
        instr = 'You have completed Run #' + str(trials.index(run)) + '.\n\n' \
                if trial_counter > 0 else ''
        instr += 'Run #' + str(trials.index(run) + 1) + ' of ' + str(len(trials)) + ' is starting soon.\n\n' + \
                 'Remember: ' + color_instr
        presenter.show_instructions(instr, next_instr_text=INSTR_NEXT_RUN)  # press space here to continue
        presenter.show_instructions(instr, next_instr_text=None, key_to_continue=TRIGGER)  # then wait for 1 trigger

        # start run
        correct_counter = 0
        for trial in run:
            trial_counter += 1
            data = show_one_trial(trial.copy())
            if data['response'] is not None and data['correct']:
                correct_counter += 1
            dataLogger.write_json(data)
            if trial_counter >= MAX_NUM_TRIALS:
                break
        total_correct_counter += correct_counter
        for _ in range(3):
            presenter.show_instructions('You earned ' + str(correct_counter) + ' point(s) out of ' + str(len(run)) +
                                        ' points possible in this run', next_instr_text=None, key_to_continue=TRIGGER)
        if trial_counter >= MAX_NUM_TRIALS:
            break

    # end
    presenter.show_instructions(INSTR_END, next_instr_text=INSTR_NEXT_RUN)  # press space here to end the program
    infoLogger.logger.info('Experiment ended')
    dataLogger.write_json({'accuracy': float(total_correct_counter) / trial_counter})
