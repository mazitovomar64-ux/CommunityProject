FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY req.txt .
RUN pip install --no-cache-dir -r req.txt

COPY . .
# на случай, если файл сохранён с Windows-окончаниями строк (CRLF)
RUN sed -i 's/\r$//' docker/entrypoint.sh && chmod +x docker/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./docker/entrypoint.sh"]
# daphne обслуживает и обычные HTTP-запросы, и WebSocket (gunicorn WebSocket не умеет)
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "motion_site.asgi:application"]