# ----------------------------------------
# CONFIG
# ----------------------------------------

REGISTRY      ?= docker.io/ferdaze          # e.g. docker.io/username OR ghcr.io/username
VERSION       ?= latest                     # Image tag
SENDER_IMAGE  := $(REGISTRY)/spidermon-sender:$(VERSION)
RECEIVER_IMAGE:= $(REGISTRY)/spidermon-receiver:$(VERSION)

# ----------------------------------------
# RULES
# ----------------------------------------

.PHONY: all logger build push login clean

all: build push

build: build-sender build-receiver

build-sender:
    docker build -t $(SENDER_IMAGE) ./sender

build-receiver:
    docker build -t $(RECEIVER_IMAGE) ./receiver

push: push-sender push-receiver

push-sender:
    docker push $(SENDER_IMAGE)

push-receiver:
    docker push $(RECEIVER_IMAGE)

login:
    docker login

clean:
    docker rmi $(SENDER_IMAGE) || true
    docker rmi $(RECEIVER_IMAGE) || true

show:
    @echo REGISTRY: $(REGISTRY)
    @echo VERSION:  $(VERSION)
    @echo SENDER_IMAGE: $(SENDER_IMAGE)
    @echo RECEIVER_IMAGE: $(RECEIVER_IMAGE)
