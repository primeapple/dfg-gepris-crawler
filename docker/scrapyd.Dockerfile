FROM vimagick/scrapyd:py3
RUN apt-get --yes update && apt-get --yes install libpq-dev gcc python3-dev
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY docker/scrapyd.conf ./
