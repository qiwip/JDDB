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
            # 低通滤波
            ba = signal.butter(8, 0.04, 'lowpass')
            ip_ = signal.filtfilt(ba[0], ba[1], ip)
            # 中值滤波
            ip = signal.medfilt(ip, 15)
            # 在0.05s没到50kA认为不是有效炮
            if ip[time >= 0.05][0] < 80:
                result['IsValidShot'] = False
                return result
            result['IpFlat'] = ip.max()
            start = 0
            end = 0
            for i in range(len(ip_ - 640)):
                if ip_[i] > ip_[i + 20] > ip_[i + 40] and ip_[i] * 0.95 > ip_[i + 160] and ip_[i] * 0.9 > ip_[i + 320] \
                        and ip_[i] * 0.8 > ip_[i + 640]:
                    start = i
                    break
            for i in range(start, len(ip_ - 640)):
                if ip_[i] <= 10:
                    end = i
                    break
            if start and end:
                if end - start < 600:
                    result['IsDisrupt'] = True
                    while end > start:
                        k = np.polyfit(time[end - 10:end], ip[end - 10:end], 1)[0]
                        if k > -1000 and ip[end] > ip[start]*0.9:
                            break
                        end -= 1
                    result['CqTime'] = time[end]
                else:
                    result['RampDownTime'] = time[start]
            else:
                result['IsValidShot'] = False
            return result
        except Exception as e:
            print(e)
            result['IsValidShot'] = False
            return result
