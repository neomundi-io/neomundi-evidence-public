<sub>🇬🇧 <b>English</b> · 🇫🇷 <a href="FUTURE_SITE.fr.md">Français</a> · <a href="../README.md">← README</a></sub>

# Product site — planned architecture

Planned address: `evidence.neomundi.org`

**Nothing is built, nothing is deployed, and the name does not resolve** —
checked on 5 November 2026. It is deliberately not linked anywhere in this
repository: a product about verifiability does not ship dead links.

This document fixes the architecture so that today's choices do not close it
off. It does not describe committed work.

---

## The three spaces

### Product — what it is, and what it is not

The value proposition and the use cases, with **the limits at the same level as
the capabilities**. That is a design constraint, not modesty: a page that
announces functions and then hides the limits at the bottom would contradict
the product it sells.

Expected content: the problem, the functions actually available, the two checks
our verifier does not perform, and what verification does not detect.

### Demo — exploring a file built on GROUNDED-S1

A **synthetic** campaign and its evidence file, browsable with nothing to
install.

Two rules that follow from the nature of the corpus:

- the `synthetic` regime must be **permanently visible**, not in a footnote:
  these answers observe no real operator;
- **no pilot data and no real-operator corpus** ever appears there. The private
  corpus is excluded from every public space, and that exclusion is not
  renegotiable for the convenience of a demonstration.

### Verify — checking an archive without us

The space that decides whether the other two are credible.

**It must run in the browser, without calling our services.** A hosted verifier
that uploaded the archive to us would prove nothing: it would ask people to
trust us in order to establish that they need not trust us.

Technical consequences to respect on the day it is built:

| | |
|---|---|
| computation happens **client-side** | the archive never leaves the visitor's machine |
| no upload to our servers | neither to verify, nor to "improve the service" |
| the logic stays that of `verify.py` | **one** implementation of the checks, otherwise two versions will diverge and neither will be authoritative |
| the `NOT TESTED` results stay visible | a check that was not performed is stated; it does not vanish from the interface |

---

## What this architecture rules out by construction

- **No collection.** A verification space that logged the archives it checked
  would become exactly what the product claims to avoid.
- **No binary verdict.** No "✓ Archive authentic": an archive can be internally
  perfect and false. The interface returns the three states, like the verifier.
- **No claim of certification**, completeness or legal value.

---

## What must exist before anything is built

Two conditions, and neither is technical:

1. **a reviewer who says they need it.** Today `verify.py` is a single readable
   file that runs with nothing installed: the *Verify* space answers a
   convenience, not yet an observed gap;
2. **a decision on publishing the repository.** While it is private, the
   verifier travels with the archive. A public space implies publishing the
   code — which is desirable for credibility, and must be decided.

> An honest priority: *Verify* is the only one of the three that would bring a
> new property. *Product* and *Demo* are presentation, and presentation is
> missed by nobody while the product has no buyer.
