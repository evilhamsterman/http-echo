FROM python:3.10-alpine as builder

RUN python -m venv venv
ENV PATH="/venv/bin:$PATH"
COPY requirements.txt /
RUN pip install --no-cache-dir -r /requirements.txt

FROM python:3.10-alpine
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"
COPY http-echo.py /srv
ENTRYPOINT ["python", "/srv/http-echo.py"]
CMD ["--address", "0.0.0.0"]