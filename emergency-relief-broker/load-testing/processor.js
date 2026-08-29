const { randomUUID } = require('crypto');

const severities = ['critical', 'high', 'medium', 'low'];

function randomInRange(min, max) {
  return min + Math.random() * (max - min);
}

function randomSeverity() {
  return severities[Math.floor(Math.random() * severities.length)];
}

function setUniqueRequestData(userContext, _events, done) {
  userContext.vars.idempotencyKey = randomUUID();
  userContext.vars.citizenId = `citizen-${randomUUID()}`;
  userContext.vars.severity = randomSeverity();
  userContext.vars.lat = Number(randomInRange(8.0, 37.0).toFixed(6));
  userContext.vars.lon = Number(randomInRange(68.0, 97.0).toFixed(6));
  userContext.vars.description = 'Emergency assistance needed at reported location';
  return done();
}

function setDuplicateBurstData(userContext, _events, done) {
  userContext.vars.duplicateIdempotencyKey = randomUUID();
  userContext.vars.duplicateCitizenId = `citizen-${randomUUID()}`;
  userContext.vars.duplicateSeverity = 'high';
  userContext.vars.duplicateLat = 19.076;
  userContext.vars.duplicateLon = 72.8777;
  userContext.vars.duplicateDescription = 'Duplicate idempotency burst validation request';
  return done();
}

function assertAcceptedStatus(req, res, _context, _events, done) {
  if (res.statusCode !== 200 && res.statusCode !== 202) {
    return done(new Error(`Unexpected status code: ${res.statusCode}`));
  }
  return done();
}

module.exports = {
  setUniqueRequestData,
  setDuplicateBurstData,
  assertAcceptedStatus,
};
