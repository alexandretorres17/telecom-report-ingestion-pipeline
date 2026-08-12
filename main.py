#! /usr/bin/python
#
# Script to connect to mailbox and trigger report load into DB based on email information
# Collect subject to identify report
# if contains zip it will unzip
import configparser
import email
import email.header
import imaplib
import os
import re
import zipfile
from shutil import copyfile
from sqlalchemy import create_engine
from email.header import decode_header
from pathlib import Path
from aux_func import del_dir, logs, datify, get_ingested_data, ingest_log, send_email_rep
from networks import import_networks
from externals import import_externals
from pki import import_pki
from hua_logs import import_logs
from others import import_others


#############
##Variables##
#############
config = configparser.ConfigParser()
config_path = os.environ.get(
    "REPORT_PIPELINE_CONFIG",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini"),
)
config.read(config_path)
## /!\ Email setup
EMAIL_SERVER_CO = config.get('EMAIL', 'server')
EMAIL_ACCOUNT = config.get('EMAIL', 'account')
EMAIL_PASS = config.get('EMAIL', 'pass')
EMAIL_FOLDER = config.get('EMAIL', 'folder')
# /!\ Database setup
HOST = config.get('DATABASE', 'host')
USER = config.get('DATABASE', 'user')
PASSWD = config.get('DATABASE', 'pass')
DATABASE = config.get('DATABASE', 'dbschema')
## /!\ Misc setup
path_temp = config.get('DEFAULT', 'path_tmp')
path_script = config.get('DEFAULT', 'path_script')
path_script_temp = path_script + "temp/"
oss_names = config.get('DEFAULT', 'oss').split(',')
weekplan_path = config.get('DEFAULT', 'weekplan_path')
network_recipients = config.get('EMAIL', 'network_recipients')
external_recipients = config.get('EMAIL', 'external_recipients')
pki_recipients = config.get('EMAIL', 'pki_recipients')
log_path = os.path.dirname(os.path.abspath(__file__))
my_logger = logs(log_path, 'script.log')

#################
# Aux Functions #
#################


def unzip_file(orig_file, dest_file):
    list_files = []
    destination = Path(dest_file).resolve()
    with zipfile.ZipFile(orig_file, 'r') as zip_ref:
        for name in zip_ref.namelist():
            target = (destination / name).resolve()
            if destination not in target.parents and target != destination:
                raise ValueError(f"Unsafe archive member: {name}")
            list_files.append(name)
        zip_ref.extractall(destination)
    os.unlink(orig_file)
    return list_files


def read_emails(imap_con):
    typ, msgs = imap_con.search(None, 'ALL')
    msgs = msgs[0].split()
    for email_id in msgs:
        report_info = dict()
        resp, data = imap_con.fetch(email_id, "(RFC822)")
        email_body = data[0][1]
        file_names = []
        m = email.message_from_bytes(email_body)
        subject = decode_header(m["Subject"])[0][0]
        subject_array = re.split(r"[\[\]]", subject)
        subject_array = list(filter(None, subject_array))
        report_info["report_id"] = subject_array[0]
        if subject_array[1] != "" and report_info["report_id"] == "Report":
            if subject_array[1] in oss_names:
                report_info["oss_report"] = subject_array[1]
                report_info["report_name"] = subject_array[2]
                report_info["report_date"] = subject_array[3]
            else:
                report_info["oss_report"] = ""
                report_info["report_name"] = subject_array[1]
                report_info["report_date"] = subject_array[2]

            if report_info["oss_report"] != "":
                print("Found the E-mail for Report: " + report_info["report_id"] + ", for the OSS: " + report_info["oss_report"] + ", with the name: "
                      + report_info["report_name"] + ", with the date: " + report_info["report_date"])
                full_path = path_temp + report_info["report_name"] + "/" + report_info["oss_report"] + "/"

            else:
                print("Found the E-mail for Report: " + report_info["report_id"] + ", with the name: " + report_info["report_name"] +
                      ", with the date: " + report_info["report_date"])
                full_path = path_temp + report_info["report_name"] + "/"

            Path(full_path).mkdir(parents=True, exist_ok=True)
            # check if there is a file or not and collects the file or the body of the email
            for part in m.walk():
                filename = part.get_filename()
                if filename is not None:
                    for parts in decode_header(part.get_filename()):
                        if parts[1] != None:
                            filename = (str(*parts))
                    full_path_file = os.path.join(full_path, filename)
                    n, file_extension = os.path.splitext(full_path_file)
                    if file_extension == ".csv":
                        fp = open(full_path_file, 'wb')
                        fp.write(part.get_payload(decode=True))
                        fp.close()
                        file_names.append(filename)
                        file_names = list(filter(None, file_names))
                        # print(file_names)

                    elif file_extension == ".zip":
                        fp = open(full_path_file, 'wb')
                        fp.write(part.get_payload(decode=True))
                        fp.close()
                        file_names = unzip_file(full_path_file, full_path)
                        # print(file_names)

                    else:
                        fp = open(full_path_file, 'wb')
                        fp.write(part.get_payload(decode=True))
                        fp.close()
                        file_names.append(filename)

                else:
                    if part.get_content_type() == 'text/plain':
                        content = part.get_payload(None, True)  # prints the raw text
                        file_names.append(filename)
                        # print("E-mail Content: " + str(content))
        imap_con.copy(email_id, EMAIL_FOLDER + '/old')
        imap_con.store(email_id, '+FLAGS', '\\Deleted')

        report_import(report_info, full_path, file_names)
        try:
            del_dir(full_path)
        except OSError as e:
            my_logger.error("Error: %s - %s." % (e.filename, e.strerror))
    imap_con.expunge()


def report_import(report_info, full_path, file_list):
    """
    :param report_info: dicionario constituido por: oss_report; report_name; report_date
    :param full_path: o caminho onde estão os ficheiros
    :param file_list: array com o nome dos ficheiros que vieram do email
    """
    # Report_info dicionario constituido por: oss_report; report_name; report_date
    # Full_path o caminho onde estão os ficheiros
    # file_list array com o nome dos ficheiros que vieram do email
    print("Pandas data handling:")
    check_name = report_info['report_name'].upper()
    check_region = report_info['oss_report'].upper()
    check_date = datify(report_info['report_date'])[:10]
    succ_msg = f"Report: {check_name} ({check_date}) from {check_region} successfully loaded!"
    err_msg = f"Error occured for report: [{check_name}][{check_region}][{check_date}]"
    my_logger.info('Report found: ' + report_info['report_name'])
    db_engine = create_engine(f"mysql+mysqlconnector://{USER}:{PASSWD}@{HOST}/{DATABASE}", echo=False)
    try:
        if check_name.upper() == "WEEKPLAN":
            db_date = get_ingested_data(db_engine, check_name, check_region)
            if check_date >= db_date:
                my_logger.info("Copying file: {0}".format(str(file_list[0])))
                try:
                    copyfile(full_path + file_list[0], os.path.join(weekplan_path, file_list[0]))
                    ingest_log(db_engine, report_info, '200', 'SUCCESS', '')
                    my_logger.info(succ_msg)
                except:
                    my_logger.error(err_msg, exc_info=True)
                    ingest_log(db_engine, report_info, '500', 'INTERNAL ERROR', 'Code Bug')

        elif check_name.upper() == "NETWORKS":
            db_date = get_ingested_data(db_engine, check_name, check_region)
            if check_date > db_date:
                my_logger.info(f"Loading data for: {check_name}")
                try:
                    import_networks(check_region, check_date, full_path, file_list, db_engine, path_script_temp)
                    ingest_log(db_engine, report_info, '200', 'SUCCESS', '')
                    send_email_rep(db_engine, "NETWORKS", 2, network_recipients, path_script_temp)
                    my_logger.info(succ_msg)
                except:
                    my_logger.error(err_msg, exc_info=True)
                    ingest_log(db_engine, report_info, '500', 'INTERNAL ERROR', 'Code Bug')
        elif check_name.upper() == "EXTERNALS":
            db_date = get_ingested_data(db_engine, check_name, check_region)
            if check_date >= db_date:
                my_logger.info(f"Loading data for: {check_name}")
                try:
                    import_externals(check_region, check_date, full_path, file_list, db_engine, path_script_temp)
                    ingest_log(db_engine, report_info, '200', 'SUCCESS', '')
                    my_logger.info(succ_msg)
                    send_email_rep(db_engine, "EXTERNALS", 2, external_recipients, path_script_temp)
                except:
                    my_logger.error(err_msg, exc_info=True)
                    ingest_log(db_engine, report_info, '500', 'INTERNAL ERROR', 'Code Bug')
        elif check_name.upper() == "PKI":
            db_date = get_ingested_data(db_engine, check_name, check_region)
            if check_date > db_date:
                my_logger.info(f"Loading data for: {check_name}")
                try:
                    import_pki(full_path, file_list, db_engine, path_script_temp)
                    ingest_log(db_engine, report_info, '200', 'SUCCESS', '')
                    my_logger.info(succ_msg)
                    send_email_rep(db_engine, "PKI", 2, pki_recipients, path_script_temp)
                except:
                    my_logger.error(err_msg, exc_info=True)
                    ingest_log(db_engine, report_info, '500', 'INTERNAL ERROR', 'Code Bug')
        elif check_name.upper() == "HCMD":
            db_date = get_ingested_data(db_engine, check_name, check_region)
            if check_date >= db_date:
                my_logger.info(f"Loading data for: {check_name}")
                try:
                    import_logs(full_path, db_engine)
                    ingest_log(db_engine, report_info, '200', 'SUCCESS', '')
                    my_logger.info(succ_msg)
                except:
                    my_logger.error(err_msg, exc_info=True)
                    ingest_log(db_engine, report_info, '500', 'INTERNAL ERROR', 'Code Bug')

        else:
            db_date = get_ingested_data(db_engine, check_name, check_region)
            if check_date > db_date:
                my_logger.info(f"Loading data for: {check_name}")
                try:
                    import_others(check_name, check_region, full_path, file_list, db_engine)
                    ingest_log(db_engine, report_info, '200', 'SUCCESS', '')
                    my_logger.info(succ_msg)
                except:
                    my_logger.error(err_msg, exc_info=True)
                    ingest_log(db_engine, report_info, '500', 'INTERNAL ERROR', 'Code Bug')

    except:
        my_logger.error(err_msg, exc_info=True)


################
### Main Run ###
################
def main():
    """
    Script main run
    """
    my_logger.info('Starting script...')
    mail = imaplib.IMAP4_SSL(EMAIL_SERVER_CO)
    mail.login(EMAIL_ACCOUNT, EMAIL_PASS)
    mail.select(EMAIL_FOLDER)
    read_emails(mail)
    my_logger.info('Script execution finished!')


if __name__ == '__main__':
    main()
