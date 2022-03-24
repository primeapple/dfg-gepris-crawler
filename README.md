# DFG Gepris Scraper
This project was done in addition to my masterthesis in computer science at the [MLU](https://www.informatik.uni-halle.de/).  
It enables the user to build and maintain a dynamic database of the data in the [DFG Gepris Foerderkatalog](https://gepris.dfg.de/gepris/OCTOPUS).
The plan is to have a public API running, so that others will be able to visualize and use the scraped data further.

## Prerequisits
### Configuration
First we have to do some configurations for passwords, ports, etc.  
They exist in the `.env` file. In the beginning it is fine to just use the example environment variables:
```sh
cp example.env .env
```

### Docker
For most applications you need some external services. To set them up you need to have docker and docker-compose installed.  
We use [Docker-Compose Profiles](https://docs.docker.com/compose/profiles/) for this application. There is:
* `development` (scrapyd, database, adminer)
* `test` (test-database, adminer)
* `production` (scrapyd, database, adminer, deployer)

Choose the one you need, build it and start it:
```sh
docker-compose --profile development build
docker-compose --profile development up
```

### Other requirements
To later use the database please install some basic dependencies on your machine.
This is only needed if you want to use the `test` or `development` profile.
```shell
# this is only for Debian like Distros, please fill a request if you need it on another machine
sudo apt-get install libpq-dev gcc 
```

## Development
The corresponding profile is `development`.

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

You can already try the first command. Let's check the latest datamonitor results of GEPRIS
```sh
# this even works without running docker services
scrapy crawl data_monitor -s NO_DB=True -O test.json
```
If everything is correctly set up, there should now be a `test.json` file with content like:
```json
[
{"last_update": "2021-10-12", "last_approval": "2021-08-12", "gepris_version": "18.5.0", "current_index_version": "63037efd-37e0-424a-a956-438bfe91dc9d", "current_index_date": "2021-10-12 10:05:44", "finished_project_count": 34874, "project_count": 136266, "person_count": 87475, "institution_count": 37472, "humanities_count": 24936, "life_count": 48182, "natural_count": 34897, "engineering_count": 25362, "infrastructure_count": 11055}
]
```

### Running
Please look into the `Running the spiders` chapter for detailed info about the spiders.

Also you need several Environment Variables set. Do NOT source the `.env` file directly, rather always do:
```bash
# you can only do this in this directory, so please navigate here before running the command
source outside_docker.sh
# if you are using the fish shell, please run instead:
exec bash -c "source outside_docker.sh; exec fish"
```

You can now run any spider you want with:
```shell
scrapy crawl SPIDERNAME [-a ARG=ARG_VALUE, ...] [-s SETTING=SETTING_VALUE, ...]
```

#### Useful settings
To over write settings use the `-s` flag. Useful settings are:
* `HTTPCACHE_ENABLED=True`  
enables the HTTPCACHE (in .scrapy/httpcache/SPIDERNAME.db)
* `HTTPCACHE_FORCE_REFRESH=True`  
  on enabled HTTPCACHE it forces an overwrite on the crawled pages
* `NO_DB=TRUE`  
  makes sure the spider does not write or read from the database (disables some stuff)
* `NO_DB=TRUE`  
  makes sure the spider does not write or read from the database (disables some stuff)

#### Scrapy shell
```shell
scrapy shell https://www.whatismyip.com/ -s "NO_DB=True" -s "SPIDER_MIDDLEWARES={}" -s "HTTPCACHE_ENABLED=False"
```

#### Debug
If you want to run spiders from your IDE, please use the [runner.py](runner.py) file for it.

The cache of the crawled Websites is stored in `.scrapy/httpcache/` (if you filled the cache before, at least).
You will find a folder for each spider, each containing a `SPIDERNAME.db` file. This is a [gnu DBM](https://www.gnu.org.ua/software/gdbm/) file.
Details about its content can be found [here](https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#scrapy.extensions.httpcache.DbmCacheStorage).  
Use the `cache_control.py` script to read, delete and debug data from the cache.

### Tests
The corresponding profile is `development`.

Run the tests from the projects root directory with
```shell
python -m unittest
```
Some of the tests are heavily mocked. Some require local `.html` files. Some are not implemented yet and will fail on purpose.
Look into the [test](test) module for more information.

## Production
In Production there is a cronjob running, that schedules the spiders regularly.
Look into the [cronfile](docker/scheduler_cronfile) to see what is happening exactly.

To run it on a AMD64 Architecture, use profile `production`.
If you are running this on an ARM Architecture, please use the `docker-compose.arm.yml` file like:
```shell
docker-compose -f docker-compose.yml -f docker-compose.arm.yml --profile production up --build
```

There is the possible to receive automatic email messages for important spider runs.
Please fill the specified entries in your `.env` file.

## Running the spiders
The commands to run the spiders in `development` and `production` should be clear until this point.

We currently have 3 maintained and tested spiders to scrape items from Gepris.  
Some of them require arguments to work. 

### data_monitor
This spider fetches the latest data from https://gepris.dfg.de/gepris/OCTOPUS?task=showMonitor  

It does not use or require any argument and does only request one page.

### search_results
This spider fetches all search results for the search at https://gepris.dfg.de/gepris/OCTOPUS?task=showSearchSimple

It requires the argument `context`(str), which can be `projekt`, `person` or `institution`.

It takes an optional argument `items`(int), which is the number of displayed results per page (so less items means smaller but more documents to be fetched). It defaults to `1000`.

### details
This spider fetches the details pages for the given ids, for example: https://gepris.dfg.de/gepris/projekt/216628603  
Some pages also have results ("Projektergebnisse"), like https://gepris.dfg.de/gepris/projekt/234920277 . In this case, the result is also fetched and added to the scraped item.
Each page is fetched in german and in english language. So have to fetch 2 or 4 documents per ID and produce a single item for each ID.

It requires the argument `context`(str), which can be `projekt`, `person` or `institution`.

It requires the argument `ids`(str), which tells the spider which ids to scrape. It can be either:
* `[ID1,ID2,...]`
* `file.json`  
In this case the `file.json` has to contain a single valid json array, that contain objects, where each of them has the key `id`.
This can for example be the output of the `search_results` spider.
* `db:all:LIMIT`  
This fetches the LIMIT (a number) latest scraped item ids for this context from the database.
* `db:needed:LIMIT`  
This fetches the LIMIT (a number) latest scraped item ids for this context from the database, that require a refresh.

## Using Proxies
There is the option to use proxies. We currently only support proxies of [webshare.io](https://www.webshare.io/).
To use them, register yourself on the website, buy a plan and then head to [your proxy list overview](https://proxy.webshare.io/proxy/list), press the "Download Proxy List" button and copy the link.
This link has to be set in your `.env` file, at the key `WEBSHARE_PROXY_LIST_URL`.
You will now be using the webshare proxies

# TODOs:
* A good strategy would be to every day only crawl N Projects. For each project we crawl it's references to person and institution
  * Make N so that we will average around a fixed amount of total requests
  * What is with subinstitutions?
