## Inspecting the cache
The cache of the crawled Websites is stored in `dfg-gepris/.scrapy/httpcache`.
You will find a folder for each spider, each containing a `SPIDERNAME.db` file. This is a [gnu DBM](https://www.gnu.org.ua/software/gdbm/) file.
Details about its content can be found [here](https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#scrapy.extensions.httpcache.DbmCacheStorage).

Use the `cache_control.py` script to read, delete and debug data from the cache.

## Development
First go ahead and create a virtual environment:
```sh
python3 -m venv venv
```
