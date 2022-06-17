FROM python:3.9-slim-buster

RUN useradd --create-home --shell /bin/bash japarr

# install deps
RUN python -m pip install --upgrade pip toml
COPY pyproject.toml /tmp/pyproject.toml
RUN python3 \
  -c 'import toml; c=toml.load("/tmp/pyproject.toml"); print("\0".join(c["project"]["dependencies"]), end="")' \
  | xargs -0 pip install
RUN python3 \
  -c 'import toml; c=toml.load("/tmp/pyproject.toml"); print("\0".join(c["project"]["optional-dependencies"]["test"]), end="")' \
  | xargs -0 pip install

# copy source
RUN mkdir -p /src
RUN chown -R japarr:japarr /src
WORKDIR /src
USER japarr

COPY --chown=japarr:japarr ./src /src/japarr/src
COPY --chown=japarr:japarr ./tests /src/japarr/tests
COPY --chown=japarr:japarr ./pyproject.toml /src/japarr
RUN echo ls /src/japarr

# COPY --chown=japarr:japarr pyproject.tml /src/japarr
RUN python -m pip install --user -e /src/japarr[test]

ENV PYTHONUNBUFFERED=1
CMD ["python", "/src/japarr/src/japarr/main.py"]
# ENTRYPOINT ["tail", "-f", "/dev/null"]