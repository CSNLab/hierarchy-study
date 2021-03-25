#!/usr/bin/env python

from psychopy_util import *
from config import *
import dumb_text_input as dt
import copy


def show_one_trial(param, question=False):
    # 0 anchor face
    presenter.draw_stimuli_for_duration(images[param['anchor']], FACE_TIME)
    # 1 fixation
    presenter.show_fixation(FIXATION_TIME)
    # 2 number
    num_stim = visual.TextStim(presenter.window, str(param['distance']), height=1, color=DIR_COLORS[param['direction']])
    presenter.draw_stimuli_for_duration(num_stim, NUMBER_TIME)
    # 3 fixation (mental navigation)
    presenter.show_fixation(BLANK_TIME)
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
    selection_time = float('inf') if question else SELECTION_TIME
    highlight.size = (option_img_size[0] * 1.1, option_img_size[1] * 1.1)
    response = presenter.select_from_stimuli(option_stims, options, RESPONSE_KEYS, selection_time, 0, highlight,
                                             lambda x: x == correct_option, None, resp_feedback, no_resp_feedback,
                                             FEEDBACK_TIME)
    # 4.2 recover central positions
    for option in option_stims:
        option.pos = presenter.CENTRAL_POS
        option.size = None
    # - question
    if question:
        anchors = [visual.ImageStim(presenter.window, images[param['anchor']]._imName) for i in range(4)]
        if param['distance'] == 2:
            for i, pos in enumerate(two_step_anchor_pos):
                anchors[i].pos = pos
                anchors[i].size = two_step_img_size
            stims = two_step_stim + anchors
        else:
            for i, pos in enumerate(three_step_anchor_pos):
                anchors[i].pos = pos
                anchors[i].size = three_step_img_lg
            stims = three_step_stim + anchors
        visualization = presenter.select_from_stimuli(stims, ('down', 'up', 'left', 'right', 'none'), MULTI_CHOICE_KEYS,
                                                      feedback_time=0)
        param['visualization'] = visualization
    # 6 interval between trials
    presenter.show_fixation(random.choice(TRIAL_INTERVALS))
    # return
    param['options'] = options
    if response is None:
        param['response'] = None
    else:
        param.update(response)
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
    trials = [list(unique_trials) for i in range(NUM_RUNS)]
    for prac in practices:
        prac['answer_index'] = random.randrange(4)
    ans_indexes = [[i for _ in range(int(len(unique_trials) / 4 / 2)) for i in range(4)],
                   [i for _ in range(int(len(unique_trials) / 4 / 2)) for i in range(4)]]  # up & down trials
    for run in trials:
        random.shuffle(ans_indexes[0])
        random.shuffle(ans_indexes[1])
        counters = [0, 0]
        for trial in run:
            direction = DIRECTIONS.index(trial['direction'])  # 0 or 1
            trial['answer_index'] = ans_indexes[direction][counters[direction]]
            counters[direction] += 1
        random.shuffle(run)
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


def construct_questions():
    quesion = visual.TextStim(presenter.window, INSTR_MULTI_CHOICE_Q, pos=(0, 0.9), height=0.08, wrapWidth=1.95)
    option_v = visual.TextStim(presenter.window, 'None of the above', pos=(0, -0.85))
    # arrange stimuli
    grey = '#727272'
    shapes = [visual.Rect(presenter.window, width=0.2, height=1, pos=(-0.6, 0), lineWidth=0, fillColor=grey),
              visual.Rect(presenter.window, width=0.2, height=1, pos=(-0.2, 0), lineWidth=0, fillColor=grey),
              visual.Rect(presenter.window, width=0.6, height=0.3, pos=(0.4, 0.35), lineWidth=0, fillColor=grey),
              visual.Rect(presenter.window, width=0.6, height=0.3, pos=(0.4, -0.35), lineWidth=0, fillColor=grey),
              visual.Rect(presenter.window, width=0.6, height=0.15, pos=(0, -0.85), lineWidth=0, fillColor=grey)]
    option_pos = [(-0.73, 0.53), (-0.33, 0.53), (0.07, 0.53), (0.07, -0.17), (-0.33, -0.75)]
    option_letters = [visual.TextStim(presenter.window, str(k.upper()), pos=pos, color='yellow')
                      for k, pos in zip(MULTI_CHOICE_KEYS, option_pos)]
    #  a) 2 steps
    two_step_img_size = (0.12, 0.12 * presenter.window.size[0] / presenter.window.size[1])
    two_step_stim = [copy.copy(shape) for shape in shapes]
    two_step_stim += [quesion, option_v]
    two_step_stim += option_letters
    two_step_arrows = []
    for i in range(2):
        two_step_arrows += presenter.load_all_images(IMG_FOLDER, '.png', 'arrow')
    two_arrow_pos = [(-0.6, 0.175), (0.3, 0.35), (0.3, -0.35), (-0.2, -0.175),  # down, left, right, up
                     (-0.6, -0.175), (0.5, 0.35), (0.5, -0.35), (-0.2, 0.175)]  # down, left, right, up
    for stim, pos in zip(two_step_arrows, two_arrow_pos):
        stim.pos = pos
    two_step_stim += two_step_arrows
    two_step_stim += [visual.ImageStim(presenter.window, image=IMG_FOLDER + 'person.png', size=two_step_img_size)
                      for i in range(4)]
    two_step_stim += [visual.ImageStim(presenter.window, image=IMG_FOLDER + 'person_in_q.png',
                                       size=two_step_img_size) for i in range(4)]
    person_pos = [(-0.6, 0), (0.395, 0.35), (0.395, -0.35), (-0.2, 0),  # person
                  (-0.6, -0.35), (0.195, 0.35), (0.595, -0.35), (-0.2, 0.35)]  # person in question
    for i, pos in enumerate(person_pos):
        two_step_stim[i - 8].pos = pos
    two_step_anchor_pos = [(-0.6, 0.35), (0.595, 0.35), (0.195, -0.35), (-0.2, -0.35)]  # down, left, right, up
    #  b) 3 steps
    three_step_img_lg = (0.1, 0.1 * presenter.window.size[0] / presenter.window.size[1])
    three_step_img_sm = (0.08, 0.08 * presenter.window.size[0] / presenter.window.size[1])
    three_step_stim = shapes
    three_step_stim += [quesion, option_v]
    three_step_stim += option_letters
    three_step_arrows = []
    for i in range(3):
        three_step_arrows += presenter.load_all_images(IMG_FOLDER, '.png', 'arrow')
    three_arrow_pos = [(-0.6, 0.245), (0.25, 0.35), (0.25, -0.35), (-0.2, -0.245),  # down, left, right, up
                       (-0.6, 0), (0.4, 0.35), (0.4, -0.35), (-0.2, 0),  # down, left, right, up
                       (-0.6, -0.245), (0.55, 0.35), (0.55, -0.35), (-0.2, 0.245)]  # down, left, right, up
    for stim, pos in zip(three_step_arrows, three_arrow_pos):
        stim.pos = pos
        stim.size = (0.05, 0.05 * presenter.window.size[0] / presenter.window.size[1])
    three_step_stim += three_step_arrows
    three_step_stim += [visual.ImageStim(presenter.window, image=IMG_FOLDER + 'person.png', size=three_step_img_sm)
                        for i in range(8)]
    three_step_stim += [visual.ImageStim(presenter.window, image=IMG_FOLDER + 'person_in_q.png',
                                         size=three_step_img_lg) for i in range(4)]
    person_pos = [(-0.6, 0.125), (0.325, 0.35), (0.325, -0.35), (-0.2, 0.125),  # person
                  (-0.6, -0.125), (0.475, 0.35), (0.475, -0.35), (-0.2, -0.125),  # person
                  (-0.6, -0.38), (0.17, 0.35), (0.63, -0.35), (-0.2, 0.38)]  # person in question
    for i, pos in enumerate(person_pos):
        three_step_stim[i - 12].pos = pos
    three_step_anchor_pos = [(-0.6, 0.38), (0.63, 0.35), (0.17, -0.35), (-0.2, -0.38)]  # down, left, right, up
    return two_step_stim, two_step_img_size, two_step_anchor_pos, \
           three_step_stim, three_step_img_lg, three_step_img_sm, three_step_anchor_pos


if __name__ == '__main__':
    # subject ID dialog
    sinfo = {'ID': '',
             'Gender': ['Female', 'Male'],
             'Age': '',
             'Type': ['Normal', 'After navigation'],
             'Screen': ['Exp', 'Test']}
    show_form_dialog(sinfo, validation, order=['ID', 'Gender', 'Age', 'Type', 'Screen'])
    sid = int(sinfo['ID'])
    img_prefix = sinfo['Gender'][0]

    # create data file
    file_postfix = '' if sinfo['Type'] == 'Normal' else '_questions'
    dataLogger = DataHandler(DATA_FOLDER, str(sid) + file_postfix + '.txt')
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
    #     img.size = option_img_size
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

    # show instructions
    if sinfo['Type'] != 'After navigation':  # normal
        presenter.show_instructions(INSTR_0)
        presenter.show_instructions(color_instr)
        presenter.show_instructions(INSTR_1)
        presenter.show_instructions(INSTR_2, TOP_INSTR_POS, example_images, next_instr_pos=(0, -0.9))
        show_key_mapping()
        # practice
        presenter.show_instructions(INSTR_PRACTICE)
        practices = random.sample(practices, NUM_PRACTICE_TRIALS)
        for trial in practices:
            presenter.show_instructions(color_instr)
            data = show_one_trial(trial.copy())
            data['practice'] = True
            dataLogger.write_data(data)
    # show trials
    if sinfo['Type'] == 'Normal':
        total_correct_counter = 0
        presenter.show_instructions(INSTR_4)
        trial_counter = 0
        for run in trials:
            # instructions
            presenter.show_instructions('Block #' + str(trials.index(run) + 1) + '\n\nRemember: ' + color_instr)
            # start run
            correct_counter = 0
            for trial in run:
                trial_counter += 1
                data = show_one_trial(trial.copy())
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
        accuracy = float(total_correct_counter)/len(trials)/len(trials[0])  # overall accuracy
        print('accuracy', accuracy)
        dataLogger.write_data({'overall_accuracy': accuracy})

    # show a free response question (strategy)
    if sinfo['Type'] != 'Normal':
        q_stim = visual.TextStim(presenter.window, INSTR_OPEN_ENDED_Q1, pos=(0, 0.65), height=0.09, wrapWidth=1.9)
        cont_stim = visual.TextStim(presenter.window, INSTR_OPEN_ENDED_CONT, pos=(0, -0.9), height=0.08, wrapWidth=1.5)
        text_in = dt.DumbTextInput(presenter.window, width=1.5, height=1, pos=(0, -0.2), other_stim=[q_stim, cont_stim])
        warning_color = 0
        while True:
            response, rt, last_key = text_in.wait_key()
            response = response.strip()
            if last_key[0] == 'return' and last_key[1]['command']:
                if len(response) == 0:
                    warning = visual.TextStim(presenter.window, WARNING_OPEN_ENDED_Q, pos=(-0.75, 0.35), height=0.04,
                                              color='yellow' if warning_color == 0 else 'red', alignHoriz='left')
                    text_in.add_other_stim(warning)
                    warning_color = 1 - warning_color  # toggle
                else:
                    break
        dataLogger.write_data({'response': response, 'rt': rt})

    # show multiple choice questions
    if sinfo['Type'] != 'Normal':  # after navigation or after mouse tracker
        two_step_stim, two_step_img_size, two_step_anchor_pos, \
        three_step_stim, three_step_img_lg, three_step_img_sm, three_step_anchor_pos = construct_questions()
        # generate trials
        question_trials = [{
            'anchor': random.randint(NUM_FACES / 2 - 1, NUM_FACES / 2 + 1),
            'direction': DIRECTIONS[0] if i % 2 == 0 else DIRECTIONS[1],
            'distance': 2 if i < 2 else 3,
            'answer_index': i
        } for i in range(4)]
        random.shuffle(question_trials)
        # start
        which_task_instr = INSTR_WHICH_TASK[1] if sinfo['Type'] == 'After navigation' else INSTR_WHICH_TASK[0]
        presenter.show_instructions(INSTR_QUESTION.format(which_task=which_task_instr) + '\n\nRemember: ' + color_instr)
        if sinfo['Type'] == 'After navigation':  # show a reminder
            show_key_mapping()
        for q in question_trials:
            data = show_one_trial(q, True)
            dataLogger.write_data(data)

    # another free response question (what could make things easier)
    if sinfo['Type'] == 'After navigation':
        q_stim = visual.TextStim(presenter.window, INSTR_OPEN_ENDED_Q2, pos=(0, 0.65), wrapWidth=1.5)
        cont_stim = visual.TextStim(presenter.window, INSTR_OPEN_ENDED_CONT, pos=(0, -0.9), height=0.08, wrapWidth=1.5)
        text_in = dt.DumbTextInput(presenter.window, width=1.5, height=1, pos=(0, -0.2), other_stim=[q_stim, cont_stim])
        warning_color = 0
        while True:
            response, rt, last_key = text_in.wait_key()
            response = response.strip()
            if last_key[0] == 'return' and last_key[1]['command']:
                if len(response) == 0:
                    warning = visual.TextStim(presenter.window, WARNING_OPEN_ENDED_Q, pos=(-0.75, 0.35), height=0.04,
                                              color='yellow' if warning_color == 0 else 'red', alignHoriz='left')
                    text_in.add_other_stim(warning)
                    warning_color = 1 - warning_color  # toggle
                else:
                    break
        dataLogger.write_data({'response': response, 'rt': rt})

    # end
    presenter.show_instructions(INSTR_END)
