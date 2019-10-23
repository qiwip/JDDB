"""
分析等离子体电流，获取等离子体电流相关的信息
==========
通过滤波算法找到等离子体平顶电流大小，开始下降时间等信息

"""
from DDB.Label import GeneratorBase
import numpy as np
from scipy import signal
import matplotlib.pyplot as plt


class PF(GeneratorBase):

    def __init__(self):
        pass

    def device(self):
        return 'J-TEXT'

    def get_request_signal(self):
        return [r'\DRMP_DC_Io2']

    def calculate(self, data):
        result = {

        }
        pf_t = data[r'\DRMP_DC_Io2']
        if pf_t.shape[0] == 2 and pf_t.shape[1] != 0:
            pf = pf_t[0]
            time = pf_t[1]
        else:
            result['NoData'] = True
            return result

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
