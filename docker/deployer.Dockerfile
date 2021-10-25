FROM python:3.9-slim
LABEL maintainer=toni.mueller@student.uni-halle.de
# install dependencies
RUN apt-get --yes update && \
    apt-get --yes install gcc cron
RUN pip install scrapyd-client

# setting up workspace
ENV APP_HOME /opt/app/dfg-gepris
RUN mkdir -p $APP_HOME
WORKDIR $APP_HOME
# copy the important stuff for deploying
# cant merge this two lines, because it extracts all the files in gepris_crawler into $APP_HOME
COPY gepris_crawler gepris_crawler/
COPY __init__.py setup.py docker/scrapy.cfg docker/deployer_cronfile docker/entrypoint.sh ${APP_HOME}

# Write the crontab:
# run foekat_farmer_cron.sh to download the csv file every day at 2 am
RUN crontab deployer_cronfile

ENTRYPOINT ["sh", "entrypoint.sh"]
CMD ["scrapyd-client", "spiders", "-p", "gepris_crawler"]
