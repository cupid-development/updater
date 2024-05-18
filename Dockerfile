FROM python:3.11-alpine

ARG VERSION=dev
ENV VERSION=$VERSION

COPY . /app
WORKDIR /app

ENV GERRIT_URL "https://review.lineageos.org"
ENV CACHE_DEFAULT_TIMEOUT "3600"
ENV CACHE_TYPE "simple"
ENV WIKI_INSTALL_URL "https://wiki.lineageos.org/devices/{device}/install"
ENV WIKI_INFO_URL "https://wiki.lineageos.org/devices/{device}"
ENV UPSTREAM_URL ""
ENV DOWNLOAD_BASE_URL "https://mirrorbits.lineageos.org"
ENV FLASK_APP "app.py"

RUN pip install -r requirements.txt

EXPOSE 8080

CMD gunicorn -b [::]:8080 -w 8 app:app
