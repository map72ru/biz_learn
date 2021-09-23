from sklearn.metrics import accuracy_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from config import models_path, model_config
from logger_settings import log
import pandas as pd
import numpy as np
import pickle
import os
import collecting_data


class Model:

    def __init__(self, fieldName, boreholeName):
        self.fieldName = fieldName
        self.boreholeName = boreholeName
        self.rootPath = models_path + fieldName + '\\'
        self.previous = 0
        self.data = None
        self.values = None
        self.model = None
        self.scaler = None
        self.expertData = None
        if not os.path.exists(self.rootPath):
            os.mkdir(self.rootPath)
        self.logger = log
        self.model_init()

    def model_init(self):
        try:
            dirName = self.rootPath + self.boreholeName
            self.previous = len(os.listdir(dirName))
            dirName += '\\current_version'
            with open(dirName + '\\model.pkl', 'rb') as filePath:
                self.model = pickle.load(filePath)
                self.logger.debug('Model loaded from:' + dirName + '\\model.pkl')
            self.data = np.load(dirName + '\\data.npy').tolist()
            self.values = np.load(dirName + '\\values.npy').tolist()
            if os.path.exists(dirName + '\\expertdata.xlsx'):
                self.expertData = pd.read_excel(dirName + '\\expertdata.xlsx')
        except:
            print('There is no model with this name')
            self.logger.debug('Not found model with field:' + self.fieldName + ' borehole:' + self.boreholeName)
            self.load_standard_model()
            self.save()
        self.load_standard_scaler()

    def load_standard_model(self):
        self.previous = 1
        try:
            dirName = self.rootPath + 'StandardModel\\'
            with open(dirName + 'model.pkl', 'rb') as filePath:
                self.model = pickle.load(filePath)
            self.data = np.load(dirName + '\\data.npy').tolist()
            self.values = np.load(dirName + '\\values.npy').tolist()
        except:
            print('There is no standard model')
            self.logger.debug('Not found standard model with field:' + self.fieldName)
            self.create_standard_model()

    def load_standard_scaler(self):
        try:
            with open(self.rootPath + 'StandardModel\\scaler.pkl', 'rb') as filePath:
                self.scaler = pickle.load(filePath)
        except:
            print('There is no scaler')
            self.logger.debug('Not found scaler with field:' + self.fieldName)
            self.create_standard_model()

    def create_standard_model(self):
        model = RandomForestClassifier(**model_config)
        try:
            data, values, testdata, testvalues = collecting_data.load_whole_dataset_without_one(self.fieldName)
        except:
            self.logger.exception('No dataset on field: ' + self.fieldName)
            raise Exception('No dataset on field: ' + self.fieldName)
        self.data = data.tolist()
        self.values = values.tolist()
        scaler = StandardScaler()
        scaler.fit(data)
        data = scaler.transform(data)
        model.fit(data, values)
        dirName = self.rootPath + 'StandardModel\\'
        if not os.path.exists(dirName):
            os.mkdir(dirName)
        with open(dirName + 'model.pkl', 'wb') as filePath:
            pickle.dump(model, filePath)
        with open(dirName + 'scaler.pkl', 'wb') as filePath:
            pickle.dump(scaler, filePath)
        np.save(dirName + 'data', data)
        np.save(dirName + 'values', values)
        self.model = model
        self.scaler = scaler
        self.logger.debug('Created standard model on field:' + self.fieldName)
        self.logger.debug('Saved standard model and scaler to ' + dirName)

    def replace(self):
        dirName = self.rootPath + self.boreholeName
        for i in range(self.previous):
            index = self.previous - i
            if not os.path.exists(dirName + '\\previous_model' + str(index)):
                os.mkdir(dirName + '\\previous_model' + str(index))
            if i == self.previous - 1:
                os.replace(dirName + '\\current_version\\model.pkl',
                           dirName + '\\previous_model' + str(index) + '\\model.pkl')
                os.replace(dirName + '\\current_version\\data.npy',
                           dirName + '\\previous_model' + str(index) + '\\data.npy')
                os.replace(dirName + '\\current_version\\values.npy',
                           dirName + '\\previous_model' + str(index) + '\\values.npy')
                if os.path.exists(dirName + '\\current_version\\expertdata.xlsx'):
                    os.replace(dirName + '\\current_version\\expertdata.xlsx',
                               dirName + '\\previous_model' + str(index) + '\\expertdata.xlsx')
            else:
                os.replace(dirName + '\\previous_model' + str(index - 1) + '\\model.pkl',
                           dirName + '\\previous_model' + str(index) + '\\model.pkl')
                os.replace(dirName + '\\previous_model' + str(index - 1) + '\\data.npy',
                           dirName + '\\previous_model' + str(index) + '\\data.npy')
                os.replace(dirName + '\\previous_model' + str(index - 1) + '\\values.npy',
                           dirName + '\\previous_model' + str(index) + '\\values.npy')
                if os.path.exists(dirName + '\\previous_model' + str(index - 1) + '\\expertdata.xlsx'):
                    os.replace(dirName + '\\previous_model' + str(index - 1) + '\\expertdata.xlsx',
                               dirName + '\\previous_model' + str(index) + '\\expertdata.xlsx')

    def save(self):
        dirName = self.rootPath + self.boreholeName
        if not os.path.exists(dirName):
            os.mkdir(dirName)
            dirName = dirName + '\\current_version\\'
            os.mkdir(dirName)
        else:
            self.replace()
            dirName = dirName + '\\current_version\\'
        with open(dirName + 'model.pkl', 'wb') as filePath:
            pickle.dump(self.model, filePath)
        np.save(dirName + 'data', self.data)
        np.save(dirName + 'values', self.values)
        if self.expertData is not None:
            self.save_expert_data()
        if os.path.exists(self.rootPath + self.boreholeName + '\\previous_model6'):
            os.remove(self.rootPath + self.boreholeName + '\\previous_model6')
        self.logger.debug('Model saved to ' + dirName + '\\model.pkl')

    def train(self, data, values):
        train_data = self.scaler.transform(data)
        for sample in train_data:
            self.data.append(sample)
        self.values += values
        self.model.fit(self.data, self.values)
        self.logger.debug('Model trained by data:' + str(data) + ' and values' + str(values))
        self.save()

    def check(self, testdata, testvalues):
        data = self.scaler.transform(testdata)
        predict = self.model.predict(data)
        mean = accuracy_score(testvalues, predict)
        print('model validate acc:%f' % mean)
        return mean

    def predict(self, data):
        data = self.scaler.transform(data)
        predict = self.model.predict(data)
        return predict

    def save_expert_data(self):
        dirName = self.rootPath + self.boreholeName + '\\current_version\\expertdata.xlsx'
        writer = pd.ExcelWriter(dirName)
        self.expertData.to_excel(writer, sheet_name='Data', index=None)
        writer.save()

    def add_expert_data(self, data, values):
        packElements = ['Глубина, м', 'MgO', 'Al2O3', 'SiO2', 'P2O5', 'S*', 'K2O', 'CaO', 'TiO2', 'MnO', 'Fe',
                        'Оценка эксперта']
        expertdata = pd.DataFrame(data)
        expertdata.columns = packElements[:-1]
        expertdata[packElements[-1]] = values
        if self.expertData is None:
            self.expertData = expertdata
        else:
            alldata = self.expertData.values.tolist() + expertdata.values.tolist()
            alldata = pd.DataFrame(alldata)
            alldata.columns = packElements
            self.expertData = alldata
        self.save_expert_data()
