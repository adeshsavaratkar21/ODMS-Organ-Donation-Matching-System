# Organ Donation Matching System — Implementation Report

## Objective
Implement an integrated academic prototype of ODMS with persistent donor and recipient records and a transparent candidate-screening workflow.

## Implemented modules
1. **Donor Data Management:** create, list, search, filter, view, edit, and change availability of donor profiles.
2. **Recipient Waitlist Management:** create, list, search, filter, edit, and change recipient status while preserving the waiting-list date.
3. **Automated Matching Engine:** query saved donor/recipient records, apply the documented demonstration organ-type and ABO filters, rank candidates by a transparent urgency/waiting-time score, and persist match runs/results.
4. **Supporting functionality:** login/logout, basic role checks, notifications, audit logs, dashboard summaries, and synthetic seed data.

## Architecture
React/Vite frontend communicates with a Flask REST API. Flask-SQLAlchemy persists records in SQLite by default for a zero-setup local demo and supports PostgreSQL through `DATABASE_URL`. The backend validates submitted data and records important actions.

## Database entities
Facility, User, Donor, Recipient, MatchRun, MatchResult, Notification, and AuditLog. Foreign keys link facilities to records and match results to their originating run, donor, and recipient.

## Demo workflow
Sign in → inspect dashboard → register donor → register recipient → run matching → review candidates → inspect match history, notifications, and audit trail.

## Test status
Run the included tests using `pytest -q` from the backend environment. Record the actual output in the submitted report after running tests locally; do not report unexecuted tests as passing.

## Limitations
This is a synthetic educational prototype. Matching is simplified and not clinically validated. It does not implement official allocation policies, validated HLA crossmatching, hospital integration, or external notifications. A potential match is not a clinical recommendation or authorization to transplant.

## Demo video
[Insert the actual 2–5 minute video link after recording and uploading the demonstration.]
