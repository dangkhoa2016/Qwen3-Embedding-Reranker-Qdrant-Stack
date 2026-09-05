# Lộ trình hiệu năng sau release
> 🌐 Language / Ngôn ngữ: [English](roadmap.md) | **Tiếng Việt**

Release `1.0.0` giữ ổn định cấu hình CPU production demo đã được kiểm chứng. Các thay đổi hiệu năng tương lai nên được đánh giá như qualification work mới thay vì âm thầm thay baseline đã publish.

Các hướng có thể xem xét:

1. Kiểm chứng GPU reranker với candidate pool lớn hơn.
2. Topology GPU embedding + reranker.
3. Qdrant retrieval pool và rerank depth lớn hơn khi tài nguyên cho phép.
4. Adaptive Top-K dựa trên retrieval ambiguity/confidence.
5. Candidate shortlisting nhẹ trước rerank.
6. Dense+sparse Qdrant hybrid retrieval.
7. Separate hoặc distributed inference workers.

Mọi thay đổi được promote cần giữ reproducibility, memory-safety evidence, semantic validation và runtime/data provenance rõ ràng.
