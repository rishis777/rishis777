# Emergency Relief Request Broker (Serverless MVP)

Initial implementation scaffold for an auto-scaling, serverless emergency relief request broker.

## Architecture (AWS)

- **CloudFront + API Gateway**: global ingress and API management
- **Lambda**: request router, priority dispatcher, geo-router
- **SQS**: decoupled request queueing with DLQ
- **DynamoDB**: request state + idempotency tracking

## Project Structure

- `template.yaml` - AWS SAM template for core infrastructure
- `src/request_router` - ingest, authorize, deduplicate, persist, and enqueue emergency requests
- `src/priority_dispatcher` - priority mapping and dispatch status updates
- `src/geo_router` - region selection and failover selection logic
- `shared/schemas` - request contract schemas
- `tests` - local unit tests

## Environment Variables

- `REQUEST_QUEUE_URL` - target SQS queue URL
- `REQUEST_TABLE_NAME` - DynamoDB table for request lifecycle
- `IDEMPOTENCY_TABLE_NAME` - DynamoDB table for idempotency keys
- `EXPECTED_API_KEY` - optional API key to enforce in `x-api-key` header

## Local Test

```bash
cd /home/runner/work/rishis777/rishis777/emergency-relief-broker
python -m unittest discover -s tests -v
```

## Next Steps

1. Add API authorization with managed AWS authorizers/JWT.
2. Add WAF managed rule packs and abuse protection.
3. Add CI pipeline and load-test suite for burst simulation.

## Load Testing (Artillery)

- Config file: `/home/runner/work/rishis777/rishis777/emergency-relief-broker/load-testing/artillery.yml`
- Processor hooks: `/home/runner/work/rishis777/rishis777/emergency-relief-broker/load-testing/processor.js`

Run:

```bash
cd /home/runner/work/rishis777/rishis777/emergency-relief-broker/load-testing
TARGET_URL="https://<api-id>.execute-api.<region>.amazonaws.com/prod" npx artillery run artillery.yml
```
