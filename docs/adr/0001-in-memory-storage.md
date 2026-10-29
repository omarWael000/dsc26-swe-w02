# 1. In-Memory Parcel Storage

## Status

Accepted

## Context

The Tawseel parcel service must create, retrieve, list, and update parcels. The task requires an in-memory implementation, and each application instance must maintain independent state. A database could provide persistence, but would add setup and complexity beyond the current requirements.

## Decision

We will store parcels in an in-memory dictionary keyed by parcel ID, with separate in-memory structures for merchant reference uniqueness, creation order, and pagination cursors. We will initialize all these structures inside `create_app()` so application instances do not share state.

## Consequences

The implementation is simple, fast, and requires no external database. However, data is lost when the application restarts, and state is not shared between multiple workers. A production deployment requiring persistence and multi-worker consistency would need a different storage approach.