"""The single rule that decides which supplier price applies (ADR-002 §Selection).

Order: valid on the tariff date -> approved -> conditions -> priority -> newest version of the
same tariff -> most specific. Anything left with more than one rule is a conflict, never "the
cheapest" or "the first".
"""
from .model import Match, Result, Status


def match(rule, shipment):
    """Return (Match, missing input names) for the rule conditions against the shipment inputs."""
    missing = set()
    for name, accepted in rule.conditions.items():
        value = shipment.get(name)
        if value in (None, False, ""):
            missing.add(name)
        elif value not in accepted:
            return Match.NO, set()
    return (Match.UNKNOWN, missing) if missing else (Match.YES, set())


def _most_specific(rules):
    """Keep priority winners, the newest version of each tariff, then drop dominated rules."""
    top = min(r.priority for r in rules)
    rules = [r for r in rules if r.priority == top]
    newest = {}
    for r in rules:
        newest[r.lineage_id] = max(newest.get(r.lineage_id, 0), r.version)
    rules = [r for r in rules if r.version == newest[r.lineage_id]]
    keys = {r.id: set(r.conditions) for r in rules}
    return [r for r in rules if not any(keys[o.id] > keys[r.id] for o in rules)]


def select(rules, shipment, day):
    """Pick the rule for one service + charge basis. `rules` are already filtered by both."""
    if not rules:
        return Result(Status.NO_TARIFF, steps=[("no_rule", {})])
    if day is None:
        return Result(Status.MISSING_INPUT, missing=["tariff_date"])
    dated = [r for r in rules if r.valid_on(day)]
    if not dated:
        return Result(Status.NO_TARIFF, steps=[("no_rule_on_date", {"date": day})])

    matched, missing = [], set()
    for rule in (r for r in dated if r.approved):
        outcome, needs = match(rule, shipment)
        if outcome is Match.UNKNOWN:
            missing |= needs
        elif outcome is Match.YES:
            matched.append(rule)
    if missing:
        return Result(Status.MISSING_INPUT, missing=sorted(missing))
    if matched:
        best = _most_specific(matched)
        if len(best) > 1:
            return Result(Status.CONFLICT, candidates=best)
        return Result(Status.OK, rule=best[0])

    pending = [r for r in dated if not r.approved and match(r, shipment)[0] is Match.YES]
    if pending:
        return Result(Status.PENDING_APPROVAL, candidates=pending)
    return Result(Status.NO_TARIFF, steps=[("no_match", {})])
