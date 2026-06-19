## Misplaced projection in a foreign write-side table (orphaned ownership)

### Smell
A derived, read-oriented value — a *projection* of events that happened in another context — is
materialized as a column on an **operational write-side table**, and the job that keeps it fresh
lives in a service that owns **neither the source of truth nor the destination table**. Three
failures stack on top of each other:

1. **Misplaced data.** The value is a read model (a lookup/reporting projection), yet it sits
   inside a table whose reason to exist is operational writes. Every reader of that table now
   couples to a column unrelated to the table's purpose, and the table's owner can no longer reason
   about who writes it or when.
2. **Misplaced behaviour.** The context that actually produces the underlying event does **not**
   write the value — frequently because writing it inline would overwhelm the database (millions of
   writes/day, connection exhaustion). So the write is exiled to a batch/queue job in a *third*
   service that reads from one store (analytics/event log) and writes into a table it does not own.
3. **No owner.** Because the data and the behaviour are split across contexts that each disown them,
   nobody owns the failure mode. The job breaks in production and stays broken: the event producer
   says "not my table", the table's owner says "not my job", the job's host service says "not my
   data". Chronic, unowned failure is the diagnostic symptom that the smell has set in.

The tell: *"we keep the projection on `<operational_table>` because that's where readers already
look, and a job in `<other_service>` backfills it from `<analytics_store>` because writing it at the
source would blow up the DB."*

### Trigger
- A column on an operational table is written **only** by a job in a different service — never by
  the code that owns the table, nor by the code that owns the event the value summarizes.
- That backfill/projection job fails repeatedly in production and no single team treats it as theirs.
- The justification for not writing the value at its source is a scaling concern ("too many
  writes"). That is precisely the signal the value wants to be an **async projection with a
  deliberate owner**, not a column smuggled into someone else's table.

### Refactoring
1. **Name the source of truth.** Identify the context that owns the event (e.g. delivery to
   crawlers → the delivery/cache context, whose events already land in the analytics store).
2. **Make the projection a first-class read model with one owner.** Move it out of the operational
   table into a store the read side owns (its own projection table / materialized view / read
   cache). The operational table goes back to holding only what its own writers own.
3. **Give the maintaining behaviour to the owner of the source of truth.** The producing context
   publishes the event (stream / outbox / domain event); the read side subscribes and updates its
   own projection. The scaling problem that forced the batch hack is now solved by async projection
   with backpressure — not by exiling a write to a foreign job.
4. **Delete the orphan job, or relocate it into the owning context** as an explicit, owned projector
   with its own alerting and SLO. Either way it gains a single team that owns its failures.
5. **Point readers at the projection**, not at a column bolted onto the write table.

### Structure after refactoring
- Operational table: only fields its writers own; no foreign-maintained columns.
- Projection store: owned by the read side, fed by events from the source-of-truth context.
- Exactly one projector, with a clear home, explicit ownership, and its own monitoring.
- **Data and the behaviour that maintains it share a single owner** — this is the fix; the
  data-placement change without the ownership change just moves the orphan.

### Tests
- Projector test: given source events, the projection updates correctly — idempotent, tolerant of
  replay and out-of-order delivery.
- Reader test: reads come from the projection, with defined behaviour when it is stale or missing.
- Regression test proving the operational table no longer needs (or carries) the foreign column.

### Example
**`last_delivered_at` on an operational `resources` table.** The value represents the last time a
resource was delivered to a consumer — a read-only projection consumed by many. It lived as a column
on `resources` (an operational write table). The delivery context, which owns delivering to
consumers, deliberately did **not** write it inline, because doing so would issue millions of writes
a day and exhaust DB connections. Instead a job in a separate queue service (`LastDeliveredJob`) read
delivery data from the analytics store and wrote the projection back into `resources` — a table it
does not own. The result: a misplaced read projection, behaviour with no real owner, and a job that
fails consistently in production with no team that treats it as theirs. The fix is ownership: the
delivery context owns and publishes delivery events; the projection becomes a read model owned by
its readers and fed from those events; the orphan job is retired or rehomed into the owning context
with its own alerting. See `~/.claude/skills/cqrs/SKILL.md` for read/write ownership conventions.
