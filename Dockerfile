FROM python:3.12.8-slim@sha256:2199a62885a12290dc9c5be3ca0681d367576ab7bf037da120e564723292a2f0
WORKDIR /app
COPY mercy /app/mercy
COPY inputs /app/inputs
RUN useradd --uid 10001 --create-home investigator && mkdir /app/logs && chown investigator:investigator /app/logs
USER investigator
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
CMD ["python", "-m", "mercy.run"]
