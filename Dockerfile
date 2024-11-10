FROM python:3.11

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

COPY * /app

EXPOSE 5000
WORKDIR /app/src
CMD ["python", "app.py"]
