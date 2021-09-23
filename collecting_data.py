from sqlalchemy.sql import label
from config import data_path, excel_path
from logger_settings import log
from db_prepare import session, PackTable, SynonymTable
import pandas as pd
import numpy as np
import os


someSynonyms = []


def get_all_packs():
    return session.query(PackTable).all()


def get_all_synonyms():
    query = session.query(label('name', PackTable.name), label('synonym', SynonymTable.name))
    query = query.join(SynonymTable, SynonymTable.stratigraphy_sludge_id == PackTable.id)
    return query.all()


def check_pack(packName):
    try:
        query = session.query(label('name', PackTable.name))
        query = query.join(SynonymTable, SynonymTable.stratigraphy_sludge_id == PackTable.id)
        query = query.filter(SynonymTable.name == packName)
        return query.one()
    except:
        if packName not in someSynonyms:
            print(packName)
            log.info('Pack synonym not found:' + packName)
            someSynonyms.append(packName)
        return np.NaN


def get_data_from_excel(packElements, path, dataSheet, valuesSheet, depthName, packName, rowNumber):
    log.debug('Reading excel from ' + path)
    data = pd.read_excel(path, sheet_name=dataSheet)
    values = pd.read_excel(path, sheet_name=valuesSheet)
    if 'Глубина_м' in data.columns:
        packElements[0] = 'Глубина_м'
    data = data.loc[:, packElements]
    if dataSheet == 'report':
        data[packElements[0]] = data[packElements[0]].apply(lambda depth: int(depth.split('-')[2]))
    values = values.loc[:, [depthName, packName]]
    if valuesSheet == 'Титул':
        if rowNumber is not None:
            values = values.iloc[rowNumber:]
        else:
            log.exception('Exception: rowNumber expected')
            raise Exception('rowNumber expected')
    values = values.rename(columns={depthName: packElements[0]})
    values.replace(0, np.nan, inplace=True)
    values = values.dropna()
    values[packName] = values[packName].apply(lambda pack: pack.replace("?", ""))
    values[packName] = values[packName].apply(lambda pack: check_pack(pack))
    values = values.dropna()
    values[packName] = values[packName].apply(lambda pack: pack[0])
    fullData = values.merge(data, on=[packElements[0]])
    dataList = fullData.loc[:, packElements[:]].values.tolist()
    valuesList = fullData[packName].values.tolist()
    if packElements[0] == 'Глубина_м':
        packElements[0] = 'Глубина, м'
    return dataList, valuesList


def get_dataset_from_report():
    packElements = ['Name', 'Mg', 'Al', 'Si', 'P', 'S', 'Cl', 'Ca', 'Ti', 'Fe', 'Zn', 'Sr']
    dataList, valuesList = get_data_from_excel(packElements, excel_path + 'report\\1_Рапорт_состав_шлам.xlsx', 'report', 'GK', 'Глубина, м', 'Стратиграфи-ческая привязка пробы', None)
    dataList2, valuesList2 = get_data_from_excel(packElements, excel_path + 'report\\2-115.xlsx', 'report', 'GK', 'Глубина, м', 'Стратиграфи-ческая привязка пробы', None)
    dataList3, valuesList3 = get_data_from_excel(packElements, excel_path + 'report\\3-66.xlsx', 'report', 'Интерпретация', 'Глубина, м', 'Стратигра-фическая привязка', None)
    dataList4, valuesList4 = get_data_from_excel(packElements, excel_path + 'report\\4_Шлам_27_16 07 18.xlsx', 'report', 'Титул', 'Unnamed: 2', 'Unnamed: 10', 6)
    data = dataList + dataList2 + dataList3 + dataList4
    values = valuesList + valuesList2 + valuesList3 + valuesList4
    testdata = []
    testvalues = []
    testdata.append(dataList), testdata.append(dataList2), testdata.append(dataList3), testdata.append(dataList4)
    testvalues.append(valuesList), testvalues.append(valuesList2), testvalues.append(valuesList3), testvalues.append(valuesList4)
    return data, values, testdata, testvalues


def get_dataset_from_data():
    packElements = ['Глубина, м', 'MgO', 'Al2O3', 'SiO2', 'P2O5', 'S*', 'K2O', 'CaO', 'TiO2', 'MnO', 'Fe']
    packElementsForBadData = ['Глубина, м', 'MgO.1', 'Al2O3.1', 'SiO2.1', 'P2O5.1', 'S*.1', 'K2O.1', 'CaO.1', 'TiO2.1', 'MnO.1', 'Fe.1']
    dataList, valuesList = get_data_from_excel(packElements, excel_path + 'Data\\3_Шлам-72.xlsx', 'Data', 'Титул', 'Unnamed: 2', 'Unnamed: 10', 6)
    dataList2, valuesList2 = get_data_from_excel(packElements, excel_path + 'Data\\4_Шлам-61.xlsx', 'Data', 'Титул', 'Unnamed: 2', 'Unnamed: 10', 6)
    dataList3, valuesList3 = get_data_from_excel(packElements, excel_path + 'Data\\5_Шлам-17.xlsx', 'Data', 'Титул', 'Unnamed: 2', 'Unnamed: 9', 6)
    dataList4, valuesList4 = get_data_from_excel(packElements, excel_path + 'Data\\6_Шлам_БЕЗ ИНТЕРПРЕТАЦИИ.xlsx', 'Data', 'Интерпретация', 'Глубина, м', 'Стратигра-фическая привязка', None)
    dataList5, valuesList5 = get_data_from_excel(packElements, excel_path + 'Data\\7_Шлам-70.xlsx', 'Data', 'Интерпретация', 'Глубина, м', 'Стратигра-фическая привязка', None)
    dataList6, valuesList6 = get_data_from_excel(packElements, excel_path + 'Data\\8_Шлам-63.xlsx', 'Data', 'Интерпретация', 'Глубина, м', 'Стратигра-фическая привязка', None)
    dataList7, valuesList7 = get_data_from_excel(packElements, excel_path + 'Data\\9_Шлам-69.xlsx', 'Data', 'Титул', 'Unnamed: 2', 'Unnamed: 9', 6)
    dataList8, valuesList8 = get_data_from_excel(packElements, excel_path + 'Data\\10_Шлам-69.xlsx', 'Data', 'Титул', 'Unnamed: 2', 'Unnamed: 9', 6)
    dataList9, valuesList9 = get_data_from_excel(packElements, excel_path + 'Data\\11_Шлам-73.XLSX', 'Data', 'Интерпретация', 'Глубина, м', 'Стратигра-фическая привязка', None)
    dataList10, valuesList10 = get_data_from_excel(packElements, excel_path + 'report\\12_ГГИ_Шлам-66.xlsx', 'Data', 'Титул', 'Unnamed: 2', 'Unnamed: 9', 6)
    dataList11, valuesList11 = get_data_from_excel(packElements, excel_path + 'Data\\13_Шлам-75.xlsx', 'Data', 'Титул', 'Unnamed: 2', 'Unnamed: 9', 6)
    dataList12, valuesList12 = get_data_from_excel(packElementsForBadData, excel_path + 'BadData\\14_Шлам-10.xlsx', 'Data', 'Титул', 'Unnamed: 2', 'Unnamed: 9', 6)
    dataList13, valuesList13 = get_data_from_excel(packElementsForBadData, excel_path + 'BadData\\15_Шлам-29.xlsx', 'Data', 'Титул', 'Unnamed: 2', 'Unnamed: 9', 6)
    dataList14, valuesList14 = get_data_from_excel(packElementsForBadData, excel_path + 'BadData\\16_Шлам-22_(3754).xlsx', 'Data', 'Титул', 'Unnamed: 2', 'Unnamed: 9', 6)
    dataList15, valuesList15 = get_data_from_excel(packElementsForBadData, excel_path + 'BadData\\17_Шлам-73.xlsx', 'Data', 'Титул', 'Unnamed: 2', 'Unnamed: 9', 6)
    dataList16, valuesList16 = get_data_from_excel(packElementsForBadData, excel_path + 'BadData\\18_Шлам-67.xlsx', 'Data', 'Титул', 'Unnamed: 2', 'Unnamed: 9', 6)
    data = dataList + dataList2 + dataList3 + dataList4 + dataList5 + dataList6 + dataList7 + dataList8 + dataList9 + dataList10 + dataList11 + dataList12 + dataList13 + dataList14 + dataList15
    values = valuesList + valuesList2 + valuesList3 + valuesList4 + valuesList5 + valuesList6 + valuesList7 + valuesList8 + valuesList9 + valuesList10 + valuesList11 + valuesList12 + valuesList13 + valuesList14 + valuesList15
    testdata = []
    testvalues = []
    testdata.append(dataList), testdata.append(dataList2), testdata.append(dataList3), testdata.append(dataList4), testdata.append(dataList5)
    testdata.append(dataList6), testdata.append(dataList7), testdata.append(dataList8), testdata.append(dataList9), testdata.append(dataList10)
    testdata.append(dataList11), testdata.append(dataList12), testdata.append(dataList13), testdata.append(dataList14), testdata.append(dataList15), testdata.append(dataList16)
    testvalues.append(valuesList), testvalues.append(valuesList2), testvalues.append(valuesList3), testvalues.append(valuesList4), testvalues.append(valuesList5)
    testvalues.append(valuesList6), testvalues.append(valuesList7), testvalues.append(valuesList8), testvalues.append(valuesList9), testvalues.append(valuesList10)
    testvalues.append(valuesList11), testvalues.append(valuesList12), testvalues.append(valuesList13), testvalues.append(valuesList14), testvalues.append(valuesList15), testvalues.append(valuesList16)
    return data, values, testdata, testvalues


def get_dataset_from_baddata():
    packElements = ['Глубина, м', 'MgO.1', 'Al2O3.1', 'SiO2.1', 'P2O5.1', 'S*.1', 'K2O.1', 'CaO.1', 'TiO2.1', 'MnO.1', 'Fe.1']
    dataList, valuesList = get_data_from_excel(packElements, excel_path + 'BadData\\19_Шлам-10.xlsx', 'Data', 'Титул', 'Unnamed: 2', 'Unnamed: 9', 6)
    dataList2, valuesList2 = get_data_from_excel(packElements, excel_path + 'BadData\\20_Шлам-29.xlsx', 'Data', 'Титул', 'Unnamed: 2', 'Unnamed: 9', 6)
    dataList3, valuesList3 = get_data_from_excel(packElements, excel_path + 'BadData\\21_Шлам-22_(3754).xlsx', 'Data', 'Титул', 'Unnamed: 2', 'Unnamed: 9', 6)
    dataList4, valuesList4 = get_data_from_excel(packElements, excel_path + 'BadData\\22_Шлам-73.xlsx', 'Data', 'Титул', 'Unnamed: 2', 'Unnamed: 9', 6)
    dataList5, valuesList5 = get_data_from_excel(packElements, excel_path + 'BadData\\23_Шлам-67.xlsx', 'Data', 'Титул', 'Unnamed: 2', 'Unnamed: 9', 6)
    bushdata = dataList + dataList2
    bushdata2 = dataList3 + dataList4 + dataList5
    bushvalues = valuesList + valuesList2
    bushvalues2 = valuesList3 + valuesList4 + valuesList5
    fulldata = bushdata + bushdata2
    fullvalues = bushvalues + bushvalues2
    testdata=[]
    testvalues=[]
    testdata.append(bushdata), testdata.append(bushdata2)
    testvalues.append(bushvalues), testvalues.append(bushvalues2)
    return fulldata, fullvalues, testdata, testvalues


def save_dataset(fieldName, directoryName):
    data, values, testdata, testvalues = test()
    print(len(data), len(values))
    save_path = data_path + fieldName + '\\'
    if not os.path.exists(save_path):
        os.mkdir(save_path)
    save_path = save_path + directoryName +'\\'
    if not os.path.exists(save_path):
        os.mkdir(save_path)
    np.save(save_path + 'dataset', data)
    np.save(save_path + 'values', values)
    np.save(save_path + 'testdataset', testdata)
    np.save(save_path + 'testvalues', testvalues)
    log.debug('Saved dataset to: ' + save_path + '. Length of data:' + str(len(data)) + ' Length of values:' + str(len(values)))


def load_dataset(fieldName, directoryName):
    data = np.load(data_path + fieldName + '\\' + directoryName + '\\dataset.npy')
    values = np.load(data_path + fieldName + '\\' + directoryName + '\\values.npy')
    testdata = np.load(data_path + fieldName + '\\' + directoryName + '\\testdataset.npy', allow_pickle=True)
    testvalues = np.load(data_path + fieldName + '\\' + directoryName + '\\testvalues.npy', allow_pickle=True)
    return data, values, testdata, testvalues


def load_whole_dataset_without_one(fieldName):
    return load_dataset(fieldName, 'WholeDatasetWithoutOne')


def load_whole_dataset(fieldName):
    return load_dataset(fieldName, 'WholeDatasetWithDepth')


def load_dataset_from_data(fieldName):
    return load_dataset(fieldName, 'BadDataWithDepth')


def load_dataset_from_report(fieldName):
    return load_dataset(fieldName, 'ReportWithoutDepth')


def load_dataset_from_report_with_division(fieldName):
    data, packElements = load_data_from_report(fieldName)
    data, someElements = add_division_to_report(data, packElements)
    values = np.load(data_path + fieldName + '\\ReportWithoutDepth\\values.npy')
    testdata = np.load(data_path + fieldName + '\\ReportWithoutDepth\\testdataset.npy', allow_pickle=True)
    for i in range(len(testdata)):
        testdata[i], someElements = add_division_to_report(testdata[i], packElements)
    testvalues = np.load(data_path + fieldName + '\\ReportWithoutDepth\\testvalues.npy', allow_pickle=True)
    return data, values, testdata, testvalues


def load_data_from_report(fieldName):
    packElements = ['Mg', 'Al', 'Si', 'P', 'S', 'Cl', 'Ca', 'Ti', 'Fe', 'Zn', 'Sr']
    data = np.load(data_path + fieldName +'\\ReportWithoutDepth\\dataset.npy')
    return data, packElements


def add_division_to_report(data, packElements):
    df = pd.DataFrame(data, columns=packElements[:])
    newPackElements = packElements.copy()
    df['Al/Si'] = df['Al'] / df['Si']
    newPackElements.append('Al/Si')
    df['(Si+Ca+Mg)/S'] = (df['Si'] + df['Ca'] + df['Mg']) / df['S']
    newPackElements.append('(Si+Ca+Mg)/S')
    df['S/Ti'] = df['S'] / df['Ti']
    newPackElements.append('S/Ti')
    df['P/Ti'] = df['P'] / df['Ti']
    newPackElements.append('P/Ti')
    df['Fe/S'] = df['Fe'] / df['S']
    newPackElements.append('Fe/S')
    df['Sr/Ca'] = df['Sr'] / df['Ca']
    newPackElements.append('Sr/Ca')
    df = df.replace(np.inf, 0)
    return df.values.tolist(), newPackElements


def read_data(filePath):
    packElements = ['Глубина, м', 'MgO', 'Al2O3', 'SiO2', 'P2O5', 'S*', 'K2O', 'CaO', 'TiO2', 'MnO', 'Fe']
    try:
        data = pd.read_excel(filePath, sheet_name='Data')
    except:
        log.exception('Failed to find sheet Data')
        raise Exception('Failed to find sheet Data')
    try:
        data = data.loc[:, packElements]
    except:
        log.exception('Failed to collect all data on sheet')
        raise Exception('Failed to collect all on sheet')
    data = data.dropna()
    return data.values.tolist()


def create_excel(filePath, data, values):
    packElements = ['Глубина, м', 'MgO', 'Al2O3', 'SiO2', 'P2O5', 'S*', 'K2O', 'CaO', 'TiO2', 'MnO', 'Fe']
    df = pd.DataFrame(data)
    df.columns = packElements
    df['Статиграфическая привязка пробы'] = values
    df['Оценка эксперта'] = np.NaN
    writer = pd.ExcelWriter(filePath)
    df.to_excel(writer, sheet_name='На проверку', index=None)
    writer.save()


def check_excel(filePath):
    packElements = ['Глубина, м', 'MgO', 'Al2O3', 'SiO2', 'P2O5', 'S*', 'K2O', 'CaO', 'TiO2', 'MnO', 'Fe', 'Статиграфическая привязка пробы', 'Оценка эксперта']
    data = pd.read_excel(filePath, sheet_name='На проверку')
    data = data.loc[:, packElements]
    data = data.dropna()
    if len(data):
        data['Совпало'] = data['Статиграфическая привязка пробы'] == data['Оценка эксперта']
        expertdata = data.loc[:, packElements[:-2]].values.tolist()
        expertvalues = data.loc[:, ['Оценка эксперта']].values.tolist()
        falsedata = data[data.Совпало == False]
        traindata = falsedata.loc[:, packElements[:-2]]
        trainvalues = falsedata.loc[:, ['Оценка эксперта']]
        data_length = len(expertdata)
        data = []
        values = []
        for i in range(data_length):
            data.append(expertdata[i])
            values += expertvalues[i]
        return data, values, traindata.values.tolist(), trainvalues.values.tolist()
    else:
        return None, None, None, None


def predict_value(data, expertPath):

    return data