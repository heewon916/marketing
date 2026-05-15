FROM mcr.microsoft.com/playwright/python:v1.59.0-noble

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn playwright

COPY naver_map_menu_hours.py .

EXPOSE 8010

CMD ["uvicorn", "naver_map_menu_hours:app", "--host", "0.0.0.0", "--port", "8010"]
