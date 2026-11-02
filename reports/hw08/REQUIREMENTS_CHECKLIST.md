# HW8 Requirements Checklist

- [x] Section 0 configuration and restaurant-inspection domain retained.
- [x] Part 1 protocol, validation, UUID IDs, correlation IDs, two topics, API wrapper, and worker runtime.
- [x] Part 2 four-topic Planner/Writer/Reviewer pipeline and separate entry points.
- [x] Part 3 deterministic duplicate, consumer-death, poison/dead-letter, and 20-message ordering artifact.
- [x] Offline tests and objective smoke-test script.
- [x] Live Docker/Kafka service, consumer-death, dead-letter, and ordering logs/raw artifacts captured; screenshots intentionally deferred for manual capture.
- [x] Part 3 consumer death: dedicated Writer crashed before processing, same group redelivered, and post-success offset was recorded.
- [x] Part 3 ordering: exactly 20 unkeyed and 20 keyed messages captured with two Writer members, partitions, offsets, and zero-lag group evidence.
- [ ] JMeter benchmark: not run; supporting PDF treated as separate demo.
- [ ] Final commit hash and annotated hw8 tag: after packaging.
- [ ] Collaborator access: account-level check pending.
