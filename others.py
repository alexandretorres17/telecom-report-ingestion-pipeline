from aux_func import file_load, db_load
import datetime as dt

def import_others(report_name, report_oss, full_path, file_list, engine):
    """
    Import misc reports automatically
    :param engine: db engine used to connect to DB
    :param report_oss: argument passed by main run .py with oss region
    :type report_oss: str
    :param report_date: argument passed by main run .py with report date
    :type report_date: str
    :param full_path: path where the .csv files are
    :type full_path: str
    :param file_list list of files to be loaded
    :type file_list: list
    """
    for file_name in file_list:
        print('File found: ' + file_name)
        report_df = file_load(full_path + file_name, 0)
        if not report_df.dropna().empty:
           db_table = f"{report_name}".lower().strip().replace(' ', '_').replace('.', '')
           now_date = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
           report_df['oss'] = report_oss
           report_df['insert_time'] = now_date
           report_df = report_df.astype(str)
           db_load(report_df, engine, db_table)
