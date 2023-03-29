FROM python:3.8-slim

WORKDIR /backend

COPY requirements.txt /backend

RUN python -m pip install --upgrade pip

RUN pip3 install -r /backend/requirements.txt --no-cache-dir

COPY . /backend

CMD ["gunicorn", "foodgram_backend.wsgi:application", "--bind", "0:8000" ]