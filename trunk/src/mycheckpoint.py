#!/usr/bin/python

#
# Collect GLOBAL STATUS, GLOBAL VARIABLES master & slave status.
#
# Released under the BSD license
#
# Copyright (c) 2009, Shlomi Noach
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
#     * Neither the name of the organization nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

import getpass
import MySQLdb
import traceback
from optparse import OptionParser

def parse_options():
    usage = "usage: mycheckpoint [options] [create/upgrade]"
    parser = OptionParser(usage=usage)
    parser.add_option("-u", "--user", dest="user", default="", help="MySQL user")
    parser.add_option("-H", "--host", dest="host", default="localhost", help="MySQL host (default: localhost)")
    parser.add_option("-p", "--password", dest="password", default="", help="MySQL password")
    parser.add_option("--ask-pass", action="store_true", dest="prompt_password", help="Prompt for password")
    parser.add_option("-P", "--port", dest="port", type="int", default="3306", help="TCP/IP port (default: 3306)")
    parser.add_option("-S", "--socket", dest="socket", default="/var/run/mysqld/mysql.sock", help="MySQL socket file. Only applies when host is localhost")
    parser.add_option("", "--defaults-file", dest="defaults_file", default="", help="Read from MySQL configuration file. Overrides all other options")
    parser.add_option("-d", "--database", dest="database", default="openark", help="Database name (required unless query uses fully qualified table names)")
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true", help="Print user friendly messages")
    return parser.parse_args()


def verbose(message):
    if options.verbose:
        print "-- %s" % message

def print_error(message):
    print "-- ERROR: %s" % message

def open_connection():
    if options.defaults_file:
        conn = MySQLdb.connect(
            read_default_file = options.defaults_file,
            db = database_name)
    else:
        if options.prompt_password:
            password=getpass.getpass()
        else:
            password=options.password
        conn = MySQLdb.connect(
            host = options.host,
            user = options.user,
            passwd = password,
            port = options.port,
            db = database_name,
            unix_socket = options.socket)
    return conn;

def act_query(query):
    """
    Run the given query, commit changes
    """
    connection = conn
    cursor = connection.cursor()
    num_affected_rows = cursor.execute(query)
    cursor.close()
    connection.commit()
    return num_affected_rows


def get_row(query):
    connection = conn
    cursor = connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(query)
    row = cursor.fetchone()

    cursor.close()
    return row


def get_rows(query):
    connection = conn
    cursor = connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(query)
    rows = cursor.fetchall()

    cursor.close()
    return rows


def table_exists(check_database_name, check_table_name):
    """
    See if the a given table exists:
    """
    count = 0

    query = """
        SELECT COUNT(*) AS count
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA='%s'
            AND TABLE_NAME='%s'
        """ % (check_database_name, check_table_name)

    row = get_row(query)
    count = int(row['count'])

    return count


def is_neglectable_variable(variable_name):
    if variable_name.startswith("ssl_"):
        return True
    if variable_name.startswith("ndb_"):
        return True
    if variable_name == "last_query_cost":
        return True
    return False


def normalize_variable_value(variable_value):
    if variable_value == "off":
        variable_value = 0
    elif variable_value == "on":
        variable_value = 1
    elif variable_value == "demand":
        variable_value = 2
    elif variable_value == "no":
        variable_value = 0
    elif variable_value == "yes":
        variable_value = 1
    return variable_value


def get_global_variables():
    global_variables = [
        "auto_increment_increment",
        "binlog_cache_size",
        "bulk_insert_buffer_size",
        "concurrent_insert",
        "connect_timeout",
        "delay_key_write",
        "delayed_insert_limit",
        "delayed_insert_timeout",
        "delayed_queue_size",
        "expire_logs_days",
        "foreign_key_checks",
        "group_concat_max_len",
        "innodb_additional_mem_pool_size",
        "innodb_autoextend_increment",
        "innodb_autoinc_lock_mode",
        "innodb_buffer_pool_size",
        "innodb_checksums",
        "innodb_commit_concurrency",
        "innodb_concurrency_tickets",
        "innodb_fast_shutdown",
        "innodb_file_io_threads",
        "innodb_file_per_table",
        "innodb_flush_log_at_trx_commit",
        "innodb_force_recovery",
        "innodb_lock_wait_timeout",
        "innodb_log_buffer_size",
        "innodb_log_file_size",
        "innodb_log_files_in_group",
        "innodb_max_dirty_pages_pct",
        "innodb_max_purge_lag",
        "innodb_mirrored_log_groups",
        "innodb_open_files",
        "innodb_rollback_on_timeout",
        "innodb_stats_on_metadata",
        "innodb_support_xa",
        "innodb_sync_spin_loops",
        "innodb_table_locks",
        "innodb_thread_concurrency",
        "innodb_thread_sleep_delay",
        "join_buffer_size",
        "key_buffer_size",
        "key_cache_age_threshold",
        "key_cache_block_size",
        "key_cache_division_limit",
        "large_files_support",
        "large_page_size",
        "large_pages",
        "locked_in_memory",
        "log_queries_not_using_indexes",
        "log_slow_queries",
        "long_query_time",
        "low_priority_updates",
        "max_allowed_packet",
        "max_binlog_cache_size",
        "max_binlog_size",
        "max_connect_errors",
        "max_connections",
        "max_delayed_threads",
        "max_error_count",
        "max_heap_table_size",
        "max_insert_delayed_threads",
        "max_join_size",
        "max_length_for_sort_data",
        "max_prepared_stmt_count",
        "max_relay_log_size",
        "max_seeks_for_key",
        "max_sort_length",
        "max_sp_recursion_depth",
        "max_tmp_tables",
        "max_user_connections",
        "max_write_lock_count",
        "min_examined_row_limit",
        "multi_range_count",
        "myisam_data_pointer_size",
        "myisam_max_sort_file_size",
        "myisam_repair_threads",
        "myisam_sort_buffer_size",
        "myisam_use_mmap",
        "net_buffer_length",
        "net_read_timeout",
        "net_retry_count",
        "net_write_timeout",
        "old_passwords",
        "open_files_limit",
        "optimizer_prune_level",
        "optimizer_search_depth",
        "port",
        "preload_buffer_size",
        "profiling",
        "profiling_history_size",
        "protocol_version",
        "pseudo_thread_id",
        "query_alloc_block_size",
        "query_cache_limit",
        "query_cache_min_res_unit",
        "query_cache_size",
        "query_cache_type",
        "query_cache_wlock_invalidate",
        "query_prealloc_size",
        "range_alloc_block_size",
        "read_buffer_size",
        "read_only",
        "read_rnd_buffer_size",
        "relay_log_space_limit",
        "rpl_recovery_rank",
        "server_id",
        "skip_external_locking",
        "skip_networking",
        "skip_show_database",
        "slave_compressed_protocol",
        "slave_net_timeout",
        "slave_transaction_retries",
        "slow_launch_time",
        "slow_query_log",
        "sort_buffer_size",
        "sql_auto_is_null",
        "sql_big_selects",
        "sql_big_tables",
        "sql_buffer_result",
        "sql_log_bin",
        "sql_log_off",
        "sql_log_update",
        "sql_low_priority_updates",
        "sql_max_join_size",
        "sql_notes",
        "sql_quote_show_create",
        "sql_safe_updates",
        "sql_select_limit",
        "sql_warnings",
        "sync_binlog",
        "sync_frm",
        "table_definition_cache",
        "table_lock_wait_timeout",
        "table_open_cache",
        "thread_cache_size",
        "thread_stack",
        "timed_mutexes",
        "timestamp",
        "tmp_table_size",
        "transaction_alloc_block_size",
        "transaction_prealloc_size",
        "unique_checks",
        "updatable_views_with_limit",
        "wait_timeout",
        "warning_count",
        ]
    return global_variables


def fetch_status_variables():
    """
    Fill in the status_dict. We make point of filling in all variables, even those not existing,
    for havign the dictionary hold the keys. Based on these keys, tables and views are created.
    So it is important that we have the dictionary include all possible keys.
    """
    status_dict = {}

    query = "SHOW GLOBAL STATUS"
    rows = get_rows(query);
    for row in rows:
        variable_name = row["Variable_name"].lower()
        variable_value = row["Value"].lower()
        if not is_neglectable_variable(variable_name):
            status_dict[variable_name] = normalize_variable_value(variable_value)

    # Listing of interesting global variables:
    global_variables = get_global_variables()
    query = "SHOW GLOBAL VARIABLES"
    rows = get_rows(query);
    for row in rows:
        variable_name = row["Variable_name"].lower()
        variable_value = row["Value"].lower()
        if variable_name in global_variables:
            status_dict[variable_name] = normalize_variable_value(variable_value)

    # Master status
    status_dict["master_position"] = None
    query = "SHOW MASTER STATUS"
    master_status = get_row(query)
    if master_status:
        status_dict["master_position"] = master_status["Position"]

    # Slave status
    slave_status_variables = ["Read_Master_Log_Pos", "Relay_Log_Pos", "Exec_Master_Log_Pos", "Relay_Log_Space", "Seconds_Behind_Master"]
    for variable_name in slave_status_variables:
        status_dict[variable_name.lower()] = None
    query = "SHOW SLAVE STATUS"
    slave_status = get_row(query)
    if slave_status:
        for variable_name in slave_status_variables:
            status_dict[variable_name.lower()] = slave_status[variable_name]

    return status_dict


def get_status_variables_columns():
    """
    Return all columns participating in the status variables table. Most of these are STATUS variables.
    Others are parameters. Others yet represent slave or master status etc.
    """
    status_dict = fetch_status_variables()
    return sorted(status_dict.keys())


def get_variables_and_status_columns():
    variables_columns = get_global_variables()
    status_columns = [column_name for column_name in get_status_variables_columns() if not column_name in variables_columns]
    return variables_columns, status_columns


def create_status_variables_table():
    columns_listing = ",\n".join(["%s BIGINT UNSIGNED" % column_name for column_name in get_status_variables_columns()])
    query = """CREATE TABLE %s.%s (
            id INT AUTO_INCREMENT PRIMARY KEY,
            ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            %s,
            UNIQUE KEY ts (ts)
       )
    """ % (database_name, table_name, columns_listing)
    act_query(query)


def upgrade_status_variables_table():
    query = """
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA='%s' AND TABLE_NAME='%s'
        """ % (database_name, table_name)
    existing_columns = [row["COLUMN_NAME"] for row in get_rows(query)]
    new_columns = [column_name for column_name in get_status_variables_columns() if column_name not in existing_columns]

    if new_columns:
        columns_listing = ",\n".join(["ADD COLUMN %s BIGINT UNSIGNED" % column_name for column_name in new_columns])
        query = """ALTER TABLE %s.%s
                %s
        """ % (database_name, table_name, columns_listing)
        act_query(query)


def create_status_variables_diff_view():
    global_variables, diff_columns = get_variables_and_status_columns()

    # Global variables are used as-is
    global_variables_columns_listing = ",\n".join([" ${status_variables_table_alias}2.%s AS %s" % (column_name, column_name,) for column_name in global_variables])
    # Status variables are diffed. This does not make sense for all of them, but we do it for all nonetheless.
    diff_columns_listing = ",\n".join([" ${status_variables_table_alias}2.%s -  ${status_variables_table_alias}1.%s AS %s" % (column_name, column_name, column_name,) for column_name in diff_columns])

    query = """
        CREATE
        OR REPLACE
        ALGORITHM = MERGE
        DEFINER = CURRENT_USER
        SQL SECURITY INVOKER
        VIEW ${status_variables_table_name}_diff AS
          SELECT
            ${status_variables_table_name}2.id,
            ${status_variables_table_name}2.ts,
            TIMESTAMPDIFF(SECOND, ${status_variables_table_name}1.ts, ${status_variables_table_name}2.ts) AS ts_diff_seconds,
            %s,
            %s
          FROM
            ${status_variables_table_name} AS ${status_variables_table_alias}1
            INNER JOIN ${status_variables_table_name} AS ${status_variables_table_alias}2
            ON (${status_variables_table_alias}1.id = ${status_variables_table_alias}2.id-GREATEST(1, IFNULL(${status_variables_table_alias}2.auto_increment_increment, 1)))
    """ % (diff_columns_listing, global_variables_columns_listing)
    query = query.replace("${status_variables_table_name}", "%s.%s" % (database_name, table_name,))
    query = query.replace("${status_variables_table_alias}", table_name)
    act_query(query)


def create_status_variables_psec_diff_view():
    global_variables, diff_columns = get_variables_and_status_columns()

    # Global variables are used as-is
    global_variables_columns_listing = ",\n".join(["%s" % (column_name,) for column_name in global_variables])

    # Status variables are diffed. This does not make sense for all of them, but we do it for all nonetheless.
    diff_columns_listing = ",\n".join([" %s" % (column_name,) for column_name in diff_columns])
    change_psec_columns_listing = ",\n".join([" ROUND(%s/ts_diff_seconds, 2) AS %s_psec" % (column_name, column_name,) for column_name in diff_columns])
    query = """
        CREATE
        OR REPLACE
        ALGORITHM = MERGE
        DEFINER = CURRENT_USER
        SQL SECURITY INVOKER
        VIEW ${status_variables_table_name}_psec_diff AS
          SELECT
            id,
            ts,
            ts_diff_seconds,
            %s,
            %s,
            %s
          FROM
            ${status_variables_table_name}_diff
    """ % (diff_columns_listing, change_psec_columns_listing, global_variables_columns_listing)
    query = query.replace("${status_variables_table_name}", "%s.%s" % (database_name, table_name,))
    act_query(query)


def create_status_variables_hour_diff_view():
    global_variables, diff_columns = get_variables_and_status_columns()

    # Global variables are used as-is
    global_variables_columns_listing = ",\n".join([" MIN(%s) AS %s" % (column_name, column_name,) for column_name in global_variables])
    # Status variables are diffed. This does not make sense for all of them, but we do it for all nonetheless.
    sum_diff_columns_listing = ",\n".join([" SUM(%s) AS %s" % (column_name, column_name,) for column_name in diff_columns])
    avg_psec_columns_listing = ",\n".join([" ROUND(AVG(%s_psec), 2) AS %s_psec" % (column_name, column_name,) for column_name in diff_columns])
    query = """
        CREATE
        OR REPLACE
        ALGORITHM = TEMPTABLE
        DEFINER = CURRENT_USER
        SQL SECURITY INVOKER
        VIEW ${status_variables_table_name}_hour_diff AS
          SELECT
            MIN(id) AS id,
            DATE(ts) + INTERVAL HOUR(ts) HOUR AS ts,
            DATE(ts) + INTERVAL (HOUR(ts) + 1) HOUR AS end_ts,
            %s,
            %s,
            %s
          FROM
            ${status_variables_table_name}_psec_diff
          GROUP BY DATE(ts), HOUR(ts)
    """ % (sum_diff_columns_listing, avg_psec_columns_listing, global_variables_columns_listing)
    query = query.replace("${status_variables_table_name}", "%s.%s" % (database_name, table_name,))
    act_query(query)



def create_status_variables_parameter_change_view():
    global_variables, diff_columns = get_variables_and_status_columns()

    global_variables_select_listing = ["""
        SELECT ${status_variables_table_alias}2.ts AS ts, '%s' AS variable_name, ${status_variables_table_alias}1.%s AS old_value, ${status_variables_table_alias}2.%s AS new_value
        FROM
          ${status_variables_table_name} AS ${status_variables_table_alias}1
          INNER JOIN ${status_variables_table_name} AS ${status_variables_table_alias}2
          ON (${status_variables_table_alias}1.id = ${status_variables_table_alias}2.id-GREATEST(1, IFNULL(${status_variables_table_alias}2.auto_increment_increment, 1)))
        WHERE ${status_variables_table_alias}2.%s != ${status_variables_table_alias}1.%s
        """ % (column_name, column_name, column_name,
               column_name, column_name,) for column_name in global_variables if column_name != 'timestamp']
    global_variables_select_union = " UNION ALL \n".join(global_variables_select_listing)

    query = """
        CREATE
        OR REPLACE
        ALGORITHM = TEMPTABLE
        DEFINER = CURRENT_USER
        SQL SECURITY INVOKER
        VIEW ${status_variables_table_name}_parameter_change_union AS
          %s
    """ % (global_variables_select_union)
    query = query.replace("${status_variables_table_name}", "%s.%s" % (database_name, table_name,))
    query = query.replace("${status_variables_table_alias}", table_name)
    act_query(query)

    query = """
        CREATE
        OR REPLACE
        ALGORITHM = TEMPTABLE
        DEFINER = CURRENT_USER
        SQL SECURITY INVOKER
        VIEW ${status_variables_table_name}_parameter_change AS
          SELECT * FROM ${status_variables_table_name}_parameter_change_union
          ORDER BY ts, variable_name
    """
    query = query.replace("${status_variables_table_name}", "%s.%s" % (database_name, table_name,))
    act_query(query)


def create_custom_views(view_base_name, view_columns):
    global_variables, status_variables = get_variables_and_status_columns()

    columns_list = [column_name.strip() for column_name in view_columns.split(",")]
    global_variables_columns_listing = ",\n".join([column_name for column_name in columns_list if column_name in global_variables])
    status_variables_columns_listing = ",\n".join([column_name for column_name in columns_list if column_name in status_variables])
    status_variables_psec_columns_listing = ",\n".join(["%s_psec" % (column_name,) for column_name in columns_list if column_name in status_variables])

    query = """
        CREATE
        OR REPLACE
        ALGORITHM = MERGE
        DEFINER = CURRENT_USER
        SQL SECURITY INVOKER
        VIEW %s.sv_%s${view_name_extension} AS
          SELECT
            id,
            ts,
            %s,
            %s,
            %s
          FROM
            ${status_variables_table_name}${view_name_extension}
    """ % (database_name, view_base_name,
           global_variables_columns_listing, status_variables_columns_listing, status_variables_psec_columns_listing)
    query = query.replace("${status_variables_table_name}", "%s.%s" % (database_name, table_name,))

    psec_diff_query = query.replace("${status_variables_table_name}", "_psec_diff")
    act_query(psec_diff_query)

    hour_diff_query = query.replace("${status_variables_table_name}", "_hour_diff")
    act_query(hour_diff_query)


def create_status_variables_views():
    create_status_variables_diff_view()
    create_status_variables_psec_diff_view()
    create_status_variables_hour_diff_view()
    create_status_variables_parameter_change_view()
    create_custom_views("tmp_tables", "tmp_table_size, max_heap_table_size, created_tmp_tables, created_tmp_disk_tables")
    pass


def collect_status_variables():
    query = "SET SESSION SQL_LOG_BIN=0"
    act_query(query)

    status_dict = fetch_status_variables()

    column_names = ", ".join(["%s" % column_name for column_name in sorted(status_dict.keys())])
    for column_name in status_dict.keys():
        if status_dict[column_name] is None:
            status_dict[column_name] = "NULL"
        if status_dict[column_name] == "":
            status_dict[column_name] = "NULL"
    variable_values = ", ".join(["%s" % status_dict[column_name] for column_name in sorted(status_dict.keys())])
    query = """INSERT /*! IGNORE */ INTO %s.%s
            (%s)
            VALUES (%s)
    """ % (database_name, table_name,
        column_names,
        variable_values)
    act_query(query)


def exit_with_error(error_message):
    """
    Notify and exit.
    """
    print_error(error_message)
    exit(1)


try:
    try:
        conn = None
        reuse_conn = True
        (options, args) = parse_options()

        database_name = options.database
        table_name = "status_variables"
        status_dict = None

        if not database_name:
            exit_with_error("No database specified. Specify with -d or --database")

        conn = open_connection()
        if "create" in args:
            create_status_variables_table()
            create_status_variables_views()
            verbose("Table and views created")
        elif "upgrade" in args:
            upgrade_status_variables_table()
            create_status_variables_views()
            verbose("Table and views upgraded")
        else:
            collect_status_variables()
            verbose("Status variables checkpoint complete")
    except Exception, err:
        print err
        traceback.print_exc()
finally:
    if conn:
        conn.close()
