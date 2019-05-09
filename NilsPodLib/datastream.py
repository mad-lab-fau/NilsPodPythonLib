# -*- coding: utf-8 -*-
"""
Created on Thu Sep 28 11:32:22 2017

@author: Nils Roth, Arne Küderle
"""
import copy
from typing import Optional, Iterable, List, TypeVar

import numpy as np
import pandas as pd
from scipy import signal
from scipy.signal import decimate

from NilsPodLib.consts import SENSOR_LEGENDS, SENSOR_UNITS
from NilsPodLib.utils import inplace_or_copy

T = TypeVar('T')


class Datastream:
    data: np.ndarray
    sampling_rate_hz: float
    is_calibrated: bool = False
    sensor: Optional[str]
    _unit: str
    _columns: Optional[List]

    def __init__(self, data: np.ndarray, sampling_rate: float = 1., columns: Optional[Iterable] = None,
                 sensor_type: Optional[str] = None, unit: Optional[str] = None):
        self.data = data
        self.sampling_rate_hz = float(sampling_rate)
        self.sensor = sensor_type
        self._columns = list(columns) if columns else columns
        self._unit = unit

    def __repr__(self):
        return 'Datastream(sensor={}, sampling_rate_hz={}, is_calibrated={}, data={}'.format(self.sensor,
                                                                                             self.sampling_rate_hz,
                                                                                             self.is_calibrated,
                                                                                             self.data)

    @property
    def unit(self):
        if self.is_calibrated is True:
            if self._unit:
                return self._unit
            if self.sensor and SENSOR_UNITS.get(self.sensor, None):
                return SENSOR_UNITS[self.sensor]
        return 'a.u.'

    @property
    def columns(self):
        if self._columns:
            return self._columns
        elif self.sensor:
            if SENSOR_LEGENDS.get(self.sensor, None):
                return list(SENSOR_LEGENDS[self.sensor])
        return list(range(self.data.shape[-1]))

    def __len__(self):
        return len(self.data)

    def norm(self) -> np.ndarray:
        return np.linalg.norm(self.data, axis=1)

    def normalize(self) -> 'Datastream':
        ds = copy.deepcopy(self)
        ds.data /= ds.data.max(axis=0)
        return ds

    def cut(self: T, start: Optional[int] = None, stop: Optional[int] = None, step: Optional[int] = None,
            inplace: bool = False) -> T:
        s = inplace_or_copy(self, inplace)
        sl = slice(start, stop, step)
        s.data = s.data[sl]
        return s

    def downsample(self: T, factor: int, inplace: bool = False) -> T:
        """Downsample the datastreams by a factor using a iir filter."""
        s = inplace_or_copy(self, inplace)
        s.data = decimate(s.data, factor, axis=0)
        s.sampling_rate_hz /= factor
        return s

    def filter_butterworth(self, fc, order, filter_type='low'):
        fn = fc / (self.sampling_rate_hz / 2.0)
        b, a = signal.butter(order, fn, btype=filter_type)
        return signal.filtfilt(b, a, self.data.T, padlen=150).T

    def data_as_df(self, index_as_time: bool = True) -> pd.DataFrame:
        df = pd.DataFrame(self.data, columns=self.columns)
        if index_as_time:
            df.index /= self.sampling_rate_hz
            df.index.name = 't'
        return df