"""
分析等离子体电流，获取等离子体电流相关的信息
==========
通过滤波算法找到等离子体平顶电流大小，开始下降时间等信息

"""
from DDB.Label import GeneratorBase
import numpy as np
from scipy import signal as signal
import collections


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
            'IpFlat': 0.0,  # 平顶电流大小
            'IsFlatTopDisrupt': False,  # 是否是平顶阶段破裂
            'IsRampUpDisrupt': False,  # 是否是上升阶段破裂
            'IsRampDownDisrupt': False,  # 是否是下降阶段破裂
            'IpCq': 0.0,  # 破裂时的等离子体电流
            'IsRunaway': False,  # 是否出现逃逸
            'RunawayDuration': 0.0,  # 逃逸持续时间
            'RunawayIp': 0.0  # 逃逸电流大小
        }
        try:
            ip, time = data[r'\ip']
            start = np.where(time >= 0)[0][0]
            end = np.where(time >= 1)[0][0]
            ip = ip[start:end]
            time = time[start:end]
            ip_filtered = signal.medfilt(ip, 31)
            # 没放起来,在0-0.03s内为击穿阶段,判断0.05s后的电流，如果没有就是无效炮
            index = np.where(np.array(time) > 0.03)[0][0]
            if ip_filtered[index] < 50:
                result['IsValidShot'] = False
                return result
            # 0.03到0.05s为电流爬升阶段
            index = np.where(np.array(time) > 0.05)[0][0]

            if ip_filtered[index] < 20:
                result['IsDisrupt'] = True
                result['IsRampUpDisrupt'] = True
                # 上升阶段破裂，最大电流时刻作为破裂时间
                index = ip.tolist().index(max(ip))
                result['CqTime'] = time[index]
                result['IpCq'] = ip[index]
                # 电流淬灭的持续时间
                start = np.where(np.array(ip) >= ip[index] * 0.9)[0][0]
                end = np.where(np.array(ip) >= ip[index] * 0.1)[0][0]
                result['CqDuration'] = time[end] - time[start]

                return result

            def flattop(ip):
                _ip = ip[np.where(np.array(ip) >= max(ip_filtered) * 0.8)[0][0]:]
                ip_ = _ip[:np.where(np.array(_ip) <= max(ip_filtered) * 0.4)[0][0]]
                # 出现次数最多的IP值
                count = collections.Counter(ip_)
                return count.most_common(1)[0][0]

            # 平顶电流大小
            try:
                result['IpFlat'] = flattop(ip)
            except Exception:
                result['IsValidShot'] = False
                return result

            interval = 120

            # 去掉前一部分分析过的数据和下降之后的数据
            index = np.where(ip >= result['IpFlat'])[0][0]
            ip = ip[index:]
            time = time[index:]
            try:
                index = np.where(ip <= 1)[0][0]
            except Exception:
                index = np.argmin(ip)
            # 去掉下降后的数据
            ip = ip[:index+interval]
            time = time[:index+interval]
            i = 0
            down = False

            while i < len(ip) - interval:
                # 斜率
                k = np.polyfit(time[i:i + interval], ip[i:i + interval], 1)[0]

                # 平顶阶段
                if not down:
                    # 开始下降
                    if -3000 < k < -500:
                        index = np.where(time >= time[i] + 0.1)[0][0]
                        if ip[index] < result['IpFlat'] / 2:
                            down = True
                            result['RampDownTime'] = time[i]

                    # 破裂
                    elif -3000 > k:
                        result['IsDisrupt'] = True
                        result['IsFlatTopDisrupt'] = True  # 平顶阶段破裂
                        frame = ip[i:i + interval]
                        frame_t = time[i:i + interval]
                        result['CqTime'] = frame_t[0]
                        result['IpCq'] = frame[0]
                        count = 0
                        for i in range(0, len(frame) - 1):
                            if frame[i+1] <= frame[i]:
                                count += 1
                            else:
                                count = 0
                            if count == 5:
                                result['CqTime'] = frame_t[i-4]
                                result['IpCq'] = frame[i-4]
                        start = np.where(ip <= (result['IpFlat'] * 0.9))[0][0]
                        end = np.where(ip <= (result['IpFlat'] * 0.1))[0][0]
                        result['CqDuration'] = time[end] - time[start]
                        break
                    else:
                        pass
                # 下降阶段
                else:
                    # 破裂
                    if -3000 > k:
                        result['IsDisrupt'] = True
                        result['IsRampDownDisrupt'] = True  # 下降阶段破裂
                        frame = ip[i:i + interval]
                        frame_t = time[i:i + interval]
                        result['CqTime'] = frame_t[0]
                        result['IpCq'] = frame[0]
                        count = 0
                        for i in range(0, len(frame) - 1):
                            if frame[i + 1] <= frame[i]:
                                count += 1
                            else:
                                count = 0
                            if count == 5:
                                result['CqTime'] = frame_t[i - 4]
                                result['IpCq'] = frame[i - 4]
                        end = np.where(ip <= result['IpFlat'] * 0.1)[0][0]
                        result['CqDuration'] = time[end] - time[i]
                        break

                i += 10

            # 非破裂处理完
            if result['IsDisrupt'] is False:
                return result
            # 找逃逸电流
            else:
                interval = 100
                down = True
                if i > interval:
                    k0 = np.polyfit(time[i - interval:i], ip[i - interval:i], 1)[0]
                else:
                    k0 = 0
                while i < len(ip) - interval:
                    # 斜率
                    k1 = np.polyfit(time[i:i + interval], ip[i:i + interval], 1)[0]
                    # 下降阶段
                    if down:
                        if k1 > k0:
                            down = False
                    # 回升阶段
                    else:
                        if k1 < k0 < -3000:
                            # 再次下降
                            # 逃逸电流
                            result['IsRunaway'] = True
                            result['RunawayIp'] = ip[i]
                            result['RunawayDuration'] = time[-1] - time[i]
                            return result
                    i += 10
                    k0 = k1
            return result
        except Exception as e:
            print(e)
            return {}
