FROM python:3.12-slim

WORKDIR /app

COPY .devops/shadow-control/requirements.txt /app/requirements.txt

RUN pip install \
    --no-cache-dir \
    -r /app/requirements.txt

COPY \
    .devops/shadow-control/preprocessor_shadow_control.py \
    /app/preprocessor_shadow_control.py

ENTRYPOINT ["python", "/app/preprocessor_shadow_control.py"]