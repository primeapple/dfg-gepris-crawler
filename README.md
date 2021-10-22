## Inspecting the cache
The cache of the crawled Websites is stored in `dfg-gepris/.scrapy/httpcache`.
You will find a folder for each spider, each containing a `SPIDERNAME.db` file. This is a [gnu DBM](https://www.gnu.org.ua/software/gdbm/) file.
Details about its content can be found [here](https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#scrapy.extensions.httpcache.DbmCacheStorage).

Use the `cache_control.py` script to read, delete and debug data from the cache.

## Configuring
First we have to do some configurations for passwords, ports, etc.  
They exist in the `.env` file. In the beginning it is fine to just use the example environment variables:
```sh
cp example.env .env
```

## Development

### Basic Set Up
First go ahead and create a virtual environment:
```sh
python3 -m venv venv
```
Now activate it:
```sh
# for bash/zsh
source venv/bin/activate
# for fish
source venv/bin/activate.fish
```
and install dependencies:
```sh
pip install -r requirements.txt
```

You can already try the first command. Let's check the latest datamonitor results of GEPRIS:
```sh
scrapy crawl data_monitor -s NO_DB=True -O test.json
```
If everything is correctly set up, there should now be a `test.json` file with content like:
```json
[
{"last_update": "2021-10-12", "last_approval": "2021-08-12", "gepris_version": "18.5.0", "current_index_version": "63037efd-37e0-424a-a956-438bfe91dc9d", "current_index_date": "2021-10-12 10:05:44", "finished_project_count": 34874, "project_count": 136266, "person_count": 87475, "institution_count": 37472, "humanities_count": 24936, "life_count": 48182, "natural_count": 34897, "engineering_count": 25362, "infrastructure_count": 11055}
]
```
To later use the database please install some basic dependencies on your machine:
```shell
# this is only for Debian like Distros, please fill a request if you need it on another machine
sudo apt-get install libpq-dev gcc 
```


### Database
The core of this application is the database. To set it up you need to have docker installed:
```sh
# setup database
docker-compose --profile development build
docker-compose --profile development up
```

### Running
Please look into the `Running the spiders` chapter for detailed info about the spiders.

Also you may need several Environment Variables set. Do NOT source the `.env` file directly, rather always do:
```bash
# you can only do this in this directory, so please navigate here before running the command
source outside_docker.sh
# if you are using the fish shell, please run instead:
exec bash -c "source outside_docker.sh; exec fish"
```

### Tests
First make sure your test database is setup:
```shell
docker-compose --profile test up
```

Run the tests from the projects root directory with
```shell
python -m unittest
```

## Production

## Running the spiders



### Advanced configuration
#### HTTP-Cache
#### HTTP Proxies
#### Other options
* No Database
