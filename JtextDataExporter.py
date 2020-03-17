from DDB.Data import Exporter, Reader
from MDSplus import connection
import numpy as np
from scipy import signal
import logging
import platform
import traceback
import os
import time
import DDB
import json


class JTEXTDataExporter:
    if platform.system() == 'Windows':
        hdf5path = r'C:\J-TEXT'
    else:
        hdf5path = r'~/J-TEXT'

    def __init__(self, root=None):
        """connect to mdsplus server and init data importer"""
        if root:
            self.hdf5path = root
        self.exporter = Exporter(self.hdf5path)
        self.reader = Reader(self.hdf5path)
        # log
        log_dir = os.path.abspath('') + os.sep + 'log'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(level=logging.INFO)
        handler = logging.FileHandler(log_dir + os.sep + 'JTEXTDataExporter_log_{}.txt'.format(
            time.strftime("%Y%m%d%H%M%S", time.localtime(time.time()))))
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        self.logger.addHandler(handler)
        self.logger.addHandler(console)

    def download(self, shots=None, tags=None, sr=None):
        """Download J-TEXT data
        @:param shots: shot list
        @:param tags: tag list
        @:param sr: sample rate for resample(kHz), if sr<sr0: do resample, else: do nothing
        :return: null
        """
        if shots is None or len(shots) == 0:
            raise ValueError('Param Error, '
                             'shot list can\'t be Empty!')
        if tags is None or len(tags) == 0:
            raise ValueError('Param Error, '
                             'tag list can\'t be Empty!')
        self.logger.info('Start download data')
        for shot in shots:
            try:
                c = connection.Connection('211.67.27.245')
                c.openTree('jtext', shot=shot)
                for tag in tags:
                    try:
                        print('read {}:{}'.format(shot, tag))
                        data = np.array(c.get(tag))
                        time = np.array(c.get(r'DIM_OF(BUILD_PATH({}))'.format(tag)))
                        if data.shape[0] == 0 or time.shape[0] == 0:
                            self.logger.info('shot:{}, tag:{}, Shape of signal or dim_of(signal) is 0')
                        elif abs(data.shape[0] - time.shape[0]) > 10:
                            self.logger.info('shot:{}, tag:{}, Shape of signal and dim_of(signal) not equal')
                        else:
                            if 0 < data.shape[0] - time.shape[0] < 10:
                                data = data[:time.shape[0]]
                            if 0 < time.shape[0] - data.shape[0] < 10:
                                time = time[:data.shape[0]]
                            sr0 = int(len(data) / (time[-1] - time[0]) / 10) * 10

                            if sr and sr < sr0/100:
                                num = sr*(int(round(time[-1]*1000 - time[0]*1000)))
                                data = signal.resample(data, num)
                                duration = (time[-1] - time[0]) / num
                                time = []
                                for i in range(num):
                                    time.append(i*duration)
                            self.exporter.save(data, time, shot, tag)
                            self.logger.info('shot:{}, tag:{}, Finish.'.format(shot, tag))
                    except Exception as e:
                        self.logger.info('shot:{}, tag:{}, error occurs:{}\n{}.'.
                                         format(shot, tag, e, traceback.format_exc()))
                        self.exporter.save([], [], shot, tag)
                c.closeTree('jtext', shot=shot)
            except Exception as err:
                self.logger.info('shot {} is Empty, reason: {}\n{}'.format(shot, err, traceback.format_exc()))
                if 'SS-W-SUCCESS' in '{}'.format(err):
                    self.logger.info('stop at shot {}\n{}'.format(shot, traceback.format_exc()))
                    exit(-1)


if __name__ == '__main__':
    shots = range(1062000, 1066000)
    tags = [r'\Bt', r'\Ihfp', r'\Ivfp', r'\MA_POL_CA01T', r'\MA_POL_CA02T', r'\MA_POL_CA03T', r'\MA_POL_CA05T', r'\MA_POL_CA06T', r'\MA_POL_CA07T', r'\MA_POL_CA19T', r'\MA_POL_CA20T', r'\MA_POL_CA21T', r'\MA_POL_CA22T', r'\MA_POL_CA23T', r'\MA_POL_CA24T', r'\axuv_ca_01', r'\ip', r'\sxr_cb_024', r'\sxr_cc_049', r'\vs_c3_aa001', r'\vs_ha_aa001']
    jdi = JTEXTDataExporter()
    jdi.download(shots, tags)
