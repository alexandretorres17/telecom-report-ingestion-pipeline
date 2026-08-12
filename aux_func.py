import pandas as pd
import os
from shutil import rmtree
import logging
from logging.handlers import RotatingFileHandler
import datetime as dt
import zipfile
from sqlalchemy.sql import update, table, column, select, text, func, and_
import csv


def file_load(src_file, rows_skip):
    """
     function to load input files (either with xls or csv extension)
    :param src_file: input file to be loaded
    :param rows_skip: parameter do define how many rows to skip when loading csv
    :type src_file: str
    :type rows_skip: int
    """
    if src_file.endswith('.xlsx') or src_file.endswith('.xls'):
        df = pd.read_excel(src_file, sheet_name=0, dtype='unicode')
        df = df.apply(lambda x: x.str.strip().str.encode('utf-8'))

    elif src_file.endswith('.csv'):    
        with open(src_file, 'r') as csvfile:
            temp_lines = csvfile.readline() + '\n' + csvfile.readline()
            dialect = csv.Sniffer().sniff(temp_lines, [',',';'])
            df = pd.read_csv(src_file, skiprows=rows_skip, dtype='unicode', delimiter=dialect.delimiter) 
    else:
        print('WRONG FILE EXTENSION')

    if not df.empty:
        df.columns = df.columns.str.lower().str.strip().str.replace(' ', '_').str.replace('.', '')

    return df


def del_file(file):
    """
    Function to delete files from given path
    :param file: complete path to the file to be removed, e.g. /tmp/reports/123.csv
    :type str
    """
    try:
        os.remove(file)
        print("%s has been removed successfully" % file)
    except OSError as e:
        print("Error: %s - %s." % (e.filename, e.strerror))


def del_dir(path):
    """
    Function for recursive directory delete
    :param path: complete path to the report to be removed, e.g. /tmp/reports/networks
    :type str
    """
    rmtree(path)
    print("Directory: %s has been removed successfully" % path)


def truncate_table(db_table, engine):
    """
    Function used to truncate table data before loading
    :param db_table: table to be truncated
    :type db_table: str
    :param engine: db engine to be used
    :param flag: boolean flag to truncate or not
    :type flag: bool
    """
    truncate_sql = f"TRUNCATE TABLE {db_table}"
    with engine.connect() as con:
        con.execution_options(autocommit=True).execute(truncate_sql)
        print('Table %s truncated' % db_table)


def db_load(df, engine, db_table):
    """
    :param engine: db engine
    :param df: df to be inserted into the database
    :type df: pandas dataframe
    :param db_table: database table
    :type db_table: str
    """
    if engine.has_table(db_table):
        df.to_sql(db_table, con=engine, chunksize=1000, if_exists='append', index=False)
        print(f"Data sucessfully loaded into {db_table}!")
    else:
        df.to_sql(db_table, con=engine, chunksize=1000, if_exists='replace', index=True, index_label='id')
        print(f"New table: {db_table} created sucessfully!")


def tableCheck(engine, table):
    """
    Function to check if table exists
    :param engine: db engine
    :param table: database table
    :return: bool True or False
    """
    return engine.has_table(table)


def loadData(engine, query, db_table, report_data, sort_col, drop_col):
    """
    Function that queries database table (if exists),
    Merge both dataframes into one (updating existing/adding new rows)
    Sort and drop duplicate entries and finally load report into the database
    :param engine: db engine to be used
    :param query: sql query to database
    :param db_table: table from BD
    :param report_data: dataframe with the report data to be ingested
    :param sort_col: column to be used to sort dataframe
    :param drop_col: column to be used to drop duplicate entries (normally unique ids)
    """
    if engine.has_table(db_table):
        df = pd.read_sql_query(query, engine)
        df = df.astype(str)
        df = df.append(report_data)
        df = df.sort_values(by=sort_col).drop_duplicates(subset=[drop_col], keep='last').dropna(subset=[drop_col])
        truncate_table(db_table, engine)
        df.to_sql(db_table, con=engine, chunksize=1000, if_exists='append', index=False)
    else:
        report_data.to_sql(db_table, con=engine, chunksize=1000, if_exists='replace', index=True, index_label='id')


def df_compare(df1, df2, merge_cols, which=None):
    """
    Find rows that are different between two DataFrames
    """
    comparison_df = df1.merge(df2,
                              on=merge_cols,
                              indicator=True,
                              how='outer')
    if which is None:
        final_df = comparison_df[comparison_df['_merge'] != 'both']
    else:
        final_df = comparison_df[comparison_df['_merge'] == which]

    return final_df


def logs(path, file):
    """
    create a log file to record the script logs
    :param path: Path to root feature dir
    :param file: Log file name
    :type path: str
    :type file: str
    """
    log_file = os.path.join(path, file)
    if not os.path.isfile(log_file):
        open(log_file, "w+").close()
    console_logging_format = "%(levelname)s: %(asctime)s: %(message)s"
    file_logging_format = "%(levelname)s: %(asctime)s: %(message)s"
    logging.basicConfig(level=logging.WARNING, format=console_logging_format, datefmt='%d-%m-%Y %H:%M:%S')
    logger = logging.getLogger()
    handler = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding='utf-8')
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(file_logging_format, "%d-%m-%Y %H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def datify(report_date):
    """
    function to convert str to datetime format
    :param report_date: df date to be converted
    :type report_date: str
    :return str with datetime format
    """
    try:
        date = dt.datetime.strptime(report_date, '%Y-%m-%d')
    except:
        date = dt.datetime.strptime(report_date, '%d-%m-%Y')

    return str(date)


def get_ingested_data(engine, report_name, report_oss):
    """
    Function to get data that was previously loaded from db ingestion log table
    :param engine: db engine
    :param report_name: report name from report_info dict
    :param report_oss:  report oss region from report_info dict
    :return:
    """
    ing_table = 'report_ing_log'
    query = f"select max(report_date) as max_date from {ing_table} where upper(report_name) = '{report_name}' and upper(report_oss) = '{report_oss}' and error_code = '200'"
    df_file_logs = pd.read_sql_query(query, engine)
    if df_file_logs.max_date[0] != None:
        last_date = df_file_logs['max_date'][0]
    else:
        print(f"No data found for {report_oss}")
        last_date = ''

    return str(last_date)


def ingest_log(db_engine, report_info, code, type_, description):
    """
    Function to log ingested data into our logs table
    :param db_engine: db engine
    :param report_info: report info dict
    :param code: error codes (eg: 200(for SUCCESS), 500(for Code Bug), etc)
    :param type_:  error type, if occurs (eg: INTERNAL ERROR)
    :param description: Error description (eg: Code Bug)
    """
    db_table = 'report_ing_log'
    in_oss = report_info['oss_report'].upper()
    in_report = report_info['report_name'].upper()
    in_date = datify(report_info['report_date'])[:10]
    now_date = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    ing_dic = {'id': '', 'report_name': [in_report], 'report_oss': [in_oss], 'report_date': [in_date],
               'error_code': [code], 'error_type': [type_], 'description': [description], 'ingest_date': [now_date]}
    df_ing_log = pd.DataFrame(ing_dic)
    df_ing_log = df_ing_log.astype('str')
    try:
        db_load(df_ing_log, db_engine, db_table)
    except:
        print('Failed connection to database!')
        print(df_ing_log)


def send_email_rep(db_engine, report_name, report_count, to_address, temp_root):
    query = """SELECT count(*) as repcount, report_name 
    from `report_ing_log`
    where report_date >= CURDATE()
    AND error_code = '200'
    AND report_name = '{report_name}'
    AND email_sent = 0
    group by report_name""".format(report_name=report_name)
    update_query = text("""UPDATE `report_ing_log` SET `email_sent`=1 
    WHERE report_date >= CURDATE()
    AND error_code = '200'
    AND report_name = '{report_name}'
    AND email_sent = 0""".format(report_name=report_name))
    repCheck = pd.read_sql_query(query, db_engine)
    path = os.path.abspath(temp_root) + os.sep
    dir_path = os.listdir(path + report_name + "/")
    subject = report_name + " Dump - " + dt.datetime.now().strftime("%d-%m-%Y")
    message = "Hi all\n\n in attach the " + report_name + " Dump.\n\n"

    if repCheck.repcount[0] >= report_count:
        print("Creating Zip File!")
        zipFile = zipfile.ZipFile(path + report_name + "/" + report_name + '_dump.zip', 'w')
        for file_name in dir_path:
            zipFile.write(path + report_name + "/" + file_name, file_name, compress_type=zipfile.ZIP_DEFLATED)
        zipFile.close()
        print("Sending e-mail!")
        print(
            "Notification ready for configured recipient(s): "
            + to_address
            + ". The retired deployment handed this ZIP to its local mail gateway."
        )
        if os.path.exists(path + report_name + "/") and os.path.isdir(path + report_name + "/"):
            del_dir(path + report_name + "/")
        db_engine.execute(update_query)
