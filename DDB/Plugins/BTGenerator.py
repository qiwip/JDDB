"""

==========


"""
from DDB.Label import GeneratorBase
import numpy as np


class Generator(GeneratorBase):

    def __init__(self):
        pass

    def requested_signal(self):
        """ Return list of tag of signals that processor need"""
        return [r'\Bt']

    def run(self, data):
        result = {
            'Bt': 0.0
        }
        try:
            bt, time = data['\Bt']
            start = np.where(time > 0)[0][0]
            end = np.where(time > 0.4)[0][0]
            bt = bt[start:end]
            bt = np.average(bt)
            result['Bt'] = bt
            return result
        except Exception as e:
            print(e)
            return {}
