#! /usr/bin/python
import pandas as pd
import numpy as np
from aux_func import file_load, loadData
import re
import os
from pathlib import Path

REPORT_NAME = "NETWORKS"


def import_networks(report_oss, report_date, full_path, file_list, engine, script_path):
    """
    Import Network information from Huawei
    :param engine: db engine used to connect to DB
    :param report_oss: argument passed by main run .py with oss region
    :type report_oss: str
    :param report_date: argument passed by main run .py with report date
    :type report_date: str
    :param full_path: path where the .csv files are
    :type full_path: str
    :param file_list list of files to be loaded
    :type file_list: list
    :param script_path: path of the script
    :type script_path: str
    """
    allowed_files = ['2G_BSC_List.csv', 'NodeB Info.csv', '3G_Cell_List.csv', '2G_Cell_List.csv', '5G_Cell_List.csv',
                     '2G_Cell_TRX.csv', '5G_Site_List.csv', '3G_Site_List.csv', '2G_Site_List.csv',
                     '4G_Site_List.csv', '4G_Cell_List.csv']
    files_filter = [f for f in file_list if f in allowed_files]

    for file_name in files_filter:
        table_data = file_load(full_path+file_name, 1)
        if file_name == "2G_BSC_List.csv":
            db_table = "huawei_parent"
            columns = ["huawei_parent_name", "huawei_parent_osp_code",
                       "huawei_parent_sw", "huawei_parent_oss",
                       "huawei_parent_update_date"]
            table_data_rnc = file_load(full_path + "3G_RNC_List.csv", 1)
            table_data_rnc.rename(columns={'node_id': 'osp_code[whole_number]'}, inplace=True)
            table_data = table_data.append(table_data_rnc, ignore_index=True)
            table_data["oss"] = report_oss
            table_data.rename(columns={'bsc_name': 'name', 'nedspver': 'sw', 'osp_code[whole_number]': 'osp_code'},
                              inplace=True)

            table_data["update_date"] = report_date
            table_data.columns = [db_table + '_' + str(col_name) for col_name in table_data.columns]
            table_data = table_data[columns]
            query = f"""select {str(columns)[1:-1].replace("'", "")} from {db_table} where {db_table}_update_date like '{report_date}%'"""
            loadData(engine, query, db_table, table_data, f"{db_table}_update_date", f"{db_table}_name")

            # Create a Readble report to be sent to team
            filter_cols = ["huawei_parent_name", "huawei_parent_osp_code",
                           "huawei_parent_sw", "huawei_parent_oss"]

            table_data = table_data[filter_cols]
            # Change the name of the columns to the original
            table_data.rename(columns={"huawei_parent_name": "BSC Name",
                                       "huawei_parent_osp_code": "OSP code[Whole Number]",
                                       "huawei_parent_sw": "NeDspVer", "huawei_parent_oss": "Area"},
                              inplace=True)

        if file_name == "2G_Site_List.csv":
            db_table = "huawei_2g_site"
            columns = ["huawei_2g_site_unique_id", "huawei_2g_site_bts_index", "huawei_2g_site_bts_name",
                       "huawei_2g_site_numb_name", "huawei_2g_site_bts_type", "huawei_2g_site_serv_type",
                       "huawei_2g_site_status", "huawei_2g_site_bts_software_version", "huawei_2g_site_parent",
                       "huawei_2g_site_sran", "huawei_2g_site_oss", "huawei_2g_site_update_date"]
            table_data["unique_id"] = table_data['bsc_name'] + "-" + table_data['bts_index']
            data_co_mpt = file_load(full_path + "CO-MPT 2G.csv", 1)
            table_data = pd.merge(table_data, data_co_mpt[['gbts_function_name', 'ne_name', 'product_version']],
                                  left_on=["bts_name"], right_on=['gbts_function_name'], how='outer')
            software_list = ["bts_software_version_1", "product_version"]
            table_data[software_list] = table_data[software_list].fillna("UNKNOWN")
            table_data['bts_software_version'] = table_data.apply(lambda x: sw_merge(x['bts_software_version_1'], x['product_version'],
                                                                   'UNKNOWN'), axis=1)
            table_data['sran'] = table_data['ne_name'].fillna("")
            table_data = table_data.drop(columns=['bts_software_version_1', 'gbts_function_name', 'product_version', 'ne_name'])
            table_data["oss"] = report_oss
            table_data["numb_name"] = table_data["bts_name"].str.replace(r"\D", "")
            table_data.rename(columns={'bsc_name': 'parent', 'service_type': 'serv_type', 'active_status': 'status'},
                              inplace=True)
            table_data["update_date"] = report_date
            table_data.columns = [db_table + '_' + str(col_name) for col_name in table_data.columns]
            table_data = table_data[columns]
            table_data = table_data.dropna(subset=['huawei_2g_site_bts_name', 'huawei_2g_site_sran']).drop_duplicates(['huawei_2g_site_bts_name'])
            query = f"""select {str(columns)[1:-1].replace("'", "")} from {db_table} where {db_table}_update_date like '{report_date}%'"""
            loadData(engine, query, db_table, table_data, f"{db_table}_update_date", f"{db_table}_unique_id")

            # Create a Readble report to be sent to team
            filter_cols = ["huawei_2g_site_bts_index", "huawei_2g_site_bts_name",
                           "huawei_2g_site_bts_type", "huawei_2g_site_serv_type",
                           "huawei_2g_site_status", "huawei_2g_site_bts_software_version", "huawei_2g_site_parent",
                           "huawei_2g_site_sran", "huawei_2g_site_oss", "huawei_2g_site_numb_name"]
            table_data = table_data[filter_cols]
            # Change the name of the columns to the original
            table_data.rename(columns={"huawei_2g_site_bts_index": "BTS Index", "huawei_2g_site_bts_name": "BTS Name",
                                       "huawei_2g_site_bts_type": "BTS Type", "huawei_2g_site_serv_type": "Service Type"
                                       , "huawei_2g_site_status": "Active Status",
                                       "huawei_2g_site_bts_software_version": "BTS Software Version 1",
                                       "huawei_2g_site_parent": "BSC Name",
                                       "huawei_2g_site_sran": "SRAN", "huawei_2g_site_oss": "Area", "huawei_2g_site_numb_name": "SiteId"},
                              inplace=True)
            # Reorder columns
            table_data = table_data[["BSC Name", "BTS Name", "BTS Index", "BTS Type", "Service Type", "Active Status",
                                     "SRAN", "BTS Software Version 1", "Area", "SiteId"]]
            table_data['NE Name'] = table_data.apply(lambda row: row['BTS Name'] if row['SRAN'] == '' else row['SRAN'], axis=1)

        elif file_name == "2G_Cell_List.csv":
            db_table = "huawei_2g_cell"
            columns = ["huawei_2g_cell_unique_id", "huawei_2g_cell_index", "huawei_2g_cell_cgi", "huawei_2g_cell_name",
                       "huawei_2g_cell_freq", "huawei_2g_cell_mcc", "huawei_2g_cell_mnc", "huawei_2g_cell_lac",
                       "huawei_2g_cell_ci", "huawei_2g_cell_ncc", "huawei_2g_cell_bcc", "huawei_2g_cell_rac",
                       "huawei_2g_cell_bts_index", "huawei_2g_cell_bts_name", "huawei_2g_cell_name_numb",
                       "huawei_2g_cell_state", "huawei_2g_cell_active", "huawei_2g_cell_operator",
                       "huawei_2g_cell_parent", "huawei_2g_cell_local_cell_id", "huawei_2g_cell_oss",
                       "huawei_2g_cell_update_date"]

            table_data["cgi"] = table_data['mcc'] + "-" + table_data['mnc'] + "-" + table_data['cell_lac'] + "-" + \
                                table_data['cell_ci']
            table_data["unique_id"] = table_data['bsc_name'] + "-" + table_data['cgi']
            table_data["name_numb"] = table_data["bts_name"].str.replace(r"\D", "")
            table_data["oss"] = report_oss
            table_data["update_date"] = report_date
            table_data.rename(columns={'bsc_name': 'parent', 'cell_name': 'name', 'cell_lac': 'lac', 'cell_ci': 'ci',
                                       'cell_index': 'index', 'administrative_state': 'state',
                                       'active_status': 'active', 'operator_name': 'operator', 'routing_area': 'rac',
                                       'freq_band': 'freq'},
                              inplace=True)
            table_data = table_data.sort_values(by=['unique_id', 'rac'])
            table_data.columns = [db_table + '_' + str(col_name) for col_name in table_data.columns]
            table_data = table_data[columns]
            query = f"""select {str(columns)[1:-1].replace("'", "")} from {db_table} where {db_table}_update_date like '{report_date}%'"""
            loadData(engine, query, db_table, table_data, f"{db_table}_update_date", f"{db_table}_unique_id")

            # Create a Readble report to be sent to team
            filter_cols = ["huawei_2g_cell_index", "huawei_2g_cell_cgi", "huawei_2g_cell_name",
                           "huawei_2g_cell_freq", "huawei_2g_cell_mcc", "huawei_2g_cell_mnc", "huawei_2g_cell_lac",
                           "huawei_2g_cell_ci", "huawei_2g_cell_ncc", "huawei_2g_cell_bcc", "huawei_2g_cell_rac",
                           "huawei_2g_cell_bts_index", "huawei_2g_cell_bts_name",
                           "huawei_2g_cell_state", "huawei_2g_cell_active", "huawei_2g_cell_operator",
                           "huawei_2g_cell_parent", "huawei_2g_cell_local_cell_id", "huawei_2g_cell_oss"]

            table_data = table_data[filter_cols]
            # Change the name of the columns to the original
            table_data.rename(columns={"huawei_2g_cell_index": "Cell Index", "huawei_2g_cell_cgi": "CGI",
                                       "huawei_2g_cell_name": "Cell Name", "huawei_2g_cell_freq": "Freq. Band",
                                       "huawei_2g_cell_mcc": "MCC", "huawei_2g_cell_mnc": "MNC",
                                       "huawei_2g_cell_lac": "Cell LAC", "huawei_2g_cell_ci": "Cell CI",
                                       "huawei_2g_cell_ncc": "NCC", "huawei_2g_cell_bcc": "BCC",
                                       "huawei_2g_cell_rac": "Routing Area", "huawei_2g_cell_bts_index": "BTS Index",
                                       "huawei_2g_cell_bts_name": "BTS Name",
                                       "huawei_2g_cell_state": "Administrative State",
                                       "huawei_2g_cell_active": "active status",
                                       "huawei_2g_cell_operator": "Operator Name", "huawei_2g_cell_parent": "BSC Name",
                                       "huawei_2g_cell_local_cell_id": "Local Cell ID", "huawei_2g_cell_oss": "Area"},
                              inplace=True)
            # Reorder columns
            table_data = table_data[["BSC Name", "BTS Name", "Cell Name", "Cell Index", "Freq. Band", "MCC", "MNC",
                                     "Cell LAC", "Cell CI", "NCC", "BCC", "BTS Index", "Administrative State",
                                     "active status", "Operator Name", "Routing Area", "Local Cell ID", "CGI", "Area"]]

        elif file_name == "2G_Cell_TRX.csv":
            db_table = "huawei_2g_trx"
            columns = ["huawei_2g_trx_unique_id", "huawei_2g_trx_parent", "huawei_2g_trx_bts_name",
                       "huawei_2g_trx_bsc_cell_name", "huawei_2g_trx_bsc_cell_index", "huawei_2g_trx_cell_index",
                       "huawei_2g_trx_main_bcch", "huawei_2g_trx_freq", "huawei_2g_trx_number", "huawei_2g_trx_trx_id",
                       "huawei_2g_trx_active_status", "huawei_2g_trx_admin_status", "huawei_2g_trx_oss",
                       "huawei_2g_trx_update_date", "huawei_2g_trx_name"]

            table_data["unique_id"] = table_data['bsc_name'] + "-" + table_data['cell_name'] + "-" + \
                                      table_data['cell_index'] + "-" + table_data['trx_id']
            table_data["oss"] = report_oss
            table_data["update_date"] = report_date
            table_data.rename(columns={'bsc_name': 'parent', 'is_main_bcch_trx': 'main_bcch', 'frequency': 'freq',
                                       'trx_no': 'number', 'administrative_state': 'admin_status',
                                       'cell_name': 'bsc_cell_name', 'cell_index': 'bsc_cell_index',
                                       'cell_index1': 'cell_index', "trx_name": "name"},
                              inplace=True)
            table_data = table_data.sort_values(by=['unique_id']).drop_duplicates('unique_id')
            table_data.columns = [db_table + '_' + str(col_name) for col_name in table_data.columns]
            table_data = table_data[columns]
            query = f"""select {str(columns)[1:-1].replace("'", "")} from {db_table} where {db_table}_update_date like '{report_date}%'"""
            loadData(engine, query, db_table, table_data, f"{db_table}_update_date", f"{db_table}_unique_id")

            # Create a Readble report to be sent to team
            filter_cols = ["huawei_2g_trx_parent", "huawei_2g_trx_bts_name",
                           "huawei_2g_trx_bsc_cell_name", "huawei_2g_trx_bsc_cell_index", "huawei_2g_trx_cell_index",
                           "huawei_2g_trx_main_bcch", "huawei_2g_trx_freq", "huawei_2g_trx_number",
                           "huawei_2g_trx_trx_id",
                           "huawei_2g_trx_active_status", "huawei_2g_trx_admin_status", "huawei_2g_trx_name",
                           "huawei_2g_trx_oss"]

            table_data = table_data[filter_cols]
            # Change the name of the columns to the original
            table_data.rename(columns={"huawei_2g_trx_parent": "BSC Name", "huawei_2g_trx_bts_name": "BTS Name",
                                       "huawei_2g_trx_bsc_cell_name": "Cell Name",
                                       "huawei_2g_trx_bsc_cell_index": "BSC Cell Index",
                                       "huawei_2g_trx_cell_index": "Cell Index",
                                       "huawei_2g_trx_main_bcch": "Is Main BCCH TRX",
                                       "huawei_2g_trx_freq": "Frequency", "huawei_2g_trx_number": "TRX No.",
                                       "huawei_2g_trx_trx_id": "TRX ID", "huawei_2g_trx_active_status": "Active Status",
                                       "huawei_2g_trx_admin_status": "Administrative State",
                                       "huawei_2g_trx_name": "TRX Name", "huawei_2g_trx_oss": "Area"},
                              inplace=True)
            # Reorder columns
            table_data = table_data[["BSC Name", "BTS Name", "Cell Name", "BSC Cell Index", "Cell Index",
                                     "Is Main BCCH TRX", "Frequency", "TRX No.", "TRX ID", "Active Status",
                                     "Administrative State", "TRX Name", "Area"]]

        elif file_name == "3G_Site_List.csv":
            db_table = "huawei_3g_site"
            columns = ["huawei_3g_site_unique_id", "huawei_3g_site_name", "huawei_3g_site_numb", "huawei_3g_site_index",
                       "huawei_3g_site_subrack_no", "huawei_3g_site_slot_no", "huawei_3g_site_subsystem_no",
                       "huawei_3g_site_iub_transport", "huawei_3g_site_sharing_type", "huawei_3g_site_state",
                       "huawei_3g_site_nodeb_ip_trans_ip_address", "huawei_3g_site_nodeb_ip_trans_ip_mask",
                       "huawei_3g_site_nodeb_ip_trans_subrack_no", "huawei_3g_site_nodeb_ip_trans_slot_no",
                       "huawei_3g_site_nodeb_atm_trans_ip_address", "huawei_3g_site_nodeb_atm_trans_ip_mask",
                       "huawei_3g_site_nodeb_atm_trans_subrack_no", "huawei_3g_site_nodeb_atm_trans_slot_no",
                       "huawei_3g_site_parent", "huawei_3g_site_software", "huawei_3g_site_cabinet",
                       "huawei_3g_site_sran_name", "huawei_3g_site_oss", "huawei_3g_site_update_date"]
            data_co_mpt = file_load(full_path + "CO-MPT 3G.csv", 1).dropna(subset=['nodeb_function_name'])
            data_nodeb_info = file_load(full_path + "NodeB Info.csv", 0)
            table_data = pd.merge(table_data, data_co_mpt[['nodeb_function_name', 'ne_name', 'product_version',
                                                           'cabinet_type']],left_on=["nodeb_name"], right_on=['nodeb_function_name'], how='outer')
            table_data = pd.merge(table_data, data_nodeb_info[["nodeb_name", 'nodeb_version', 'nodeb_type']], on=['nodeb_name'], how='outer')
            table_data = table_data.sort_values(by=['ne_name'])
            table_data["unique_id"] = table_data['bsc_name'] + "-" + table_data['nodeb_id']
            table_data['cabinet'] = table_data['nodeb_type'].replace("UMTS", np.nan).combine_first(table_data['cabinet_type']).fillna("UNKNOWN")
            software_list = ["nodeb_version", "product_version"]
            table_data[software_list] = table_data[software_list].fillna("UNKNOWN")
            table_data['software'] = table_data.apply(lambda x: sw_merge(x['nodeb_version'], x['product_version'],
                                                                   'UNKNOWN'), axis=1)
            table_data['sran_name'] = table_data['ne_name'].fillna("")
            table_data = table_data.drop(columns=['nodeb_version', 'nodeb_function_name', 'product_version', 'ne_name',
                                                  'nodeb_type', 'cabinet_type'])
            table_data["oss"] = report_oss
            table_data["numb"] = table_data["nodeb_name"].str.replace(r"\D", "").str.lstrip('0')
            table_data.rename(columns={'bsc_name': 'parent', 'nodeb_name': 'name', 'nodeb_id': 'index',
                                       'iub_transport_bearer_type': 'iub_transport',
                                       'sharing_type_of_nodeb': 'sharing_type', 'administrative_state': 'state'},
                              inplace=True)
            table_data.columns = [db_table + '_' + str(col_name) for col_name in table_data.columns]
            table_data[db_table+'_update_date'] = report_date
            table_data = table_data[columns]
            query = f"""select {str(columns)[1:-1].replace("'", "")} from {db_table} where {db_table}_update_date like '{report_date}%'"""
            loadData(engine, query, db_table, table_data, f"{db_table}_update_date", f"{db_table}_unique_id")

            # Create a Readble report to be sent to team
            filter_cols = ["huawei_3g_site_name", "huawei_3g_site_index",
                           "huawei_3g_site_subrack_no", "huawei_3g_site_slot_no", "huawei_3g_site_subsystem_no",
                           "huawei_3g_site_iub_transport", "huawei_3g_site_sharing_type", "huawei_3g_site_state",
                           "huawei_3g_site_nodeb_ip_trans_ip_address", "huawei_3g_site_nodeb_ip_trans_ip_mask",
                           "huawei_3g_site_nodeb_ip_trans_subrack_no", "huawei_3g_site_nodeb_ip_trans_slot_no",
                           "huawei_3g_site_nodeb_atm_trans_ip_address", "huawei_3g_site_nodeb_atm_trans_ip_mask",
                           "huawei_3g_site_nodeb_atm_trans_subrack_no", "huawei_3g_site_nodeb_atm_trans_slot_no",
                           "huawei_3g_site_parent", "huawei_3g_site_software", "huawei_3g_site_cabinet",
                           "huawei_3g_site_sran_name", "huawei_3g_site_oss", "huawei_3g_site_numb"]

            table_data = table_data[filter_cols]
            # Change the name of the columns to the original
            table_data.rename(columns={"huawei_3g_site_name": "NodeB Name", "huawei_3g_site_index": "NodeB ID",
                                       "huawei_3g_site_subrack_no": "Subrack No.", "huawei_3g_site_slot_no": "Slot No.",
                                       "huawei_3g_site_subsystem_no": "Subsystem No.",
                                       "huawei_3g_site_iub_transport": "IUB Transport Bearer Type",
                                       "huawei_3g_site_sharing_type": "Sharing Type Of NodeB",
                                       "huawei_3g_site_state": "Administrative state",
                                       "huawei_3g_site_nodeb_ip_trans_ip_address": "NodeB IP_TRANS IP address",
                                       "huawei_3g_site_nodeb_ip_trans_ip_mask": "NodeB IP_TRANS IP Mask",
                                       "huawei_3g_site_nodeb_ip_trans_subrack_no": "NodeB IP_TRANS Subrack No.",
                                       "huawei_3g_site_nodeb_ip_trans_slot_no": "NodeB IP_TRANS Slot No.",
                                       "huawei_3g_site_nodeb_atm_trans_ip_address": "NodeB ATM_TRANS IP address",
                                       "huawei_3g_site_nodeb_atm_trans_ip_mask": "NodeB ATM_TRANS IP Mask",
                                       "huawei_3g_site_nodeb_atm_trans_subrack_no": "NodeB ATM_TRANS Subrack No.",
                                       "huawei_3g_site_nodeb_atm_trans_slot_no": "NodeB ATM_TRANS Slot No.",
                                       "huawei_3g_site_parent": "BSC Name", "huawei_3g_site_software": "Software",
                                       "huawei_3g_site_cabinet": "Cabinet Type", "huawei_3g_site_sran_name": "SRAN",
                                       "huawei_3g_site_oss": "Area", "huawei_3g_site_numb": "SiteId"},
                              inplace=True)
            # Reorder columns
            table_data = table_data[["BSC Name", "NodeB Name", "NodeB ID", "Subrack No.", "Slot No.", "Subsystem No.",
                                     "IUB Transport Bearer Type", "Sharing Type Of NodeB", "Administrative state",
                                     "NodeB IP_TRANS IP address", "NodeB IP_TRANS IP Mask",
                                     "NodeB IP_TRANS Subrack No.", "NodeB IP_TRANS Slot No.",
                                     "NodeB ATM_TRANS IP address", "NodeB ATM_TRANS IP Mask",
                                     "NodeB ATM_TRANS Subrack No.", "NodeB ATM_TRANS Slot No.", "Software",
                                     "Cabinet Type", "SRAN", "Area", "SiteId"]]
            table_data['NE Name'] = table_data.apply(lambda row: row['NodeB Name'] if row['SRAN'] == '' else row['SRAN'],
                                                     axis=1)

        elif file_name == "3G_Cell_List.csv":
            db_table = "huawei_3g_cell"
            columns = ["huawei_3g_cell_unique_id", "huawei_3g_cell_cgi", "huawei_3g_cell_cell_id",
                       "huawei_3g_cell_name", "huawei_3g_cell_max_power", "huawei_3g_cell_band",
                       "huawei_3g_cell_uplink", "huawei_3g_cell_downlink", "huawei_3g_cell_offset",
                       "huawei_3g_cell_dl_primary_sc", "huawei_3g_cell_site_name", "huawei_3g_cell_local_cell_id",
                       "huawei_3g_cell_lac", "huawei_3g_cell_sac", "huawei_3g_cell_rac_indi", "huawei_3g_cell_rac",
                       "huawei_3g_cell_subrack_no", "huawei_3g_cell_slot_no", "huawei_3g_cell_val_ind",
                       "huawei_3g_cell_state", "huawei_3g_cell_parent", "huawei_3g_cell_cn_opt_index",
                       "huawei_3g_cell_cn_opt_gr_index", "huawei_3g_cell_cn_operator_name",
                       "huawei_3g_cell_mnc", "huawei_3g_cell_mcc", "huawei_3g_cell_oss", "huawei_3g_cell_update_date"]

            table_data["cgi"] = table_data['mobile_country_code'] + "-" + table_data['mobile_network_code'] + "-" \
                                + table_data['location_area_code'] + "-" + table_data['cell_id']

            table_data["unique_id"] = table_data['bsc_name'] + "-" + table_data['cgi']
            table_data["name_numb"] = table_data["nodeb_name"].str.replace(r"\D", "").str.lstrip('0')
            table_data["oss"] = report_oss
            table_data["update_date"] = report_date
            table_data.rename(columns={'bsc_name': 'parent', 'nodeb_name': 'site_name', 'cell_name': 'name',
                                       'max_transmit_power_of_cell': 'max_power', 'band_indicator': 'band',
                                       'uplink_uarfcn': 'uplink', 'downlink_uarfcn': 'downlink',
                                       'time_offset': 'offset', 'dl_primary_scrambling_code': 'dl_primary_sc',
                                       'location_area_code': 'lac', 'service_area_code': 'sac',
                                       'rac_configuration_indication': 'rac_indi', 'routing_area_code': 'rac',
                                       'cell_administrative_state': 'state', 'validation_indication': 'val_ind',
                                       'cn_operator_group_index': 'cn_opt_gr_index', 'mobile_country_code': 'mcc',
                                       'mobile_network_code': 'mnc', 'cn_operator_index': 'cn_opt_index'},
                              inplace=True)
            table_data = table_data.sort_values(by=['unique_id'])
            table_data.columns = [db_table + '_' + str(col_name) for col_name in table_data.columns]
            table_data = table_data[columns]
            query = f"""select {str(columns)[1:-1].replace("'", "")} from {db_table} where {db_table}_update_date like '{report_date}%'"""
            loadData(engine, query, db_table, table_data, f"{db_table}_update_date", f"{db_table}_unique_id")

            # Create a Readble report to be sent to team
            filter_cols = ["huawei_3g_cell_cgi", "huawei_3g_cell_cell_id",
                           "huawei_3g_cell_name", "huawei_3g_cell_max_power", "huawei_3g_cell_band",
                           "huawei_3g_cell_uplink", "huawei_3g_cell_downlink", "huawei_3g_cell_offset",
                           "huawei_3g_cell_dl_primary_sc", "huawei_3g_cell_site_name", "huawei_3g_cell_local_cell_id",
                           "huawei_3g_cell_lac", "huawei_3g_cell_sac", "huawei_3g_cell_rac_indi", "huawei_3g_cell_rac",
                           "huawei_3g_cell_subrack_no", "huawei_3g_cell_slot_no", "huawei_3g_cell_val_ind",
                           "huawei_3g_cell_state", "huawei_3g_cell_parent", "huawei_3g_cell_cn_opt_index",
                           "huawei_3g_cell_cn_opt_gr_index", "huawei_3g_cell_cn_operator_name",
                           "huawei_3g_cell_mnc", "huawei_3g_cell_mcc", "huawei_3g_cell_oss"]

            table_data = table_data[filter_cols]
            # Change the name of the columns to the original
            table_data.rename(columns={"huawei_3g_cell_cgi": "CGI", "huawei_3g_cell_cell_id": "Cell ID",
                                       "huawei_3g_cell_name": "Cell Name",
                                       "huawei_3g_cell_max_power": "Max Transmit Power of Cell",
                                       "huawei_3g_cell_band": "Band Indicator",
                                       "huawei_3g_cell_uplink": "Uplink UARFCN",
                                       "huawei_3g_cell_downlink": "Downlink UARFCN",
                                       "huawei_3g_cell_offset": "Time Offset",
                                       "huawei_3g_cell_dl_primary_sc": "DL Primary Scrambling Code",
                                       "huawei_3g_cell_site_name": "NodeB Name",
                                       "huawei_3g_cell_local_cell_id": "Local Cell ID",
                                       "huawei_3g_cell_lac": "Location Area Code",
                                       "huawei_3g_cell_sac": "Service Area Code",
                                       "huawei_3g_cell_rac_indi": "RAC Configuration Indication",
                                       "huawei_3g_cell_rac": "Routing Area Code",
                                       "huawei_3g_cell_subrack_no": "Subrack No.", "huawei_3g_cell_slot_no": "Slot No.",
                                       "huawei_3g_cell_val_ind": "Validation indication",
                                       "huawei_3g_cell_state": "Cell administrative state",
                                       "huawei_3g_cell_parent": "BSC Name",
                                       "huawei_3g_cell_cn_opt_index": "Cn Operator Index",
                                       "huawei_3g_cell_cn_opt_gr_index": "Cn Operator Group Index",
                                       "huawei_3g_cell_cn_operator_name": "Cn Operator Name",
                                       "huawei_3g_cell_mnc": "Mobile network code",
                                       "huawei_3g_cell_mcc": "Mobile country code", "huawei_3g_cell_oss": "Area"},
                              inplace=True)
            # Reorder columns
            table_data = table_data[["BSC Name", "NodeB Name", "Cell Name", "Max Transmit Power of Cell",
                                     "Band Indicator", "Cell ID", "Downlink UARFCN", "Uplink UARFCN", "Time Offset",
                                     "DL Primary Scrambling Code", "Local Cell ID", "Location Area Code",
                                     "Service Area Code", "RAC Configuration Indication", "Routing Area Code",
                                     "Cell administrative state", "Subrack No.", "Slot No.", "Validation indication",
                                     "Cn Operator Group Index", "Mobile country code", "Mobile network code",
                                     "Cn Operator Index", "Cn Operator Name", "Area"]]

        elif file_name == "4G_Site_List.csv":
            db_table = "huawei_4g_site"
            columns = ["huawei_4g_site_unique_id", "huawei_4g_site_name", "huawei_4g_site_type", "huawei_4g_site_sw",
                       "huawei_4g_site_number", "huawei_4g_site_enodeb_id", "huawei_4g_site_sran_name",
                       "huawei_4g_site_oss", "huawei_4g_site_update_date"]
            data_co_mpt = file_load(full_path + "CO-MPT 4G.csv", 1).dropna(subset=['enodeb_function_name'])\
                .drop_duplicates(['enodeb_function_name'])
            data_co_mpt = data_co_mpt.rename(columns={"ne_name": "sran_name", "enodeb_function_name": "ne_name"})
            table_data = table_data.append(data_co_mpt, ignore_index=True)
            software_list = ['hot_patch_version', 'product_version', 'software_version']
            table_data[software_list] = table_data[software_list].fillna("UNKNOWN")
            table_data['sw'] = table_data.apply(lambda x: sw_merge(x['hot_patch_version'], x['software_version'],
                                                                   x['product_version']), axis=1)
            table_data["number"] = table_data["ne_name"].str[-5:].str.lstrip('0')
            table_data["unique_id"] = report_oss + "-" + table_data['ne_name']
            table_data["oss"] = report_oss
            table_data = table_data.drop(columns=software_list)
            table_data["update_date"] = report_date
            table_data.rename(columns={'ne_name': 'name', 'cabinet_type': 'type'}, inplace=True)
            table_data['sran_name'] = table_data['sran_name'].fillna("")
            table_data.columns = [db_table + '_' + str(col_name) for col_name in table_data.columns]
            table_data = table_data[columns]
            table_data = table_data.sort_values(by=['huawei_4g_site_unique_id','huawei_4g_site_type'])\
                .drop_duplicates('huawei_4g_site_unique_id')
            query = f"""select {str(columns)[1:-1].replace("'", "")} from {db_table} where {db_table}_update_date like '{report_date}%'"""
            loadData(engine, query, db_table, table_data, f"{db_table}_update_date", f"{db_table}_unique_id")

            # Create a Readble report to be sent to team
            filter_cols = ["huawei_4g_site_name", "huawei_4g_site_type", "huawei_4g_site_sw",
                           "huawei_4g_site_enodeb_id", "huawei_4g_site_sran_name", "huawei_4g_site_oss", "huawei_4g_site_number"]

            table_data = table_data[filter_cols]
            # Change the name of the columns to the original
            table_data.rename(columns={"huawei_4g_site_name": "eNodeB Function Name", "huawei_4g_site_type": "Cabinet Type",
                                       "huawei_4g_site_sw": "Software Version",
                                       "huawei_4g_site_enodeb_id": "eNodeB ID", "huawei_4g_site_sran_name": "SRAN",
                                       "huawei_4g_site_oss": "Area", "huawei_4g_site_number": "SiteId"},
                              inplace=True)
            # Reorder columns
            table_data['NE Name'] = table_data.apply(lambda row: row['eNodeB Function Name'] if row['SRAN'] == "" else row['SRAN'],
                                                     axis=1)
            table_data = table_data[["NE Name", "Cabinet Type", "Software Version", "eNodeB ID", "eNodeB Function Name", "SRAN", "Area", "SiteId"]]

        elif file_name == "4G_Cell_List.csv":
            db_table = "huawei_4g_cell"
            columns = ["huawei_4g_cell_unique_id", "huawei_4g_cell_ecgi", "huawei_4g_cell_local_id", "huawei_4g_cell_name",
                       "huawei_4g_cell_freq_band", "huawei_4g_cell_ul_earfcn", "huawei_4g_cell_dl_earfcn",
                       "huawei_4g_cell_cell_id", "huawei_4g_cell_pci", "huawei_4g_cell_mcc", "huawei_4g_cell_mnc",
                       "huawei_4g_cell_operator_name", "huawei_4g_cell_active_state", "huawei_4g_cell_admin_state",
                       "huawei_4g_cell_ne", "huawei_4g_cell_cell_fdd_tdd_indication", "huawei_4g_cell_uplink_bandwidth",
                       "huawei_4g_cell_downlink_bandwidth", "huawei_4g_cell_custom_bw_conf_inf",
                       "huawei_4g_cell_customi_uplink_bw", "huawei_4g_cell_custom_downlink_bw",
                       "huawei_4g_cell_downlink_punct_rb_numb", "huawei_4g_cell_tac", "huawei_4g_cell_enodb_id",
                       "huawei_4g_cell_enodb_function_name", "huawei_4g_cell_oss", "huawei_4g_cell_update_date",
                       "huawei_4g_cell_rsi"]

            data_co_mpt = file_load(full_path + "CO-MPT 4G_Cell_List.csv", 1).dropna(subset=['enodeb_function_name'])
            table_data = pd.merge(table_data, data_co_mpt, how='outer')
            table_data["ecgi"] = ((pd.to_numeric(table_data['enodeb_id'])*256) + pd.to_numeric(table_data['cell_id']))
            table_data["ecgi"] = table_data['mobile_country_code'] + "-" + table_data['mobile_network_code'] + \
                                 "-" + table_data["ecgi"].apply(str)
            table_data["unique_id"] = report_oss + "-" + table_data['ne_name']+"-"+table_data["ecgi"]
            table_data.rename(columns={'cell_name': 'name', 'frequency_band': 'freq_band', 'uplink_earfcn': 'ul_earfcn',
                                       'downlink_earfcn': 'dl_earfcn', 'physical_cell_id': 'pci',
                                       'mobile_country_code': 'mcc', 'mobile_network_code': 'mnc',
                                       'cn_operator_name': 'operator_name', 'cell_active_state': 'active_state',
                                       'cell_admin_state': 'admin_state', 'ne_name': 'ne',
                                       'customized_bandwidth_configure_indicator': 'custom_bw_conf_inf',
                                       'customized_uplink_bandwidth(01mhz)': 'customi_uplink_bw',
                                       'customized_downlink_bandwidth(01mhz)': 'custom_downlink_bw',
                                       'downlink_punctured_rb_number': 'downlink_punct_rb_numb',
                                       'tracking_area_code': 'tac', 'enodeb_id': 'enodb_id', 'root_sequence_index': 'rsi',
                                       'enodeb_function_name': 'enodb_function_name', 'local_cell_id': 'local_id'},
                              inplace=True)
            table_data["oss"] = report_oss
            table_data["update_date"] = report_date
            table_data.columns = [db_table + '_' + str(col_name) for col_name in table_data.columns]
            table_data = table_data[columns]
            query = f"""select {str(columns)[1:-1].replace("'", "")} from {db_table} where {db_table}_update_date like '{report_date}%'"""
            loadData(engine, query, db_table, table_data, f"{db_table}_update_date", f"{db_table}_unique_id")

            # Create a Readble report to be sent to team
            filter_cols = ["huawei_4g_cell_ecgi", "huawei_4g_cell_local_id", "huawei_4g_cell_name",
                           "huawei_4g_cell_freq_band", "huawei_4g_cell_ul_earfcn", "huawei_4g_cell_dl_earfcn",
                           "huawei_4g_cell_cell_id", "huawei_4g_cell_pci", "huawei_4g_cell_mcc", "huawei_4g_cell_mnc",
                           "huawei_4g_cell_operator_name", "huawei_4g_cell_active_state", "huawei_4g_cell_admin_state",
                           "huawei_4g_cell_ne", "huawei_4g_cell_cell_fdd_tdd_indication",
                           "huawei_4g_cell_uplink_bandwidth", "huawei_4g_cell_downlink_bandwidth",
                           "huawei_4g_cell_custom_bw_conf_inf", "huawei_4g_cell_customi_uplink_bw",
                           "huawei_4g_cell_custom_downlink_bw", "huawei_4g_cell_downlink_punct_rb_numb",
                           "huawei_4g_cell_tac", "huawei_4g_cell_enodb_id", "huawei_4g_cell_enodb_function_name",
                           "huawei_4g_cell_oss", "huawei_4g_cell_rsi"]

            table_data = table_data[filter_cols]
            # Change the name of the columns to the original
            table_data.rename(columns={"huawei_4g_cell_ecgi": "ECGI", "huawei_4g_cell_local_id": "Local Cell ID",
                                       "huawei_4g_cell_name": "Cell Name", "huawei_4g_cell_freq_band": "Frequency band",
                                       "huawei_4g_cell_ul_earfcn": "Uplink EARFCN",
                                       "huawei_4g_cell_dl_earfcn": "Downlink EARFCN",
                                       "huawei_4g_cell_cell_id": "Cell ID", "huawei_4g_cell_pci": "Physical cell ID",
                                       "huawei_4g_cell_mcc": "Mobile country code",
                                       "huawei_4g_cell_mnc": "Mobile network code",
                                       "huawei_4g_cell_operator_name": "CN Operator name",
                                       "huawei_4g_cell_active_state": "Cell active state",
                                       "huawei_4g_cell_admin_state": "Cell admin state", "huawei_4g_cell_ne": "NE Name",
                                       "huawei_4g_cell_cell_fdd_tdd_indication": "Cell FDD TDD indication",
                                       "huawei_4g_cell_uplink_bandwidth": "Uplink bandwidth",
                                       "huawei_4g_cell_downlink_bandwidth": "Downlink bandwidth",
                                       "huawei_4g_cell_custom_bw_conf_inf": "Customized bandwidth configure indicator",
                                       "huawei_4g_cell_customi_uplink_bw": "Customized uplink bandwidth(0.1MHz)",
                                       "huawei_4g_cell_custom_downlink_bw": "Customized downlink bandwidth(0.1MHz)",
                                       "huawei_4g_cell_downlink_punct_rb_numb": "Downlink Punctured RB Number",
                                       "huawei_4g_cell_tac": "Tracking area code",
                                       "huawei_4g_cell_enodb_id": "eNodeB ID",
                                       "huawei_4g_cell_enodb_function_name": "eNodeB Function Name",
                                       "huawei_4g_cell_oss": "Area", "huawei_4g_cell_rsi": "Root sequence index"},
                              inplace=True)

            # Order of the columns
            table_data = table_data[["NE Name", "Local Cell ID", "Cell Name", "Frequency band", "Uplink EARFCN",
                                     "Downlink EARFCN", "Cell ID", "Physical cell ID", "Cell active state",
                                     "Cell admin state", "Cell FDD TDD indication", "Uplink bandwidth",
                                     "Downlink bandwidth", "Customized bandwidth configure indicator",
                                     "Customized uplink bandwidth(0.1MHz)", "Customized downlink bandwidth(0.1MHz)",
                                     "Downlink Punctured RB Number", "Tracking area code", "Mobile country code",
                                     "Mobile network code", "CN Operator name", "eNodeB ID", "eNodeB Function Name",
                                     "ECGI", "Root sequence index", "Area"]]

        elif file_name == "5G_Site_List.csv":
            db_table = "huawei_5g_site"
            columns = ["huawei_5g_site_unique_id", "huawei_5g_site_name", "huawei_5g_site_type", "huawei_5g_site_sw",
                       "huawei_5g_site_number", "huawei_5g_site_gnodeb_id", "huawei_5g_site_oss",
                       "huawei_5g_site_update_date"]
            software_list = ['hot_patch_version', 'product_version', 'software_version']
            table_data[software_list] = table_data[software_list].fillna("UNKNOWN")
            table_data['sw'] = table_data.apply(lambda x: sw_merge(x['hot_patch_version'], x['software_version'],
                                                                   x['product_version']),axis=1)
            table_data["unique_id"] = report_oss + "-" + table_data['ne_name']
            table_data["number"] = table_data["ne_name"].str[-5:].str.lstrip('0')
            table_data.rename(columns={'ne_name': 'name', 'cabinet_type': 'type'},
                              inplace=True)
            table_data["oss"] = report_oss
            table_data["update_date"] = report_date
            table_data.columns = [db_table + '_' + str(col_name) for col_name in table_data.columns]
            table_data = table_data[columns]
            query = f"""select {str(columns)[1:-1].replace("'", "")} from {db_table} where {db_table}_update_date like '{report_date}%'"""
            loadData(engine, query, db_table, table_data, f"{db_table}_update_date", f"{db_table}_unique_id")

            # Create a Readble report to be sent to team
            filter_cols = ["huawei_5g_site_name", "huawei_5g_site_type", "huawei_5g_site_sw",
                           "huawei_5g_site_gnodeb_id", "huawei_5g_site_oss", "huawei_5g_site_number"]

            table_data = table_data[filter_cols]
            # Change the name of the columns to the original
            table_data.rename(columns={"huawei_5g_site_name": "NE Name", "huawei_5g_site_type": "Cabinet Type",
                                       "huawei_5g_site_sw": "Software Version",
                                       "huawei_5g_site_gnodeb_id": "gNodeB ID", "huawei_5g_site_oss": "Area", 
                                       "huawei_5g_site_number": "SiteId"},
                              inplace=True)

            # Order of the columns
            table_data = table_data[["NE Name", "Cabinet Type", "Software Version", "gNodeB ID", "Area", "SiteId"]]

        elif file_name == "5G_Cell_List.csv":
            db_table = "huawei_5g_cell"
            columns = ["huawei_5g_cell_unique_id", "huawei_5g_cell_ncgi", "huawei_5g_cell_ne_name",
                       "huawei_5g_cell_nr_cell_id",
                       "huawei_5g_cell_cell_name", "huawei_5g_cell_cell_id", "huawei_5g_cell_freq_band",
                       "huawei_5g_cell_duplex_mode", "huawei_5g_cell_user_label", "huawei_5g_cell_active_state",
                       "huawei_5g_cell_nr_du_cell_id", "huawei_5g_cell_nr_du_cell_name",
                       "huawei_5g_cell_physical_cell_id", "huawei_5g_cell_up_narfcn", "huawei_5g_cell_down_narfcn",
                       "huawei_5g_cell_up_bandwidth", "huawei_5g_cell_down_bandwidth", "huawei_5g_cell_radius",
                       "huawei_5g_cell_subcarrier_spacing", "huawei_5g_cell_cyclic_prefix_length",
                       "huawei_5g_cell_slot_assignment", "huawei_5g_cell_slot_structure",
                       "huawei_5g_cell_ran_notification_area_id", "huawei_5g_cell_lampsite_flag",
                       "huawei_5g_cell_tracking_area", "huawei_5g_cell_ta_offset",
                       "huawei_5g_cell_admin_state", "huawei_5g_cell_ssb_freq_posi_describe_method",
                       "huawei_5g_cell_ssb_freq_postion", "huawei_5g_cell_ssb_period", "huawei_5g_cell_ssb1_period",
                       "huawei_5g_cell_logical_root_sequence_index", "huawei_5g_cell_prach_freq_start_position",
                       "huawei_5g_cell_tracking_area_code", "huawei_5g_cell_gnodeb_id", "huawei_5g_cell_gnodeb_name",
                       "huawei_5g_cell_oss", "huawei_5g_cell_update_date"]
            table_data["ncgi"] = ((pd.to_numeric(table_data['gnodeb_id']) * 256) + pd.to_numeric(table_data['nr_cell_id']))
            table_data["unique_id"] = table_data['gnodeb_function_name'] + '-' + report_oss + '-' + table_data['ncgi'].apply(str)
            table_data.rename(columns={'frequency_band': 'freq_band', 'cell_activate_state': 'active_state',
                                       'uplink_narfcn': 'up_narfcn', 'downlink_narfcn': 'down_narfcn',
                                       'uplink_bandwidth': 'up_bandwidth', 'downlink_bandwidth': 'down_bandwidth',
                                       'cell_radius(m)': 'radius', 'subcarrier_spacing(khz)': 'subcarrier_spacing',
                                       'lampsite_cell_flag': 'lampsite_flag', 'tracking_area_id': 'tracking_area',
                                       'cell_administration_state': 'admin_state',
                                       'ssb_frequency_position_describe_method': 'ssb_freq_posi_describe_method',
                                       'ssb_frequency_position': 'ssb_freq_postion', 'ssb_period(ms)': 'ssb_period',
                                       'sib1_period(ms)': 'ssb1_period',
                                       'prach_frequency_start_position': 'prach_freq_start_position',
                                       'gnodeb_function_name': 'gnodeb_name'}, inplace=True)
            table_data["oss"] = report_oss
            table_data["update_date"] = report_date
            table_data = table_data.sort_values('unique_id')
            table_data.columns = [db_table + '_' + str(col_name) for col_name in table_data.columns]
            table_data = table_data[columns]
            query = f"""select {str(columns)[1:-1].replace("'", "")} from {db_table} where {db_table}_update_date like '{report_date}%'"""
            loadData(engine, query, db_table, table_data, f"{db_table}_update_date", f"{db_table}_unique_id")

            # Create a Readble report to be sent to team
            filter_cols = ["huawei_5g_cell_ncgi", "huawei_5g_cell_nr_cell_id",
                           "huawei_5g_cell_cell_name", "huawei_5g_cell_cell_id", "huawei_5g_cell_freq_band",
                           "huawei_5g_cell_duplex_mode", "huawei_5g_cell_user_label", "huawei_5g_cell_active_state",
                           "huawei_5g_cell_nr_du_cell_id", "huawei_5g_cell_nr_du_cell_name",
                           "huawei_5g_cell_physical_cell_id", "huawei_5g_cell_up_narfcn", "huawei_5g_cell_down_narfcn",
                           "huawei_5g_cell_up_bandwidth", "huawei_5g_cell_down_bandwidth", "huawei_5g_cell_radius",
                           "huawei_5g_cell_subcarrier_spacing", "huawei_5g_cell_cyclic_prefix_length",
                           "huawei_5g_cell_slot_assignment", "huawei_5g_cell_slot_structure",
                           "huawei_5g_cell_ran_notification_area_id", "huawei_5g_cell_lampsite_flag",
                           "huawei_5g_cell_tracking_area", "huawei_5g_cell_ta_offset",
                           "huawei_5g_cell_admin_state", "huawei_5g_cell_ssb_freq_posi_describe_method",
                           "huawei_5g_cell_ssb_freq_postion", "huawei_5g_cell_ssb_period", "huawei_5g_cell_ssb1_period",
                           "huawei_5g_cell_logical_root_sequence_index", "huawei_5g_cell_prach_freq_start_position",
                           "huawei_5g_cell_tracking_area_code", "huawei_5g_cell_ne_name", "huawei_5g_cell_ne_name",
                           "huawei_5g_cell_gnodeb_id", "huawei_5g_cell_oss"]

            table_data = table_data[filter_cols]
            # Change the name of the columns to the original
            table_data.rename(columns={"huawei_5g_cell_ncgi": "NCGI", "huawei_5g_cell_nr_cell_id": "NR Cell ID",
                                       "huawei_5g_cell_cell_name": "Cell Name", "huawei_5g_cell_cell_id": "Cell ID",
                                       "huawei_5g_cell_freq_band": "Frequency Band",
                                       "huawei_5g_cell_duplex_mode": "Duplex Mode",
                                       "huawei_5g_cell_user_label": "User Label",
                                       "huawei_5g_cell_active_state": "Cell Activate State",
                                       "huawei_5g_cell_nr_du_cell_id": "NR DU Cell ID",
                                       "huawei_5g_cell_nr_du_cell_name": "NR DU Cell Name",
                                       "huawei_5g_cell_physical_cell_id": "Physical Cell ID",
                                       "huawei_5g_cell_up_narfcn": "Uplink NARFCN",
                                       "huawei_5g_cell_down_narfcn": "Downlink NARFCN",
                                       "huawei_5g_cell_up_bandwidth": "Uplink Bandwidth",
                                       "huawei_5g_cell_down_bandwidth": "Downlink Bandwidth",
                                       "huawei_5g_cell_radius": "Cell Radius(m)",
                                       "huawei_5g_cell_subcarrier_spacing": "Subcarrier Spacing(KHz)",
                                       "huawei_5g_cell_cyclic_prefix_length": "Cyclic Prefix Length",
                                       "huawei_5g_cell_slot_assignment": "Slot Assignment",
                                       "huawei_5g_cell_slot_structure": "Slot Structure",
                                       "huawei_5g_cell_ran_notification_area_id": "RAN Notification Area ID",
                                       "huawei_5g_cell_lampsite_flag": "LampSite Cell Flag",
                                       "huawei_5g_cell_tracking_area": "Tracking Area ID",
                                       "huawei_5g_cell_ta_offset": "TA Offset",
                                       "huawei_5g_cell_admin_state": "Cell Administration State",
                                       "huawei_5g_cell_ssb_freq_posi_describe_method": "SSB Frequency "
                                                                                       "Position Describe Method",
                                       "huawei_5g_cell_ssb_freq_postion": "SSB Frequency Position",
                                       "huawei_5g_cell_ssb_period": "SSB Period(ms)",
                                       "huawei_5g_cell_ssb1_period": "SIB1 Period(ms)",
                                       "huawei_5g_cell_logical_root_sequence_index": "Logical Root Sequence Index",
                                       "huawei_5g_cell_prach_freq_start_position": "PRACH Frequency Start Position",
                                       "huawei_5g_cell_tracking_area_code": "Tracking Area Code",
                                       "huawei_5g_cell_gnodeb_id": "gNodeB ID",
                                       "huawei_5g_cell_ne_name": "NE Name",
                                       "huawei_5g_cell_oss": "Area"},
                              inplace=True)

            # Order of the columns
            table_data = table_data[["NE Name", "NR Cell ID", "Cell Name", "Cell ID", "Frequency Band", "Duplex Mode",
                                     "User Label", "Cell Activate State", "NR DU Cell ID", "NR DU Cell Name",
                                     "Physical Cell ID", "Uplink NARFCN", "Downlink NARFCN", "Uplink Bandwidth",
                                     "Downlink Bandwidth", "Cell Radius(m)", "Subcarrier Spacing(KHz)",
                                     "Cyclic Prefix Length", "Slot Assignment", "Slot Structure",
                                     "RAN Notification Area ID", "LampSite Cell Flag", "Tracking Area ID", "TA Offset",
                                     "Cell Administration State", "SSB Frequency Position Describe Method",
                                     "SSB Frequency Position", "SSB Period(ms)", "SIB1 Period(ms)",
                                     "Logical Root Sequence Index", "PRACH Frequency Start Position",
                                     "Tracking Area Code", "gNodeB ID", "NCGI", "Area"]]

        # if file does not exist write header
        Path(script_path + REPORT_NAME).mkdir(parents=True, exist_ok=True)
        if not os.path.isfile(script_path + REPORT_NAME + '/'+file_name):
            table_data.to_csv(script_path + REPORT_NAME + '/'+file_name, header='column_names', index=False)
        else: # else it exists so append without writing the header
            table_data.to_csv(script_path + REPORT_NAME + '/'+file_name, mode='a', header=False, index=False)


def sw_merge(hotpatch, sw, product):
    """
    Function to parse SW version from 3 different columns, removing unnecessary info
    :param hotpatch: Hotpatch column from dataframe
    :param sw: software_version column from dataframe
    :param product: product_version from dataframe
    :return parsed sw version without BTS model and corrected SP->SPC
    """
    regex = r"V\w*"
    replace_regex = r"(V\w+)(SP)(\d+)"
    subst = "\\g<1>SPC\\g<3>"
    try:
        if hotpatch != 'UNKNOWN':
            sw_version = re.search(regex, str(hotpatch), re.IGNORECASE).group()
            return re.sub(replace_regex, subst, sw_version, re.IGNORECASE)
        else:
            if sw != 'UNKNOWN':
                sw_version = re.search(regex, str(sw), re.IGNORECASE).group()
                return re.sub(replace_regex, subst, sw_version, re.IGNORECASE)
            elif product != 'UNKNOWN':
                sw_version = re.search(regex, str(product), re.IGNORECASE).group()
                return re.sub(replace_regex, subst, sw_version, re.IGNORECASE)
            else:
                return 'UNKNOWN'
    except:
        return 'UNKNOWN'


#Unused
def merge_software(software_column, data_stream, software_list):
    """
        Merge all columns that contain the software and clear al unnecessary info to have a clean software
    :param software_column: name of the new column you want to output
    :param data_stream: dataframe you are working
    :param software_list: list of column names to merge
    :return: Panda DataFrame column
    """
    remove_tags = ["Micro", "Pico", "BTS3902E", "BTS5900", "BTS3202E", "BTS3000", " ", "SPC", "SP", "BTS3900_5900",
                   "BTS3900"]
    replace_tags = ["", "", "", "", "", "", "", "SP", "SPC", "", ""]
    i = 0
    for software in software_list:
        print (software)
        if i == 0:
            if data_stream[software].empty:
                data_stream[software_column] = data_stream[software]
            else:
                data_stream[software_column] = data_stream[software].replace(remove_tags, replace_tags, regex=True)
            i += 1
        else:
            data_stream[software_column] = data_stream[software_column].combine_first(data_stream[software]).replace(
                remove_tags, replace_tags, regex=True).fillna("UNKNOWN")
    return data_stream[software_column]
