from scrapy.utils.project import get_project_settings


def get_settings(database=True):
    settings = get_project_settings()
    settings.set('NO_DB', not database)
    return settings
