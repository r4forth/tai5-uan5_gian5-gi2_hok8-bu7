FROM i3thuan5/tai5-uan5_gian5-gi2_kang1-ku7
MAINTAINER i3thuan5

ARG TOX_ENV

RUN mkdir -p /usr/local/tai5-uan5_gian5-gi2_hok8-bu7
WORKDIR /usr/local/tai5-uan5_gian5-gi2_hok8-bu7
RUN pip3 install tox
COPY . .
RUN LANG=zh_TW.utf8 tox --sitepackages -e ${TOX_ENV}

# RUN echo TAI5TSUAN2HUA2 = \'`/sbin/ip route|awk '/default/ { print $3 }'`\' >> 設定/settings.py
