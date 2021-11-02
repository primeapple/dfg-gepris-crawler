#
# Dockerfile for scrapyd-arm (python3)
# it is mostly taken from https://github.com/vimagick/dockerfiles/blob/master/scrapyd/arm/Dockerfile
# because the published version easypi/scrapyd-arm is not up to date yet
#
# I added installation of libpq-dev, gcc and cargo, as well as some pip packages
#

FROM debian:bullseye
MAINTAINER EasyPi Software Foundation

ENV SCRAPY_VERSION=2.5.1
ENV SCRAPYD_VERSION=1.2.1
ENV SCRAPYD_CLIENT_VERSION=v1.2.0
ENV SCRAPYRT_VERSION=v0.12
ENV PILLOW_VERSION=8.3.2

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
                          cargo \
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
                          libpq-dev \
                          gcc \
    && curl -sSL https://bootstrap.pypa.io/get-pip.py | python3 \
    && pip install --no-cache-dir git+https://github.com/scrapy/scrapy.git@$SCRAPY_VERSION \
                   git+https://github.com/scrapy/scrapyd.git@$SCRAPYD_VERSION \
                   git+https://github.com/scrapy/scrapyd-client.git@$SCRAPYD_CLIENT_VERSION \
                   git+https://github.com/scrapinghub/scrapy-splash.git \
                   git+https://github.com/scrapinghub/scrapyrt.git@$SCRAPYRT_VERSION \
                   git+https://github.com/python-pillow/Pillow.git@$PILLOW_VERSION \
    && curl -sSL https://github.com/scrapy/scrapy/raw/master/extras/scrapy_bash_completion -o /etc/bash_completion.d/scrapy_bash_completion \
    && echo 'source /etc/bash_completion.d/scrapy_bash_completion' >> /root/.bashrc \
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

# the following is my stuff
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY docker/scrapyd.conf /etc/scrapyd/
# here my stuff ends


CMD ["scrapyd", "--pidfile="]

