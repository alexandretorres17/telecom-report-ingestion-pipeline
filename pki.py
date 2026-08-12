from aux_func import file_load, loadData
import datetime as dt
import os
from pathlib import Path

REPORT_NAME = "PKI"


def import_pki(full_path, file_list, engine, temp_path):
    """
     function used for PKI report ETL process
    :param full_path: path where the .csv files are
    :type full_path: str
    :param file_list list of files to be loaded
    :type file_list: list
    :param engine: db engine passed from main.py
    """
    for file_name in file_list:
        print('File found: ' + file_name)
        report_df = file_load(full_path + file_name, 0)
        db_table = 'pki_project'
        now_date = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        report_df['insert_time'] = now_date
        report_df = report_df.dropna(subset=['site_name'])
        report_df.rename(columns={'type': 'site_type'}, inplace=True)
        cols = ['site_name', 'ca_name', 'certificate_date', 'certificate_expiration_date', 's1_secgw', 's1_secgw_ip',
                'x2_secgw', 'x2_secgw_ip', 'certificate_file_name', 'certificate_common_name',
                'certificate_serial_number', 'oss', 'site_type', 'insert_time']
        report_df = report_df[cols]
        query = f"""select {str(cols)[1:-1].replace("'", "")} from {db_table}"""
        report_df = report_df.astype(str)
        loadData(engine, query, db_table, report_df, "insert_time", "site_name")

        # if file does not exist write header
        Path(temp_path + REPORT_NAME).mkdir(parents=True, exist_ok=True)
        if not os.path.isfile(temp_path + REPORT_NAME + '/' + file_name):
            report_df.to_csv(temp_path + REPORT_NAME + '/' + file_name, header='column_names')
        else:  # else it exists so append without writing the header
            report_df.to_csv(temp_path + REPORT_NAME + '/' + file_name, mode='a', header=False)