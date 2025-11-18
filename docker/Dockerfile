FROM python:alpine
RUN apk add git
WORKDIR /app
RUN git clone https://github.com/YeNLoR/blogprototype repo
RUN pip install --no-cache-dir -r repo/requirements.txt
EXPOSE 5000
WORKDIR /app/repo
CMD ["python", "main.py"]
#CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]