## Service suffix instead of a domain name

### Smell

Any class named `*Service` — `CarService`, `UserService`, `EffectiveFeaturesService`.

**A service is not an object.** An object has a name in the domain, state it is responsible for,
and behaviour that protects it. A service is a place to keep procedures that operate on somebody
else's data — so naming a class `Service` announces, in the identifier itself, that it models
nothing. The suffix names the layer the class sits in, and a reader learns only that somebody had
behaviour and nowhere obvious to put it.

The naming is not merely uninformative, it is *attractive*. `CarService` answers the question
"where does this new car-related function go?" for every car-related function anyone writes next.
The class has no thesis to violate, so nothing ever looks out of place in it, and it grows:

- **Maintenance** — the file becomes a table of contents for a subsystem rather than a unit with
  one responsibility. Reading it tells you nothing about which parts relate.
- **Testing** — a class with eight unrelated methods has the union of their collaborators in its
  constructor, so every test builds the whole world to exercise one branch.
- **Merge conflicts** — unrelated work lands in the same file, so parallel changes collide over
  code that was never related.

### Trigger

The name. Reading `*Service` on a class is the whole trigger — there is no further test to apply
and no version of the name that survives review.

These are not extra conditions, they are how far it has already gone:

- You are adding a method to an existing `*Service` and the honest reason is "it's about the same
  noun", not "it belongs with what is already here".
- The constructor has grown a collaborator that only one of its methods uses.
- You cannot say in one phrase what the class answers or does — the class is now several things,
  and the rename is a split.

### Refactoring

1. Say out loud what the class actually does, in domain words: *"it answers which features an
   account effectively holds"*, *"it charges a subscription"*, *"it decides whether a booking
   overlaps"*.
2. Name it that. The phrase usually contains the name:
   - **answers a question about state** → the read-side vocabulary: `*Query`, `*Finder`,
     `*Reader`, `*Report` (see *Read-side port named "Repository"*).
   - **performs one business action** → a use case named for the action: `ChargeSubscription`,
     `CancelBooking`.
   - **holds a rule or a calculation** → the rule: `OverlapPolicy`, `UsageQuota`,
     `TrialEligibility`.
   - **adapts an external system** → the system and its role: `PostgresApiTokenStore`,
     `HubspotContactSync`.
3. If no single phrase fits because the class does several unrelated things, that is the answer:
   **split it**, one class per phrase, and name each. The impossibility of naming is the smell
   reporting itself.
4. Rename the file, the bean name or qualifier, the fakes and the test doubles to match.
5. Leave the method names alone unless they carried the same problem — a rename is behaviour
   preserving and should read as one in the diff.

### Structure after refactoring

- Each class name states a responsibility a reader can hold in their head, so a method that does
  not serve it is visibly out of place — the class resists growth instead of inviting it.
- Constructor dependencies shrink to what that one responsibility needs.
- Two people adding two features touch two files.

### Tests

- A pure rename: the scenarios do not change, only the symbols and file names.
- If step 3 applied and the class was split, the tests split with it, and each new spec builds
  only the collaborators its class actually has. That reduction is the evidence the split was
  real rather than cosmetic.

### There is no framework exemption

Spring is commonly cited as requiring this name. It does not. Spring requires a **stereotype
annotation** — `@Component`, or its alias `@Service` — or a `@Bean` method, and it never reads the
class name. `@Service` is `@Component` under another name; annotating a class with it does not
oblige the class to be called one. `*Service` comes from example code, and an example is not a
constraint.

Nor is "it only wires a client" an exemption. A class that hands out a configured Postgres client
is a **connection pool**, or a **client factory**, or the store it fronts — each of those names
says what the reader gets. `DbService` says only that it is a bean, which the annotation
already said.

An existing codebase full of `*Service` classes is a backlog, not a counter-example. Rename them
as you touch them, in their own commit, ahead of the change you came to make. Nothing here asks
for a big-bang rename, and nothing here treats the ones already there as correct.

### Example

**Kotlin — a feature-flag read path**

A class introduced to answer one question was named for its layer:

```kotlin
@Service
class EffectiveFeaturesService {
    fun featuresFor(sources: FeatureSources): Set<FeatureName> { ... }
}
```

It composes an account's own grants with the features its plan maps, then applies the
per-feature toggle state to each. That is a question about state, and the codebase's read side already had the word
for it — `PlanLimitsQuery`, `BillingHistoryQuery`, `ApiTokensQuery`:

```kotlin
@Component
class EffectiveFeaturesQuery {
    fun featuresFor(sources: FeatureSources): Set<FeatureName> { ... }
}
```

No behaviour changed. What changed is that the next person with a feature-flag-ish function now
has to ask where it belongs, instead of finding a class whose name already said "anything about
features goes here".

See also *Anemic domain model → rich model*, where business rules that ended up in a `*Service`
are moved back onto the entities that own them.
