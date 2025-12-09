.PHONY: run-isimpathy-eval run-eval chat

run-isimpathy-eval:
	uv run inspect eval evals/isimpathy.py --model openai/azure/gpt-4.1-mini --limit $(limit)

run-eval:
	uv run inspect eval evals/$(script).py --model vllm/$(or $(model),meta-llama/Llama-3.1-8B-Instruct) --limit $(limit) --no-fail-on-error --max-connections 30

serve-vllm:
	uv run vllm serve $(or $(model),meta-llama/Llama-3.1-8B-Instruct) --api-key token-abcd1234 --enable-auto-tool-choice --tool-call-parser llama3_json --gpu-memory-utilization 0.8 --max-model-len 16384 --gpus all

serve-vllm-docker:
	docker run --gpus all -p 8000:8000 \
		-v /data/.cache/huggingface/hub:/root/.cache/huggingface/hub \
		-e HF_HUB_CACHE=/root/.cache/huggingface/hub \
		vllm/vllm-openai:v0.8.5 \
		--model $(or $(model),meta-llama/Llama-3.1-8B-Instruct) \
		--api-key token-abcd1234 \
		$(if $(tool-parser),--enable-auto-tool-choice,) \
		$(if $(tool-parser),--tool-call-parser $(tool-parser),) \
		--gpu-memory-utilization 0.8 \
		--max-model-len 32768 \
		--tensor-parallel-size 2

serve-vllm-docker-openai:
	docker run --gpus all -p 8000:8000 \
		-v /data/.cache/huggingface/hub:/root/.cache/huggingface/hub \
		-e HF_HUB_CACHE=/root/.cache/huggingface/hub \
		--shm-size=8g \
		vllm/vllm-openai:v0.11.0 \
		--model $(or $(model),meta-llama/Llama-3.1-8B-Instruct) \
		--api-key token-abcd1234 \
		--gpu-memory-utilization 0.95 \
		--max-model-len 65536 \
		--tensor-parallel-size 2 

serve-vllm-docker-openai-test:
	docker run --gpus all -p 8000:8000 \
		-v /data/.cache/huggingface/hub:/root/.cache/huggingface/hub \
		-e HF_HUB_CACHE=/root/.cache/huggingface/hub \
		--shm-size=8g \
		vllm/vllm-openai:gptoss \
		--model $(or $(model),openai/gpt-oss-20b) \
		--api-key token-abcd1234 \
		--tensor-parallel-size 2 

# Note you can have a pythonic tool call parser as well

chat:
	uv run python chat.py -m $(or $(model),meta-llama/Llama-3.1-8B-Instruct)