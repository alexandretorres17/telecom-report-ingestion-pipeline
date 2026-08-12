from aux_func import file_load, loadData
import os
from pathlib import Path

REPORT_NAME = "EXTERNALS"


def import_externals(report_oss, report_date, full_path, file_list, engine, script_path):
    """
     function used for 2G+3G Externals ETL process
    :param report_oss: argument passed by main run .py with oss region
    :type report_oss: str
    :param report_date: argument passed by main run .py with report date
    :type report_date: str
    :param full_path: path where the .csv files are
    :type full_path: str
    :param file_list list of files to be loaded
    :type file_list: list
    :param engine database engine
    """
    for file_name in file_list:
        print('File found: '+file_name)
        report_df = file_load(full_path + file_name, 1)
        if file_name == "2G - External 2G (GEXT2GCELL).csv":
            db_table = 'huawei_2g_ext_to_2g'
            report_df['cgi'] = report_df.mcc+'-'+report_df.mnc+'-'+report_df.cell_lac+'-'+report_df.cell_ci
            report_df['unique_id'] = report_df.bsc_name+'-'+report_df.cell_index
            report_df['oss'] = report_oss
            report_df['update_date'] = report_date
            report_df = report_df.dropna(subset=['unique_id'])
            report_df.rename(columns={'bsc_name': 'parent', 'cell_ci': 'ci', 'cell_lac': 'lac'}, inplace=True)
            report_df.columns = [db_table+'_'+str(col_name) for col_name in report_df.columns]
            cols = ['huawei_2g_ext_to_2g_cgi', 'huawei_2g_ext_to_2g_parent', 'huawei_2g_ext_to_2g_cell_index',
                    'huawei_2g_ext_to_2g_cell_name','huawei_2g_ext_to_2g_mnc','huawei_2g_ext_to_2g_mcc','huawei_2g_ext_to_2g_lac',
                    'huawei_2g_ext_to_2g_ci','huawei_2g_ext_to_2g_bcch_fd', 'huawei_2g_ext_to_2g_ncc','huawei_2g_ext_to_2g_bcc',
                    'huawei_2g_ext_to_2g_rac','huawei_2g_ext_to_2g_oss','huawei_2g_ext_to_2g_unique_id','huawei_2g_ext_to_2g_update_date']
            report_df = report_df[cols]
            query = f"""select {str(cols)[1:-1].replace("'", "")} from {db_table} where {db_table}_update_date like '{report_date}%'"""
            loadData(engine, query, db_table, report_df, f"{db_table}_update_date", f"{db_table}_unique_id")
            filter_cols = ['huawei_2g_ext_to_2g_parent', 'huawei_2g_ext_to_2g_cell_index',
                    'huawei_2g_ext_to_2g_cell_name','huawei_2g_ext_to_2g_mnc','huawei_2g_ext_to_2g_mcc','huawei_2g_ext_to_2g_lac',
                    'huawei_2g_ext_to_2g_ci','huawei_2g_ext_to_2g_bcch_fd', 'huawei_2g_ext_to_2g_ncc','huawei_2g_ext_to_2g_bcc',
                    'huawei_2g_ext_to_2g_rac','huawei_2g_ext_to_2g_oss']
            report_df = report_df[filter_cols]
            report_df.rename(columns={'huawei_2g_ext_to_2g_parent': 'BSC Name',
                                      'huawei_2g_ext_to_2g_cell_index': 'Cell Index',
                                      'huawei_2g_ext_to_2g_cell_name': 'Cell Name',
                                      'huawei_2g_ext_to_2g_mnc': 'MNC', 'huawei_2g_ext_to_2g_mcc': 'MCC',
                                      'huawei_2g_ext_to_2g_lac': 'Cell LAC','huawei_2g_ext_to_2g_ci': 'Cell CI',
                                      'huawei_2g_ext_to_2g_bcch_fd': 'BCCH FD', 'huawei_2g_ext_to_2g_ncc': 'NCC',
                                      'huawei_2g_ext_to_2g_bcc': 'BCC', 'huawei_2g_ext_to_2g_rac': 'RAC',
                                      'huawei_2g_ext_to_2g_oss': 'OSS'}, inplace=True)

        elif file_name == "2G - External 3G (GEXT3GCELL).csv":
            db_table = 'huawei_2g_ext_to_3g'
            report_df['cgi'] = report_df.mcc+'-'+report_df.mnc+'-'+report_df.cell_lac+'-'+report_df.cell_ci
            report_df['unique_id'] = report_df.bsc_name+'-'+report_df.cell_index
            report_df['oss'] = report_oss
            report_df['update_date'] = report_date
            report_df = report_df.dropna(subset=['unique_id'])
            report_df.rename(columns={'bsc_name': 'parent', 'cell_lac': 'lac', 'rnc_id': 'parent_id',
                                      'neighboring_rnc_index': 'neighboring_rnc_id',
                                      'layer_of_the_cell': 'layer_of_cell',
                                      'scrambling_code_or_cell_parameter_id': 'scrambling_code',
                                      'route_area': 'rac',
                                      'cell_index': 'cell_id'}, inplace=True)
            report_df.columns = [db_table+'_'+str(col_name) for col_name in report_df.columns]
            cols = ['huawei_2g_ext_to_3g_cgi','huawei_2g_ext_to_3g_parent','huawei_2g_ext_to_3g_cell_id',
                    'huawei_2g_ext_to_3g_cell_name','huawei_2g_ext_to_3g_mcc','huawei_2g_ext_to_3g_mnc','huawei_2g_ext_to_3g_lac',
                    'huawei_2g_ext_to_3g_cell_ci','huawei_2g_ext_to_3g_parent_id','huawei_2g_ext_to_3g_neighboring_rnc_id','huawei_2g_ext_to_3g_layer_of_cell',
                    'huawei_2g_ext_to_3g_dl_uarfcn','huawei_2g_ext_to_3g_scrambling_code', 'huawei_2g_ext_to_3g_rac',
                    'huawei_2g_ext_to_3g_oss','huawei_2g_ext_to_3g_unique_id','huawei_2g_ext_to_3g_update_date']
            report_df = report_df[cols]
            query = f"""select {str(cols)[1:-1].replace("'", "")} from {db_table} where {db_table}_update_date like '{report_date}%'"""
            loadData(engine, query, db_table, report_df, f"{db_table}_update_date", f"{db_table}_unique_id")
            filter_cols = ['huawei_2g_ext_to_3g_parent','huawei_2g_ext_to_3g_cell_id', 'huawei_2g_ext_to_3g_cell_name',
                           'huawei_2g_ext_to_3g_mcc', 'huawei_2g_ext_to_3g_mnc','huawei_2g_ext_to_3g_lac',
                           'huawei_2g_ext_to_3g_rac', 'huawei_2g_ext_to_3g_cell_ci','huawei_2g_ext_to_3g_parent_id',
                           'huawei_2g_ext_to_3g_neighboring_rnc_id','huawei_2g_ext_to_3g_layer_of_cell',
                           'huawei_2g_ext_to_3g_dl_uarfcn', 'huawei_2g_ext_to_3g_scrambling_code',
                           'huawei_2g_ext_to_3g_oss']
            report_df = report_df[filter_cols]
            report_df.rename(columns={'huawei_2g_ext_to_3g_parent': 'BSC Name',
                                      'huawei_2g_ext_to_3g_cell_id': 'Cell Index',
                                      'huawei_2g_ext_to_3g_cell_name': 'Cell Name',
                                      'huawei_2g_ext_to_3g_mcc': 'MCC', 'huawei_2g_ext_to_3g_mnc': 'MNC',
                                      'huawei_2g_ext_to_3g_lac': 'Cell LAC', 'huawei_2g_ext_to_3g_rac': 'Cell RAC',
                                      'huawei_2g_ext_to_3g_cell_ci': 'Cell CI',
                                      'huawei_2g_ext_to_3g_parent_id': 'RNC ID',
                                      'huawei_2g_ext_to_3g_neighboring_rnc_id': 'Neighboring RNC Index',
                                      'huawei_2g_ext_to_3g_layer_of_cell': 'Layer of the cell',
                                      'huawei_2g_ext_to_3g_dl_uarfcn': 'DL UARFCN',
                                      'huawei_2g_ext_to_3g_scrambling_code': 'Scrambling Code',
                                      'huawei_2g_ext_to_3g_oss': 'OSS'}, inplace=True)

        elif file_name == "2G - External 4G (GEXTLTECELL).csv":
            db_table = 'huawei_2g_ext_to_4g'
            report_df['ecgi'] = report_df.mcc+'-'+report_df.mnc+'-'+report_df.cell_ci+'-'+report_df.physical_cell_id
            report_df['unique_id'] = report_df.bsc_name+'-'+report_df.cell_index
            report_df['oss'] = report_oss
            report_df['update_date'] = report_date
            report_df = report_df.dropna(subset=['unique_id'])
            report_df.rename(columns={'bsc_name': 'parent', 'physical_cell_id': 'pci',
                               'operator_name': 'opt_name',
                               'sharing_operator_group_index': 'sharing_opt_index'}, inplace=True)
            report_df.columns = [db_table+'_'+str(col_name) for col_name in report_df.columns]
            cols = ['huawei_2g_ext_to_4g_ecgi','huawei_2g_ext_to_4g_parent','huawei_2g_ext_to_4g_cell_index',
                    'huawei_2g_ext_to_4g_cell_name','huawei_2g_ext_to_4g_mcc','huawei_2g_ext_to_4g_mnc','huawei_2g_ext_to_4g_enodeb_type',
                    'huawei_2g_ext_to_4g_cell_ci', 'huawei_2g_ext_to_4g_cell_tac', 'huawei_2g_ext_to_4g_earfcn', 'huawei_2g_ext_to_4g_pci',
                    'huawei_2g_ext_to_4g_eutran_cell_type','huawei_2g_ext_to_4g_opt_name', 'huawei_2g_ext_to_4g_sharing_opt_index',
                    'huawei_2g_ext_to_4g_oss', 'huawei_2g_ext_to_4g_unique_id','huawei_2g_ext_to_4g_update_date']
            report_df = report_df[cols]
            query = f"""select {str(cols)[1:-1].replace("'", "")} from {db_table} where {db_table}_update_date like '{report_date}%'"""
            loadData(engine, query, db_table, report_df, f"{db_table}_update_date", f"{db_table}_unique_id")

        elif file_name == "3G - External 2G (UEXT2GCELL).csv":
            db_table = 'huawei_3g_ext_to_2g'
            report_df['cgi'] = report_df.mobile_country_code+'-'+report_df.mobile_network_code+'-'\
                               +report_df.location_area_code+'-'+report_df.gsm_cell_id
            report_df['unique_id'] = report_df.bsc_name+'-'+report_df.gsm_cell_name
            report_df['oss'] = report_oss
            report_df['update_date'] = report_date
            report_df = report_df.dropna(subset=['unique_id'])
            report_df.rename(columns={'bsc_name': 'parent', 'neighboring_bsc_index': 'neighboring_bsc_id',
                               'mobile_country_code': 'mcc', 'mobile_network_code': 'mnc',
                               'cn_operator_group_index': 'cn_opt_index', 'location_area_code': 'lac',
                               'routing_area_code': 'rac', 'network_color_code': 'ncc',
                               'bs_color_code': 'bcc', 'inter-rat_cell_frequency_number': 'inter_rat_cell_freq',
                               'inter-rat_cell_frequency_band_indicator': 'inter_rat_cell_freq_band'}, inplace=True)
            report_df.columns = [db_table+'_'+str(col_name) for col_name in report_df.columns]
            cols = ['huawei_3g_ext_to_2g_cgi','huawei_3g_ext_to_2g_parent','huawei_3g_ext_to_2g_gsm_cell_index',
                    'huawei_3g_ext_to_2g_gsm_cell_name','huawei_3g_ext_to_2g_neighboring_bsc_id','huawei_3g_ext_to_2g_mcc',
                    'huawei_3g_ext_to_2g_mnc','huawei_3g_ext_to_2g_cn_opt_index','huawei_3g_ext_to_2g_lac','huawei_3g_ext_to_2g_rac',
                    'huawei_3g_ext_to_2g_gsm_cell_id','huawei_3g_ext_to_2g_ncc', 'huawei_3g_ext_to_2g_bcc', 'huawei_3g_ext_to_2g_inter_rat_cell_freq',
                    'huawei_3g_ext_to_2g_inter_rat_cell_freq_band','huawei_3g_ext_to_2g_node_id','huawei_3g_ext_to_2g_unique_id',
                    'huawei_3g_ext_to_2g_oss', 'huawei_3g_ext_to_2g_update_date']
            report_df = report_df[cols]
            query = f"""select {str(cols)[1:-1].replace("'", "")} from {db_table} where {db_table}_update_date like '{report_date}%'"""
            loadData(engine, query, db_table, report_df, f"{db_table}_update_date", f"{db_table}_unique_id")
            filter_cols = ['huawei_3g_ext_to_2g_parent', 'huawei_3g_ext_to_2g_gsm_cell_name', 'huawei_3g_ext_to_2g_gsm_cell_index',
                           'huawei_3g_ext_to_2g_neighboring_bsc_id', 'huawei_3g_ext_to_2g_mcc', 'huawei_3g_ext_to_2g_mnc',
                           'huawei_3g_ext_to_2g_cn_opt_index', 'huawei_3g_ext_to_2g_lac', 'huawei_3g_ext_to_2g_rac',
                           'huawei_3g_ext_to_2g_gsm_cell_id', 'huawei_3g_ext_to_2g_ncc', 'huawei_3g_ext_to_2g_bcc',
                           'huawei_3g_ext_to_2g_inter_rat_cell_freq', 'huawei_3g_ext_to_2g_inter_rat_cell_freq_band',
                           'huawei_3g_ext_to_2g_node_id', 'huawei_3g_ext_to_2g_oss']
            report_df = report_df[filter_cols]
            report_df.rename(columns={'huawei_3g_ext_to_2g_parent': 'RNC Name',
                                      'huawei_3g_ext_to_2g_gsm_cell_name': 'GSM Cell Name',
                                      'huawei_3g_ext_to_2g_gsm_cell_index': 'GSM Cell Index',
                                      'huawei_3g_ext_to_2g_neighboring_bsc_id': 'Neighboring BSC Index',
                                      'huawei_3g_ext_to_2g_mcc': 'MCC', 'huawei_3g_ext_to_2g_mnc': 'MNC',
                                      'huawei_3g_ext_to_2g_cn_opt_index': 'CN Operator Index',
                                      'huawei_3g_ext_to_2g_lac': 'LAC', 'huawei_3g_ext_to_2g_rac': 'RAC',
                                      'huawei_3g_ext_to_2g_gsm_cell_id': 'GSM Cell ID',
                                      'huawei_3g_ext_to_2g_ncc': 'NCC', 'huawei_3g_ext_to_2g_bcc': 'BCC',
                                      'huawei_3g_ext_to_2g_inter_rat_cell_freq': 'Inter-RAT Cell Frequency Number',
                                      'huawei_3g_ext_to_2g_inter_rat_cell_freq_band': 'Inter-RAT Cell Frequency Band Indicator',
                                      'huawei_3g_ext_to_2g_node_id': 'Node ID', 'huawei_3g_ext_to_2g_oss': 'OSS'}, inplace=True)

        elif file_name == "3G - External 3G (UEXT3GCELL).csv":
            db_table = 'huawei_3g_ext_to_3g'
            report_df['cgi'] = report_df.mobile_country_code+'-'+report_df.mobile_network_code+'-'\
                               +report_df.location_area_code+'-'+report_df.cell_id_of_neighboring_rnc
            report_df['unique_id'] = report_df.bsc_name+'-'+report_df.neighboring_rnc_id+'-'+report_df.cell_id_of_neighboring_rnc
            report_df['oss'] = report_oss
            report_df['update_date'] = report_date
            report_df = report_df.dropna(subset=['unique_id'])
            report_df.rename(columns={'bsc_name': 'parent', 'cell_id_of_neighboring_rnc': 'cell_id_neighbouring_rnc',
                               'mobile_country_code': 'mcc', 'mobile_network_code': 'mnc',
                               'cn_operator_group_index': 'cn_opt_index', 'location_area_code': 'lac',
                               'routing_area_code': 'rac', 'network_color_code': 'ncc',
                               'bs_color_code': 'bcc', 'dl_primary_scrambling_code': 'dl_primary_sc',
                               'uplink_uarfcn': 'ul_uarfcn', 'downlink_uarfcn': 'dl_uarfcn',
                               'ul_frequency_ind': 'ul_freq_ind', 'neighboring_rnc_id':'neighbouring_rnc_id'}, inplace=True)
            report_df.columns = [db_table+'_'+str(col_name) for col_name in report_df.columns]
            cols = ['huawei_3g_ext_to_3g_cgi', 'huawei_3g_ext_to_3g_parent', 'huawei_3g_ext_to_3g_neighbouring_rnc_id',
                    'huawei_3g_ext_to_3g_cell_id_neighbouring_rnc', 'huawei_3g_ext_to_3g_cell_name', 'huawei_3g_ext_to_3g_cn_opt_index',
                    'huawei_3g_ext_to_3g_dl_primary_sc', 'huawei_3g_ext_to_3g_band_indicator', 'huawei_3g_ext_to_3g_ul_freq_ind',
                    'huawei_3g_ext_to_3g_ul_uarfcn', 'huawei_3g_ext_to_3g_dl_uarfcn', 'huawei_3g_ext_to_3g_lac', 'huawei_3g_ext_to_3g_rac',
                    'huawei_3g_ext_to_3g_node_id', 'huawei_3g_ext_to_3g_mnc', 'huawei_3g_ext_to_3g_mcc', 'huawei_3g_ext_to_3g_cn_operator_name',
                    'huawei_3g_ext_to_3g_oss', 'huawei_3g_ext_to_3g_unique_id', 'huawei_3g_ext_to_3g_update_date']
            report_df = report_df[cols]
            query = f"""select {str(cols)[1:-1].replace("'", "")} from {db_table} where {db_table}_update_date like '{report_date}%'"""
            loadData(engine, query, db_table, report_df, f"{db_table}_update_date", f"{db_table}_unique_id")
            filter_cols = ['huawei_3g_ext_to_3g_parent', 'huawei_3g_ext_to_3g_neighbouring_rnc_id',
                           'huawei_3g_ext_to_3g_cell_id_neighbouring_rnc', 'huawei_3g_ext_to_3g_cell_name',
                           'huawei_3g_ext_to_3g_cn_opt_index', 'huawei_3g_ext_to_3g_dl_primary_sc',
                           'huawei_3g_ext_to_3g_band_indicator', 'huawei_3g_ext_to_3g_ul_freq_ind',
                           'huawei_3g_ext_to_3g_ul_uarfcn', 'huawei_3g_ext_to_3g_dl_uarfcn', 'huawei_3g_ext_to_3g_lac',
                           'huawei_3g_ext_to_3g_rac', 'huawei_3g_ext_to_3g_node_id', 'huawei_3g_ext_to_3g_mcc',
                           'huawei_3g_ext_to_3g_mnc', 'huawei_3g_ext_to_3g_cn_operator_name', 'huawei_3g_ext_to_3g_oss']
            report_df = report_df[filter_cols]
            report_df.rename(columns={'huawei_3g_ext_to_3g_parent': 'RNC Name',
                                      'huawei_3g_ext_to_3g_neighbouring_rnc_id': 'Neighboring RNC ID',
                                      'huawei_3g_ext_to_3g_cell_id_neighbouring_rnc': 'Cell ID of Neighboring RNC',
                                      'huawei_3g_ext_to_3g_cell_name': 'Cell Name',
                                      'huawei_3g_ext_to_3g_cn_opt_index': 'CN Operator Index',
                                      'huawei_3g_ext_to_3g_dl_primary_sc': 'DL Primary Scrambling Code',
                                      'huawei_3g_ext_to_3g_band_indicator': 'Band Indicator',
                                      'huawei_3g_ext_to_3g_ul_freq_ind': 'UL Frequency Ind',
                                      'huawei_3g_ext_to_3g_ul_uarfcn': 'Uplink UARFCN',
                                      'huawei_3g_ext_to_3g_dl_uarfcn': 'Downlink UARFCN',
                                      'huawei_3g_ext_to_3g_lac': 'LAC', 'huawei_3g_ext_to_3g_rac': 'RAC',
                                      'huawei_3g_ext_to_3g_node_id': 'Node ID',
                                      'huawei_3g_ext_to_3g_mcc': 'MCC', 'huawei_3g_ext_to_3g_mnc': 'MNC',
                                      'huawei_3g_ext_to_3g_cn_operator_name': 'Cn Operator Name',
                                      'huawei_3g_ext_to_3g_oss': 'OSS'}, inplace=True)

        elif file_name == "3G - External 4G (ULTECELL).csv":
            db_table = 'huawei_3g_ext_to_4g'
            report_df['ecgi'] = report_df.mobile_country_code+'-'+report_df.mobile_network_code+'-'\
                                +report_df.eutran_cell_identity+'-'+report_df.lte_physical_cell_identity
            report_df['unique_id'] = report_df.bsc_name+'-'+report_df.lte_cell_index
            report_df['oss'] = report_oss
            report_df['update_date'] = report_date
            report_df = report_df.dropna(subset=['unique_id'])
            report_df.rename(columns={'bsc_name': 'parent', 'eutran_cell_identity': 'lte_cell_identity',
                               'mobile_country_code': 'mcc', 'mobile_network_code': 'mnc',
                               'tracking_area_code': 'tac', 'operator_group_index': 'opt_group_index',
                               'lte_physical_cell_identity': 'lte_pci', 'lte_cell_frequency_band': 'lte_cell_freq_band',
                               'lte_cell_downlink_frequency': 'lte_cell_dl_freq', 'lte_cell_supporting_ps_ho_indicator': 'lte_cell_sup_ps_ho',
                               'blackcell_list_flag': 'blackcell_lst', 'cn_operator_index_for_routing_in_u2l_rim': 'cn_opt_index_rout_u2l_rim'
                               }, inplace=True)
            report_df.columns = [db_table+'_'+str(col_name) for col_name in report_df.columns]
            cols = ['huawei_3g_ext_to_4g_ecgi','huawei_3g_ext_to_4g_parent','huawei_3g_ext_to_4g_lte_cell_index',
                    'huawei_3g_ext_to_4g_lte_cell_name','huawei_3g_ext_to_4g_lte_cell_identity','huawei_3g_ext_to_4g_mcc','huawei_3g_ext_to_4g_mnc',
                    'huawei_3g_ext_to_4g_tac','huawei_3g_ext_to_4g_opt_group_index','huawei_3g_ext_to_4g_lte_pci','huawei_3g_ext_to_4g_lte_cell_freq_band',
                    'huawei_3g_ext_to_4g_lte_cell_dl_freq','huawei_3g_ext_to_4g_lte_cell_sup_ps_ho','huawei_3g_ext_to_4g_blackcell_lst',
                    'huawei_3g_ext_to_4g_cn_opt_index_rout_u2l_rim','huawei_3g_ext_to_4g_oss','huawei_3g_ext_to_4g_unique_id','huawei_3g_ext_to_4g_update_date']
            report_df = report_df[cols]
            query = f"""select {str(cols)[1:-1].replace("'", "")} from {db_table} where {db_table}_update_date like '{report_date}%'"""
            loadData(engine, query, db_table, report_df, f"{db_table}_update_date", f"{db_table}_unique_id")

        # if file does not exist write header
        Path(script_path + REPORT_NAME).mkdir(parents=True, exist_ok=True)
        if not os.path.isfile(script_path + REPORT_NAME + '/' +file_name):
            report_df.to_csv(script_path + REPORT_NAME + '/' +file_name, header='column_names', index=False)
        else: # else it exists so append without writing the header
            report_df.to_csv(script_path + REPORT_NAME + '/' +file_name, mode='a', header=False, index=False)
