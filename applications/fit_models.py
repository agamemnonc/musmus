"""
Fits and saves models for specified subject.
"""

import os

from argparse import ArgumentParser
from configparser import ConfigParser

import numpy as np
import pandas as pd
import h5py
import joblib

from sklearn.preprocessing import MinMaxScaler
from sklearn.pipeline import Pipeline


def fit_models(data, trials):
    """Fits models.

    Parameters
    ----------
    data : h5py file
        Processed data.
    trials: df
        Trial information.
    trim_sampels : int
        Number of samples to discard at start and end of each trial.
    n_iter : int
        Number of iterations for RandomizedSearchCV
    fpr_threshold : float
        FPR threshold for estimating ROC thresholds.

    Returns
    -------
    models : list
        List of (name, estimator/transformer) tuples.
    """

    n_total_trials = trials.shape[0]

    # Collect training data
    X = np.zeros((0,len(CHANNELS)))
    for trial in range(n_total_trials):
        data_trial = data.get(str(trial))[()].T
        X = np.append(X, data_trial, axis=0)

    X = MVC * X
    mdl = Pipeline(steps=[
        ('mms', MinMaxScaler(feature_range=(-0.5,0.5)))])
    mdl.fit(X)

    return [('mdl', mdl)]


def save_models(models, subject):
    """Saves all models/estimators to disk."""
    root_models = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               'data', subject, 'models')
    if not os.path.exists(root_models):
        os.makedirs(root_models)

    for model in models:
        fname = os.path.join(root_models, model[0])
        joblib.dump(model[1], fname, compress=True)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument("subject", type=str,
                        help="Subject ID")
    args = parser.parse_args()

    cp = ConfigParser()
    cp.read(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                         'config.ini'))
    DEVICE = cp.get('hardware', 'device')
    channels_lookup = 'channels_' + DEVICE
    LEFT = cp.getint(channels_lookup, 'left')
    RIGHT = cp.getint(channels_lookup, 'right')
    UP = cp.getint(channels_lookup, 'up')
    DOWN = cp.getint(channels_lookup, 'down')
    MVC = cp.getfloat('fit', 'mvc')
    N_BITS = cp.getint('midi', 'n_bits')

    CHANNELS = [LEFT, RIGHT, UP, DOWN]

    subject = args.subject
    root_trials = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               'data', subject, 'calibration', 'trials.csv')
    root_data = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             'data', subject, 'calibration', 'data_proc.hdf5')

    data = h5py.File(root_data)
    trials = pd.read_csv(root_trials)
    models = fit_models(data=data, trials=trials)
    save_models(models, subject=args.subject)
