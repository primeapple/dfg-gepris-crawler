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
    && pip install --no-cache-dir git+https://github.com/scrapy/scrapy.git@$SCRAPY_VERSION \
                   git+https://github.com/scrapy/scrapyd.git@$SCRAPYD_VERSION

# the following is my stuff
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY docker/scrapyd.conf /etc/scrapyd/
# here my stuff ends

VOLUME /etc/scrapyd/ /var/lib/scrapyd/
EXPOSE 6800

CMD ["scrapyd", "--pidfile="]

