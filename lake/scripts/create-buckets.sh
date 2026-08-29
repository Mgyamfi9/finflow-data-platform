#!/bin/bash
# ============================================================
# MinIO Bucket Initialization
# Runs as a one-shot container after MinIO is healthy
# ============================================================
set -e
echo 'Waiting for MinIO to be ready...'
until mc alias set finflow http://minio:9000 \
"${MINIO_ROOT_USER}" "${MINIO_ROOT_PASSWORD}" 2>/dev/null; do
echo ' MinIO not ready, retrying in 2s...'
sleep 2
done
echo 'Creating buckets...'
mc mb --ignore-existing finflow/${MINIO_BUCKET_RAW}
mc mb --ignore-existing finflow/${MINIO_BUCKET_BRONZE}
mc mb --ignore-existing finflow/${MINIO_BUCKET_SILVER}
mc mb --ignore-existing finflow/${MINIO_BUCKET_GOLD}
mc mb --ignore-existing finflow/${MINIO_BUCKET_QUARANTINE}
echo 'Buckets created:'
mc ls finflow/
echo 'MinIO initialization complete.'
