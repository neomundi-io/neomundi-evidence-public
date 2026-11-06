<sub>🇬🇧 <a href="B1_EXPERIMENTAL_SIGNING_DECISION.md">English</a> · 🇫🇷 <b>Français</b> · <a href="../README.fr.md">← README</a></sub>

# B-1 — Politique de signature expérimentale, à approuver

**6 novembre 2026.** Condition **B-1**. Pendant de
[`SIGNING_POLICY.fr.md`](SIGNING_POLICY.fr.md), qui analyse ; celui-ci
**décide**.

> **Rien ici n'est en vigueur.** C'est une fiche de décision : elle énonce
> exactement ce qui est autorisé, par qui, pour quel périmètre, et ce
> qu'elle ne couvre explicitement pas. Elle prend effet quand le bloc
> d'approbation à la fin est rempli et daté.

---

## Pourquoi ce document, alors que `SIGNING_POLICY.fr.md` avait déjà analysé

Parce que B-1 était bloquée pour une raison qui n'était pas juridique du
tout : **rien n'était sous une forme approuvable.** L'analyse posait trois
entités candidates et cinq rôles, puis demandait une décision — sans en
mettre une sur la table.

Une fiche de décision est l'objet qui manquait. Et une chose la rend
tenable maintenant : le périmètre est **expérimental, scientifique et non
commercial**. C'est un engagement bien plus léger qu'une attestation
commerciale, et c'est la raison pour laquelle cela peut être tranché plutôt
que différé une fois de plus.

---

## Ce qui est proposé

### L'entité engageante

**NeoMundi Recherche** — l'association française, RNA **W563015824**.

Pourquoi celle-là, et pas les deux autres :

| Entité | Pourquoi non |
|---|---|
| La Sàrl suisse | signer au nom d'une entité commerciale importe une responsabilité commerciale dans une expérience qui n'a aucun objet commercial. Juste pour un pilote payant ; faux, et plus lourd que nécessaire, pour ceci. |
| L'organisation GitHub | **n'est pas une personne juridique.** Elle ne peut pas s'engager, et ne doit jamais être nommée comme entité engageante. |

L'association est l'entité dont l'objet — la recherche sans but lucratif —
correspond à ce qui est réellement attesté. Le choix n'est pas un défaut par
élimination : c'est la seule des trois dont l'objet couvre l'acte.

### Le périmètre de ce qu'une signature engage

C'est la partie opérante, et elle est délibérément étroite.

> Une attestation signée sous cette politique affirme exactement ceci :
> **NeoMundi Recherche, dans le cadre d'une expérience scientifique, s'est
> engagée sur l'empreinte de ce dossier de mesure à la date déclarée.**

Et elle n'affirme rien d'autre. En particulier **aucun** des points
suivants :

- que la mesure est juste, ni que ses valeurs signifient ce qu'un lecteur
  suppose ;
- que l'exécution a eu lieu, ni quand, ni chez qui ;
- que la date déclarée est vraie — aucune horloge de confiance n'intervient ;
- aucune garantie, aucun niveau de service, aucun engagement commercial ;
- aucune validation médicale, juridique ou factuelle.

Le vérificateur dit déjà tout cela à chaque exécution. Cette politique
ajoute un énoncé que le vérificateur ne peut pas produire : **qui**
s'engage, et à quel titre.

### Les cinq rôles, tels que proposés

| Rôle | Proposé | S'engage sur |
|---|---|---|
| **Entité engageante** | NeoMundi Recherche (RNA W563015824) | le contenu de l'énoncé, dans le périmètre ci-dessus |
| **Représentant habilité** | **à nommer ci-dessous** | que l'association est liée |
| **Détenteur de la clé** | le magasin DPAPI du poste de l'opérateur | rien ; il détient le secret |
| **Opérateur technique** | **à nommer ci-dessous**, par rôle | rien ; il lance la commande |
| **Auteur de la mesure** | `nm-station` | la mesure, pas l'engagement |

Le détenteur et l'opérateur peuvent être la même personne. Le
**représentant** et le **détenteur** doivent rester distinguables au
registre même quand c'est la même personne, parce qu'ils s'engagent sur des
choses différentes — et un magasin qui les fusionnerait ferait lire le
secret d'un poste comme la signature d'une organisation.

### Ce qui va au magasin de confiance, et ce qui n'y va pas

| Champ | Valeur | Note |
|---|---|---|
| `store_kind` | `production` | seulement une fois cette fiche approuvée |
| `legal_name` | `NeoMundi Recherche` | le nom d'une entité est public |
| `kind` | `association` | |
| `jurisdiction` | `FR` | |
| `registration_reference` | `RNA W563015824` | entrée au registre public |
| `legal_capacity_to_attest` | `experimental` | **voir ci-dessous** |
| le **nom** du représentant | **absent** | le nom d'une personne physique n'est pas à nous de le publier ; le rôle est consigné, la personne non |

#### Une quatrième valeur pour `legal_capacity_to_attest`

Le champ accepte aujourd'hui `unverified`, et la politique dit qu'il ne
quitte cet état que sur un contrôle vérifié des pouvoirs. Pour une
attestation commerciale, cela reste juste.

Pour ce périmètre, ce serait **faux dans les deux sens** : `unverified`
sous-dit une décision qui a réellement été prise, et `verified` sur-dirait
un contrôle que personne n'a effectué sur les statuts.

La valeur honnête est une troisième : **`experimental`** — l'entité est
nommée et a décidé, le périmètre est non commercial, et **aucune
vérification des pouvoirs n'a été effectuée.** Le vérificateur doit le
rapporter sur une ligne propre, ni comme un échec ni comme une capacité
pleine.

> Cela demande d'ajouter `experimental` à l'énumération du schéma, et une
> ligne de vérificateur qui dise précisément ce que cela signifie. **Pas
> encore fait** — c'est le premier geste technique après approbation, et il
> ne doit pas être fait avant : une valeur au schéma que personne n'a
> autorisée serait une invitation à s'en servir.

---

## Ce que cela n'autorise PAS

Énuméré parce qu'une approbation se lit toujours plus largement qu'elle n'a
été donnée.

1. **Aucune attestation commerciale.** Un pilote payant demande la décision
   sur la Sàrl, ou une extension explicite de celle-ci. Cette fiche ne la
   fournit pas.
2. **Aucune génération de clé.** C'est B-2, qui a sa propre approbation.
3. **Aucune publication du magasin de confiance.** C'est C-5, qui demande en
   plus un audit de contenu.
4. **Aucune resignature rétroactive** de ce qui a déjà été attesté avec une
   clé de test. Ces dossiers restent des démonstrations ; les réattester
   produirait des attestations **rétrospectives**, qui sont un acte distinct.
5. **Aucune revendication de qualification eIDAS**, jamais, sous aucune
   configuration.

---

## La décision — APPROUVÉE le 6 novembre 2026

Prise comme décision de direction. Consignée telle qu'elle a été donnée.

```
D-1  L entite engageante est NeoMundi Recherche, RNA W563015824--
     l association scientifique portant actuellement le projet.

     APPROUVE -- 6 novembre 2026, decision de direction.
     Perimetre : experimental, scientifique, NON COMMERCIAL.

D-2  Le representant habilite de l association pour les actes de signature
     sous cette politique est :

     role : le representant legal de NeoMundi Recherche
     (c est le ROLE que le magasin consigne. La personne physique est
     nommee au registre interne seulement, et n est jamais publiee --
     voir << le nom de la personne n est pas a nous de le publier >>.)

D-3  L operateur technique autorise a lancer une signature, et le
     detenteur de la cle privee :

     role      : l operateur technique du poste de signature
     detenteur : le magasin DPAPI de ce poste

     Meme personne qu en D-2 ?   NON RENSEIGNE -- et cela ne change
     aucun verdict. Le verificateur rapporte deja la coincidence des
     roles, a chaque passage (<< la separation est nominale >>). Y
     repondre documenterait un fait que la sortie enonce deja ; le
     laisser en blanc ne retient rien.

     ---

     `legal_capacity_to_attest` vaut `experimental`, au sens enonce
     ci-dessus : entite nommee et decidee, perimetre non commercial,
     AUCUNE verification des pouvoirs effectuee.

     Volontairement NON FAIT, et non requis : la constitution de la
     future societe commerciale, et toute qualification juridique
     exhaustive. Ni l une ni l autre ne bloque ce perimetre.
```

### Ce que ceci ne tranche pas

La **personne** qui porte le rôle D-2. Sa place est au registre interne, pas
ici et pas au magasin de confiance — le champ accueillant le nom d'un
représentant est délibérément absent du schéma. Les développements ne
l'attendent pas : aucun chemin de code ne le lit, et aucun verdict n'en
dépend.

### Ce qui a été fait depuis l'approbation

1. ✅ `experimental` ajouté au schéma du magasin, avec une ligne de
   vérificateur qui dit ce que cela signifie et ce que cela ne signifie pas,
   dans les deux langues — et
   [`tests/test_capacite.py`](../tests/test_capacite.py) verrouille les trois
   façons de la mal lire ;
2. ✅ `sign.py --signer-capacity experimental --signer-registration` l'émet ;
3. ⏳ **B-2** : l'outillage de garde et de rotation est construit et testé ;
   la clé de production elle-même n'est **pas générée** — voir
   [`B2_KEY_CUSTODY_AND_ACTIVATION.fr.md`](B2_KEY_CUSTODY_AND_ACTIVATION.fr.md) ;
4. ⏳ **C-5** : préparé, non publié ;
5. ⏳ le magasin passe en `store_kind: production` seulement au geste 3.

Tant que la clé de production n'existe pas, toute attestation que ce produit
émet reste une **démonstration**, et doit être décrite comme telle. Le
vérificateur le dit de lui-même : une clé `test` n'accorde rien sans
`--allow-test-keys`.
