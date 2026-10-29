# 2. Parcel State Machine

## Status

Accepted

## Context

Parcel lifecycle events must follow explicit rules, including allowed state transitions, retry limits, and terminal delivered or returned states. Implementing these rules directly inside HTTP handlers would couple business logic to FastAPI and make the rules harder to test independently.

## Decision

We will implement parcel lifecycle transitions in a pure Python `apply_event` function that returns a new immutable `Parcel` or raises `InvalidTransition` when an event is not allowed.

## Consequences

The lifecycle rules remain independent of HTTP concerns and can be tested without running an API server. Immutable parcels help prevent accidental state changes, but API handlers must translate domain exceptions into appropriate HTTP errors and store the returned parcel objects.
