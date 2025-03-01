FROM python:3-slim

EXPOSE 17780

# build
RUN groupadd --gid 10001 delta && \
    useradd --uid 10001 --gid 10001 --home-dir /delta --create-home --shell /bin/false delta

COPY delta /delta/delta
COPY data /delta/data
COPY clients /delta/clients
COPY *.txt /delta/

RUN chown -R delta:delta /delta && \
    pip install --upgrade pip && pip install --upgrade --requirement /delta/requirements.txt

# run
USER delta

ENV HOME=/delta \
    PYTHONPATH=/delta/ \
    DELTATG_API_TOKEN="" \
    DELTATG_WEBHOOK_URL="/"

WORKDIR /delta

CMD ["python", \
    "/delta/clients/delta_tgbot.py", \
    "/delta/data/dictionary-russian.xml", \
    "--verbose", \
    "--host",  "0.0.0.0", \
    "--port",  "17780" ]
