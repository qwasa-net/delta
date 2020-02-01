FROM python:3

EXPOSE 17777

# build
RUN useradd --home-dir /delta --create-home --shell /bin/false delta
COPY . /delta/
RUN chown -R delta:delta /delta
RUN pip install --upgrade pip && pip install --upgrade --requirement /delta/requirements.txt

# run
USER delta
ENV HOME /delta
ENV PYTHONPATH .:/delta/
WORKDIR /delta
CMD ["python", "/delta/clients/delta_commander.py",\
    "data/dictionary-russian.xml",\
    "--verbose",\
    "--tcpserver", "", "17777"]
