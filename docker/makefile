# ----------------------------------------
# CONFIG
# ----------------------------------------

REGISTRY      ?= docker.io/ferdaze
VERSION       ?= 1.4
SENDER_IMAGE  := $(REGISTRY)/SpiderMon/docker/spidermon-sender/spidermon-sender:$(VERSION)
RECEIVER_IMAGE:= $(REGISTRY)/SpiderMon/docker/soidermon-receiver/spidermon-receiver:$(VERSION)

# ----------------------------------------
# RULES
# ----------------------------------------

.PHONY: all build push login clean show

all: build push

build: build-sender build-receiver

build-sender:
        docker build -t $(SENDER_IMAGE) ./spidermon-sender

build-receiver:
        docker build -t $(RECEIVER_IMAGE) ./spidermon-receiver

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
        @echo "REGISTRY:       $(REGISTRY)"
        @echo "VERSION:        $(VERSION)"
        @echo "SENDER_IMAGE:   $(SENDER_IMAGE)"
        @echo "RECEIVER_IMAGE: $(RECEIVER_IMAGE)"
