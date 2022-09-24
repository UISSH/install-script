FROM debian:bullseye

COPY . /

ENTRYPOINT ["/test_install.sh"]
