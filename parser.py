from db_prepare import session, WellInfoTable, FieldViewTable, ZakLoadRegisterTable, ZakIrTable, SludgeHdrTable, \
    SludgeLasTable
from decimal import Decimal
from sqlalchemy import func
from transliterate import translit
from config import workfiles_path
from datetime import datetime
import pandas as pd
import warnings
import lasio
import re
import sys


def read_las(filepath):
    las = lasio.read(filepath)
    date = las.header['Well']['DATE'].value
    values = pd.DataFrame(las.values()).T
    return values, date


def find_table(data, comment_column):
    first_row = data.dropna(thresh=10).index[0]
    datalist = data.values.tolist()
    header = data.iloc[first_row].values.tolist()
    length = len(header)
    for i in range(length):
        column = header[i]
        currentrow = first_row
        while column != column and currentrow > 0:
            currentrow = currentrow - 1
            column = datalist[currentrow][i]
        header[i] = column
    ink_data = data.iloc[first_row + 1:]
    ink_data.columns = header
    for i in range(length):
        current = header[length - 1 - i]
        if current != current:
            header.remove(current)
    header.remove(comment_column)
    ink_data = ink_data.loc[:, header].dropna()
    return ink_data


def check_list(word_list, aim):
    for i in range(len(word_list)):
        word = word_list[i]
        if type(word) is str:
            if aim in word:
                return word_list.index(word)
    return -1


def find_date(data):
    columns = data.columns
    bad_columns = filter(lambda some: not (type(some) is str and 'Unnamed' in some), columns)
    list_columns = list(bad_columns)
    index = check_list(list_columns, "Дата")
    if index != -1:
        return list_columns[index+1]
    for i in range(len(columns)):
        daterow = data[columns[i]]
        try:
            mask = daterow.str.contains("Дата", na=False)
        except:
            continue
        if mask.any():
            row = data[mask].dropna(axis=1).values.tolist()[0]
            index = check_list(row, "Дата")
            date = row[index+1]
            return date
    return None


def find_fieldnames(filepath):
    data = pd.read_excel(filepath)
    columns = data.columns
    name_cell = ''
    for i in range(len(columns)):
        daterow = data[columns[i]]
        try:
            mask = daterow.str.contains("Месторождение", na=False)
        except:
            continue
        if mask.any():
            row = data[mask].dropna(axis=1).values.tolist()[0]
            index = check_list(row, "Месторождение")
            name_cell = row[index]
            break
    all_chars = name_cell.split(',')
    all_chars = list(map(lambda some: some.replace(" ", ""), all_chars))
    FieldName = ''
    BoreholeName = ''
    for i in all_chars:
        if "месторождение" in i.lower():
            FieldName = i.split(':')[1]
            continue
        if "скважина" in i.lower():
            BoreholeName = i.split(':')[1]
            continue
    return FieldName, BoreholeName


def read_excel_fact_inc(filepath):
    data = pd.read_excel(filepath)
    ink_data = find_table(data, 'Примечание')
    date = find_date(data)
    return ink_data, date


def read_excel_profile_inc(filepath):
    data = pd.read_excel(filepath)
    ink_data = find_table(data, 'Комментарий')
    date = find_date(data)
    return ink_data, date


def parse_filename(filepath, filename):
    pattern = r'(?P<WellLog>(?P<WellFieldName>.+?)_(?P<WellBushName>\d+)_(?P<WellBoreholeName>.+?)_.*?\.las)|' \
              r'(?P<Inc_Fact>Инклинометрия_(?P<IncFieldName>.+?)_(?P<IncBushName>\d+)_(?P<IncBoreholeName>.+?)_.*?\.xlsx)|' \
              r'(?P<Inc_Profile>Профиль.+?\.xlsx)'
    s = re.search(pattern, filename)
    FieldName = None
    BoreholeName = None
    if s.group('WellLog') is not None:
        FieldName = s.group('WellFieldName')
        BoreholeName = s.group('WellBoreholeName')
        wellid = get_wellid(FieldName, BoreholeName)
        values, date = read_las(filepath)
        if wellid is not None:
            add_well_las(wellid, values, date)
            return True
    if s.group('Inc_Fact') is not None:
        FieldName = s.group('IncFieldName')
        BoreholeName = s.group('IncBoreholeName')
        wellid = get_wellid(FieldName, BoreholeName)
        values, date = read_excel_fact_inc(filepath)
        if wellid is not None:
            add_well_fact_inc(wellid, values, date)
            return True
    if s.group('Inc_Profile') is not None:
        values, date = read_excel_profile_inc(filepath)
        FieldName, BoreholeName = find_fieldnames(filepath)
        wellid = get_wellid(FieldName, BoreholeName)
        if type(date) is str:
            date = datetime.strptime(date, '%d.%m.%Y')
        if wellid is not None:
            add_well_prof_inc(wellid, values, date)
            return True
    print('Wrong Name:', FieldName, BoreholeName)


def get_wellid(FieldName, BoreholeName):
    query = session.query(FieldViewTable.id)
    query = query.filter(FieldViewTable.name == FieldName)
    field_id = query.scalar()
    borehole_name = translit(BoreholeName, 'ru')
    query = session.query(WellInfoTable.wellid)
    query = query.filter(WellInfoTable.field_id == field_id)
    query = query.filter(WellInfoTable.well_name == borehole_name)
    return query.scalar()


def get_fileid(wellid, date_research, version_id):
    query = session.query(ZakLoadRegisterTable.fileid)
    query = query.filter(ZakLoadRegisterTable.wellid == wellid)
    query = query.filter(ZakLoadRegisterTable.version_id == version_id)
    query = query.filter(ZakLoadRegisterTable.filedate == date_research)
    return query.scalar()


def get_or_create_fileid(wellid, date_research, version_id):
    fileid = get_fileid(wellid, date_research, version_id)
    if fileid is None:
        file = ZakLoadRegisterTable(wellid=wellid, version_id=version_id, filedate=date_research, registerid=216207,
                                    filetype=16)
        session.add(file)
        session.commit()
    fileid = get_fileid(wellid, date_research, version_id)
    return fileid


def get_last_depth_inc(fileid):
    query = session.query(func.max(ZakIrTable.depth))
    query = query.filter(ZakIrTable.fileid == fileid)
    return query.scalar()


def get_last_depth_las(hdrid):
    query = session.query(func.max(SludgeLasTable.md))
    query = query.filter(SludgeLasTable.well_sludge_hdr_id == hdrid)
    return query.scalar()


def get_hdrid(wellid, date_research):
    query = session.query(SludgeHdrTable.id)
    query = query.filter(SludgeHdrTable.wellid == wellid)
    query = query.filter(SludgeHdrTable.date_research == date_research)
    return query.scalar()


def get_or_create_hdrid(wellid, date_research):
    hdrid = get_hdrid(wellid, date_research)
    if hdrid is None:
        file = SludgeHdrTable(wellid=wellid, date_research=date_research, type_data=3)
        session.add(file)
        session.commit()
    hdrid = get_hdrid(wellid, date_research)
    return hdrid


def add_well_las(wellid, data, date_research):
    hdrid = get_or_create_hdrid(wellid, date_research)
    last_depth = get_last_depth_las(hdrid)
    if last_depth is not None:
        data = data[data[data.columns[0]] > last_depth + Decimal(0.01)]
    for i in data.values:
        row = SludgeLasTable(well_sludge_hdr_id=hdrid, md=i[0], tvd=i[1], gr=i[2])
        session.add(row)
        session.commit()


def parse_dataframe(fileid, data):
    for i in data.values:
        row = ZakIrTable(depth=i[0], angle=i[1], azimuth_true=i[2], azimuth_magnetic=i[3], z_meas=i[4], absdepth=i[5],
                         x_meas=i[6], y_meas=i[7], displacement=i[8], intensity_curvature=i[9], fileid=fileid)
        session.add(row)
        session.commit()


def add_well_prof_inc(wellid, data, date_research):
    fileid = get_or_create_fileid(wellid, date_research, 21)
    data = data.loc[:,
           ['Глубина по стволу, м', 'Зенитный угол, град', 'Азимут дирекц., град', 'Азимут магнитный, град',
            'Глубина по вертикали, м', 'Абсолютная отметка, м', 'Лок. смещение к северу, м',
            'Лок. смещение к востоку, м', 'Отклонение от устья, м', 'Пространст. интенсивность, град/10 м']]
    last_depth = get_last_depth_inc(fileid)
    if last_depth is not None:
        data = data[data['Глубина по стволу, м'] > last_depth + Decimal(0.1)]
    parse_dataframe(fileid, data)


def add_well_fact_inc(wellid, data, date_research):
    fileid = get_or_create_fileid(wellid, date_research, 18)
    data = data.loc[:, ['Глубина по датчику, м', 'Зенитный угол, град', 'Азимут дирекц., град', 'Азимут магнитный, град',
                        'Глубина по вертикали, м', 'Абсолютная отметка, м', 'Лок. смещение к северу, м',
                        'Лок. смещение к востоку, м', 'Смещение от устья, м', 'Простр. интенсив-ность, град/10 м']]
    last_depth = get_last_depth_inc(fileid)
    if last_depth is not None:
        data = data[data['Глубина по датчику, м'] > last_depth + Decimal(0.1)]
    parse_dataframe(fileid, data)


if not sys.warnoptions:
    warnings.simplefilter("ignore")
parse_filename(workfiles_path+'\\SREDNE-NAZYMSKOE_100_105G_export_MD.las', 'SREDNE-NAZYMSKOE_100_105G_export_MD.las')
