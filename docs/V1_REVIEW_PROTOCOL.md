<sub>🇬🇧 <b>English</b> · 🇫🇷 <a href="V1_REVIEW_PROTOCOL.fr.md">Français</a> · <a href="../README.md">← README</a></sub>

# Review protocol — NeoMundi Evidence V1

**Monday 9 November 2026.** Product sheet:
[`V1_CANDIDATE.md`](V1_CANDIDATE.md).

---

## What we ask of you, and what we do not

**We ask you to try to catch us out.** A "looks good" teaches us nothing; a
counter-example is worth a week of development.

**We are not asking you to validate.** None of you has to sign anything, and
the candidate is not waiting for your approval — it is waiting for your
**objections**.

---

## Before you start: what is synthetic

> The whole demonstration package is **fabricated**. The signing key was an
> **ephemeral demonstration key**, **destroyed**. The external receipt is
> **invented**.
>
> One thing only is real: the **timestamp proof**, obtained from the four
> public calendars. It is **`PENDING`**, and **that attests no date**.

**None of the five functions has been exercised on a real pilot package.**
That is this review's dominant limit, and it is where your objections will be
most useful.

---

## Preparation — five minutes

```sh
git clone https://github.com/neomundi-io/neomundi-evidence-public
cd neomundi-evidence-public/examples/dossier-v1
```

Python 3.11 or later. **No dependency is needed** for the 21 integrity
controls. For the two signature lines: `pip install cryptography` — and if you
do not install it, the tool returns `NOT TESTED`, never `PASS`.

The guided demonstration: `sh demo_v1_5min.sh` from the root.

The auditor's guide, with the five commands and expected results:
[`examples/dossier-v1/README.md`](../examples/dossier-v1/README.md).

---

## Proposed scopes

One scope per reviewer, chosen so nobody reviews what another reviews — and
nobody reviews their own work.

### Dennis — reconciliation, and the adapter designed for your package

You are the only one who can say whether the adapter will **actually** read
your package.

| To exercise | Where |
|---|---|
| Does the importer collect the fields of a receipt of **your** shape? | `adapters/receipt_import.py` |
| Is the correspondence table **fillable** by someone who knows both sides? | `examples/dossier-v1/map-*.json` |
| Do the five statuses cover your cases, or is one missing? | `docs/RECONCILIATION.md` |
| **Does the `NOT COMPARABLE` distinction hold?** | the heart of the matter |

**The question that matters.** We refuse to conclude that `0.3863` against
`0.594` is a computation divergence, because the measurement version, the
coverage and the definition are missing on each side. **Does that refusal seem
right to you, or excessive?** If you can supply those four elements, the
comparison becomes possible — and that is the only route.

> `RECONCILIATION.md` and the receipt itself **have not reached us**. The
> adapter is therefore designed on the described shape, not on your package.

### Sergei — operations, and the stopping rule

You have run real campaigns. You know what breaks.

| To exercise | Where |
|---|---|
| Does a package produced by a real campaign pass the 21 controls? | `verify.py` |
| Are the 2 structural `NOT TESTED` acceptable for a pilot? | chaining, origin |
| Does `--strict` suit an automated pipeline? | `docs/INTEGRATION.md` |
| **Is the operational cost of one attestation per package** sustainable? | `sign.py` |

**The question that matters.** Signing a package requires a private key on an
operator's workstation, and custody discipline. **Is that compatible with how
your campaigns actually run?** If not, that is a structural objection and we
would rather hear it now.

### Pradeep — the reasoning, and the premises

Your previous contribution was about a premise, not a bug. That is exactly the
reading we need here.

| To exercise | Where |
|---|---|
| **Is the level derivation** honest, or is there a path to a false `cryptographically_attested`? | `verify_attestation.py` |
| Does the canonicalisation profile's equivalence to RFC 8785 **hold over its domain**? | `canonical.py` |
| `rotated` versus `compromised`: is the retroactivity correctly reasoned? | `docs/ATTESTATION.md` |
| Is a `NOT TESTED` line ever used to **mask** a failure? | everywhere |

**The question that matters.** We assert that a comparability boundary must
not bite on a digest. **Is that sound reasoning, or a convenience we granted
ourselves?**

### Patrick — the position of an auditor arriving with no context

*We have no record of previous work by you on this product. That is precisely
the reason for this scope: you are the only one who can judge what the package
is worth to someone with no context.*

| To exercise | Where |
|---|---|
| Is the auditor's guide sufficient **on its own**, without asking us anything? | `examples/dossier-v1/README.md` |
| Do the expected results match what you obtain? | the five commands |
| Does anything **read** as a stronger guarantee than it is? | all the output |
| **Do the four attempts to catch us out** succeed? | the guide's dedicated section |

**The question that matters.** An evidence package that needs its author to be
understood is not an evidence package. **Do you get there alone?**

### Daniel — coherence with the measurement, and the signals

| To exercise | Where |
|---|---|
| Does an exported package faithfully reflect what the measurement produced? | `verify.py`, cardinality and nullity controls |
| Does a `null` signal stay **unmeasured**, never zero? | the `coherence des signaux nuls` control |
| Are the comparability boundaries the right ones? | `measurement_version`, coverage |
| Does the vocabulary say what the signals **actually measure**? | `docs/BINDING.md`, terminology section |

**The question that matters.** We write that `stability_score` is an
**aggregate** and not a signal, and we refuse to compare it with a third
party's score without knowing the definitions. **Is that accurate, and
sufficient?**

---

## The eight suites, to re-run if you wish

```sh
python verify.py <archive> --corpus <corpus>            # 19 PASS, 0 FAIL, 2 NOT TESTED
python tests/test_falsification.py <archive> <corpus>   # 10/10
python tests/test_adversarial.py <archive> <corpus>     # 13 detected, 2 limits
python tests/test_binding.py <archive> examples/binding # 0 problems
python tests/test_attestation.py <archive> <corpus>     # 25/25
python tests/test_timestamp.py                          # 21/21, offline
python tests/test_reconciliation.py                     # 24/24, self-contained
python tests/test_timestamp_network.py                  # 3/3, NETWORK, never in CI
```

CI runs the first seven on **Python 3.11, 3.12 and 3.13** on every pull
request. The eighth never runs in CI: it depends on four third-party servers,
and a CI that is red without an internal cause teaches people to ignore red.

---

## How to send us an objection

**A reproducible counter-example beats an opinion.** If you find a path to a
false verdict, the most useful form is:

1. the file or command that produces it;
2. what the tool answered;
3. what it should have answered, in your view.

If your objection is about a **premise** rather than a behaviour — such as
"you should not call that a guarantee" — say it in that form. Those are the
most useful objections, and the hardest to find alone.

---

## What the review cannot establish

It covers a **synthetic** package and a **demonstration** key. It will not say
whether the product holds on a real pilot package — nobody has submitted one
yet. That is condition **B-3** of the product sheet, and it remains
**blocking** for a commercial offer.
