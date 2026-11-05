<sub>🇬🇧 <a href="ADR-001-ANCHORING.md">English</a> · 🇫🇷 <b>Français</b> · <a href="../README.fr.md">← README</a></sub>

# ADR-001 — Ancrage tiers, et les quatre prétentions temporelles

**Statut : ACCEPTÉE, 6 novembre 2026.** Condition **D-8** de
[`V1_CANDIDATE.fr.md`](V1_CANDIDATE.fr.md).

---

## Le problème

Quatre choses différentes s'appellent « horodaté », et elles ne sont pas des
degrés l'une de l'autre. Trois d'entre elles sont couramment présentées comme
la quatrième, et c'est ainsi qu'un dossier finit par revendiquer une date que
personne n'a établie.

Cette ADR fixe le vocabulaire, dit quelles prétentions V1 peut émettre, et
tranche si l'ancrage tiers vaut son coût d'exploitation.

---

## Les quatre prétentions, la plus forte en dernier

| nº | Prétention | Ce qui l'établit | Ce qu'elle vaut seule |
|---|---|---|---|
| 1 | **Date déclarée** | quelqu'un l'a écrite dans un champ | **rien** — celui qui l'écrit la choisit |
| 2 | **Signature cryptographique** | une clé a vérifié sur le contenu | l'*engagement*, **pas la date** |
| 3 | **Ancrage OpenTimestamps confirmé** | l'empreinte est engagée dans un bloc Bitcoin miné | une **borne supérieure** : elle existait au plus tard à ce bloc |
| 4 | **Horodatage qualifié eIDAS** | un prestataire de services de confiance qualifié l'émet | une présomption légale, dans l'UE |

### Pourquoi (1) ne vaut rien

`attested_at_declared` est écrit par le signataire. Une signature dessus
prouve que le signataire s'est engagé sur cette valeur — pas que la valeur est
vraie. Un détenteur de la clé peut écrire n'importe quelle date, passée ou
future, et la signature vérifiera. **Nous ne qualifions jamais une date
déclarée d'horodatage indépendant.**

### Pourquoi (2) ne porte pas de date

C'est la confusion la plus importante, parce qu'une signature vérifiée *a
l'air* d'un acte daté. Elle ne l'est pas. La signature lie une clé à un
contenu ; la date à l'intérieur du contenu est la prétention (1). Rien dans la
cryptographie n'observe une horloge.

### Ce que (3) établit réellement, et ce qu'elle n'établit pas

Une preuve OpenTimestamps dont l'attestation est un **en-tête de bloc
Bitcoin** dit : cette empreinte existait **au plus tard** à ce bloc. C'est une
borne supérieure réelle et indépendante, obtenue d'une partie qui n'a aucun
intérêt dans nos dossiers.

Elle ne dit **pas** quand l'empreinte a été créée — seulement qu'elle n'est
pas plus récente que le bloc. Et convertir une hauteur de bloc en date
d'horloge demande l'**en-tête de bloc**, que ce dépôt n'a pas et n'ira pas
chercher. Cette conversion est déléguée au client officiel : `ots verify`.

La ligne de notre outil est donc, et reste :

```
[PASS      ] attestation confirmee par la chaine - 2 attestation(s) Bitcoin, bloc(s) 974714, 974715
[NOT TESTED] temps verifie par un tiers - hors de portee de cet outil
```

**Une hauteur de bloc n'est pas une date.** Nous rapportons la hauteur que
nous lisons, et refusons de nommer l'heure.

### Pourquoi (4) n'est pas revendiquée, et ne le sera pas

OpenTimestamps n'est pas un prestataire de services de confiance qualifié au
sens d'eIDAS. Aucune configuration ne l'y transforme. La ligne `NOT TESTED`
sur la qualification eIDAS est **permanente** — ce n'est pas un manque en
attente de travail — et elle existe pour que personne ne lise la prétention
(3) comme la (4).

---

## L'état `PENDING`, le plus facile à mal lire

Une preuve fraîchement soumise porte des attestations `PENDING`. Un
calendrier s'est engagé à inclure l'empreinte dans une future transaction
Bitcoin.

> **Une preuve `PENDING` n'atteste aucune date, d'aucune sorte.**

Elle est plus faible que la prétention (3) et n'apprend rien que la (1)
n'apprenait déjà. Elle atteste qu'une soumission a eu lieu, et c'est tout.

C'est observable dans le dépôt à l'instant, et c'est voulu :

| Preuve | État | `verify --strict` |
|---|---|---|
| `examples/timestamp/…jws.confirmed.ots` | 2 attestations Bitcoin, blocs 974714 / 974715 | **0** |
| `examples/dossier-v1/…jws.ots` | 4 `PENDING`, 0 Bitcoin | **2** |

Les deux cohabitent délibérément, pour que le cycle de vie soit visible aux
deux bouts — et pour qu'un consommateur automatisé ne puisse pas être trompé
par un nom de fichier. La seconde preuve ne porte aucun nom particulier, et
`--strict` la refuse sur son contenu.

---

## Décision

**V1 adopte OpenTimestamps comme ancre tierce optionnelle, et ne revendique
que ce que les octets d'une preuve établissent.**

Concrètement :

1. **La prétention (1) n'est jamais appelée un horodatage.**
   `attested_at_declared` est toujours rendu comme déclaré, par nous.
2. **La prétention (2) n'est jamais appelée une date.** La ligne
   d'attestation dit qu'une partie s'est engagée ; une ligne séparée dit ce
   qu'on sait du temps.
3. **La prétention (3) est rapportée comme la hauteur de bloc lue dans la
   preuve**, jamais convertie en heure. La vérification du temps est
   déléguée, nommément, à `ots verify`.
4. **La prétention (4) n'est jamais émise.** La ligne eIDAS est un
   `NOT TESTED` permanent.
5. **L'ancrage reste optionnel.** Aucun niveau de garantie n'en dépend : un
   dossier sans preuve atteint `cryptographically_attested` exactement comme
   un dossier avec preuve confirmée. L'ancrage ajoute une borne supérieure
   indépendante sur le temps ; il n'ajoute pas d'engagement.
6. **Seules des empreintes quittent la machine.** La soumission envoie une
   empreinte de 32 octets à quatre calendriers publics — jamais une archive,
   jamais les données d'un pilote. C'est ce qui rend l'ancre acceptable.

### Le coût d'exploitation, qui est le vrai contenu de D-8

| Coût | Réalité | Conséquence pour une offre |
|---|---|---|
| Argent | **aucun** — pas de compte, pas de frais | rien à tarifer |
| Réseau | une soumission vers quatre calendriers publics | un opérateur isolé **ne peut pas ancrer** ; le dire plutôt que le promettre |
| Latence | des heures entre la soumission et une attestation Bitcoin | **« horodaté » n'est pas disponible au moment du scellement** |
| Une seconde étape | `upgrade`, plus tard, qui écrit une **nouvelle** preuve | une étape d'exploitation que quelqu'un doit réellement lancer |
| Croissance | la preuve est passée de 786 à 2 717 octets à la confirmation | négligeable |

C'est la latence qui mord sur un contrat. Un dossier scellé et remis
aussitôt porte une preuve `PENDING`, qui n'atteste rien. **Une offre peut
donc promettre un ancrage, jamais un ancrage « à la livraison ».** La
formulation honnête est qu'une borne supérieure indépendante devient
disponible dans les heures qui suivent le scellement, par une étape que
l'opérateur lance.

### Politique V1 minimale

| | |
|---|---|
| Ancrer au scellement | **oui**, soumettre — cela ne coûte rien et lance le compte |
| Livrer avec une preuve `PENDING` | **oui**, en la disant n'attestant aucune date |
| Promettre un ancrage confirmé à la livraison | **non** |
| Relancer `upgrade` | l'étape de l'opérateur ; elle n'écrase jamais la preuve antérieure |
| Conserver la preuve antérieure | **toujours** — c'est une pièce à part entière, et `upgraded_from` chaîne les deux |
| Exigé pour un niveau de garantie | **jamais** |

---

## Conséquences

- `verify.py`, `verify_attestation.py` et `timestamp.py` conservent leurs
  lignes `NOT TESTED` permanentes sur le temps tiers et eIDAS. Ces lignes
  *sont* la décision, écrite dans la sortie.
- `upgrade` écrit une preuve neuve et un descripteur neuf, et laisse le
  prédécesseur octet pour octet. Vérifié par le cas 27 de la suite
  d'horodatage : l'upgrade ne doit pas changer l'objet engagé.
- Un document d'offre qui écrit « horodaté » sans nommer laquelle des quatre
  prétentions est visée est un défaut, et doit être traité comme tel.

## Solutions écartées

| Solution | Pourquoi non |
|---|---|
| Lire nous-mêmes l'en-tête de bloc Bitcoin | demande un nœud ou un explorateur de confiance. Un « explorateur de confiance » est une dépendance de confiance qu'il faudrait divulguer, et il remplacerait une délégation propre par une délégation cachée. |
| Exiger un ancrage confirmé pour `cryptographically_attested` | le niveau porte sur l'engagement, pas sur le temps. Les coupler rendrait le niveau inatteignable pendant des heures après le scellement, sans rien ajouter à ce qu'il affirme. |
| Acheter un horodatage qualifié eIDAS | défendable plus tard, et une vraie option pour un contrat dans l'UE. Hors V1 : cela introduit un prestataire payant, un coût par dossier et une question de juridiction, dont aucun n'est tranché. |
| Abandonner l'ancrage | il est gratuit, n'envoie qu'une empreinte, et c'est la seule borne indépendante sur le temps que nous puissions obtenir. L'abandonner laisserait la prétention (1) comme seule prétention temporelle — et elle ne vaut rien. |
