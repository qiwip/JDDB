"""
分析扰动场设置，找到是否投入扰动场
==========


"""
from DDB.Label import GeneratorBase
import numpy as np
from scipy import signal
import matplotlib.pyplot as plt


class Generator(GeneratorBase):

    def __init__(self):
        pass

    def requested_signal(self):
        return [r'\DRMP_DC_Io2']

    def run(self, data):
        result = {

        }
        pf, time = data[r'\DRMP_DC_Io2']
        start = np.where(time > 0)[0][0]
        end = np.where(time > 0.8)[0][0]
        pf = pf[start:end]
        time = time[start:end]
        # pf = signal.medfilt(pf, 5)
        plt.figure()
        plt.plot(time, pf)
        plt.show()
        # pf = np.average(pf)
        if np.abs(pf).max() > 0.1:
            result['PerturbationField'] = True
        return result
