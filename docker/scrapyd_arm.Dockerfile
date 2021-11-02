#
# Dockerfile for scrapyd-arm (python3)
# it is mostly taken from https://github.com/vimagick/dockerfiles/blob/master/scrapyd/arm/Dockerfile
#

FROM debian:bullseye AS base
ENV SCRAPY_VERSION=2.5.1
ENV SCRAPYD_VERSION=1.2.1

RUN set -xe \
    && apt-get update \
    && apt-get install -y autoconf \
                          build-essential \
                          curl \
                          git \
                          libffi-dev \
                          libssl-dev \
                          libtool \
                          libxml2 \
                          libxml2-dev \
                          libxslt1.1 \
                          libxslt1-dev \
                          python3 \
                          python3-dev \
                          python3-distutils \
                          vim-tiny \
    && apt-get install -y libtiff5 \
                          libtiff5-dev \
                          libfreetype6-dev \
                          libjpeg62-turbo \
                          libjpeg62-turbo-dev \
                          liblcms2-2 \
                          liblcms2-dev \
                          libwebp6 \
                          libwebp-dev \
                          zlib1g \
                          zlib1g-dev \
    && curl -sSL https://bootstrap.pypa.io/get-pip.py | python3 \
    && pip install --no-cache-dir git+https://github.com/scrapy/scrapy.git@$SCRAPY_VERSION \
                   git+https://github.com/scrapy/scrapyd.git@$SCRAPYD_VERSION \
    && apt-get purge -y --auto-remove autoconf \
                                      build-essential \
                                      curl \
                                      libffi-dev \
                                      libssl-dev \
                                      libtool \
                                      libxml2-dev \
                                      libxslt1-dev \
                                      python3-dev \
    && apt-get purge -y --auto-remove libtiff5-dev \
                                      libfreetype6-dev \
                                      libjpeg62-turbo-dev \
                                      liblcms2-dev \
                                      libwebp-dev \
                                      zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

VOLUME /etc/scrapyd/ /var/lib/scrapyd/
EXPOSE 6800
CMD ["scrapyd", "--pidfile="]

# the following is my stuff
FROM base
COPY requirements.txt ./
RUN set -xe \
    && apt-get update \
    && apt-get install -y libpq-dev \
                          gcc \
                          python3-dev \
    && pip install --no-cache-dir -r requirements.txt \
    && rm -rf /var/lib/apt/lists/*
COPY docker/scrapyd.conf /etc/scrapyd/


