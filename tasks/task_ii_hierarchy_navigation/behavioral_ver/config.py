# Experimental parameters
NUM_PRACTICE_TRIALS = 5
MAX_NUM_TRIALS = 999  # -> just to test the program
NUM_RUNS = 3
NUM_FACES = 9
NUM_OPTIONS = 4
DIRECTIONS = ('D', 'U')
ANCHOR_INDEXES = (2, 3, 4, 5, 6)
MIN_DISTANCE = 2
MAX_DISTANCE = 4
RESPONSE_KEYS = ('up', 'down', 'left', 'right')
MULTI_CHOICE_KEYS = ('a', 's', 'e', 'd', 'x')  # down, left, right, up, none
# Colors
DIR_COLORS = ('#f0ad4e', '#5bc0de')
COLOR_NAMES = {'#f0ad4e': 'Orange', '#5bc0de': 'Blue'}
RED = '#ff0000'
GREEN = '#84ff84'
BLACK = '#000000'
# Paths
IMG_FOLDER = 'img/'
DATA_FOLDER = 'data/'
# Positions & Lengths
TOP_INSTR_POS = (0, 0.85)
OPTION_IMG_DIST = 620  # horizontal or vertical distance from images to screen center, in pixels
OPTION_IMG_HEIGHT = 0.5
# Times
FACE_TIME = 1
FIXATION_TIME = 0.5
NUMBER_TIME = 0.5
BLANK_TIME = 6
SELECTION_TIME = 1.5
FEEDBACK_TIME = 1.5
TRIAL_INTERVALS = (2, 3)
# Strings
FEEDBACK_RIGHT = IMG_FOLDER + 'correct.png'
FEEDBACK_WRONG = IMG_FOLDER + 'wrong.png'
FEEDBACK_SLOW = 'Too slow. Please respond faster.'
# Instructions
INSTR_0 = ['Welcome!\n\nIn this task, you will be asked about the organization you\'ve learned about.',
           'Each trial will begin with a "reference" person.\n\nA few seconds later, a number will appear.',
           'Your job is to figure out who is that number of steps MORE or LESS powerful than the "reference" person '
           'in the organization.\n\nThe color of the number indicates whether you need to figure out who is that '
           'number of steps MORE or LESS powerful than the reference person.']
INSTR_COLOR = '{down_color} numbers mean figure out who is that number of steps LESS powerful than the reference ' \
              'person in the organization.\n\n{up_color} numbers mean figure out who is that number of steps MORE ' \
              'powerful than the reference person in the organization.'
INSTR_1 = 'You\'ll have a few seconds to figure out your response. \n\nAfter that, 4 faces will be briefly ' \
          'presented as possible response options. They won\'t be on the screen for very long, so it\'s important ' \
          'to figure out your response before they appear so that you can respond in time.'
INSTR_2 = 'When the response options are presented, they\'ll look like this:'
INSTR_3 = 'Press one of the arrow keys to select a given person, like this:'
INSTR_PRACTICE = 'We\'ll start by doing some practice trials.\n\nIn these practice trials, you\'ll be reminded of ' \
                 'the meaning of the numbers\' colors before each trial (but this won\'t happen in the main task).'
INSTR_4 = 'You\'ve completed all of the practice trials.\n\nNow we\'ll begin the task.'
INSTR_QUESTION = 'In the next part, you will be asked to perform {which_task}, and then answer a few questions.'
INSTR_WHICH_TASK = ('the same task', 'a few trials of the second task again')  # (normal/after mt, after navigation)
INSTR_END = 'The task is complete!\nThank you for participating!'
INSTR_OPEN_ENDED_Q1 = 'We\'d like to know more about the strategies that different people use to do the second task.\n' \
                      'What strategies (e.g., memory tricks, ways of visualizing the information), if any, did you ' \
                      'use to arrive at your response on each trial?\n' \
                      'Please describe what it felt like you were doing during the period after the reference person ' \
                      'and number appeared, but before the 4 response choices appeared.'
INSTR_OPEN_ENDED_CONT = 'Press command + enter to submit and continue'
WARNING_OPEN_ENDED_Q = 'Your response is important to us. Please write something.'
INSTR_MULTI_CHOICE_Q = 'The options below illustrate a few ways that people visualize this problem. ' \
                       'Please press X, S, E, D or A to choose an option that is most similar to your approach on ' \
                       'this trial.'
INSTR_OPEN_ENDED_Q2 = 'If you found this task to be difficult, is there anything we could change that might make it ' \
                      'easier?'
