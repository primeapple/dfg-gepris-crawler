import psycopg2
from psycopg2.extras import Json
from psycopg2.extensions import AsIs
from pypika import PostgreSQLQuery, Table
from pypika.functions import CurTimestamp


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

    def execute_sql(self, sql, params=None, fetch=False):
        results = None
        with self.connection.cursor() as cursor:
            if params is None:
                cursor.execute(sql)
            else:
                cursor.execute(sql, params)
            if fetch:
                results = cursor.fetchall()
        self.connection.commit()
        return results

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
        results = self.execute_sql(q.get_sql(), fetch=True)
        return [result[0] for result in results]

    def upsert_available_item(self, item_id, search_result_item, spider):
        if spider.name == 'details':
            items = Table('available_items')
            upsert_item = PostgreSQLQuery.into(items) \
                .columns(items.id, items.context, items.last_detail_check, items.detail_check_needed) \
                .insert(item_id, spider.context, spider.run_id, False) \
                .on_conflict(items.id, items.context) \
                .do_update(items.last_detail_check, spider.run_id) \
                .do_update(items.detail_check_needed, False) \
                .get_sql()
            self.execute_sql(upsert_item)
        elif spider.name == 'search_results':
            # doesn't seem to work with pypika yet because of missing distinct from
            upsert_item = "INSERT INTO available_items AS items" \
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
                  " AND items.last_available_seen IS NOT NULL" \
                  " THEN True" \
                  " ELSE items.detail_check_needed END"
            sql_params = (item_id, spider.context, spider.run_id, spider.run_id, Json(dict(search_result_item)))
            self.execute_sql(upsert_item, params=sql_params)
        else:
            raise AttributeError(f'Spider has to be either "details" or "search_results", but was {spider.name}')

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
        if spider.name != 'search_results':
            raise AttributeError(f'Only for "search_results" spider, but was "{spider.name}"')
        items = Table('available_items')
        q = PostgreSQLQuery.update(items) \
            .set(items.detail_check_needed, True) \
            .set(items.last_available_item, None) \
            .set(items.last_available_change, spider.run_id) \
            .where(items.context.eq(spider.context)) \
            .where(items.last_available_seen.ne(spider.run_id)) \
            .where(items.last_available_seen.notnull()) \
            .where(items.last_available_item.notnull())
        self.execute_sql(q.get_sql())

    def insert_data_monitor_run(self, item):
        dm = Table('data_monitor')
        q = PostgreSQLQuery.into(dm).columns('run_ended_at', *item.keys()).insert(CurTimestamp(), *item.values())
        self.execute_sql(q.get_sql())

    def store_run(self, name, context):
        runs = Table('spider_runs')
        q = PostgreSQLQuery.into(runs) \
            .columns(runs.spider, runs.context, runs.run_started_at) \
            .insert(name, context, CurTimestamp()) \
            .returning(runs.id)
        results = self.execute_sql(q.get_sql(), fetch=True)
        return results[0][0]

    def update_run_result(self, run_id, total_items):
        runs = Table('spider_runs')
        q = PostgreSQLQuery.update(runs) \
            .set(runs.run_ended_at, CurTimestamp()) \
            .set(runs.total_scraped_items, total_items) \
            .where(runs.id.eq(run_id))
        self.execute_sql(q.get_sql())
