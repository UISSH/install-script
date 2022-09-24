FROM debian:bullseye

COPY . /
RUN  chmod a+x test_install.sh install.sh && bash install.sh

ENTRYPOINT ["/test_install.sh"]
