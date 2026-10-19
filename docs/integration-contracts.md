# Alchemist integration contracts

Custom Guild: Alchemist Lab is independently loadable. The contracts below are
optional capabilities for other Mod Manager packages; they do not make those
packages dependencies of the Alchemist Lab.

## Kingdom Plague Cleanse

The package declares this Manager v3 feature:

```json
{
  "type": "stock.typed-boolean-provider.v1",
  "feature_key": "kingdom_plague_cleanse_provider",
  "attribute": "KingdomPlagueCleanse",
  "parameter_types": ["agent", "integer", "boolean"],
  "callback_symbol": "Alchemist_Request_Kingdom_Plague_Cleanse"
}
```

The GPL callback has this signature:

```text
Alchemist_Request_Kingdom_Plague_Cleanse(agent Requester, integer Amount, boolean Commit) -> boolean
```

`Requester` must be the living building that owns the consumer action and must
belong to the same player as a true Palace. `Amount` must be exactly `5`.

When `Commit` is false, the callback performs a side-effect-free eligibility
quote. When `Commit` is true, it repeats every check and, on success, consumes
five stored Reagents from one owned, fully completed level-3 Alchemy Lab and
then charges 5,000 kingdom gold. The callback does not yield between those two
debits.

Eligibility additionally requires the kingdom's once-only Arcane Infusion to
have been completed. The provider owns eligibility and payment only. It does
not enumerate plagued units, remove plague effectors, show a consumer command,
or reference consumer-package symbols.

Consumers must treat the provider as optional. If no selected package provides
the exact attribute and parameter signature, the consumer must leave its
dependent action unavailable and perform no debit. Selecting the Alchemist Lab
without a consumer has no gameplay effect beyond the Lab's own features.
