"""
EMG control of AudioMulch Metasurface.

During calibration phase, the user is asked to reproduce a series of
movements to determine the amplitude range of the used EMG channels.

During control, the user freely user their muscles to control the cursor
position on the Metasurface.

The following input devices are supported (mutually exclusive):

trigno
    Trigno EMG system.
myo
    Myo armband.
noise
    Noise generator.

All configuration settings are stored and loaded from an external configuration
file (``config.ini``).
"""

import os
import time
from argparse import ArgumentParser
from configparser import ConfigParser

import numpy as np
from scipy.signal import butter
import joblib

from axopy.experiment import Experiment
from axopy.task import Task
from axopy import util
from axopy.timing import Counter, Timer
from axopy.gui.canvas import Canvas, Text
from axopy.pipeline import (Callable, Windower, Filter, Pipeline,
                            FeatureExtractor, Ensure2D, Transformer)
from axopy.messaging import Transmitter as AxopyTransmitter

from axopy.features import MeanAbsoluteValue, LogVar

from musmus.transmitter import Transmitter

class _BaseTask(Task):
    """Base task.

    Implements the processing pipeline and the daqstream.
    """

    def __init__(self):
        super(_BaseTask, self).__init__()
        self.pipeline = self.make_pipeline()
        self.dummy_cycles = int(WIN_SIZE / READ_LENGTH)

    def make_pipeline(self):
        # Multiple feature extraction could also be implemented using a
        # parallel pipeline and a block that joins multiple outputs.
        windower_ = Windower(int(S_RATE * WIN_SIZE))

        if FILTER:
            b, a = butter(
                N=FILTER_ORDER,
                Wn=[LOWCUT / (S_RATE * 0.5), HIGHCUT / (S_RATE * 0.5)],
                btype='bandpass')
            filter_ = Filter(b, a=a, overlap=(
                int(S_RATE * WIN_SIZE) - int(S_RATE * READ_LENGTH)))

        fe_ = FeatureExtractor([
            ('mav', LogVar())
        ],
            n_channels=len(CHANNELS)),

        ensure_2d = Ensure2D(orientation='col')

        if FILTER:
            pipeline = [windower_, filter_, fe_, ensure_2d]
        else:
            pipeline = [windower_, fe_, ensure_2d]

        pipeline = Pipeline(pipeline)

        return pipeline

    def prepare_daq(self, daqstream):
        self.daqstream = daqstream
        self.daqstream.start()
        self.timer = Counter(
            int(TRIAL_LENGTH / READ_LENGTH) + self.dummy_cycles)
        self.timer.timeout.connect(self.finish_trial)

    def reset(self):
        self.timer.reset()
        self.pipeline.clear()

    def key_press(self, key):
        super(_BaseTask, self).key_press(key)
        if key == util.key_escape:
            self.finish()

    def finish(self):
        self.daqstream.stop()
        self.finished.emit()

class Calibration(_BaseTask):
    """Collects calibration data.

    """

    def __init__(self):
        super(Calibration, self).__init__()

    def prepare_design(self, design):
        # Each block is one movement and has N_TRIALS repetitions
        block = design.add_block()
        for movement in MOVEMENTS:
            block.add_trial(attrs={
                'movement': movement
            })

    def prepare_graphics(self, container):
        self.canvas = Canvas()
        self.text = Text(text='', color='black')
        self.canvas.add_item(self.text)
        container.set_widget(self.canvas)

    def prepare_storage(self, storage):  # TODO
        self.writer = storage.create_task('calibration')

    def run_trial(self, trial):
        self.reset()

        self.text.qitem.setText("{}".format(
            trial.attrs['movement']))
        # self.text.qitem.setText("{}".format('Move'))

        trial.add_array('data_raw', stack_axis=1)
        trial.add_array('data_proc', stack_axis=1)

        self.pipeline.clear()
        self.connect(self.daqstream.updated, self.update)

    def update(self, data):
        data_proc = self.pipeline.process(data)

        if self.timer.count >= self.dummy_cycles - 1:

            # mov = self.trial.attrs['movement']
            # Update Arrays
            self.trial.arrays['data_raw'].stack(data)
            self.trial.arrays['data_proc'].stack(data_proc)

        self.timer.increment()

    def finish_trial(self):
        # self.pic.hide()
        # self.text.qitem.setText("{}".format('relax'))
        self.writer.write(self.trial)
        self.disconnect(self.daqstream.updated, self.update)

        self.wait_timer = Timer(TRIAL_INTERVAL)
        self.wait_timer.timeout.connect(self.next_trial)
        self.wait_timer.start()


class Control(_BaseTask):
    """Real-time EMG control.

    Parameters
    ----------
    subject : str
        Subject ID.
    """

    pos_x = AxopyTransmitter(object)
    pos_y = AxopyTransmitter(object)

    def __init__(self, subject):
        super(Control, self).__init__()
        self.subject = subject

        self.advance_block_key = util.key_return

        self.load_models()
        self.make_midi_connection()

        self.prediction_pipeline = self.make_prediction_pipeline()

    def load_models(self):
        root_models = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                   'data', self.subject, 'models')
        self.mdl = joblib.load(os.path.join(root_models, 'mdl'))

    def make_midi_connection(self):
        self.transmitter = Transmitter(
            midi_port=MIDI_PORT,
            channel=MIDI_CHANNEL,
            control_x=CONTROL_X,
            control_y=CONTROL_Y,
            control_snap=CONTROL_SNAP)


    def make_prediction_pipeline(self):
        """
        TODO
        Prediction pipeline.

        The input is first transposed to match sklearn expected style. Then the
        ``predict_proba`` method of the estimator is used. The final step of
        the pipeline consists of a parallel implementation which outputs
        the predicted label, the associated probability and posterior
        probability vector.
        """
        pipeline = Pipeline([
            # Callable(lambda x: x.reshape(-1,1)),  # Transpose
            Callable(lambda x: x.reshape(1,-1)),  # Transpose
            Transformer(self.mdl),
            Callable(lambda x: x.reshape(-1,)),
            Callable(lambda x: np.array([0.5 + x[0]-x[1], 0.5 + x[2]-x[3]])),
            Callable(lambda x: np.clip(x, a_min=0, a_max=1)),
            Callable(lambda x: ((2**N_BITS - 1) * x).astype(np.int)),
            # Ensure2D(orientation='col'),
            # Windower(100),
            # Callable(lambda x: np.mean(x, axis=1, keepdims=False).astype(np.int))
        ])

        return pipeline

    def prepare_design(self, design):
        # Each block includes all movements exactly once
        block = design.add_block()
        block.add_trial()

    def prepare_graphics(self, container):
        self.canvas = Canvas()
        container.set_widget(self.canvas)

    def run_trial(self, trial):

        self.pipeline.clear()
        # init pos in the middle of the screen
        self.x_ = int(2**N_BITS / 2)
        self.y_ = int(2**N_BITS / 2)
        self.connect(self.daqstream.updated, self.update)
        self.connect(self.pos_x, self.transmitter.set_x)
        self.connect(self.pos_y, self.transmitter.set_y)

    def update(self, data):
        data_proc = self.pipeline.process(data)

        if self.timer.count >= self.dummy_cycles - 1:
            pred = self.prediction_pipeline.process(data_proc)
            self.x_, self.y_ = pred
            self.pos_x.emit(self.x_)
            self.pos_y.emit(self.y_)

        self.timer.increment()

    def finish_trial(self):
        self.disconnect(self.daqstream.updated, self.update)
        self.disconnect(self.pos, self.transmitter)

    def finish(self):
        self.daqstream.stop()
        self.finished.emit()

    def key_press(self, key):
        if key == util.key_escape:
            self.finish()
        else:
            super().key_press(key)


if __name__ == '__main__':
    parser = ArgumentParser()
    task = parser.add_mutually_exclusive_group(required=True)
    task.add_argument('--calibrate', action='store_true')
    task.add_argument('--control', action='store_true')
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--myo', action='store_true')
    source.add_argument('--nidaq', action='store_true')
    source.add_argument('--noise', action='store_true')
    args = parser.parse_args()

    if args.myo:
        dev_name = 'myo'
    elif args.nidaq:
        dev_name = 'nidaq'

    cp = ConfigParser()
    cp.read(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                         'config.ini'))
    READ_LENGTH = cp.getfloat('hardware', 'read_length')
    UP = cp.getint('channels_' + dev_name, 'up')
    DOWN = cp.getint('channels_' + dev_name, 'down')
    RIGHT = cp.getint('channels_' + dev_name, 'right')
    LEFT = cp.getint('channels_' + dev_name, 'left')
    WIN_SIZE = cp.getfloat('processing', 'win_size')
    FILTER = cp.getboolean('processing', 'filter')
    LOWCUT = cp.getfloat('processing', 'lowcut')
    HIGHCUT = cp.getfloat('processing', 'highcut')
    FILTER_ORDER = cp.getfloat('processing', 'filter_order')

    CHANNELS = [RIGHT, LEFT, UP, DOWN]

    if args.myo:
        import myo
        from pydaqs.myo import MyoEMG
        from pathlib import Path
        MYO_SDK_PATH = cp.get('hardware', 'myo_sdk_path')
        S_RATE = 200.
        myo.init(sdk_path=Path(MYO_SDK_PATH))
        dev = MyoEMG(
            channels=CHANNELS,
            zero_based=False,
            samples_per_read=int(S_RATE * READ_LENGTH))

    elif args.nidaq:
        from pydaqs.nidaq import Nidaq
        S_RATE = cp.getfloat('hardware', 'rate')
        dev = Nidaq(
            channels=CHANNELS,
            rate=S_RATE,
            zero_based=False,
            samples_per_read=int(S_RATE * READ_LENGTH)
        )

    elif args.noise:
        from axopy.daq import NoiseGenerator
        S_RATE = 2000.
        dev = NoiseGenerator(
            rate=S_RATE,
            num_channels=len(CHANNELS),
            amplitude=10.0,
            read_size=int(S_RATE * READ_LENGTH))

    exp = Experiment(daq=dev, subject='test', allow_overwrite=True)

    if args.calibrate:
        N_TRIALS = cp.getint('calibration', 'n_trials')
        MOVEMENTS = cp.get('calibration', 'movements').split(',')
        N_BLOCKS = len(MOVEMENTS)
        TRIAL_LENGTH = cp.getfloat('calibration', 'trial_length')
        TRIAL_INTERVAL = cp.getfloat('calibration', 'trial_interval')
        exp.run(Calibration())
    elif args.control:
        N_BITS = cp.getint('midi', 'n_bits')
        MIDI_CHANNEL = cp.getint('midi', 'midi_channel')
        MIDI_PORT = cp.get('midi', 'midi_port')
        CONTROL_X = cp.getint('midi', 'control_x')
        CONTROL_Y = cp.getint('midi', 'control_y')
        CONTROL_SNAP = cp.getint('midi', 'control_snap')
        TRIAL_LENGTH = int(1e6)
        exp.run(Control(subject=exp.subject))
