#!/bin/bash

# ---- CONFIG ----
REGISTRY="ferdaze"
VERSION="1.0"

SENDER_IMAGE="${REGISTRY}/spidermon-sender:${VERSION}"
RECEIVER_IMAGE="${REGISTRY}/spidermon-receiver:${VERSION}"

# ---- BUILD ----
echo "🔨 Building sender image..."
docker buildx build -t $SENDER_IMAGE ./spidermon-sender || exit 1

echo "🔨 Building receiver image..."
docker buildx build -t $RECEIVER_IMAGE ./spidermon-receiver || exit 1

# ---- LOGIN ----
echo "Docker.io login..."
docker login -u "ferdaze" docker.io || exit 1

# ---- PUSH ----
echo "📤 Pushing sender image to registry..."
docker push $SENDER_IMAGE || exit 1

echo "📤 Pushing receiver image to registry..."
docker push $RECEIVER_IMAGE || exit 1

echo "✅ Done. Images pushed:"
echo "   $SENDER_IMAGE"
echo "   $RECEIVER_IMAGE"
