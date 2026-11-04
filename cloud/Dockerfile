FROM public.ecr.aws/lambda/python:3.12

# OCR runtime required by pytesseract.
RUN dnf install -y tesseract-langpack-eng && dnf clean all

COPY cloud/requirements.txt ${LAMBDA_TASK_ROOT}/requirements.txt
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

COPY backend/app ${LAMBDA_TASK_ROOT}/app
COPY backend/cloud_handler.py ${LAMBDA_TASK_ROOT}/cloud_handler.py

CMD ["cloud_handler.handler"]
