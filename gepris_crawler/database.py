import psycopg2
from psycopg2.extras import Json
from psycopg2.extensions import AsIs
from pypika import PostgreSQLQuery, Table


class PostgresDatabase:

    def __init__(self, scrapy_settings):
        self.name = scrapy_settings.get('DATABASE_NAME')
        self.user = scrapy_settings.get('DATABASE_USER')
        self.password = scrapy_settings.get('DATABASE_PASSWORD')
        self.host = scrapy_settings.get('DATABASE_HOST')
        self.port = scrapy_settings.get('DATABASE_PORT')
        self.connection = None

    def open(self):
        self.connection = psycopg2.connect(
            dbname=self.name,
            user=self.user,
            password=self.password,
            host=self.host,
            port=self.port
        )

    def close(self):
        self.connection.close()
        self.connection = None

    def execute_sql(self, sql, params=None):
        with self.connection.cursor() as cursor:
            if params is None:
                cursor.execute(sql)
            else:
                cursor.execute(sql, params)
        self.connection.commit()

    def get_ids(self, context, only_needed=False, limit=0):
        items = Table('available_items')
        runs = Table('spider_runs')
        no_detail_yet = PostgreSQLQuery \
            .from_(items) \
            .select(items.id) \
            .where(items.last_detail_check.isnull())
        detail_available = PostgreSQLQuery \
            .from_(items) \
            .select(items.id) \
            .join(runs) \
            .on(items.last_detail_check == runs.id) \
            .where(items.context == context) \
            .orderby(runs.run_started_at)
        if only_needed:
            detail_available = detail_available.where(items.detail_check_needed)
        q = no_detail_yet.union_all(detail_available)
        if limit > 0:
            q = q.limit(limit)
        with self.connection.cursor() as cursor:
            cursor.execute(q.get_sql())
            ids = [result[0] for result in cursor.fetchall()]
        return ids

    def upsert_available_item(self, item_id, item, spider):
        if spider.name == 'details':
            sql = "INSERT INTO available_items (id, context, last_detail_check, detail_check_needed)" \
                  " VALUES(%s, %s, %s, False) ON CONFLICT (id, context) DO UPDATE" \
                  " SET last_detail_check = EXCLUDED.last_detail_check, detail_check_needed = False"
            sql_params = (item_id, spider.context, spider.run_id)
        elif spider.name == 'search_results':
            sql = "INSERT INTO available_items AS items" \
                  " (id, context, last_available_seen, last_available_change," \
                  " last_available_item, detail_check_needed)" \
                  " VALUES(%s, %s, %s, %s, %s, True) ON CONFLICT (id, context) DO UPDATE" \
                  " SET last_available_seen = EXCLUDED.last_available_seen," \
                  " last_available_change = CASE " \
                  " WHEN items.last_available_item IS DISTINCT FROM EXCLUDED.last_available_item" \
                  " THEN EXCLUDED.last_available_change" \
                  " ELSE items.last_available_change END," \
                  " last_available_item = EXCLUDED.last_available_item," \
                  " detail_check_needed = CASE " \
                  " WHEN items.last_available_item IS DISTINCT FROM EXCLUDED.last_available_item" \
                  " THEN True" \
                  " ELSE items.detail_check_needed END"
            sql_params = (item_id, spider.context, spider.run_id, spider.run_id, Json(dict(item)))
        else:
            raise AttributeError(f'Spider has to be either "details" or "search_results", but was {spider.name}')
        with self.connection.cursor() as cursor:
            cursor.execute(sql, sql_params)
        self.connection.commit()

    def insert_detail_item(self, item_id, item_or_none, spider, status):
        if status not in ['success', 'error', 'moved']:
            raise AttributeError(f'Status has to be either "success", "error" or "moved", but was "{status}"')
        if item_or_none is None:
            json_item = None
        else:
            json_item = Json(dict(item_or_none))
        sql = "INSERT INTO details_items_history (id, context, created_at, item, status)" \
              " SELECT * FROM (VALUES" \
              " (%s, %s::CONTEXT_TYPE, %s, %s::JSONB, %s::DETAIL_STATUS_TYPE)) AS v" \
              " WHERE NOT EXISTS (SELECT * FROM latest_detail_items WHERE id = %s AND context = %s" \
              " AND status = %s AND item IS NOT DISTINCT FROM %s)"
        sql_params = (
        item_id, spider.context, spider.run_id, json_item, status, item_id, spider.context, status, json_item)
        with self.connection.cursor() as cursor:
            cursor.execute(sql, sql_params)
        self.connection.commit()

    def create_references_from_details_run(self, spider):
        sql = "SELECT create_non_existing_personen_references_from_details(%s)"
        sql_params = (spider.run_id,)
        with self.connection.cursor() as cursor:
            cursor.execute(sql, sql_params)
        self.connection.commit()

    def mark_not_found_available_items(self, spider):
        sql = "UPDATE available_items a SET detail_check_needed = True, last_available_item = Null," \
              " last_available_change = %s WHERE" \
              " a.context = %s AND a.last_available_seen != %s AND a.last_available_item IS NOT Null"
        sql_params = (spider.run_id, spider.context, spider.run_id)
        with self.connection.cursor() as cursor:
            cursor.execute(sql, sql_params)
        self.connection.commit()

    def insert_data_monitor_run(self, item):
        keys = item.keys()
        values = [item[k] for k in keys]
        sql = f"INSERT INTO data_monitor (run_ended_at, %s) VALUES(CURRENT_TIMESTAMP{', %s' * len(values)})"
        sql_params = (AsIs(', '.join(keys)), *values)
        with self.connection.cursor() as cursor:
            cursor.execute(sql, sql_params)
        self.connection.commit()

    def store_run(self, name, context):
        sql = "INSERT INTO spider_runs (spider, context, run_started_at)" \
              " VALUES(%s, %s, CURRENT_TIMESTAMP) RETURNING id"
        sql_params = (name, context)
        with self.connection.cursor() as cursor:
            cursor.execute(sql, sql_params)
            run_id = cursor.fetchone()[0]
        self.connection.commit()
        return run_id

    def update_run(self, run_id, total_items):
        sql = "UPDATE spider_runs SET run_ended_at = CURRENT_TIMESTAMP, total_scraped_items = %s" \
              " WHERE id = %s"
        sql_params = (total_items, run_id)
        with self.connection.cursor() as cursor:
            cursor.execute(sql, sql_params)
        self.connection.commit()
