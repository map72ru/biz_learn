import yaml

with open(config_path, encoding='utf-8') as file:
    config = yaml.load(file, Loader=yaml.FullLoader)
    data_path = config['data']['path'] + 'dataset\\'
    excel_path = config['data']['path'] + 'exceldata\\'
    workfiles_path = config['data']['path'] + 'workfiles\\'
    input_path = workfiles_path + 'input\\'
    output_path = workfiles_path + 'output\\'
    trash_path = workfiles_path + 'trash\\'
    log_path = config['data']['logsPath']
    models_path = config['data']['path'] + 'models\\'
    model_config = config['model']['config']
    output_sleep_time = config['observer']['output_sleep_time']
    input_sleep_time = config['observer']['input_sleep_time']
    connection_string = config['database']['connection_string']
