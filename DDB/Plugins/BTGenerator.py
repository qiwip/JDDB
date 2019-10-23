"""

==========


"""
from DDB.Label import GeneratorBase
import numpy as np
from scipy import signal as signal


class Bt(GeneratorBase):

    def __init__(self):
        pass

    def requested_signal(self):
        """ Return list of tag of signals that processor need"""
        return [r'\Bt']

    def run(self, data):
        result = {
            'Bt': 0.0
        }
        bt_t = data['\Bt']
        if bt_t.shape[0] == 2 and bt_t.shape[1] != 0:
            bt = bt_t[0]
            time = bt_t[1]
        else:
            result['NoData'] = True
            return result
        start = np.where(time > 0)[0][0]
        end = np.where(time > 0.4)[0][0]
        bt = bt[start:end]
        bt = np.average(bt)
        result['Bt'] = bt
        return result
