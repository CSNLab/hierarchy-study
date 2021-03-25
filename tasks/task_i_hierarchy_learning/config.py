# Numbers
NUM_BLOCKS = 12
NUM_BLOCKS_AFTER_ACC_CHECK = 2
NUM_CYCLES_PER_BLOCK_TRAIN = 2
NUM_CYCLES_PER_BLOCK_TEST = 1
TRAIN_PAIRS = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 8)]
TEST_PAIRS = [(1, 3), (1, 4), (2, 4), (2, 5), (3, 5), (3, 6), (4, 6), (4, 7)]
TRAIN_POINTS = 10
TEST_POINTS = 100
MAX_ADDITIONAL_BLOCKS = 2
# Paths
IMG_FOLDER = 'img/'
DATA_FOLDER = 'data/'
# Times
FIXATION_TIME = 1
FIRST_IMG_TIME = 1.5
IMG_INTERVAL = 0.05
SECOND_IMG_TIME = 1.5
IMG_OPTION_TIME = 1
NUM_REFRESHS_PER_IMG = 20
FEEDBACK_TIME = 1
# Colors
FEEDBACK_RED = '#FF0000'
FEEDBACK_GREEN = '#84ff84'
# Other stuff
RESPONSE_KEY = 'space'  # changed this together with the line below
RESPONSE_CHAR = ' '     # changed this together with the line above
NEXT_PAGE_KEY = 'n'
FEEDBACK_POSITION = (0, -0.5)
TOP_INSTR_POSITION = (0, 0.7)
CIRCLE_RADIUS = 250  # in pixel
CIRCLE_EDGES = 128
IMG_HALF_SIDE = 150  # in pixel
# Strings
INSTR_1 = ['We\'re interested in individual differences in how people learn about social information.',
           'You\'re going to see pictures we\'ve taken of 9 different individuals who are all members of an '
           'organization.',
           'There are 2 parts to this experiment. In this first part, you will need to learn which individuals are '
           'more powerful in the organization. '
           'In the second part, you will use the knowledge you acquired during this part to make judgments '
           'about individuals.']
INSTR_2 = ['To learn about the organization, you will see pairs of people displayed one after another (sequentially) '
           'like this:',
           'After you see the 2 faces presented sequentially, you will see the following instructions '
           'before selecting your choice:',
           'Then you can make a choice by PRESSING and HOLDING ' + RESPONSE_KEY.upper() + '. '
           'Once you press the key, the two people will be displayed again, in the same order that they were '
           'presented before. When you see the person you\'d like to choose, RELEASE the key to select that person.\n'
           'The size of the circle indicates how long the current person will remain on the screen, '
           'which looks like this:',
           'Now you can try this in a few practice trials. Select the person who WEARS GLASSES in these practice trials'
           ' -- just press and hold ' + RESPONSE_KEY + ', and release it when you see the person you want to choose.']
INSTR_3 = 'You\'ve completed the practice trials! Now we\'ll start the task. Remember, your job is to choose the ' \
          'person who is more powerful in the organization.'
INSTR_4 = 'Thank you for completing this task!'

INSTR_TRAIN = ['Get ready for Training trials.',
               'In Training Trials, you\'ll see pairs of people who are most similar in terms of how much power '
               'they have in the organization.\n\n'
               'If you respond correctly, you\'ll win ' + str(TRAIN_POINTS) + ' points. '
               'Otherwise, you\'ll lose ' + str(TRAIN_POINTS) + ' points.']
INSTR_TEST = ['Get ready for Test trials',
              'In Test Trials, you\'ll be presented with pairs of people who are more different from each other '
              '(compared to the Training Trials) in terms of how much power they have - here you\'ll have to use '
              'your judgement to choose the correct one.\n\n'
              'If you respond correctly, you\'ll win ' + str(TEST_POINTS) + ' points. '
              'Otherwise, you\'ll lose ' + str(TEST_POINTS) + ' points.',
              'You will also be asked to rate your confidence in your choices during test trials on a scale of 1-3:\n\n'
              '1 = You\'re guessing entirely\n' +
              '2 = You have some idea but are not sure\n' +
              '3 = You\'re more than 90% certain\n\n' +
              'Your confidence ratings will not affect your final score, but try to answer as accurately as possible.']
INSTR_PRESS = 'Hold down ' + RESPONSE_KEY.upper() + ' to cycle through the 2 response options, ' \
              'and release it when you see the person you want to choose.'

FEEDBACK_RIGHT = '+ {} points'
FEEDBACK_WRONG = '- {} points'

INSTR_REINFORCE = ['In this pair, the person below is relatively POWER', 'FUL', 'LESS']
INSTR_REINFORCE_PRAC = ['In this pair, the person below is ', 'wearing glasses', 'not wearing glasses']

LIKERT_SCALE_QUESTION = 'Please rate your confidence'
LIKERT_SCALE_LABELS = ('Guessing entirely', 'Not sure but have some idea', '90%-100% certain')
