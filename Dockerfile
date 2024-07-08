# For in-container logging
RUN touch /var/log/sheetsec-debug.log /var/log/sheetsec-warn.log /var/log/sheetsec-error.log
RUN chmod 666 /var/log/sheetsec-*.log