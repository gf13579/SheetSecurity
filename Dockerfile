FROM python:3
WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./src /code/src

# For in-container logging
RUN touch /var/log/sheetsec-debug.log /var/log/sheetsec-warn.log /var/log/sheetsec-error.log /var/log/sheetsec-info.log
RUN chmod 666 /var/log/sheetsec-*.log

EXPOSE 8000

CMD ["uvicorn", "src.__main__:app", "--host", "0.0.0.0", "--port", "8000", "--no-server-header"]