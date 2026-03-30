#!/usr/bin/env python3
"""Setup workspace for long-document-key-facts task."""

import os
import sys

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
os.makedirs(workspace, exist_ok=True)

whitepaper = """\
QuantumCache: Next-Generation Distributed Caching for the Modern Enterprise
Technical Whitepaper — Version 3.1
Published by QuantumCache Labs, February 2026

ABSTRACT
--------
QuantumCache is a high-performance distributed caching system designed to address the
limitations of existing solutions in latency-sensitive, large-scale deployments. This
whitepaper describes the architecture, performance characteristics, and real-world
deployment outcomes of QuantumCache in enterprise environments.

1. INTRODUCTION
---------------
As modern applications demand ever-lower latency and ever-higher throughput from their
data layers, traditional caching solutions have struggled to keep pace. Memcached and
Redis, while battle-tested, were designed for an era when single-digit millisecond latency
was considered acceptable. Today's AI-driven applications, real-time bidding platforms,
and global e-commerce systems require something fundamentally different.

QuantumCache was built from scratch with three design principles: sub-millisecond latency
as a baseline guarantee (not a best-case result), linear horizontal scalability, and
zero-configuration cluster healing. It achieves these goals through a combination of
lock-free data structures, NUMA-aware memory allocation, and a gossip-based consistency
protocol that eliminates the need for a centralized coordination layer.

2. PERFORMANCE CHARACTERISTICS
-------------------------------
2.1 Latency

In controlled benchmark conditions using synthetic workloads representative of real-world
traffic patterns, QuantumCache consistently achieves sub-millisecond latency for read
operations at the 99th percentile. Specifically, at 500,000 operations per second with
a working set of 10 GB, QuantumCache delivers:

  - p50 (median) read latency: 0.12 ms
  - p99 read latency: 0.74 ms
  - p999 read latency: 1.1 ms

These results compare favorably to Redis 7.2, which achieves p99 read latency of 2.3 ms
under the same workload conditions — a 3x improvement delivered by QuantumCache.

2.2 Availability and Uptime

QuantumCache's cluster healing protocol ensures that node failures are detected and
compensated for within 800 milliseconds, without any interruption to read availability.
Write availability may experience brief degradation during node recovery. Over a 12-month
measured period across all production deployments, QuantumCache has achieved 99.99% uptime,
corresponding to less than 53 minutes of cumulative downtime per year.

2.3 Protocol Compatibility

QuantumCache implements the Redis-compatible protocol (RESP3), meaning that any application
already using Redis can migrate to QuantumCache with no code changes. This includes support
for all common Redis data types (strings, hashes, lists, sets, sorted sets) and the vast
majority of Redis commands. The compatibility layer has been validated against the official
Redis test suite with 98.7% command parity.

3. REAL-WORLD DEPLOYMENTS
--------------------------
3.1 TechGiant Inc — E-Commerce Platform

TechGiant Inc, one of the world's largest online retailers, deployed QuantumCache in Q3 2025
to replace their existing Redis cluster serving their product recommendation engine. The
deployment consists of 48 QuantumCache nodes across three availability zones.

Results after 6 months of production operation:
  - Infrastructure cost reduction: 40% compared to prior Redis deployment
  - Average recommendation latency reduced from 4.2 ms to 0.9 ms (79% improvement)
  - Zero cache-related outages in 6 months of operation
  - Peak throughput handled: 2.1 million operations per second during Black Friday 2025

TechGiant's Head of Platform Engineering, Jerome Watkins, stated: "QuantumCache delivered
everything we hoped for and more. The 40% cost reduction alone paid for the migration project
within two quarters."

3.2 FinStream Analytics — Real-Time Trading

FinStream Analytics, a quantitative trading firm, adopted QuantumCache in January 2026 for
their market data caching layer. The firm's primary requirement was absolute latency
consistency — tail latency spikes can have material financial consequences in their domain.

FinStream reports that QuantumCache has eliminated the latency spikes they previously
experienced with their Redis deployment. Their p999 latency has dropped from 8.4 ms to
1.1 ms, a 7.5x improvement that has meaningfully improved their algorithmic trading outcomes.

4. SCALABILITY
--------------
QuantumCache supports linear horizontal scaling up to 256 nodes in a single cluster.
Capacity can be expanded with zero downtime through the automated rebalancing protocol.
In testing, a 32-node cluster was expanded to 64 nodes while sustaining 1 million operations
per second, with no client-visible interruption and rebalancing completing in under 4 minutes.

5. CONCLUSION
-------------
QuantumCache represents a significant advancement in distributed caching technology.
Its combination of sub-millisecond latency, 99.99% uptime guarantee, Redis-compatible
protocol, and demonstrated 40% cost reduction in production deployments makes it the
premier choice for organizations that cannot afford to compromise on performance or
reliability. For teams currently running Redis at scale, the zero-code-change migration
path and immediate latency improvements make the transition highly attractive.

For more information, visit quantumcache.io or contact enterprise@quantumcache.io.
"""

with open(os.path.join(workspace, "whitepaper.txt"), "w") as f:
    f.write(whitepaper)

print(f"Workspace ready: {workspace}")
