"""Mappings between the stimulus's (position, bias) and the experimental
design factors (pronoun, order, antecedent, condition code, congruency).

Used by export & analysis services so the naming stays consistent.

Position layout (matches admin entry rules):
  pos 1: 'X Y-... V-DIğInde, [eylem]'           → null pronoun, forward
  pos 2: 'X Y-... V-DIğInde, o [eylem]'         → overt 'o',  forward
  pos 3: 'X Y-... V-DIğInde, kendisi [eylem]'   → kendisi,    forward
  pos 4: '[Eylem]-IrKEN, X Y-... V-DI'          → null,       cataphora (backward)
  pos 5: 'O [eylem]-IrKEN, X Y-... V-DI'        → overt 'o',  cataphora
  pos 6: 'Kendisi [eylem]-IrKEN, X Y-... V-DI'  → kendisi,    cataphora
"""

POSITION_LABELS = {
    1: "null-forward",
    2: "overt-forward",
    3: "kendisi-forward",
    4: "null-backward",
    5: "overt-backward",
    6: "kendisi-backward",
}

POSITION_TO_PRONOUN = {1: "pro", 2: "o", 3: "kendisi", 4: "pro", 5: "o", 6: "kendisi"}
POSITION_TO_ORDER = {
    1: "forward", 2: "forward", 3: "forward",
    4: "cataphora", 5: "cataphora", 6: "cataphora",
}

# 12-cell design code matching the analysis spec:
#   C1  pro/forward/subject     C2  pro/forward/object
#   C3  pro/cataphora/subject   C4  pro/cataphora/object
#   C5  o/forward/subject       C6  o/forward/object
#   C7  o/cataphora/subject     C8  o/cataphora/object
#   C9  kendisi/forward/subject C10 kendisi/forward/object
#   C11 kendisi/cataphora/subj  C12 kendisi/cataphora/object
CONDITION_CODE = {
    ("pro",     "forward",   "subject"): "C1",
    ("pro",     "forward",   "object"):  "C2",
    ("pro",     "cataphora", "subject"): "C3",
    ("pro",     "cataphora", "object"):  "C4",
    ("o",       "forward",   "subject"): "C5",
    ("o",       "forward",   "object"):  "C6",
    ("o",       "cataphora", "subject"): "C7",
    ("o",       "cataphora", "object"):  "C8",
    ("kendisi", "forward",   "subject"): "C9",
    ("kendisi", "forward",   "object"):  "C10",
    ("kendisi", "cataphora", "subject"): "C11",
    ("kendisi", "cataphora", "object"):  "C12",
}


def design_factors(position, bias):
    """Returns dict {pronoun, order, antecedent, condition, congruency, position_label}
    for a critical trial. Returns all-None dict for fillers (position/bias missing)."""
    if position is None or bias is None:
        return {
            "pronoun": None,
            "order": None,
            "antecedent": None,
            "condition": None,
            "congruency": None,
            "position_label": None,
        }
    pronoun = POSITION_TO_PRONOUN.get(position)
    order = POSITION_TO_ORDER.get(position)
    antecedent = bias  # 'subject' | 'object'
    cond = CONDITION_CODE.get((pronoun, order, antecedent))
    # Congruent: pro/kendisi prefer the subject; overt 'o' prefers the object.
    is_congruent = (
        (pronoun in ("pro", "kendisi") and antecedent == "subject")
        or (pronoun == "o" and antecedent == "object")
    )
    return {
        "pronoun": pronoun,
        "order": order,
        "antecedent": antecedent,
        "condition": cond,
        "congruency": "congruent" if is_congruent else "incongruent",
        "position_label": POSITION_LABELS.get(position),
    }
