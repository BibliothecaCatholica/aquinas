# Status — source pilot v2.1

Experimental release, not promoted. GPU training and development generation completed on Bazzite: 40 source-conditioned examples, 3 epochs, 30 updates; 226 generation records, no generation errors or length stops. SDPA attention plus non-reentrant gradient checkpointing made the 1,178-token training example fit the RTX 3070. Peak training allocation was 5,543,983,104 bytes; peak reserved memory was 7,117,733,888 bytes. GPU use by other applications can affect feasibility.

The uploaded adapter has SHA-256 `3f9f9eb50257bb734f054f810e7604c11fd1638094a6ce6d1f32807f17b7eca4`. Its uploaded training manifest matches the results archive. It contains 8,052,736 LoRA parameters in 284 tensors. Its tokenizer mapping and template are checked against the pinned reference.

The complete v2.1 set has not received a full answer-by-answer or independent scholarly review. A limited spot check found continuing reasoning and citation weaknesses; it does not establish a winner. No merged GGUF, Ollama deployment of the adapter, mobile build, or fresh sealed confirmation test is claimed. Full-size CPU inference and the public convenience wrapper have not been run on the user's GPU here; its backend comes from the executed evaluation runner, with local integration checks.

The first 28-example pilot was superseded as a training format: it supplied citations without source evidence in actual input messages. Its 126 outputs were fully reviewed by the assistant, showed serious source errors, and were not promoted. The corrected 40-record draft supplies complete respondeo text and adds unsupported-request and premise-preservation cases. The 50 keyed philosophical articles remain disjoint from training article IDs, but the concepts overlap and the items are development questions.

Historical initial-build documents under `docs/history/` describe earlier states; this document is current. Next substantive work is expert review, fresh confirmation questions, and measured retrieval improvements. The published research alpha remains usable for inspection and local experiments while that work continues.
