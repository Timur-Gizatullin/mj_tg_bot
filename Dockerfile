FROM python:3.11.5-slim

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt update \
  && apt install -y netcat-traditional make \
  && pip install --upgrade pip \
  && pip install poetry==1.4.2

COPY ./src/pyproject.toml ./src/poetry.lock ./

ARG DEV_DEPS=False

RUN poetry config virtualenvs.create false
RUN if [ $DEV_DEPS = True ] ; then \
  poetry install --no-interaction --no-ansi ; else \
  poetry install --without dev --no-interaction --no-ansi ; fi

COPY . .

RUN chmod 777 /usr/src/app/entrypoint.sh
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]