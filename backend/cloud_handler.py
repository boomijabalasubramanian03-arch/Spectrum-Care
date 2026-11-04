"""AWS Lambda handler for the serverless Chroma Context deployment.

Architecture:
React -> API Gateway -> Lambda -> S3/DynamoDB/Polly
                         ^
                         |
                    S3 ObjectCreated

The image-processing code is shared with the local FastAPI application via
app.ml.pipeline, so the AI logic is not duplicated.
"""
import base64
import json
import os
import uuid
from datetime import datetime, timezone
from urllib.parse import unquote_plus

import boto3

s3 = boto3.client("s3")
ddb = boto3.resource("dynamodb")
polly = boto3.client("polly")

TABLE_NAME = os.environ.get("ANALYSIS_TABLE", "ChromaContextAnalyses")
RESULT_BUCKET = os.environ.get("RESULT_BUCKET")
TABLE = ddb.Table(TABLE_NAME)


def _response(status, body):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": os.environ.get("CORS_ORIGIN", "*"),
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        },
        "body": json.dumps(body, default=str),
    }


def _event_body(event):
    raw = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        raw = base64.b64decode(raw).decode("utf-8")
    return json.loads(raw)


def _save_analysis(user_id, analysis_id, image_key, result, annotated_key=None):
    now = datetime.now(timezone.utc).isoformat()
    item = {
        "pk": f"USER#{user_id}",
        "sk": f"ANALYSIS#{analysis_id}",
        "entity": "analysis",
        "analysis_id": analysis_id,
        "user_id": user_id,
        "created_at": now,
        "status": "done",
        "image_key": image_key,
        "annotated_key": annotated_key,
        "processing_time": result.get("comp_time"),
        "det_count": result.get("det_count", 0),
        "scene_text": result.get("scene_text", ""),
        "detections": result.get("detections", []),
        "ocr_results": result.get("ocr_results", []),
    }
    TABLE.put_item(Item=item)
    return item


def _process_s3_record(record):
    bucket = record["s3"]["bucket"]["name"]
    key = unquote_plus(record["s3"]["object"]["key"])
    parts = key.split("/", 3)
    user_id = parts[1] if len(parts) > 1 and parts[0] == "uploads" else "anonymous"
    analysis_id = parts[2] if len(parts) > 2 and parts[0] == "uploads" else str(uuid.uuid4())

    work_dir = "/tmp/chroma"
    os.makedirs(work_dir, exist_ok=True)
    local_input = os.path.join(work_dir, f"{analysis_id}.jpg")
    annotated_dir = os.path.join(work_dir, "annotated")
    s3.download_file(bucket, key, local_input)

    from app.ml.pipeline import run_pipeline
    result = run_pipeline(local_input, annotated_dir)

    annotated_key = None
    if RESULT_BUCKET and result.get("annotated_filename"):
        local_annotated = os.path.join(annotated_dir, result["annotated_filename"])
        annotated_key = f"results/{user_id}/{analysis_id}.jpg"
        s3.upload_file(local_annotated, RESULT_BUCKET, annotated_key, ExtraArgs={"ContentType": "image/jpeg"})

    _save_analysis(user_id, analysis_id, key, result, annotated_key)
    return {"analysis_id": analysis_id, "status": "done"}


def handler(event, context):
    # S3 notification path.
    if event.get("Records") and event["Records"][0].get("eventSource") == "aws:s3":
        results = [_process_s3_record(r) for r in event["Records"]]
        return {"processed": results}

    method = event.get("requestContext", {}).get("http", {}).get("method") or event.get("httpMethod", "GET")
    path = event.get("rawPath") or event.get("path", "")

    if method == "OPTIONS":
        return _response(204, {})

    if method == "GET" and path.endswith("/health"):
        return _response(200, {"status": "ok", "service": "chroma-context-serverless"})

    if method == "POST" and path.endswith("/upload-url"):
        body = _event_body(event)
        user_id = body.get("user_id") or "anonymous"
        filename = os.path.basename(body.get("filename") or "image.jpg")
        content_type = body.get("content_type") or "image/jpeg"
        analysis_id = str(uuid.uuid4())
        key = f"uploads/{user_id}/{analysis_id}/{filename}"
        url = s3.generate_presigned_url(
            "put_object",
            Params={"Bucket": RESULT_BUCKET, "Key": key, "ContentType": content_type},
            ExpiresIn=900,
        )
        TABLE.put_item(Item={
            "pk": f"USER#{user_id}",
            "sk": f"ANALYSIS#{analysis_id}",
            "entity": "analysis",
            "analysis_id": analysis_id,
            "user_id": user_id,
            "status": "processing",
            "image_key": key,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        return _response(200, {"analysis_id": analysis_id, "upload_url": url, "object_key": key})

    if method == "GET" and "/analysis/" in path:
        analysis_id = path.rstrip("/").split("/")[-1]
        user_id = event.get("queryStringParameters", {}).get("user_id", "anonymous")
        item = TABLE.get_item(Key={"pk": f"USER#{user_id}", "sk": f"ANALYSIS#{analysis_id}"}).get("Item")
        if not item:
            return _response(404, {"detail": "Analysis not found."})
        return _response(200, item)

    if method == "POST" and path.endswith("/speak"):
        body = _event_body(event)
        text = (body.get("text") or "").strip()
        if not text:
            return _response(400, {"detail": "Text is required."})
        result = polly.synthesize_speech(Text=text[:3000], OutputFormat="mp3", VoiceId="Joanna")
        audio = base64.b64encode(result["AudioStream"].read()).decode("ascii")
        return _response(200, {"audio_base64": audio, "content_type": "audio/mpeg"})

    return _response(404, {"detail": "Not found."})
