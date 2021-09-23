from config import workfiles_path, input_path, output_path, trash_path, output_sleep_time, input_sleep_time
from training_model import Model
from logger_settings import log
import pickle
import collecting_data
import threading
import time
import os
import re


def find_field_synonym(fieldName):
    if fieldName == 'СН':
        return 'СрединоМордорское'
    return fieldName


def defining_fieldName_from_file(fileName):
    search = re.search(r'(?P<fieldName>.+?)(?P<boreholeName>\d+.*)', fileName.split('-')[0])
    try:
        fieldName = search.group('fieldName')
        boreholeName = search.group('boreholeName')
        fieldName = find_field_synonym(fieldName)
        return fieldName, boreholeName
    except:
        log.exception('EXCEPTION wrong input filename:' + fileName + ' traceback below')
        return None, None


def observing_input_data():
    global terminated
    global counter
    while not terminated:
        print('Started observing input files')
        log.debug('Started observing input files')
        content = os.listdir(input_path)
        if content:
            for file in content:
                if file == 'stop.please':
                    log.debug('Observing terminated by stop.please')
                    terminated = True
                    os.replace(input_path + file, workfiles_path + file)
                    continue
                if re.match(r'.*\.xlsx', file):
                    fieldName, boreholeName = defining_fieldName_from_file(file)
                    if fieldName is None:
                        os.replace(input_path + file, trash_path + file)
                        continue
                    mutex.acquire()
                    try:
                        mod = Model(fieldName, boreholeName)
                    except:
                        log.exception('Failed to load model on field:' + fieldName + ' borehole:' + boreholeName)
                        os.replace(input_path + file, trash_path + file)
                        log.debug('Input file ' + file + ' replaced to trash folder')
                        continue
                    mutex.release()
                    log.debug('Observing input ' + file)
                    try:
                        data = collecting_data.read_data(input_path + file)
                    except:
                        log.exception('Failed to read data from file: ' + file)
                        os.replace(input_path + file, trash_path + file)
                        log.debug('Input file ' + file + ' replaced to trash folder')
                        continue
                    if data:
                        values = mod.predict(data)
                        fileName = fieldName + '-' + boreholeName + '-' + str(counter) + '.xlsx'
                        collecting_data.create_excel(output_path + fileName, data, values)
                        log.debug('Output file ' + fileName + ' created at output folder')
                        counter = counter + 1
                os.replace(input_path + file, trash_path + file)
                log.debug('Input file ' + file + ' replaced to trash folder')
        else:
            log.debug('Nothing found in input folder')
        if terminated:
            break
        time.sleep(input_sleep_time)


def observing_output_data():
    global terminated
    while not terminated:
        print('Started observing output files')
        log.debug('Started observing output files')
        content = os.listdir(output_path)
        if content:
            for file in content:
                if file == 'stop.please':
                    log.debug('Observing terminated by stop.please')
                    terminated = True
                    os.replace(output_path + file, workfiles_path + file)
                    continue
                if re.match(r'.*\.xlsx', file):
                    log.debug('Observing output ' + file)
                    expertdata, expertvalues, traindata, trainvalues = collecting_data.check_excel(output_path + file)
                    name = file.split('-')
                    fieldName = name[0]
                    boreholeName = name[1]
                    data = []
                    values = []
                    if expertdata is not None:
                        mod = Model(fieldName, boreholeName)
                        mod.add_expert_data(expertdata, expertvalues)
                        data_length = len(traindata)
                        if data_length:
                            for i in range(data_length):
                                data.append(traindata[i])
                                values += trainvalues[i]
                            mutex.acquire()
                            mod.train(data, values)
                            mutex.release()
                        os.replace(output_path + file, trash_path + file)
                        log.debug('Output file ' + file + ' replaced to trash folder')
                    else:
                        log.debug('Found not marked files in output folder')
                else:
                    os.replace(output_path + file, trash_path + file)
        else:
            log.debug('Nothing found in output folder')
        if terminated:
            break
        time.sleep(output_sleep_time)


terminated = False
try:
    with open(workfiles_path + 'counter.sav', 'rb') as f:
        counter = pickle.load(f)
except:
    log.info('WARNING no file for counter')
    counter = 0
mutex = threading.Lock()
tr1 = threading.Thread(target=observing_input_data, daemon=True)
tr2 = threading.Thread(target=observing_output_data, daemon=True)
tr1.start()
tr2.start()
tr1.join()
tr2.join()
print('Program terminated')
log.debug('Program terminated')
with open(workfiles_path + 'counter.sav', 'wb') as f:
    pickle.dump(counter, f)
