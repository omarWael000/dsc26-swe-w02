# AI usage

## Tools

I used ChatGPT to help understand the task requirements, implement and debug the FastAPI endpoints, reason about cursor pagination and parcel state transitions, design manual validation checks, and draft the architecture decision records. I ran the provided tests and additional manual checks to verify the implementation.

## What AI got wrong

During development, I did not treat an assistant's suggestions as proof that the implementation was correct. I verified the behavior by running the public tests and manual checks, including pagination with state changes between requests and validation error responses. I used the observed results to check the implementation rather than relying on explanations alone.

## In my own words

1. Why does `listParcels` need a cursor rather than an offset?

A cursor lets the next request continue after the last parcel's creation position. If a parcel's state changes between requests, offset pagination can skip or repeat parcels because the filtered list may shift, while a creation-position cursor avoids that problem.

2. Which of your four operations would break the courier app if you renamed one field, and who would have to approve that change?

Renaming a field in any of the four API operations could break clients that depend on that field in requests or responses. The API change should be approved by the responsible API owner and coordinated with the teams maintaining the courier app and other clients that use the API.