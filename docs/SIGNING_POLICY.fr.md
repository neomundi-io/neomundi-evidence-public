<sub>🇬🇧 <a href="SIGNING_POLICY.md">English</a> · 🇫🇷 <b>Français</b> · <a href="../README.fr.md">← README</a></sub>

# Politique de signature — identité, mandat, et garde des clés

**6 novembre 2026.** Conditions **B-1** et **B-2** de
[`V1_CANDIDATE.fr.md`](V1_CANDIDATE.fr.md).

Les deux ne font qu'un document, parce qu'une politique de clé sans politique
d'identité ne dit rien : une clé prouve que *quelque chose* la détenait,
jamais que quelqu'un avait qualité pour engager.

> **Rien dans ce document n'est en vigueur.** Il énonce ce qu'il faut
> décider, par qui, et quelle preuve ferme chaque point. Aucune clé de
> production n'existe, et aucune ne peut être générée avant que la partie A
> soit tranchée.

---

## Partie A — B-1 : qui s'engage, et sur quoi

### Ce qu'une attestation affirme réellement

Une attestation Ed25519 vérifiée établit exactement une chose :

> Le détenteur de la clé `kid` s'est engagé sur l'empreinte de ce dossier, et
> a déclaré une date de signature.

Tout le reste, qu'on y lira, n'y est pas. Elle n'affirme en particulier **pas**
que la mesure est juste, que l'exécution a eu lieu, que la date déclarée est
vraie, ni que le détenteur avait qualité pour engager qui que ce soit. C'est
ce dernier manque que la partie A existe pour combler — et **aucune ligne de
code ne le comblera.**

### Les cinq rôles, qu'il ne faut jamais confondre

Le magasin de confiance les sépare déjà. La politique dit pourquoi.

| Rôle | Qui, aujourd'hui | Sur quoi il s'engage |
|---|---|---|
| **Entité engageante** | `nm-recherche` — **non tranché** | le contenu de l'énoncé |
| **Représentant habilité** | **non consigné** | que l'entité est liée |
| **Détenteur de la clé** | `nm-operator-poste` | rien ; il détient le secret |
| **Opérateur technique** | `nm-operator-poste` | rien ; il lance la commande |
| **Auteur de la mesure** | `nm-station` | la mesure, pas l'engagement |

**Mesurer n'est pas s'engager, et détenir une clé n'est pas avoir qualité pour
s'en servir.** Confondre le détenteur avec l'entité engageante est l'erreur la
plus tentante ici : elle ferait passer le secret d'un poste de travail pour la
signature d'une organisation.

### La décision à prendre

Trois entités juridiques existent, et elles ne sont pas interchangeables.

| Candidate | Ce que signer voudrait dire | Ce qu'il faudrait |
|---|---|---|
| **L'association française** (RNA W563015824) | un organisme de recherche sans but lucratif atteste | une décision du bureau, et un contrôle que le signataire détient le pouvoir |
| **La Sàrl suisse** | une société commerciale atteste, avec la responsabilité qui va avec | une décision du gérant ; apporte la responsabilité sur laquelle un contrat pilote reposerait |
| **L'organisation GitHub** | **n'est pas une personne juridique** | rien — elle ne peut pas s'engager, et ne doit jamais être nommée comme entité engageante |

La troisième n'est citée que pour être écartée : un compte d'organisation
n'est pas une personne juridique, et une attestation qui le nommerait
affirmerait un engagement que personne n'a pris.

**C'est une décision juridique avant d'être technique.** Le défaut honnête
jusqu'à ce qu'elle soit prise est celui en vigueur aujourd'hui :
`legal_capacity_to_attest: "unverified"`, que le vérificateur rapporte à
chaque exécution.

### Comment cette condition se ferme

`legal_capacity_to_attest` quitte `unverified` quand, et seulement quand, les
trois tiennent :

1. l'entité engageante est **nommée**, avec sa référence d'enregistrement ;
2. le **représentant habilité** est consigné, et son pouvoir d'engager
   l'entité a été **contrôlé sur les statuts ou le mandat de l'entité** — non
   affirmé ;
3. une **décision humaine** est consignée, datée, par ce représentant.

**Aucun contrôle automatique ne peut poser ce champ.** Le vérificateur le lit
dans le magasin et le rapporte ; il ne le dérive jamais. Un champ que du code
pourrait poser ne vaudrait rien.

### Ce que le vérificateur fait entre-temps

Il atteint `cryptographically_attested` — la signature vérifie bien — et
rapporte la capacité juridique non vérifiée sur une ligne `NOT TESTED`
séparée et permanente. Les deux énoncés sont indépendants, et les fusionner
serait le raccourci malhonnête : une signature valide émanant d'une partie
dont la capacité n'est pas établie est exactement ce dont elle a l'air.

---

## Partie B — B-2 : la clé, et sa garde

### Pourquoi aucune clé de production n'existe encore

Parce que la partie A n'est pas tranchée. Une clé de production générée
maintenant serait détenue au nom d'une entité qui n'a pas décidé de s'engager,
et chaque dossier signé avec elle emporterait ce défaut. **La génération
attend.**

Tout ce qui a été signé à ce jour l'a été avec des **clés de test
éphémères**, détruites après usage, et leurs magasins portent
`store_kind: "test"`.

### Génération

| | |
|---|---|
| Algorithme | **Ed25519**, imposé — jamais lu dans un en-tête de jeton |
| Outil | `sign.py genkey`, qui refuse d'écrire une clé privée sous la racine du dépôt |
| Où | hors ligne, sur le poste de l'opérateur, jamais sur un serveur |
| `kid` | **jamais réutilisé**, y compris après révocation |
| Nature du magasin | `production` seulement une fois la partie A tranchée |

La convention de `kid` : `nm-ev-<entité>-<aaaamm>-<n>`. Il doit être unique
pour toujours — un `kid` réutilisé rendrait deux clés différentes
indiscernables dans un magasin, et transférerait silencieusement la confiance
de l'une à l'autre.

### Garde

| Question | Réponse exigée avant toute clé de production |
|---|---|
| Où vit le secret ? | le magasin DPAPI du poste de l'opérateur |
| Qui peut le lire ? | **à décider** — et consigné, par nom de rôle |
| Y a-t-il une sauvegarde hors machine ? | **exigée** ; une clé perdue ne resigne rien |
| Où est la sauvegarde ? | **à décider** — et elle ne doit pas être atteignable avec le poste |
| Qui peut autoriser une signature ? | **à décider** — le représentant de la partie A |

Un poste qui détient une clé capable d'engager une organisation est un point
de contrôle. La question de la sauvegarde n'est pas administrative : sans
elle, une panne de disque rend toute attestation future impossible, et incite
à régénérer sous le même `kid`, ce que la convention ci-dessus interdit.

### Rotation contre compromission — la distinction qui porte tout

Ce ne sont pas deux degrés d'un même événement. Leurs effets sur le passé sont
opposés.

| | `rotated` | `compromised` |
|---|---|---|
| Sens | la clé a été remplacée dans l'ordre | le secret est peut-être chez un autre |
| Signatures **antérieures** | **restent de confiance** | **toutes deviennent non fiables, rétroactivement** |
| Pourquoi | rien ne suggère que le détenteur ne l'ait jamais été | le détenteur peut forger n'importe quel `attested_at_declared` |
| Champ de politique | `on_rotated_key_within_window: trusted` | `on_compromised_key: untrusted_retroactively` |

**L'asymétrie est le fond du sujet.** Une compromission ne se borne pas par
une date, parce que la seule chose qu'un voleur maîtrise est la date qu'il
écrit. Une politique qui ferait confiance aux signatures antérieures ferait
confiance à un champ que l'attaquant choisit.

Conséquence, à affronter avant le premier pilote payant : marquer une clé
`compromised` invalide **tous** les dossiers qu'elle a jamais signés. La
décision de la marquer doit donc être prise en sachant si ces dossiers
demandent une réattestation sous une clé neuve — et une réattestation produit
une attestation **rétrospective**, qui énonce une vérification à la date de
signature effective et ne doit jamais être présentée comme contemporaine.

### Révocation

**Ne jamais révoquer à sec.** Remplacer d'abord, révoquer ensuite. Une
révocation dont le remplacement n'est pas déjà dans le magasin laisse chaque
consommateur avec une clé qu'il doit refuser et aucune clé qu'il puisse
accepter — le vérificateur rend `NOT TESTED` pour une clé inconnue, donc
toute la chaîne perd silencieusement un niveau au lieu d'échouer franchement.

Ordre : générer le successeur → le publier au magasin → poser `superseded_by`
sur le prédécesseur → seulement alors marquer le prédécesseur.

### Traçabilité

Chaque signature doit être attribuable après coup :

- le `kid` est dans l'en-tête du jeton, donc chaque attestation nomme sa clé ;
- le magasin consigne `valid_from_declared` et `superseded_by` ;
- **ce qui n'est consigné nulle part aujourd'hui** est un registre de quels
  dossiers ont été signés avec quel `kid`. Nécessaire avant un pilote : sans
  lui, une compromission ne peut pas être circonscrite, et la circonscrire
  est la seule chose qui en limite les dégâts.

### Vérification hors ligne, à partir de la seule clé publique

C'est déjà vrai, et cela doit le rester. `verify_attestation.py` demande le
jeton, l'archive et un magasin de confiance — aucun réseau, aucun service, et
`cryptography` est optionnelle : absente, la ligne de signature rend
`NOT TESTED`, jamais `PASS`. Un outil indépendant parvient à la même
conclusion : `openssl pkeyutl -verify` valide la même signature.

**Une vérification qui aurait besoin de nous ne serait pas une
vérification.**

---

## Ce que ce document ne tranche pas

- Quelle entité s'engage. C'est la décision ouverte de la partie A, et elle
  conditionne tout le reste.
- Qui détient la clé, et qui autorise une signature. Les deux marquées **à
  décider** ci-dessus.
- Si l'entité engageante porte la responsabilité sur laquelle un contrat
  pilote reposerait. Une question pour l'entité, pas pour ce dépôt.
- Le registre des dossiers signés. Nommé comme manquant ; pas construit.

Jusqu'à ce que la première soit tranchée, toute attestation que ce produit
émet est une **démonstration**, et doit être décrite comme telle.
