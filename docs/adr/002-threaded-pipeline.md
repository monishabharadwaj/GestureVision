# ADR-002: Threaded pipeline with ring buffer

- Status: Accepted
- Date: 2026-07-14

## Context

A single-threaded capture → process → render loop cannot meet 30–60 FPS while keeping the UI responsive.

## Decision

Use a **capture thread** writing into a fixed-size **ring buffer**, a **process thread** consuming the latest frame, and the **Qt main thread** for rendering only.

## Consequences

- Need careful ownership of frame buffers.
- Stale frames are dropped by design.
- Testability improves via a mock `FrameSource`.
