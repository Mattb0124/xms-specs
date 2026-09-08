# Security Review: XMS backend, the 2026-09-08 to 09-09 work

**Date:** 2026-09-09
**Reviewer:** independent read of `xms-backend` @ `5f9fae4`, scoped to `git log 3679482^..5f9fae4` (31 commits, migrations 0030 to 0041, about 14,000 added lines)
**Reviewed against:** `01-architecture/SECURITY-AND-TENANCY.md`, `01-architecture/DATA-MODEL.md`, `01-architecture/AUDIT-AND-ANALYTICS.md`, `01-architecture/INTEGRATION-PATTERNS.md`, and `03-delivery/REVIEW-security-2026-09-08.md` (whose 40 findings are not re-litigated here)
**Scope:** the ServiceNow outbound sync, quarterly CSAT and contact flags, out-of-scope approvals, the audit search over the operator stream, review before send and the narrative editor, the survey describe route, audit saved queries, the integrity panel and the Security and Usage dashboards, assignment groups and routing, change windows, non-ticket time, per-account portal forms, and the image re-encode.

---

## Summary

The discipline held. Every one of the twelve new migrations that creates an account-scoped table calls `sys.apply_account_isolation` or writes the equivalent block by hand (`0040_ticket_forms.sql:80-98` writes narrower portal policies deliberately and correctly), every new vocabulary is closed in both the DTO and a SQL `check`, the audit condition grammar's new null test is gated on an explicit nullable-column set, the CSAT token work is genuinely good (CSPRNG, hash at rest, `timingSafeEqual`, fragment not query string, one 404 shape for both a missing survey and a wrong token, and the public rate-limit policy already covers `csat`), and the outbound sync's loop guard is closed at three independent points rather than one. The out-of-scope flow gets the control the specification asks for: `tickets.service.ts:1417` refuses the flagger's own decision.

Three things break. The first is an authorization bypass that makes a new permission decorative: `tickets:override-change-window` gates transitioning into a deploy state outside a window, but the window itself is edited through `PATCH /v1/ticket-groups/:id`, which stands on `tickets:work`, so the same principal that is refused simply deletes the freeze and widens the span first, and the audit diff that should record it is computed from a field list `freeze_windows` is not on. The second is the image re-encode. It does what section 6 promises to the bytes it stores, but it decodes at whatever dimensions the sender chose: `sharp`'s `limitInputPixels` is left at its 268-megapixel default, the header dimensions are read and then not checked, and the dimension cap is a `resize` applied after the decode. The email intake path reaches that with no size or dimension gate of its own, which makes it the first remotely reachable memory-exhaustion vector in the product that needs no account at all. The third is the ServiceNow attachment download, where the size cap is applied after `arrayBuffer()` has already bought the whole body, and the pre-check is vacuous whenever the instance omits `content-length`.

Below those, the recurring shape is a control that exists somewhere in the codebase and was not carried to the new call site: the audit search writes its account grant clause and explains in a comment why it is needed, and the Security dashboard three hundred lines away does not; the browser upload path enforces the MIME allowlist and the connector `ingest` path does not; the internal ticket DTO caps `form_data` at 64 kB and the portal path that constructs the same field bypasses the pipe. None of these is a cross-account read under the seeded role catalog, because `audit:read` reaches only Administrator and Administrator is already bound portfolio-wide, but each is one custom role away.

Nothing found here leaks one client's data to another under the roles as seeded, and no new table skips row-level security.

---

## Findings

| # | Severity | Area | Finding |
|---|---|---|---|
| 1 | High | Authorization | `tickets:override-change-window` is bypassed by editing the window through a `tickets:work` route, and the edit leaves an empty audit diff |
| 2 | High | File handling | The image re-encode decodes at the sender's dimensions with no pre-decode cap; reachable by anyone who can email the account alias |
| 3 | High | Outbound HTTP | The ServiceNow attachment download buffers the whole response before the size cap, and the pre-check is vacuous without `content-length` |
| 4 | Medium | Tenant isolation | Five Security dashboard queries read `sys.security_events` with no account grant clause |
| 5 | Medium | Authorization | The person who requested a report run can approve it; run-now, approve and cancel are one permission |
| 6 | Medium | Secrets and tokens | Report pack delivery links are 14-day presigned URLs, over the SigV4 maximum and unrevocable |
| 7 | Medium | File handling | `AttachmentsService.ingest` skips the MIME and extension allowlist the browser path enforces |
| 8 | Medium | File handling | The presigned upload credential outlives the confirm-time re-encode and scan, and `re_encode` short-circuits a second pass |
| 9 | Medium | Authorization | The out-of-scope allowance is unbounded and edits a locked contract period |
| 10 | Medium | Input handling | Portal form `answers` is unbounded and emits one echoed problem per unknown key |
| 11 | Medium | Availability | `narrative_versions` grows without bound on a held run |
| 12 | Medium | Availability | The change calendar accepts an unbounded date range and reads tickets per window |
| 13 | Medium | Audit completeness | The change-window override and acknowledgement are audited but never reach the outbox |
| 14 | Low | Availability | `ALLOWED_TYPES[contentType]` on the email path is not an own-key lookup |
| 15 | Low | Input handling | The portal submission path bypasses the 64 kB `form_data` cap |
| 16 | Low | Information leak | Raw exception text is stored on the run row and returned by a `select r.*` |
| 17 | Low | Input handling | `attachment_limit_bytes` has no upper bound |
| 18 | Low | Input handling | `constructor` is a legal form field key and answers are read off the prototype |
| 19 | Low | Input handling | The `maps_to` allowlist is enforced at save but not at submission |
| 20 | Low | Injection | The polled `sys_id` is interpolated into the ServiceNow encoded query |
| 21 | Low | Loop guards | The journal marker is client-forgeable and `createJournal` can record the wrong entry |
| 22 | Low | Authorization | `RoutingService.replace` has no account check and fails on the policy rather than on a 404 |
| 23 | Low | Audit completeness | Withdrawing a scope flag is not published and reuses the raise event type |
| 24 | Low | Input handling | The contacts list `limit` never coerces, and the service has no account check |
| 25 | Low | Input handling | A form option label is unbounded and the field loop continues past `too_many` |
| 26 | Low | Audit completeness | The bucket audit diff omits the new taxonomy `code` |
| 27 | Low | Information leak | A dead letter's `instance_id` is returned past the account grant |

---

### 1. High. The change-window override permission is bypassed by a `tickets:work` route

**Where.** `backend/src/modules/tickets/change-windows.module.ts:492-493` and `:508-509` (both `@RequirePermission('tickets:work')`), `:373` (the patch assignment), `:299` and `:377` (`PATCH_FIELDS` and the diff), with the gate at `backend/src/modules/tickets/tickets.service.ts:1663-1687`.

**What is wrong.** The deploy gate is correct in isolation:

```ts
const open = window !== undefined && insideWindow(window, now) && frozen === undefined;
if (!open) {
  const overridable = principal.permissions.has('tickets:override-change-window') && Boolean(note);
```

but it evaluates a row the caller can edit. `POST /v1/ticket-groups` and `PATCH /v1/ticket-groups/:id` both require only `tickets:work`, which every operator role reaches (`Consultant` through `tickets:resolve`, `Dispatcher` directly), while `tickets:override-change-window` is held only by Administrator and Account Owner (`src/contracts/permissions.ts:133,160`). `assertSchedule` (`change-windows.module.ts:461-473`) checks only that a change window has both ends and that `ends_at > starts_at`; it does not bound the span, does not require a freeze to survive, and does not care whether member tickets are in flight. Line 373 always writes the freeze list, and `dto.freeze_windows ?? before.freeze_windows` treats an explicit `[]` as the new value rather than as absent:

```ts
const freezes = (dto.freeze_windows ?? before.freeze_windows ?? []) as FreezeWindow[];
...
const assignments: Record<string, unknown> = { starts_at: startsAt, ends_at: endsAt, freeze_windows: freezes };
```

The cover is the second half. `PATCH_FIELDS` at line 299 is `['name', 'description', 'owner_user_id', 'starts_at', 'ends_at', 'status']`, and line 377 computes `changed` from it, so a patch that only clears `freeze_windows` writes an audit row whose `oldValue` and `newValue` are both `{}`. That satisfies the `sys.require_audit` constraint trigger installed by `0038_change_windows.sql:45-46` while recording nothing, and the outbox payload at line 395 carries the same empty `fields` array.

**What it enables.** A consultant refused with `409 outside_change_window` sends one `PATCH /v1/ticket-groups/:id` with `{"version": n, "freeze_windows": [], "starts_at": "2000-01-01T00:00:00Z", "ends_at": "2099-01-01T00:00:00Z"}`, then retransitions. No `ticket.change_window_overridden` row is written, no reason is captured, and the patch that made it possible is recorded as a change to nothing. TM-18's freeze rule and the new permission are both defeated by an authenticated caller two permission levels below the one the design names.

**Fix.** Put the schedule of a `change_window` behind `tickets:override-change-window` or `admin:config`: either gate the whole route by `kind`, or refuse `starts_at`, `ends_at` and `freeze_windows` changes on a `change_window` without that permission and a reason, auditing the reason. Refuse a schedule edit while a member ticket sits in a state whose `effects.deploy` is set. Independently, add `freeze_windows` to the diffed set (comparing serialized JSON) so the audit row can never be empty, and add an integration test asserting that a `tickets:work` principal cannot clear a freeze.

---

### 2. High. The image re-encode decodes at the sender's dimensions

**Where.** `backend/src/common/images/reencode.ts:79-88`, reached from `backend/src/modules/email/email.service.ts:416` (email intake), `backend/src/modules/attachments/attachments.module.ts:383` (browser upload at confirm, entered from `:347`) and `:439` (connector ingest).

**What is wrong.** The module reads the header dimensions and then does not use them as a gate:

```ts
const source = sharp(body, { failOn: 'error' });
const meta = await source.metadata();
width = meta.width;
height = meta.height;
const pipeline = sharp(body, { failOn: 'error' })
  .rotate()
  .resize({ width: MAX_IMAGE_EDGE, height: MAX_IMAGE_EDGE, fit: 'inside', withoutEnlargement: true });
```

`resize` caps the output, not the decode. `limitInputPixels` is never set, here or anywhere else in the tree (verified by grep over `src/` and `test/`: no occurrence), so `sharp`'s default ceiling of 268,402,689 pixels applies. A 16,000 by 16,000 image is 256 megapixels, sits under that ceiling, compresses to a few hundred kilobytes as a flat-colour PNG, and decodes to roughly a gigabyte of raw pixels. `sharp.concurrency` and `sharp.cache` are likewise untouched, so several such decodes run at once. The module's own comment at lines 26 to 29 claims "a decompression bomb cannot be re-encoded into the object store", which is true of what is written and not of what is spent getting there.

The email path has no gate of its own. `storeAttachments` (`email.service.ts:386-416`) checks the content type and extension against `ALLOWED_TYPES` and then calls `reEncodeImage(attachment.content, ...)` directly; there is no per-attachment size check and no comparison against the account's `attachment_max_bytes`. The message as a whole is capped at 25 MB on the dev route (`email.module.ts:141`) and by whatever SES delivers on the S3 path.

**What it enables.** Anyone who knows an account's intake alias sends one email carrying a small, highly compressible image with enormous declared dimensions and exhausts the worker's memory. No account, no credential and no XMS identity is required. Before this commit those bytes went straight to `putObject` and were never decoded, so the exposure is new. The browser and connector paths are the same decode behind an authenticated caller, and the browser one runs inside the request's open database transaction (`attachments.module.ts:347`), so it also ties up a pooled connection for the duration of an S3 GET, a decode and an S3 PUT.

**Fix.** Refuse before decoding: after `metadata()`, reject when `width * height` exceeds a budget (a few tens of megapixels is generous for a screenshot) or when either edge exceeds a hard maximum, with the same `ImageNotDecodableError` the quarantine path already handles. Pass `limitInputPixels` explicitly on both `sharp()` constructions rather than inheriting the default, and set `sharp.concurrency(1)` in the worker. Give the email path a per-attachment byte cap equal to the account's `attachment_max_bytes` before it reaches the re-encode. Move the confirm-time re-encode outside the database transaction. Note also that `await sharp(out).metadata()` at `reencode.ts:94` sits outside the `try`, so a failure there is a 500 rather than a quarantine.

---

### 3. High. The ServiceNow attachment download buffers the whole response before the cap

**Where.** `backend/src/modules/connectors/snow-client.ts:254-258`, called from `backend/src/modules/connectors/sync.worker.ts:586`.

**What is wrong.**

```ts
const declared = Number(response.headers.get('content-length') ?? 0);
if (declared > maxBytes) throw new SnowError(0, `attachment ${sysId} is ${declared} bytes, over the limit`);
const bytes = Buffer.from(await response.arrayBuffer());
if (bytes.length > maxBytes) throw new SnowError(0, `attachment ${sysId} is over the limit`);
```

`Headers.get` returns `null` when the header is absent, so `null ?? 0` yields `declared = 0` and the pre-check passes for any chunked response. The second check then runs after `arrayBuffer()` has already materialised the entire body in the worker's heap. Every other outbound read in this file goes through the streaming cap the previous review's finding 17 introduced (`src/common/http/outbound.ts:64-71`, used by `send` and `request` at `snow-client.ts:278-342`); this one call does not.

**What it enables.** A compromised, misconfigured or hostile ServiceNow instance answers `/api/now/attachment/<id>/file` with a chunked multi-gigabyte body and takes down the connector worker, which also runs poll, apply, health and every other account's sync, so one account's integration partner is a denial of service against all of them. The `sys_id` fetched comes straight from the polled payload (`sync.worker.ts:586`), so the instance chooses both the trigger and the response.

**Fix.** Read `response.body` through the same reader loop as `readCappedText`, cancelling the stream past `maxBytes`, instead of `arrayBuffer()`. Treat an absent `content-length` as unknown rather than as zero. See also finding 17: `attachment_limit_bytes` itself has no upper bound, so `maxBytes` is whatever an `admin:connectors` holder typed.

---

### 4. Medium. Five Security dashboard queries read `sys.security_events` with no grant clause

**Where.** `backend/src/modules/reporting/reporting.repository.ts:241-247` (`securityTiles`), `:249-255` (`signinFailures`), `:257-263` (`isolationProbes`), `:270-278` (`abuseByKind`) and `:281-289` (`rateLimitedClients`), called from `backend/src/modules/reporting/reporting.service.ts:448-452`.

**What is wrong.** The codebase states the rule against itself. `searchEvents` at `reporting.service.ts:344-353` writes:

> `sys.security_events` is an operator table with no policy of its own, so without this an `audit:read` holder bound to one account would read another account's security rows.

and then appends `and (account_id is null or account_id = any ($n::uuid[]))`. `sys.security_events` is created at `src/db/migrations/0003_account_scope_and_events.sql` with no `apply_account_isolation` call and therefore no row-level security, yet the five dashboard queries filter only on `occurred_at` and `event_type`. `securityDashboard` runs under `uow.run(principal)` (`reporting.service.ts:447`), which binds `xms.account_ids` correctly, but the binding does nothing for a table with no policy. `openDeadLetters` (`reporting.repository.ts:385`) and the audit search do apply the clause, so the omission is inconsistent rather than deliberate.

**What it enables.** `GET /v1/dashboards/security` requires `audit:read`. A holder bound to one account reads every account's `auth.signin.failed` actor ids and `ip_hash` values, every account's isolation-probe and realm-denial actor ids, and every account's rate-limited principals. Under the seeded catalog this is not currently reachable, because `audit:read` is implied only by `audit:export`, which only Administrator holds, and Administrator is already bound to every live account through `admin:accounts` (the previous review's finding 21, decided and documented). It becomes live the moment a custom role pairs `audit:read` with a narrow grant, which is exactly what the sibling comment anticipates.

**Fix.** Thread `principal.accountIds` into all five and append the same `(account_id is null or account_id = any ($n::uuid[]))` clause the audit search uses. Add an integration test that a principal granted account A does not see account B's `auth.signin.failed` rows on the dashboard, mirroring whatever pins the audit search.

---

### 5. Medium. The person who requested a report run can approve it

**Where.** `backend/src/modules/reporting/schedules.module.ts:952-955`, with the route table at `:1259` (`run-now`), `:1297` (`approve`) and `:1307` (`cancel`).

**What is wrong.**

```ts
approve(principal: Principal, ctx: RequestContext, id: string) {
  return this.uow.run(principal, async (tx) => {
    const { run, schedule, pack, period } = await this.heldRun(tx, id);
    await this.repo.markApproved(tx, run.id, principal.userId);
```

`run.requested_by` is loaded and never compared with `principal.userId`. `POST /v1/reporting/runs/:id/run-now`, `.../approve` and `.../cancel` all declare `reports:manage` in `test/golden/routes.json`, so one permission covers generating the pack, approving it and sending it to the client. Contrast `decideScope` at `tickets.service.ts:1417`, which refuses the flagger's own decision by name, and does so for the same reason.

**What it enables.** The review gate that DR-05 exists to impose is satisfiable by one person. A single `reports:manage` holder generates a pack, edits its narrative, approves it and mails it to the client with no second reader, while the audit trail records a completed review. This is a control gap rather than a privilege escalation, but review before send is the whole point of the feature.

**Fix.** Refuse when `principal.userId === run.requested_by` unless a distinct permission is held, or introduce `reports:approve` (implied by `reports:manage` only where a second reviewer is not required by policy) and gate the approve route on it. Record the reviewer distinctly from the requester in the audit payload either way.

---

### 6. Medium. Report pack delivery links are 14-day presigned URLs

**Where.** `backend/src/modules/reporting/schedules.module.ts:91-92`, used at `:707`, `:712`, `:1032` and `:1039`, reaching `backend/src/common/storage/s3-object-store.ts:64`.

**What is wrong.**

```ts
const DELIVERY_LINK_DAYS = 14;
const LINK_SECONDS = DELIVERY_LINK_DAYS * 24 * 3600;
```

which becomes `expiresSeconds` on `presignDownload`, and then `{ expiresIn: options.expiresSeconds ?? 300 }` on `getSignedUrl`. AWS SigV4 caps `X-Amz-Expires` at 604,800 seconds; 1,209,600 is refused by S3 at redemption, and with instance-role credentials the URL dies when the temporary credentials do, typically within hours. The local store applies no cap at all (`object-store.ts:103`), so in development the 14 days are real. The delivery email words the promise from the same constant (`schedules.module.ts:1100-1101`, "PDF (valid 14 days)").

**What it enables.** Two problems from one number. In production the client is told fourteen days and gets an error, which drives people to forward the pack by other means. In any environment where the expiry is honoured, the link is an unrevocable bearer token to a client's commercial reporting, minted into a mailbox, with no stored record, no single-use property, no binding to a recipient or an account, and no way to withdraw it if the schedule's distribution list was wrong.

**Fix.** Assert a maximum of seven days inside `presignDownload` so a caller cannot mint an invalid URL, and prefer a stored, revocable, account-bound, single-use delivery token row that redeems into a short presign, in the shape the CSAT survey token already demonstrates (`src/domain/portal/csat.ts:145-158`). Word the email from whatever the token actually grants.

---

### 7. Medium. `AttachmentsService.ingest` skips the MIME and extension allowlist

**Where.** `backend/src/modules/attachments/attachments.module.ts:415-464` (`ingest`), called from `backend/src/modules/connectors/sync.worker.ts:587-600` with `fileName: file.file_name` and `contentType: file.content_type || 'application/octet-stream'` (`:592-593`).

**What is wrong.** The browser path checks the declared type against `ALLOWED_TYPES` and requires the extension to match, refusing with `unsupported_type` plus a security event (`attachments.module.ts:264-277`, and note it correctly uses `Object.hasOwn` at `:266`). `ingest` applies the image re-encode and the scan gate but never that allowlist, so the connector stores whatever the polled metadata declared. The name is sanitised (`:449`) and the key is derived from the RLS-bound row, so nothing escapes the account prefix; the type is not.

**What it enables.** A hostile or compromised ServiceNow instance stores files of any type under the client's account with an attacker-declared `content_type`, which is persisted on the row and echoed back on download. `Content-Disposition: attachment` is set on the presign (`s3-object-store.ts:61`), so this is a defence-in-depth gap rather than stored cross-site scripting today, but it means the platform's one statement about what an attachment may be is not enforced on one of the three ways an attachment arrives.

**Fix.** Run the same `ALLOWED_TYPES` and extension parity check inside `ingest`, and on failure record `abuse.upload.rejected` and either skip the file or store it quarantined, so the connector run row says what happened.

---

### 8. Medium. The upload credential outlives the confirm-time re-encode and scan

**Where.** `backend/src/modules/attachments/attachments.module.ts:310-313` (the presign), `:340-354` (`confirm`), `:379` (the short-circuit), with `backend/src/common/storage/s3-object-store.ts:27-49`.

**What is wrong.** `presignUpload` mints a presigned POST valid for 900 seconds against a fixed key (`s3-object-store.ts:32,41`), and the client holds both the URL and the key. `confirm` heads the object, re-encodes it, writes it back and scans it. The re-encode guard is:

```ts
if (row.re_encode || !isReEncodedImage(row.content_type)) return { row, quarantined: false };
```

so a second `confirm` on the same row does no re-encode at all, and on the S3 store no re-scan either (`:349-354` runs the scanner only when `this.store.kind === 'local'`).

**What it enables.** For up to fifteen minutes after the presign, the uploader can PUT the same key again. After `confirm` has set `scan_state = 'clean'` and stamped `re_encode`, a second POST replaces the stored object with arbitrary bytes while the row continues to assert that the file was scanned and rebuilt from its pixels, and `downloadUrl` (`:557-581`) mints a link on the strength of that row. The `head.size > row.size_bytes` check at `:342` bounds a second `confirm` but not a bare overwrite. The scan-bypass half of this predates the re-encode; what commit `9dcb303` adds is a durable claim on the row that the bytes were normalised, which an overwrite falsifies.

**Fix.** Make the upload credential single-use: expire it at `confirm` by recording a nonce and refusing a second confirm, and give the presign a much shorter life (a minute or two is enough for a browser that already holds the bytes). Better, re-head the object and compare an ETag or digest recorded at `confirm` before minting any download link, so a post-confirm overwrite is detected rather than served. Drop the `re_encode` short-circuit, or key it to the object's digest rather than to the row.

---

### 9. Medium. The out-of-scope allowance is unbounded and edits a locked period

**Where.** `backend/src/modules/tickets/tickets.dto.ts:381-384` and `backend/src/modules/tickets/tickets.service.ts:1424-1428`, against `backend/src/modules/time/time.module.ts:918` and `backend/src/modules/time/time.repository.ts:596-604`.

**What is wrong.** The DTO is `@IsOptional() @IsInt() @Min(1) overage_allowance_minutes?: number` with no `@Max`, and the service adds it straight to the period budget:

```ts
const current = await this.time.periodFor(tx, before.contract_id, on);
if (!current) throw new ConflictException({ code: 'no_contract_period', on });
const updated = await this.time.addCarriedOverMinutes(tx, current.id, allowance);
```

Two gaps. There is no ceiling, so a single approval can add 2^31 minutes to `carried_over_minutes` and make every subsequent overage check pass forever. And the existence check is `if (!current)`, not `if (current.locked)`, while `insertEntry` on the same period refuses outright: `if (period?.locked) throw new ConflictException({ code: 'contract_period_locked' })`. `addCarriedOverMinutes` also writes without the `and version = $n` optimistic check the rest of the time layer uses.

**What it enables.** `tickets:approve-scope` (Administrator and Account Owner) becomes an unbounded budget grant, and it edits the budget of a period that `time:lock-period` has deliberately closed, silently changing the commercial position of a period Finance considers final.

**Fix.** Add a `@Max` proportionate to a period's contracted minutes. Refuse when `current.locked`, or require `time:adjust` in addition for a locked period. Carry the version through `addCarriedOverMinutes`.

---

### 10. Medium. Portal form `answers` is unbounded and echoes one problem per unknown key

**Where.** `backend/src/modules/portal/portal.module.ts:82-84` and `backend/src/domain/portal/form-schema.ts:293-295`, returned at `portal.module.ts:343`.

**What is wrong.** The DTO field carries `@IsOptional() @IsObject()` and nothing else: no `@MaxJsonSize`, though the decorator exists and is used two files away (`src/modules/tickets/tickets.dto.ts:93`). The validator then emits one problem object per unrecognised key:

```ts
const known = new Set(definition.fields.map((field) => field.key));
for (const key of Object.keys(answers))
  if (!known.has(key))
    problems.push({ field: key, code: 'unknown_field', message: `"${key}" is not a field on this form` });
```

and the whole array is thrown as the 400 body.

**What it enables.** A portal user posts a body of many thousands of short keys inside the global 1 MB limit and gets a multi-megabyte 400 back, at the portal rate limit per minute. That is CPU and egress amplification against an authenticated but low-trust principal, and it is the one route where a client contact composes the object shape.

**Fix.** Put `@MaxJsonSize(64 * 1024)` on `answers`, cap the emitted `problems` (the first fifty plus a count), and stop enumerating unknown keys past that cap.

---

### 11. Medium. `narrative_versions` grows without bound on a held run

**Where.** `backend/src/modules/reporting/schedules.module.ts:852-861`.

**What is wrong.** Each `PATCH /v1/reporting/runs/:id/narrative` appends a version and rewrites the whole array:

```ts
await this.repo.setNarrativeVersions(tx, pack.id, [...versions, next], 'edited');
```

The DTO bounds one edit (`@MaxLength(6000)` at `:494` over at most the WSR narrative keys at `:506`), so a single PATCH is tens of kilobytes, but nothing caps how many PATCHes a held run accepts, and `runDetail`, `approve` and `regenerate` all re-read and re-parse the entire array (`narrativeVersions`, `:182-198`).

**What it enables.** One `reports:manage` holder grows a single `jsonb` column toward the 1 GB field limit, at which point the run and its pack become unreadable and unapprovable, and every read of that row is expensive on the way there. The comment at `0035_report_narrative_edit.sql:16-19` records the append-only design without a retention bound.

**Fix.** Keep the newest N versions plus version 1, or refuse a PATCH once the serialised array passes a byte budget, returning a typed 409.

---

### 12. Medium. The change calendar takes an unbounded range and reads tickets per window

**Where.** `backend/src/modules/tickets/change-windows.module.ts:285-291` (the query DTO), `:113-123` (`overlapping`) and `:407-421` (`calendar`).

**What is wrong.** `from` and `to` are `@IsISO8601({ strict: true })` with no span limit, `overlapping` carries no `LIMIT`, and `calendar` issues one `ticketsOf` query per returned window inside a loop. Tenancy itself is sound: the read runs under `uow.run(principal, ...)` and the requested account ids are intersected with `principal.accountIds` at `:403-405`, so no cross-grant read occurs.

**What it enables.** `GET /v1/change-calendar?from=0001-01-01&to=9999-12-31` from a `tickets:view` holder with many grants returns every change window ever recorded and issues one extra query per row. It is a cheap authenticated amplification and it will get worse linearly with the product's age.

**Fix.** Cap the span (366 days is generous for a calendar), add a `LIMIT` to `overlapping`, and load the member tickets for all windows in one `where ticket_group_id = any ($1)` query.

---

### 13. Medium. The change-window override and acknowledgement never reach the outbox

**Where.** `backend/src/modules/tickets/tickets.service.ts:1656-1660` and `:1680-1685` (both call the local `audit(...)` helper), against `:813` where `outboxEvents` is seeded and `:962` where it is drained.

**What is wrong.** `assertChangeWindow` returns audit entries only. The transition's outbox array is built separately from `ticket.transitioned` and never gains an entry for `ticket.change_window_overridden` or `ticket.change_window_acknowledged`, even though both event types were added to `src/contracts/events.ts:100-101`. The actor is on the audit row through `actorOf(principal)` and the reason is bounded (`change_window_reason`, `@MaxLength(1000)`, `tickets.dto.ts:203-208`), so the record itself is well formed; it simply never leaves.

**What it enables.** An override of a production freeze is a thing other systems need to know about: the connector, the notification fan-out and any alerting the client has asked for all read the outbox. Today the only way to learn that someone deployed inside a freeze is to query the audit table directly. Combined with finding 1, an escalation is both unpermissioned and unannounced.

**Fix.** Push `{ type: 'ticket.change_window_overridden', payload: { reason, window, at, freeze } }` (and the acknowledgement equivalent) onto `outboxEvents` where the audit entry is created.

---

### 14. Low. `ALLOWED_TYPES[contentType]` on the email path is not an own-key lookup

**Where.** `backend/src/modules/email/email.service.ts:393`, against `backend/src/modules/attachments/attachments.module.ts:266`.

**What is wrong.** The attachment service reads `Object.hasOwn(ALLOWED_TYPES, contentType) ? ALLOWED_TYPES[contentType] : undefined`, which is the previous review's finding 12 fix. The email path, one line above the new re-encode block, still reads `if (!ALLOWED_TYPES[contentType]?.includes(extension))`. `contentType` is the lowercased declared type of a MIME part, so `toString` or `constructor` returns a function whose `.includes` is undefined and the call throws inside the inbound apply transaction.

**What it enables.** A crafted MIME part fails the inbound apply for that message rather than being rejected with `abuse.upload.rejected`, turning a malformed email into a retry or dead letter instead of a clean refusal. Availability and log noise only; nothing is injectable.

**Fix.** Use the same `Object.hasOwn` guard, and add the email path to whatever unit test pinned the other four sites.

---

### 15. Low. The portal submission path bypasses the 64 kB `form_data` cap

**Where.** `backend/src/modules/tickets/tickets.dto.ts:91-94` (the cap) against `backend/src/modules/portal/portal.module.ts:285` and `:357`.

**What is wrong.** `form_data` on `CreateTicketDto` carries `@IsObject() @MaxJsonSize(64 * 1024)`. The portal builds the same field in code from `mapped.custom` and passes it to `this.tickets.create(...)` directly, so the validation pipe never sees it.

**What it enables.** A portal client stores substantially more `jsonb` per ticket than the internal API permits, bounded only by the global 1 MB body limit. Storage growth, not execution.

**Fix.** Bound `mapped.custom` to the same 64 kB inside `mapSubmission`, or route the portal creation through the same DTO.

---

### 16. Low. Raw exception text is stored on the run row and returned

**Where.** `backend/src/modules/reporting/reporting.service.ts:731` and `:825`, surfaced by `backend/src/modules/reporting/reporting.repository.ts:216`.

**What is wrong.** `finishRun(tx, run.id, null, (error as Error).message.slice(0, 500))` writes the driver's message into `acct.report_runs.error`, and `runs()` returns it with `select r.*` to `GET /v1/accounts/:id/reports` (`tickets:view`) and `GET /v1/reporting/runs`. `HttpExceptionFilter` is careful to return `internal_error` instead of a stack, and this path routes around it.

**What it enables.** Postgres and driver messages carry table names, constraint names and fragments of values, shown to any `tickets:view` holder on the account.

**Fix.** Store a code and log the message.

---

### 17. Low. `attachment_limit_bytes` has no upper bound

**Where.** `backend/src/modules/connectors/connectors.module.ts:86`.

**What is wrong.** `@IsOptional() @IsInt() @Min(0) attachment_limit_bytes?: number`, while `poll_interval_seconds` two lines above is `@Min(10) @Max(86400)`. The value becomes the download cap at `sync.worker.ts:586` and the upload size at the outbound push.

**What it enables.** An `admin:connectors` holder sets ten gigabytes and the worker will try, which is what makes finding 3 worse than it needs to be.

**Fix.** `@Max` matching the platform's attachment ceiling.

---

### 18. Low. `constructor` is a legal form field key

**Where.** `backend/src/domain/portal/form-schema.ts:101` (`const KEY = /^[a-z][a-z0-9_]{0,60}$/`) and `:273` (`const answer = answers[field.key]`).

**What is wrong.** `constructor` and `tostring` match `KEY`, and the answer read is a plain index, so a form with a field keyed `constructor` reads the inherited `Object` function: `isBlank` is false and the kind check always fails, so the form can never be submitted and the message is misleading. `Object.keys(answers)` at `:293` also cannot see an inherited name. This is not prototype pollution: `custom.` targets must match `KEY` (`:184`), `__proto__` cannot pass it, and a JSON `__proto__` key arrives as an own key and is rejected as `unknown_field`.

**Fix.** Reject `Object.prototype` names in `definitionProblems`, and read answers with `Object.hasOwn`.

---

### 19. Low. The `maps_to` allowlist is enforced at save but not at submission

**Where.** `backend/src/domain/portal/form-schema.ts:291-292`, against the allowlist at `:36` (`FORM_TICKET_COLUMNS`) and `:40-53` (`COLUMNS_BY_KIND`), applied only in `definitionProblems`.

**What is wrong.** `validateSubmission` trusts the stored definition and writes `columns[field.maps_to] = answer` with no re-check. It is not exploitable today: `definitionProblems` runs on create, draft edit and publish (`forms.module.ts:264,328,355,393`), the only consumer reads five named keys and never spreads `mapped.columns` (`portal.module.ts:344-355`), and `maps_to` never reaches SQL as an identifier.

**What it enables.** Nothing now. It is one new consumer that spreads `mapped.columns` away from letting a form definition write `state`, `priority` or `account_id`, and the defence lives in a different function from the write.

**Fix.** Re-apply the allowlist inside `validateSubmission` and drop any field whose target is not permitted for its kind.

---

### 20. Low. The polled `sys_id` is interpolated into the ServiceNow encoded query

**Where.** `backend/src/modules/connectors/snow-client.ts:160-161`, `:173` and `:235`.

**What is wrong.** `sysparm_query: \`element_id=${sysId}^ORDERBYsys_created_on\`` and `sysparm_query: \`table_sys_id=${sysId}\`` build ServiceNow's encoded-query grammar by concatenation. `searchParams.set` URL-encodes the result, but `^` and `=` are the grammar's own separators and survive as query structure. `sysId` originates in the polled record (`sync.worker.ts:128,131`).

**What it enables.** A hostile instance returns a `sys_id` containing `^OR...` and rewrites the query XMS sends back to it, for instance returning journal entries belonging to unrelated records which are then applied to the linked ticket. Confined to that instance's own data and that account's binding.

**Fix.** Reject a `sys_id` that does not match `/^[0-9a-f]{32}$/` before it reaches a query, at the point the polled record is parsed.

---

### 21. Low. The journal marker is forgeable and `createJournal` can record the wrong entry

**Where.** `backend/src/domain/sync/rules.ts:47` with `backend/src/modules/connectors/sync.worker.ts:476`, and `backend/src/modules/connectors/snow-client.ts:217-220` with `:160-165`.

**What is wrong.** The loop guard's marker test matches `/\[XMS:[0-9a-f]{8}\]/i` anywhere in the entry body, so a client who types `[XMS:deadbeef]` into a ServiceNow comment has it silently dropped with no run row (`stripJournalMarker` at `rules.ts:51` is anchored; the test is not). Separately, `createJournal` writes the entry and then re-reads with `sysparm_limit: '200'` ordered ascending and takes `.at(-1)`, which on a case with more than 200 journal entries is an old entry and is racy against a concurrent client comment; that wrong `sys_id` is then stored as the out-link, so the inbound dedupe misses our own entry and only the marker stops it being re-applied.

**What it enables.** Neither is a loop: the origin and `source` guards are independent and both hold (see the sound list). It is a silent data-loss path for a client comment and a weakening of the second of three defences against re-applying XMS's own writes.

**Fix.** Anchor the marker test as `stripJournalMarker` already does, and write a run row when an entry is dropped for it. Query the journal with `ORDERBYDESCsys_created_on` filtered to the element with `sysparm_limit=1`.

---

### 22. Low. `RoutingService.replace` has no account check

**Where.** `backend/src/modules/tickets/routing.module.ts:122-137`, against `backend/src/modules/tickets/change-windows.module.ts:328-329`.

**What is wrong.** The service deletes and reinserts `acct.group_routing_rules` for the path's `accountId` without first asserting it is in `principal.accountIds`. The forced policy's `with check` blocks the write, so it fails closed, but it fails as a policy error rather than as the 404 the house rule specifies for a foreign id, and the guarantee rests entirely on the policy rather than on the service and the policy.

**Fix.** Throw `NotFoundException` first, as the ticket-groups service does.

---

### 23. Low. Withdrawing a scope flag is not published and reuses the raise event type

**Where.** `backend/src/modules/tickets/tickets.service.ts:1373-1388`.

**What is wrong.** The raise path writes both an audit entry and an outbox event; the withdraw branch writes only the audit entry, and reuses `ticket.scope_flagged` as its event type, so a consumer cannot tell a raise from a retraction without reading `newValue`.

**Fix.** Emit a distinct `ticket.scope_withdrawn` to both audit and outbox.

---

### 24. Low. The contacts list `limit` never coerces, and the service has no account check

**Where.** `backend/src/modules/portal/contacts.module.ts:76` and `:92-96`.

**What is wrong.** `@IsOptional() @IsInt() limit?: number` on a query DTO under `transformOptions: { enableImplicitConversion: false }` (`src/main.ts:55`) means any `?limit=` value arrives as a string and 400s, so the parameter is unusable and has no `@Min`/`@Max` either. Separately, `list` has no `assertGranted`, unlike `forms.module.ts:410-413` and `csat.module.ts:770-771`; `uow.run` binds row-level security so a cross-account read returns an empty list rather than leaking, which is a behavioural inconsistency rather than a leak.

**Fix.** `@Type(() => Number)` with `@Min(1) @Max(500)`, and the account assertion the sibling services make.

---

### 25. Low. A form option label is unbounded and the field loop continues past `too_many`

**Where.** `backend/src/domain/portal/form-schema.ts:171-172` and `:120-128`.

**What is wrong.** `option.label` is checked only for being a non-empty string, while `label` is capped at 160 (`:153`), `help` at 400 (`:155`) and `option.value` at 120 (`:166`). And the field loop records `too_many` and then still walks every element, so an `admin:config` caller who posts a very large `fields` array gets a proportionally large 400.

**Fix.** Cap `option.label` at 160 and return as soon as the field count is exceeded.

---

### 26. Low. The bucket audit diff omits the taxonomy `code`

**Where.** `backend/src/modules/time/time.module.ts:616` (the assignment) and `:624-625` (the audit values).

**What is wrong.** `code` is written but recorded neither as `oldValue` nor as `newValue`; only `label`, `billable_class` and `status` are. Re-coding a bucket regroups its time across accounts in reporting and leaves no trace.

**Fix.** Add `code` to both sides of the diff.

---

### 27. Low. A dead letter's `instance_id` is returned past the account grant

**Where.** `backend/src/modules/reporting/reporting.repository.ts:382` and `:385`.

**What is wrong.** The query returns `d.payload->>'instance_id' as instance_id` under `where d.resolution = 'open' and (d.account_id is null or d.account_id = any ($1::uuid[]))`. For rows carrying no account the payload's id is returned whatever account owns that connector; only `instance_name` is suppressed, by row-level security on the left join.

**Fix.** Null the id as well when the joined instance row is not visible.

---

## Checked and found sound

These were traced and are correct; a future reviewer should spend time elsewhere.

**Every new account-scoped table has forced row-level security.** `acct.sync_outbound` (`0030:54`) and `acct.group_routing_rules` (`0037:36`) call `sys.apply_account_isolation`; `acct.ticket_groups` calls it and adds a `sys.require_audit` constraint trigger (`0038:45-47`); `acct.ticket_forms` and `acct.ticket_form_versions` write the block by hand (`0040:80-98`) precisely because the portal policies are narrower than the installer's, and both carry `enable` plus `force`, an operator policy with `using` and `with check`, and column-level `grant select` to `xms_portal` with the published and client-visible predicates the specification words. `op.audit_saved_queries` (`0036`) is deliberately operator scope with the reasoning written into the migration, and the owner rules are enforced in SQL, not only in the service.

**The audit search grammar cannot inject.** `translateEvents` (`audit-search.ts:74-142`) takes the column kind through `Object.hasOwn(FIELDS, ...)`, builds the column name only from a key that survived that check, gates the operator on the kind, binds every value with `$n`, escapes LIKE metacharacters, caps conditions at 20 and lists at 50, and gates the new `is_null` and `is_not_null` on an explicit `NULLABLE` set (a `Set`, so prototype keys cannot pass) and on the value being absent rather than ignored. Saved queries run the same function at save time, so a stored condition set can never hold a condition the search would refuse.

**Saved-query ownership is enforced in the query, not in a branch.** `readable` is `where q.id = $1 and (q.owner_user_id = $2 or q.shared)`, `owned` is `where q.id = $1 and q.owner_user_id = $2`, and `update` and `remove` both carry `and owner_user_id = $2` in addition to the prior `owned` read (`saved-queries.repository.ts:45-111`). Sharing is gated on `audit:export` in the service (`saved-queries.service.ts:144-148`). Running a shared query applies the runner's own grant clause, so two readers see different rows, which is the property the design depends on.

**The CSAT token work is right.** `randomBytes(24).toString('base64url')` with only the SHA-256 stored (`csat.ts:145-152`), `timingSafeEqual` behind an equal-length guard (`:155-158`), the link minted with the token in the URL fragment (`csat.module.ts:557-559`), the stored hash absent from every projection that reaches the wire (`SURVEY_COLUMNS` at `:123-137`, and every `select *` stays inside the service), the describe route sharing one gate with answer and returning the identical `not_found` for a missing survey and a wrong token (`:666-682`), the account resolved by the `SECURITY DEFINER` `sys.csat_survey_account` rather than from the body, and both public routes matched by the `public` rate-limit policy with a regression test (`rate-limit.middleware.ts:52`, `test/rate-limit.e2e-spec.ts:79`). The quarterly sweep uses `uow.perAccount`, so each iteration is one transaction bound to one account, and the recipient queries carry `account_id = $1` besides.

**The outbound sync cannot ping-pong.** `decideEnqueue` refuses `origin === 'sync:<thisInstance>'` before every other rule (`rules.ts:159-167`), apply and push both stamp `ctx.origin` (`sync.worker.ts:209,807`), the ticket service propagates that origin onto the outbox row and sets `source = 'sync'`, and `push` re-checks the source at `sync.worker.ts:846`. Three independent gates plus the per-instance link tables.

**Outbound tenancy is per account throughout the connector.** `onOutbox`, claim, deliver and failure settle each open `uow.worker([row.account_id])` (`sync.worker.ts:635,705,725,741`); `perAccount` is used for listing; there is no `uow.operator` or `uow.system` anywhere under `src/modules/connectors/`, and the one unbound query reads `op.accounts`, which is correct.

**The connector's SSRF posture holds.** `SnowClientFactory.forInstance` runs `outboundProblem(instance.base_url, ...)` on every client build including the attachment path, every URL is an absolute path resolved against the guarded base so a poisoned `sys_id` or file name cannot move the host, and `send` and `request` both set `redirect: 'manual'`, an `AbortController` timeout and a capped body read. `table_name` is `@Matches`-constrained and `encodeURIComponent`-ed at each interpolation, which closes the previous review's finding 18 at both ends.

**Field maps cannot write a column they should not.** Inbound apply writes only `short_description`, `description`, `category`, `impact` and `urgency` with length caps (`sync.worker.ts:401-407`), `account_id` comes from the instance row, and state moves only through `allowedTransitions` and `resolveInboundState`. No identity, billing or state column is reachable from a map.

**The flagger cannot decide.** `tickets.service.ts:1417-1418` refuses when `detail.flagged_by === principal.userId`, `out_of_scope` is written only by `flagScope` and `decideScope`, both paths are audited, the decision route requires `tickets:approve-scope`, and both scope routes are `realm: internal` with no `scope` field on `PortalTicketView`.

**The queue's out-of-scope filter is closed at every layer.** `out_of_scope` is in the fixed `FIELDS` map (`conditions.ts:62`), its `enum` kind limits the operators, the values are checked against the closed `OUT_OF_SCOPE` list in the translator (`:191`) and again in the DTO (`@IsIn(OUT_OF_SCOPE, { each: true })`, `tickets.dto.ts:307`), and both the fragment and `tickets.repository.ts:207` are parameterised. The group queue's `is_mine` takes group ids from `op.group_members` server-side and renders `false` on empty membership rather than dropping the filter.

**Non-ticket time inherits every control ticket time has.** `logOnBucket` funnels into the same `insertEntry`, so the period lock, the billing-period lock, the overage decision and the `time:adjust` requirement for another person's time all apply. `code` is closed in the DTO and in the check constraint (`0039:19-20`), and `contract_id` is validated against the account under the binding before insert and is not patchable, so a bucket cannot name another account's contract.

**Change-window enforcement is not bypassable through import or the connector.** `importState` is fenced on `ctx.origin !== 'import'` and the origin is set only server-side, and the sync principal holds no override permission and sends no reason, so a connector apply hits the 409 rather than crossing a freeze. The override reason itself is bounded at 1,000 characters and the actor is recorded. (Finding 1 is a different route, not this gate.)

**Per-account forms are correctly frozen and correctly scoped.** Publish re-validates the definition, the version is scoped by `form_id` under the account binding so `current_version_id` cannot point at another account's version, `updateDraft` carries `published_at is null`, and the database trigger refuses any update or delete on a published row independently of the service (`0040:68-74`). The submission's form version is resolved server-side from the account binding; the client cannot supply one. `visible_when` is pure structural equality with no `eval`, no `Function` and no regex built from input, the controlling field must be an earlier field of a conditionable kind, and fields, options and attachments are all count-capped.

**Contact flags are closed twice.** `@IsIn(CONTACT_FLAGS)` with `@ArrayUnique` in the DTO and `check (flags <@ array[...])` in SQL (`0032:9`), behind `admin:accounts`, with the path account matched against the row and the audit carrying both values.

**The permission catalog and the route snapshot moved together.** All 46 new routes declare a permission or a `@Public` reason and are present in `test/golden/routes.json`; `tickets:override-change-window` was added to the catalog, to the implications and to two seeded roles; the six new report-review, five change-window and scope event types were added to `src/contracts/events.ts`.

**`ArchiveService.summary` is correctly unbound.** It reads `sys.event_archives` on the app pool without a session binding, which is right: that table is created at `0021_archive.sql:7-22` with no account column and no policy, so this is not a repeat of the previous review's finding 1.

**The sign-in security event's new account attribution is an improvement.** `auth.guard.ts:305-311` stamps a portal sign-in with the one account it belongs to and leaves an internal sign-in portfolio-wide, which narrows rather than widens what the dashboards can attribute (and would narrow finding 4's exposure once that clause is added).

**The PDF renderer cannot be injected.** Every client string goes through pdfkit's own text path, which escapes the PDF string metacharacters; ticket titles are truncated at the call site and narrative text is DTO-capped. No raw PDF syntax is reachable from client content.

**"Regenerate keeps the numbers" does.** `schedules.module.ts:921-929` passes the frozen `pack.measures` and `pack.notable` and `reporting.service.ts:644-658` renders from them with no recomputation, so a regenerate after a narrative edit cannot silently move a figure.

---

## Open questions for the architecture owner

1. **Should a change window's schedule be editable by the people it constrains?** Finding 1 is only a bug if the answer is no. If a window is meant to be operational data that any `tickets:work` holder curates, then TM-18's freeze is advisory and `tickets:override-change-window` should be retired rather than fixed.
2. **Is review before send meant to require two people?** Finding 5 turns on whether DR-05's "review" is a second pair of eyes or a deliberate pause. The permission catalog currently makes it the latter.
3. **What should an emailed delivery link actually be?** Finding 6's fourteen days cannot be a presigned URL in AWS. A revocable token row is the obvious answer, but it means a redemption route and a rate-limit policy, so it is a design decision rather than a patch.
4. **Where is the image decode budget set?** Finding 2 needs a number the specification does not give. A megapixel budget belongs beside `MAX_IMAGE_EDGE` with the reasoning written down, and the email path needs a per-attachment byte cap that today only the browser path has.
5. **Does the connector trust boundary assume a well-behaved instance?** Findings 3, 7, 20 and 21 all read the same way: the code is careful about what XMS sends and comparatively trusting about what comes back. If a client's ServiceNow is inside the trust boundary that is defensible and should be written down; if it is not, the polled payload needs the same treatment an inbound webhook gets.
6. **Is CI any closer?** The previous review's finding 3 is still open, and every control above that has a test would be caught by one. This review found nothing that a green suite would have caught on its own, which is the argument for the suite, not against it.
