# Experimental parameters
MAX_NUM_TRIALS = 999  # -> just to test the program
NUM_RUNS = 6
NUM_TRIALS_PER_RUN = 24
NUM_FACES = 9
NUM_OPTIONS = 4
DIRECTIONS = ('D', 'U')
ANCHOR_INDEXES = (2, 3, 4, 5, 6)
MIN_DISTANCE = 2
MAX_DISTANCE = 4
RESPONSE_KEYS = ('4', '2', '3', '1')  # order should be up, down, left, right
MULTI_CHOICE_KEYS = ('a', 's', 'e', 'd', 'x')  # down, left, right, up, none
TRIGGER = '5'
# Colors
DIR_COLORS = ('#f0ad4e', '#5bc0de')
COLOR_NAMES = {'#f0ad4e': 'Orange', '#5bc0de': 'Blue'}
RED = '#ff0000'
GREEN = '#84ff84'
BLACK = '#000000'
# Paths
IMG_FOLDER = 'img/'
DATA_FOLDER = 'data/'
LOG_FOLDER = 'log/'
DESIGN_FILENAME = 'exp_designs.pkl'
# Positions & Lengths
TOP_INSTR_POS = (0, 0.85)
OPTION_IMG_DIST = 220  # horizontal or vertical distance from images to screen center, in pixels
OPTION_IMG_HEIGHT = 0.5
# Times
FACE_TRIGGER = 1
FIXATION_TIME = 0.5
NUMBER_TRIGGER = 1
BLANK_TRIGGER = 6
SELECTION_TIME = 1.5
FEEDBACK_TRIGGER = 2
# Strings
FEEDBACK_RIGHT = IMG_FOLDER + 'correct.png'
FEEDBACK_WRONG = IMG_FOLDER + 'wrong.png'
FEEDBACK_SLOW = 'Too slow. Please respond faster.'
# Instructions
INSTR_COLOR = '{down_color} numbers mean figure out who is that number of steps LESS powerful than the reference ' \
              'person in the organization.\n\n{up_color} numbers mean figure out who is that number of steps MORE ' \
              'powerful than the reference person in the organization.'
INSTR_KEY = 'Press one of the buttons to select a given person, like this:'
INSTR_NEXT_RUN = 'Waiting for the experimenter...'
INSTR_END = 'This task is complete!\nThank you!'
