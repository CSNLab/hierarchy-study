# Numbers
NUM_RUNS = 2
NUM_TRIALS_PER_RUN = 40
NUM_STEPS_PER_TRIAL = 4
# MRI stuff
TRIGGER = '5'
# Paths
LOG_FOLDER = 'log/'
# Times
STEP_TIMES = [0.5, 0.75, 1]
INITIAL_STEP_TRIGGERS = 4  # for the first central fixation in a run
ITIS = [6, 7, 8]
ITI_PART1 = 3
AFTER_RUN_TRIGGERS = 7
# Distances (in pixel)
STEP_DISTANCE = 74
LARGE_JITTER_MAX = 25
SMALL_JITTER_MAX = 15
# Instructions
INSTR = 'Run #{} of ' + str(NUM_RUNS) + ' is starting soon.\n\n' \
        'Please follow the white cross with your eyes as it moves around the screen.'
NEXT_RUN_INSTR = 'Waiting for the experimenter...'
