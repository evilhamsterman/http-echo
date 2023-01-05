FROM python:3.10-alpine

COPY . /srv

RUN pip install --no-cache-dir -r /srv/requirements.txt

ENTRYPOINT ["python", "/srv/http-echo.py"]
CMD ["--address", "0.0.0.0"]