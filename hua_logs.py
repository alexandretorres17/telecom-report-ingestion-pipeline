from aux_func import db_load
import datetime as dt
import re
import pandas as pd
from os import listdir

def import_logs(full_path, engine):
    """
     function used for Huawei Logs report ETL process
    :param full_path: path where the .csv files are
    :type full_path: str
    :param engine: db engine passed from main.py
    """
    final_df = pd.DataFrame()
    db_table = "huawei_log"
    for file in listdir(full_path):
        print('File found: ' + file)
        report_df = pd.read_csv(full_path + file, skiprows=2, dtype='unicode', delimiter=',').apply(lambda x: x.str.strip() if x.dtype == 'object' else x)
        if not report_df.empty:
            report_df.columns = report_df.columns.str.lower().str.strip().str.replace(' ', '_').str.replace('.', '')
        report_df.drop(report_df.tail(1).index, inplace=True)
        report_df.rename(columns={'operation_command': 'org_cmd', 'operator_name': 'operator',
                                  'ip_address': 'ip', 'command_code': 'cmd_code',
                                  'command_type': 'opr_type', 'operation_time': 'start_time',
                                  'operation_end_time': 'end_time'}, inplace=True)
        report_df = report_df[~report_df.org_cmd.str.contains('^CmdCode=.*, CmdName=.*, CmdContent=.*', regex=True, na=False)]
        report_df['cmd'] = report_df.apply(lambda x: cmd_log_parser(x['org_cmd']), axis=1)
        report_df['cmd_type'] = report_df.apply(lambda x: cmd_type_parser(x['cmd']), axis=1)
        report_df['opr_code'] = report_df.apply(lambda x: opr_code_parser(x['org_cmd']), axis=1)
        report_df['bsc'] = file.split('_')[0]
        cols = ['source', 'operator', 'dn', 'ip', 'cmd_code', 'opr_type', 'start_time', 'return_code', 'result',
                'end_time', 'org_cmd', 'cmd', 'cmd_type', 'opr_code', 'bsc']
        report_df = report_df[cols]
        report_df.columns = [db_table + '_' + str(col_name) for col_name in report_df.columns]
        final_df = final_df.append(report_df, ignore_index=True)
    final_df = final_df.sort_values('huawei_log_bsc').reset_index(drop=True)
    now_date = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    final_df['huawei_log_insert_time'] = now_date
    final_df = final_df.astype(str)
    db_load(final_df, engine, db_table)


def cmd_log_parser(cmd_log_col):
    """
    function to parse cmd without opr code
    :param cmd_log_col: original cmd log column
    :return: parsed cmd
    """
    regex = r"\/\*\d*.*\*\/"
    subst = ""
    parsed_col = re.sub(regex, subst, cmd_log_col, 0, re.IGNORECASE)
    return parsed_col


def cmd_type_parser(cmd_col):
    """
    function to parse cmd type from cmd col (eg DSP, LST, MOD)
    :param cmd_col: previously parsed cmd log column
    """
    regex = r"(^\w+\s)|(^\W{1}[a-zA-Z].+\W{1})\["
    result = re.search(regex, str(cmd_col), re.IGNORECASE)
    if 'BulkCM' in cmd_col:
        return 'BulkCM'
    elif 'CmdCode=' and 'TaskNo.=' in cmd_col:
        return 'CmdTask'
    else:
        try:
            if result.group(1) != None:
                result = result.group(1).upper().strip()
                if result == 'EMS':
                    return 'LOGIN'
                elif result == 'LOGIN':
                    return 'LOGIN'
                else:
                    return str(result)
            else:
                return 'FTP'

        except:
            if cmd_col.upper() == 'LOGIN':
                return 'LOGIN'
            else:
                return 'UNKNOWN'


def opr_code_parser(cmd_col):
    """
    function to parse operational cmd code from original cmd log
    :param cmd_col: original cmd log column
    """
    regex = r"\/\*(\d*).*\*\/"
    result = re.search(regex, str(cmd_col), re.IGNORECASE)
    try:
        if result.group(1).strip() == '':
            return 'OTHER'
        else:
            return str(result.group(1).strip())

    except AttributeError:
        return 'OTHER'
