# Requirement-to-Feature Traceability (initial draft)

| SRS area | Implemented feature | Status | Verification |
|---|---|---|---|
| Medical staff/facility authentication | Login/logout, hashed passwords, server-side session, role checks | Partially implemented | Test login and unauthorized requests |
| Donor Data Management | Persistent donor CRUD, search/filter, status changes, validation | Implemented for prototype scope | Create donor and retrieve it via UI/API |
| Recipient Waitlist Management | Persistent recipient CRUD, status changes, search/filter | Implemented for prototype scope | Create recipient and retrieve it via UI/API |
| Automated Organ Matching | Organ-type + demo ABO filters, transparent urgency/wait-time score, saved runs | Partially implemented | Run matching and inspect stored results |
| Match notification/logistics | Database-backed in-app notifications and demo review status | Partially implemented | Run matching, mark notification read |
| Auditing/compliance reporting | Read-only audit view for privileged roles and key events | Partially implemented | Inspect audit trail after changes |
| Production clinical allocation | Not implemented | Not implemented | Out of academic prototype scope |
| National registry/EHR/SMS/pager integrations | Not implemented | Not implemented | Future work |

**Important:** Replace generic SRS-area labels with exact requirement IDs and wording from the final SRS before submission. Status labels describe prototype scope, not a claim that all detailed SRS acceptance criteria are complete.
