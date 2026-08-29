# Emergency Relief Request Broker (Serverless MVP)

Initial implementation scaffold for an auto-scaling, serverless emergency relief request broker.

## Architecture (AWS)

- **CloudFront + API Gateway**: global ingress and API management
- **Lambda**: request router, priority dispatcher, geo-router
- **SQS**: decoupled request queueing with DLQ
- **DynamoDB**: request state tracking

## Project Structure

- `template.yaml` - AWS SAM template for core infrastructure
- `src/request_router` - ingest and validate emergency requests
- `src/priority_dispatcher` - priority mapping and dispatch decisions
- `src/geo_router` - region selection and failover selection logic
- `shared/schemas` - request contract schemas
- `tests` - local unit tests

## Local Test

```bash
cd /home/runner/work/rishis777/rishis777/emergency-relief-broker
python -m unittest discover -s tests -v
```

## Next Steps

1. Replace local stubs with AWS SDK integrations (SQS, DynamoDB).
2. Add API authorization, WAF policies, and idempotency storage.
3. Add CI pipeline and load-test suite for burst simulation.
