# -*- coding: utf-8 -*-
#
# This file is part of PyGaze - the open-source toolbox for eye tracking
#
# PyGaze is a Python module for easily creating gaze contingent experiments
# or other software (as well as non-gaze contingent experiments/software)
# Copyright (C) 2012-2014 Edwin S. Dalmaijer
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>


from psychopy_util import *
# PyGaze imports
from pygaze.libtime import clock
from pygaze.keyboard import Keyboard
from pygaze.sound import Sound

from pygaze._eyetracker.baseeyetracker import BaseEyeTracker

# we try importing the copy_docstr function, but as we do not really need it
# for a proper functioning of the code, we simply ignore it when it fails to
# be imported correctly
try:
    from pygaze._misc.misc import copy_docstr
except:
    pass

# native imports
import copy
import math
import random

# external imports
from pytribe import EyeTribe


def deg2pix(cmdist, angle, pixpercm):
    """Returns the value in pixels for given values (internal use)

    arguments
    cmdist	-- distance to display in centimeters
    angle		-- size of stimulus in visual angle
    pixpercm	-- amount of pixels per centimeter for display

    returns
    pixelsize	-- stimulus size in pixels (calculation based on size in
               visual angle on display with given properties)
    """

    cmsize = math.tan(math.radians(angle)) * float(cmdist)
    return cmsize * pixpercm


# class
class EyeTribeTracker(BaseEyeTracker):
    """A class for EyeTribeTracker objects"""

    def __init__(self, presenter, screen_size, screen_dist, logfile,
                 eventdetection='pygaze', saccade_velocity_threshold=35,
                 saccade_acceleration_threshold=9500, blink_threshold=130):

        """Initializes the EyeTribeTracker object

        arguments
        window	-- a Presenter instance
        screen_size -- display size in cm
        screen_dist -- distance to the display in cm
        logfile	-- logfile name (string value); note that this is the
                   name for the eye data log file (default = LOGFILE)
        """

        # try to copy docstrings (but ignore it if it fails, as we do
        # not need it for actual functioning of the code)
        try:
            copy_docstr(BaseEyeTracker, EyeTribeTracker)
        except:
            # we're not even going to show a warning, since the copied
            # docstring is useful for code editors; these load the docs
            # in a non-verbose manner, so warning messages would be lost
            pass

        # object properties
        self.presenter = presenter
        self.dispsize = presenter.window.size  # display size in pixels
        self.screensize = screen_size  # display size in cm
        self.screendist = screen_dist  # distance to the display in cm
        self.errorbeep = Sound(osc='saw', freq=100, length=100)

        # output file properties
        self.outputfile = logfile

        # eye tracker properties
        self.connected = False
        self.recording = False
        self.errdist = 2  # degrees; maximal error for drift correction
        self.pxerrdist = 30  # initial error in pixels
        self.maxtries = 100  # number of samples obtained before giving up (for obtaining accuracy and tracker distance information, as well as starting or stopping recording)
        self.prevsample = (-1, -1)
        self.prevps = -1

        # event detection properties
        self.fixtresh = 1.5  # degrees; maximal distance from fixation start (if gaze wanders beyond this, fixation has stopped)
        self.fixtimetresh = 100  # milliseconds; amount of time gaze has to linger within self.fixtresh to be marked as a fixation
        self.spdtresh = saccade_velocity_threshold  # degrees per second; saccade velocity threshold
        self.accthresh = saccade_acceleration_threshold  # degrees per second**2; saccade acceleration threshold
        self.blinkthresh = blink_threshold  # milliseconds; blink detection threshold used in PyGaze method
        self.eventdetection = eventdetection
        self.set_detection_type(self.eventdetection)
        self.weightdist = 10  # weighted distance, used for determining whether a movement is due to measurement error (1 is ok, higher is more conservative and will result in only larger saccades to be detected)

        # connect to the tracker
        self.eyetribe = EyeTribe(logfilename=logfile)

        # get info on the sample rate
        self.samplerate = self.eyetribe._samplefreq
        self.sampletime = 1000.0 * self.eyetribe._intsampletime

        # initiation report
        self.log("pygaze initiation report start")
        self.log("display resolution: %sx%s" % (self.dispsize[0], self.dispsize[1]))
        self.log("display size in cm: %sx%s" % (self.screensize[0], self.screensize[1]))
        self.log("samplerate: %.2f Hz" % self.samplerate)
        self.log("sampletime: %.2f ms" % self.sampletime)
        self.log("fixation threshold: %s degrees" % self.fixtresh)
        self.log("speed threshold: %s degrees/second" % self.spdtresh)
        self.log("acceleration threshold: %s degrees/second**2" % self.accthresh)
        self.log("pygaze initiation report end")

    def calibrate(self, pre_calib_wait=500, calib_wait=1000):

        """Calibrates the eye tracking system

        returns
        success	-- returns True if calibration succeeded, or False if
                   not; in addition a calibration log is added to the
                   log file and some properties are updated (i.e. the
                   thresholds for detection algorithms)
        """

        def get_psychopy_pos(x, y):
            return (x - self.dispsize[0] / 2), (y - self.dispsize[1] / 2)

        # CALIBRATION
        # determine the calibration points
        calibpoints = []
        margin = int(self.dispsize[1] / 10)
        gap_x = int((self.dispsize[0] - 2 * margin) / 3)
        gap_y = int((self.dispsize[1] - 2 * margin) / 3)
        for x in range(4):
            for y in range(4):
                calibpoints.append((margin + gap_x * x, margin + gap_y * y))
        random.shuffle(calibpoints)  # shuffle two lists together

        # show a message
        black_bg = visual.Rect(self.presenter.window, width=2.1, height=2.1, fillColor='black')
        self.presenter.show_instructions('Press space to calibrate\n\nFollow circles with your eyes',
                                         other_stim=[black_bg], next_instr_text=None)
        quited = False

        # Pause the processing of samples during the calibration.
        # self.eyetribe._pause_sample_processing()
        # run until the user is statisfied, or quits
        calibrated = False
        calibresult = None
        while not quited and not calibrated:

            # Clear the existing calibration.
            if self.eyetribe._tracker.get_iscalibrated():
                self.eyetribe._lock.acquire(True)
                self.eyetribe.calibration.clear()
                self.eyetribe._lock.release()

            # Wait for a bit.
            clock.pause(1500)

            # start a new calibration
            if not self.eyetribe._tracker.get_iscalibrating():
                self.eyetribe._lock.acquire(True)
                self.eyetribe.calibration.start(pointcount=len(calibpoints))
                self.eyetribe._lock.release()

            # loop through calibration points
            for cpos in calibpoints:
                # Check whether the calibration is already done.
                # (Not sure how or why, but for some reason some data
                # can persist between calbrations, and the tracker will
                # simply stop allowing further pointstart requests.)
                if self.eyetribe._tracker.get_iscalibrated():
                    break

                # Draw a calibration target.
                point = get_psychopy_pos(cpos[0], cpos[1])
                self.draw_calibration_target(point[0], point[1], black_bg)
                # wait for a bit to allow participant to start looking at
                # the calibration point
                clock.pause(pre_calib_wait)
                # start calibration of point
                self.eyetribe._lock.acquire(True)
                self.eyetribe.calibration.pointstart(cpos[0], cpos[1])
                self.eyetribe._lock.release()
                # wait for a second
                clock.pause(calib_wait)
                # stop calibration of this point
                self.eyetribe._lock.acquire(True)
                self.eyetribe.calibration.pointend()
                self.eyetribe._lock.release()

            # empty display
            self.presenter.draw_stimuli_for_duration([black_bg], duration=None)
            # allow for a bit of calculation time
            # (this is waaaaaay too much)
            clock.pause(1000)

    def show_calibration(self):

        def get_psychopy_pos(x, y):
            return (x - self.dispsize[0] / 2), (y - self.dispsize[1] / 2)

        # get the calibration result
        self.eyetribe._lock.acquire(True)
        calibresult = self.eyetribe._tracker.get_calibresult()
        self.eyetribe._lock.release()

        # results
        # clear the screen
        # self.screen.clear()
        # draw results for each point
        if type(calibresult) != dict:
            stimuli = [visual.TextStim(self.presenter.window, text='Calibration failed.')]
        else:
            stimuli = []
            for p in calibresult['calibpoints']:
                # only draw the point if data was obtained
                if p['state'] > 0:
                    # draw the mean error
                    # self.screen.draw_circle(colour=(252,233,79),
                    # 	pos=(p['cpx'],p['cpy']), r=p['mepix'], pw=0,
                    # 	fill=True)
                    line = visual.Line(win=self.presenter.window, units='pix', lineWidth=0.5,
                                       start=get_psychopy_pos(p['cpx'], p['cpy']),
                                       end=get_psychopy_pos(p['mecpx'], p['mecpy']))
                    # draw the point
                    point = visual.Circle(self.presenter.window, units='pix', lineWidth=1,
                                          lineColor='white', edges=128, radius=3, opacity=1,
                                          pos=get_psychopy_pos(p['cpx'], p['cpy']))
                    # draw the estimated point
                    est_point = visual.Circle(self.presenter.window, units='pix', lineWidth=1,
                                              lineColor='red', edges=128, radius=3, opacity=1,
                                              pos=get_psychopy_pos(p['mecpx'], p['mecpy']))
                    # annotate accuracy
                    text = visual.TextStim(self.presenter.window, text='%.2f' % p['acd'],
                                           pos=get_psychopy_pos(p['cpx'] + 15, p['cpy'] + 15),
                                           height=0.07)
                    stimuli += [text, line, point, est_point]
                # if no data was obtained, draw the point in red
                else:
                    stimuli.append(visual.Circle(self.presenter.window, units='pix', lineWidth=1,
                                                 lineColor='red', edges=4, radius=3, opacity=1,
                                                 pos=get_psychopy_pos(p['cpx'], p['cpy'])))
            # draw result
            if calibresult['result']:
                stimuli.append(visual.TextStim(self.presenter.window, text='Calibration successful',
                                               color='#84ff84', pos=(0, -0.4), height=0.05))
            else:
                stimuli.append(visual.TextStim(self.presenter.window, text='Calibration failed',
                                               color='red', pos=(0, -0.4), height=0.05))
            # draw average accuracy
            stimuli.append(visual.TextStim(self.presenter.window, pos=(0, -0.5), height=0.08,
                                           text='Average error = %.2f degrees' % (calibresult['deg'])))
        # show the results
        self.presenter.draw_stimuli_for_response(stimuli, response_keys=['space'])

        # NOISE CALIBRATION
        # get all error estimates (pixels)
        var = []
        for p in calibresult['calibpoints']:
            # only draw the point if data was obtained
            if p['state'] > 0:
                var.append(p['mepix'])
        noise = sum(var) / float(len(var))
        self.pxdsttresh = (noise, noise)

        # AFTERMATH
        # store some variables
        pixpercm = (self.dispsize[0] / float(self.screensize[0]) + self.dispsize[1] / float(self.screensize[1])) / 2
        screendist = self.screendist
        # calculate thresholds based on tracker settings
        self.accuracy = ((calibresult['Ldeg'], calibresult['Ldeg']), (calibresult['Rdeg'], calibresult['Rdeg']))
        self.pxerrdist = deg2pix(screendist, self.errdist, pixpercm)
        self.pxfixtresh = deg2pix(screendist, self.fixtresh, pixpercm)
        self.pxaccuracy = (
        (deg2pix(screendist, self.accuracy[0][0], pixpercm), deg2pix(screendist, self.accuracy[0][1], pixpercm)),
        (deg2pix(screendist, self.accuracy[1][0], pixpercm), deg2pix(screendist, self.accuracy[1][1], pixpercm)))
        self.pxspdtresh = deg2pix(screendist, self.spdtresh / 1000.0, pixpercm)  # in pixels per millisecond
        self.pxacctresh = deg2pix(screendist, self.accthresh / 1000.0, pixpercm)  # in pixels per millisecond**2

        # calibration report
        self.log("pygaze calibration report start")
        self.log("accuracy (degrees): LX=%s, LY=%s, RX=%s, RY=%s" % (
        self.accuracy[0][0], self.accuracy[0][1], self.accuracy[1][0], self.accuracy[1][1]))
        self.log("accuracy (in pixels): LX=%s, LY=%s, RX=%s, RY=%s" % (
        self.pxaccuracy[0][0], self.pxaccuracy[0][1], self.pxaccuracy[1][0], self.pxaccuracy[1][1]))
        self.log("precision (RMS noise in pixels): X=%s, Y=%s" % (self.pxdsttresh[0], self.pxdsttresh[1]))
        self.log("distance between participant and display: %s cm" % screendist)
        self.log("fixation threshold: %s pixels" % self.pxfixtresh)
        self.log("speed threshold: %s pixels/ms" % self.pxspdtresh)
        self.log("acceleration threshold: %s pixels/ms**2" % self.pxacctresh)
        self.log("pygaze calibration report end")

        return True

    def close(self):

        """Neatly close connection to tracker

        arguments
        None

        returns
        Nothing	-- saves data and sets self.connected to False
        """

        # close connection
        self.eyetribe.close()
        self.connected = False

    def connected(self):

        """Checks if the tracker is connected

        arguments
        None

        returns
        connected	-- True if connection is established, False if not;
                   sets self.connected to the same value
        """

        res = self.eyetribe._tracker.get_trackerstate()

        if res == 0:
            self.connected = True
        else:
            self.connected = False

        return self.connected

    def drift_correction(self, pos=None, fix_triggered=True):

        """Performs a drift check

        arguments
        None

        keyword arguments
        pos			-- (x, y) position of the fixation dot or None for
                       a central fixation (default = None)
        fix_triggered	-- Boolean indicating if drift check should be
                       performed based on gaze position (fix_triggered
                       = True) or on spacepress (fix_triggered =
                       False) (default = False)

        returns
        checked		-- Boolaan indicating if drift check is ok (True)
                       or not (False); or calls self.calibrate if 'q'
                       or 'escape' is pressed
        """

        if pos is None:
            pos = self.dispsize[0] / 2, self.dispsize[1] / 2
        if fix_triggered:
            return self.fix_triggered_drift_correction(pos)
        raise RuntimeError('Don\'t trigger drift correction by key alright?')
        # self.draw_drift_correction_target(pos[0], pos[1])
        # pressed = False
        # while not pressed:
        #     pressed, presstime = self.kb.get_key()
        #     if pressed:
        #         if pressed == 'escape' or pressed == 'q':
        #             print("libeyetribe.EyeTribeTracker.drift_correction: 'q' or 'escape' pressed")
        #             return self.calibrate()
        #         gazepos = self.sample()
        #         if ((gazepos[0] - pos[0]) ** 2 + (gazepos[1] - pos[1]) ** 2) ** 0.5 < self.pxerrdist:
        #             return True
        #         else:
        #             self.errorbeep.play()
        # return False

    def draw_drift_correction_target(self, x, y, bg=None):

        """
        Draws the drift-correction target.

        arguments
        x		--	The X coordinate
        y		--	The Y coordinate
        """
        center = visual.Circle(self.presenter.window, units='pix', lineWidth=0, fillColor='white',
                               edges=128, radius=2, pos=(x, y))
        border = visual.Circle(self.presenter.window, units='pix', lineWidth=0, fillColor='white',
                               edges=128, radius=4, opacity=0.5, pos=(x, y))
        out_border = visual.Circle(self.presenter.window, units='pix', lineWidth=3, fillColor='white',
                                   edges=128, radius=22, opacity=0.1, pos=(x, y))
        stims = [center, border, out_border] if bg is None else [bg, center, border, out_border]
        self.presenter.draw_stimuli_for_duration(stims, duration=None)

    def draw_calibration_target(self, x, y, bg=None):

        self.draw_drift_correction_target(x, y, bg)

    def fix_triggered_drift_correction(self, pos=None, min_samples=10, max_dev=60, reset_threshold=30):

        """Performs a fixation triggered drift correction by collecting
        a number of samples and calculating the average distance from the
        fixation position

        arguments
        None

        keyword arguments
        pos			-- (x, y) position of the fixation dot or None for
                       a central fixation (default = None)
        min_samples		-- minimal amount of samples after which an
                       average deviation is calculated (default = 10)
        max_dev		-- maximal deviation from fixation in pixels
                       (default = 60)
        reset_threshold	-- if the horizontal or vertical distance in
                       pixels between two consecutive samples is
                       larger than this threshold, the sample
                       collection is reset (default = 30)

        returns
        checked		-- Boolaan indicating if drift check is ok (True)
                       or not (False); or calls self.calibrate if 'q'
                       or 'escape' is pressed
        """

        if pos is None:
            pos = self.dispsize[0] / 2, self.dispsize[1] / 2
        self.draw_drift_correction_target(pos[0], pos[1])

        # loop until we have sufficient samples
        lx = []
        ly = []
        while len(lx) < min_samples:

            # pressing escape enters the calibration screen
            # if self.kb.get_key()[0] in ['escape', 'q']:
            #     print("libeyetribe.EyeTribeTracker.fix_triggered_drift_correction: 'q' or 'escape' pressed")
            #     return self.calibrate()

            # collect a sample
            x, y = self.sample()

            if len(lx) == 0 or x != lx[-1] or y != ly[-1]:

                # if present sample deviates too much from previous sample, reset counting
                if len(lx) > 0 and (abs(x - lx[-1]) > reset_threshold or abs(y - ly[-1]) > reset_threshold):
                    lx = []
                    ly = []

                # collect samples
                else:
                    lx.append(x)
                    ly.append(y)

            if len(lx) == min_samples:

                avg_x = sum(lx) / len(lx)
                avg_y = sum(ly) / len(ly)
                d = ((avg_x - pos[0]) ** 2 + (avg_y - pos[1]) ** 2) ** 0.5

                if d < max_dev:
                    return True
                else:
                    lx = []
                    ly = []

    def log(self, msg):

        """Writes a message to the log file

        arguments
        ms		-- a string to include in the log file

        returns
        Nothing	-- uses native log function of iViewX to include a line
                   in the log file
        """

        self.eyetribe.log_message(msg)

    def prepare_drift_correction(self, pos):

        """Not supported for EyeTribeTracker (yet)"""

        print("function not supported yet")

    def pupil_size(self):

        """Return pupil size

        arguments
        None

        returns
        pupil size	-- returns pupil diameter for the eye that is currently
                   being tracked (as specified by self.eye_used) or -1
                   when no data is obtainable
        """

        # get newest pupil size
        ps = self.eyetribe.pupil_size()

        # invalid data
        if ps is None:
            return -1

        # check if the new pupil size is the same as the previous
        if ps != self.prevps:
            # update the pupil size
            self.prevps = copy.copy(ps)

        return self.prevps

    def sample(self):

        """Returns newest available gaze position

        arguments
        None

        returns
        sample	-- an (x,y) tuple or a (-1,-1) on an error
        """

        # get newest sample
        s = self.eyetribe.sample()

        # invalid data
        if s == (None, None):
            return -1, -1

        # check if the new sample is the same as the previous
        if s != self.prevsample:
            # update the current sample
            self.prevsample = copy.copy(s)

        return self.prevsample

    def send_command(self, cmd):

        """Sends a command to the eye tracker

        arguments
        cmd		--	the command to be sent to the EyeTribe, which should
                    be a list with the following information:
                        [category, request, values]

        returns
        Nothing
        """

        self.eyetribe._connection.request(cmd)

    def start_recording(self):

        """Starts recording eye position

        arguments
        None

        returns
        Nothing	-- sets self.recording to True when recording is
                   successfully started
        """

        self.eyetribe.start_recording()
        self.recording = True

    def stop_recording(self):

        """Stop recording eye position

        arguments
        None

        returns
        Nothing	-- sets self.recording to False when recording is
                   successfully started
        """

        self.eyetribe.stop_recording()
        self.recording = False

    def set_detection_type(self, eventdetection):

        """Set the event detection type to either PyGaze algorithms, or
        native algorithms as provided by the manufacturer (only if
        available: detection type will default to PyGaze if no native
        functions are available)

        arguments
        eventdetection	--	a string indicating which detection type
                        should be employed: either 'pygaze' for
                        PyGaze event detection algorithms or
                        'native' for manufacturers algorithms (only
                        if available; will default to 'pygaze' if no
                        native event detection is available)
        returns		--	detection type for saccades, fixations and
                        blinks in a tuple, e.g.
                        ('pygaze','native','native') when 'native'
                        was passed, but native detection was not
                        available for saccade detection
        """

        if eventdetection in ['pygaze', 'native']:
            self.eventdetection = eventdetection

        return 'pygaze', 'pygaze', 'pygaze'

    def wait_for_event(self, event):

        """Waits for event

        arguments
        event		-- an integer event code, one of the following:
                    3 = STARTBLINK
                    4 = ENDBLINK
                    5 = STARTSACC
                    6 = ENDSACC
                    7 = STARTFIX
                    8 = ENDFIX

        returns
        outcome	-- a self.wait_for_* method is called, depending on the
                   specified event; the return values of corresponding
                   method are returned
        """

        if event == 5:
            outcome = self.wait_for_saccade_start()
        elif event == 6:
            outcome = self.wait_for_saccade_end()
        elif event == 7:
            outcome = self.wait_for_fixation_start()
        elif event == 8:
            outcome = self.wait_for_fixation_end()
        elif event == 3:
            outcome = self.wait_for_blink_start()
        elif event == 4:
            outcome = self.wait_for_blink_end()
        else:
            raise Exception("Error in libsmi.SMItracker.wait_for_event: eventcode %s is not supported" % event)

        return outcome

    def wait_for_blink_end(self):

        """Waits for a blink end and returns the blink ending time

        arguments
        None

        returns
        timestamp		--	blink ending time in milliseconds, as
                        measured from experiment begin time
        """

        # # # # #
        # EyeTribe method

        if self.eventdetection == 'native':
            # print warning, since EyeTribe does not have a blink detection
            # built into their API

            print("WARNING! 'native' event detection has been selected, "
                  "but EyeTribe does not offer blink detection; PyGaze algorithm "
                  "will be used")

        # # # # #
        # PyGaze method

        blinking = True

        # loop while there is a blink
        while blinking:
            # get newest sample
            gazepos = self.sample()
            # check if it's valid
            if self.is_valid_sample(gazepos):
                # if it is a valid sample, blinking has stopped
                blinking = False

        # return timestamp of blink end
        return clock.get_time()

    def wait_for_blink_start(self):

        """Waits for a blink start and returns the blink starting time

        arguments
        None

        returns
        timestamp		--	blink starting time in milliseconds, as
                        measured from experiment begin time
        """

        # # # # #
        # EyeTribe method

        if self.eventdetection == 'native':
            # print warning, since EyeTribe does not have a blink detection
            # built into their API

            print("WARNING! 'native' event detection has been selected, "
                  "but EyeTribe does not offer blink detection; PyGaze algorithm "
                  "will be used")

        # # # # #
        # PyGaze method

        blinking = False

        # loop until there is a blink
        while not blinking:
            # get newest sample
            gazepos = self.sample()
            # check if it's a valid sample
            if not self.is_valid_sample(gazepos):
                # get timestamp for possible blink start
                t0 = clock.get_time()
                # loop until a blink is determined, or a valid sample occurs
                while not self.is_valid_sample(self.sample()):
                    # check if time has surpassed BLINKTHRESH
                    if clock.get_time() - t0 >= self.blinkthresh:
                        # return timestamp of blink start
                        return t0

    def wait_for_fixation_end(self):

        """Returns time and gaze position when a fixation has ended;
        function assumes that a 'fixation' has ended when a deviation of
        more than self.pxfixtresh from the initial fixation position has
        been detected (self.pxfixtresh is created in self.calibration,
        based on self.fixtresh, a property defined in self.__init__)

        arguments
        None

        returns
        time, gazepos	-- time is the starting time in milliseconds (from
                       expstart), gazepos is a (x,y) gaze position
                       tuple of the position from which the fixation
                       was initiated
        """

        # # # # #
        # EyeTribe method

        if self.eventdetection == 'native':
            # print warning, since EyeTribe does not have a blink detection
            # built into their API

            print("WARNING! 'native' event detection has been selected, \
				but EyeTribe does not offer fixation detection; \
				PyGaze algorithm will be used")

        # # # # #
        # PyGaze method

        # function assumes that a 'fixation' has ended when a deviation of more than fixtresh
        # from the initial 'fixation' position has been detected

        # get starting time and position
        stime, spos = self.wait_for_fixation_start()

        # loop until fixation has ended
        while True:
            # get new sample
            npos = self.sample()  # get newest sample
            # check if sample is valid
            if self.is_valid_sample(npos):
                # check if sample deviates to much from starting position
                if (npos[0] - spos[0]) ** 2 + (npos[1] - spos[1]) ** 2 > self.pxfixtresh ** 2:  # Pythagoras
                    # break loop if deviation is too high
                    break

        return clock.get_time(), spos

    def wait_for_fixation_start(self):

        """Returns starting time and position when a fixation is started;
        function assumes a 'fixation' has started when gaze position
        remains reasonably stable (i.e. when most deviant samples are
        within self.pxfixtresh) for five samples in a row (self.pxfixtresh
        is created in self.calibration, based on self.fixtresh, a property
        defined in self.__init__)

        arguments
        None

        returns
        time, gazepos	-- time is the starting time in milliseconds (from
                       expstart), gazepos is a (x,y) gaze position
                       tuple of the position from which the fixation
                       was initiated
        """

        # # # # #
        # EyeTribe method

        if self.eventdetection == 'native':
            # print warning, since EyeTribe does not have a fixation start
            # detection built into their API (only ending)

            print("WARNING! 'native' event detection has been selected, \
				but EyeTribe does not offer fixation detection; \
				PyGaze algorithm will be used")

        # # # # #
        # PyGaze method

        # function assumes a 'fixation' has started when gaze position
        # remains reasonably stable for self.fixtimetresh

        # get starting position
        spos = self.sample()
        while not self.is_valid_sample(spos):
            spos = self.sample()

        # get starting time
        t0 = clock.get_time()

        # wait for reasonably stable position
        moving = True
        while moving:
            # get new sample
            npos = self.sample()
            # check if sample is valid
            if self.is_valid_sample(npos):
                # check if new sample is too far from starting position
                if (npos[0] - spos[0]) ** 2 + (npos[1] - spos[1]) ** 2 > self.pxfixtresh ** 2:  # Pythagoras
                    # if not, reset starting position and time
                    spos = copy.copy(npos)
                    t0 = clock.get_time()
                # if new sample is close to starting sample
                else:
                    # get timestamp
                    t1 = clock.get_time()
                    # check if fixation time threshold has been surpassed
                    if t1 - t0 >= self.fixtimetresh:
                        # return time and starting position
                        return t1, spos

    def wait_for_saccade_end(self):

        """Returns ending time, starting and end position when a saccade is
        ended; based on Dalmaijer et al. (2013) online saccade detection
        algorithm

        arguments
        None

        returns
        endtime, startpos, endpos	-- endtime in milliseconds (from
                               expbegintime); startpos and endpos
                               are (x,y) gaze position tuples
        """

        # # # # #
        # EyeTribe method

        if self.eventdetection == 'native':
            # print warning, since EyeTribe does not have a blink detection
            # built into their API

            print("WARNING! 'native' event detection has been selected, "
                  "but EyeTribe does not offer saccade detection; PyGaze "
                  "algorithm will be used")

        # # # # #
        # PyGaze method

        # get starting position (no blinks)
        t0, spos = self.wait_for_saccade_start()
        # get valid sample
        prevpos = self.sample()
        while not self.is_valid_sample(prevpos):
            prevpos = self.sample()
        # get starting time, intersample distance, and velocity
        t1 = clock.get_time()
        s = ((prevpos[0] - spos[0]) ** 2 + (
                    prevpos[1] - spos[1]) ** 2) ** 0.5  # = intersample distance = speed in px/sample
        v0 = s / (t1 - t0)

        # run until velocity and acceleration go below threshold
        saccadic = True
        while saccadic:
            # get new sample
            newpos = self.sample()
            t1 = clock.get_time()
            if self.is_valid_sample(newpos) and newpos != prevpos:
                # calculate distance
                s = ((newpos[0] - prevpos[0]) ** 2 + (newpos[1] - prevpos[1]) ** 2) ** 0.5  # = speed in pixels/sample
                # calculate velocity
                v1 = s / (t1 - t0)
                # calculate acceleration
                a = (v1 - v0) / (
                            t1 - t0)  # acceleration in pixels/sample**2 (actually is v1-v0 / t1-t0; but t1-t0 = 1 sample)
                # check if velocity and acceleration are below threshold
                if v1 < self.pxspdtresh and (a > -1 * self.pxacctresh and a < 0):
                    saccadic = False
                    epos = newpos[:]
                    etime = clock.get_time()
                # update previous values
                t0 = copy.copy(t1)
                v0 = copy.copy(v1)
            # udate previous sample
            prevpos = newpos[:]

        return etime, spos, epos

    def wait_for_saccade_start(self):

        """Returns starting time and starting position when a saccade is
        started; based on Dalmaijer et al. (2013) online saccade detection
        algorithm

        arguments
        None

        returns
        endtime, startpos	-- endtime in milliseconds (from expbegintime);
                       startpos is an (x,y) gaze position tuple
        """

        # # # # #
        # EyeTribe method

        if self.eventdetection == 'native':
            # print warning, since EyeTribe does not have a blink detection
            # built into their API

            print("WARNING! 'native' event detection has been selected, "
                  "but EyeTribe does not offer saccade detection; PyGaze "
                  "algorithm will be used")

        # # # # #
        # PyGaze method

        # get starting position (no blinks)
        newpos = self.sample()
        while not self.is_valid_sample(newpos):
            newpos = self.sample()
        # get starting time, position, intersampledistance, and velocity
        t0 = clock.get_time()
        prevpos = newpos[:]
        s = 0
        v0 = 0

        # get samples
        saccadic = False
        while not saccadic:
            # get new sample
            newpos = self.sample()
            t1 = clock.get_time()
            if self.is_valid_sample(newpos) and newpos != prevpos:
                # check if distance is larger than precision error
                sx = newpos[0] - prevpos[0]
                sy = newpos[1] - prevpos[1]
                if (sx / self.pxdsttresh[0]) ** 2 + (sy / self.pxdsttresh[
                    1]) ** 2 > self.weightdist:  # weigthed distance: (sx/tx)**2 + (sy/ty)**2 > 1 means movement larger than RMS noise
                    # calculate distance
                    s = ((sx) ** 2 + (sy) ** 2) ** 0.5  # intersampledistance = speed in pixels/ms
                    # calculate velocity
                    v1 = s / (t1 - t0)
                    # calculate acceleration
                    a = (v1 - v0) / (t1 - t0)  # acceleration in pixels/ms**2
                    # check if either velocity or acceleration are above threshold values
                    if v1 > self.pxspdtresh or a > self.pxacctresh:
                        saccadic = True
                        spos = prevpos[:]
                        stime = clock.get_time()
                    # update previous values
                    t0 = copy.copy(t1)
                    v0 = copy.copy(v1)

                # udate previous sample
                prevpos = newpos[:]

        return stime, spos

    def is_valid_sample(self, gazepos):

        """Checks if the sample provided is valid, based on EyeTribe specific
        criteria (for internal use)

        arguments
        gazepos		--	a (x,y) gaze position tuple, as returned by
                        self.sample()

        returns
        valid		--	a Boolean: True on a valid sample, False on
                        an invalid sample
        """

        # return False if a sample is invalid
        if gazepos == (None, None) or gazepos == (-1, -1):
            return False

        # in any other case, the sample is valid
        return True
