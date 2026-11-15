# Aquinas v0.2.0 alpha 1

Experimental local Thomistic study tool from Bibliotheca Catholica. Includes the primary-source retrieval code, Summa I and I-II texts with provenance and original notices, a 40-example source-conditioned LoRA adapter, and installation/reproduction instructions.

The adapter trained for 30 optimizer updates on an RTX 3070 and completed 226 matched development responses with zero generation errors or output-limit stops. Independent philosophical review is pending; answer correctness, improved reliability, and doctrinal authority are not claimed. It is not promoted over the official baseline.

Download the attached ZIP or clone the source repository, then follow README.md. The ~31 MiB adapter is included; download of the separate pinned LiquidAI/LFM3-1.7B base is required for adapter inference. Original code is MIT licensed; the adapter/tokenizer, upstream model source and Gutenberg texts retain the separate terms in THIRD_PARTY_NOTICES.md.

No merged GGUF, mobile package or Ollama import of the adapter is included. Existing Ollama models are preserved.
