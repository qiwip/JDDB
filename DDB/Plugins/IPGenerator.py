"""
分析等离子体电流，获取等离子体电流相关的信息
==========
通过滤波算法找到等离子体平顶电流大小，开始下降时间等信息

"""
from DDB.Label import GeneratorBase
import numpy as np
from scipy import signal as signal


class Generator(GeneratorBase):

    def __init__(self):
        pass

    def requested_signal(self):
        return [r'\ip']

    def run(self, data):
        result = {
            'IsValidShot': True,  # 是否是有效放电
            'IsDisrupt': False,  # 是否破裂
            'RampDownTime': 0.0,  # 等离子体电流下降时间
            'CqTime': 0.0,  # 电流淬灭时间
            'CqDuration': 0.0,  # 电流淬灭持续时间
            'IpFlat': 0.0  # 平顶电流大小
        }
        try:
            ip, time = data[r'\ip']
            ip = ip[(time >= 0) & (time <= 1)]
            time = time[(time >= 0) & (time <= 1)]
            ip = signal.medfilt(ip, 15)
            # 在0.03s没爬到50kA认为不是有效炮
            if ip[time >= 0.05][0] < 50:
                result['IsValidShot'] = False
                return result
            # 0.03到0.05s为电流爬升阶段
            result['IpFlat'] = ip.max()
            ks = []
            window = 20
            for s in range(0, len(ip), window):
                k = np.polyfit(time[s:s + window], ip[s:s + window], 1)[0]
                ks.append([k for j in range(window)])
            ks = np.array(ks)
            ks = ks.reshape(ks.shape[0] * ks.shape[1])
            start = 0

            if ks.min() < -10000 and ip[ks < -10000][0] > 100:
                result['IsDisrupt'] = True
                for index in range(ks.shape[0]):
                    if ks[index] < -10000 and start == 0:
                        start = time[index]
                    elif ks[index] > -10000 and start != 0:
                        result['CqDuration'] = time[index] - start
                        result['CqTime'] = start
                        return result
            else:
                count = 0
                for index in range(ks.shape[0]):
                    if ks[index] < 0 and start == 0:
                        start = time[index]
                        count += 1
                    elif ks[index] > 0 and count < 300:
                        start = -1
                        count = 0
                    elif ks[index] > 0 and count >= 300:
                        # end = time[index]
                        result['RampDownTime'] = start
                        return result
                    else:
                        count += 1
            result['IsValidShot'] = False
            return result
        except Exception as e:
            print(e)
            result['IsValidShot'] = False
            return result
