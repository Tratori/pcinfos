FROM python:3.10

WORKDIR /app

# scrapy-user-agents scrapy-rotating-proxies
RUN pip install scrapy 

COPY . .

CMD ["python", "src/main.py"]
