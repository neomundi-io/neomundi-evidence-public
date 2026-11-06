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

## La décision à approuver

Trois blancs. Rien d'autre n'est ouvert.

```
D-1  L entite engageante est NeoMundi Recherche, RNA W563015824.

     Approuve / Amende : ......................................

D-2  Le representant habilite de l association pour les actes de signature
     sous cette politique est :

     role : .................................................
     (le role est consigne au magasin ; le nom de la personne non)

D-3  L operateur technique autorise a lancer une signature, et le
     detenteur de la cle privee, est :

     role : .................................................

     Meme personne qu en D-2 ?   oui / non
     (si oui, les deux roles restent distincts au registre)

     ---

     `legal_capacity_to_attest` vaut `experimental`, au sens enonce
     ci-dessus : entite nommee et decidee, perimetre non commercial,
     aucune verification des pouvoirs effectuee.

     Date : ...............   Signature : ..............................
```

### Ce qui se passe au moment de l'approbation

Dans cet ordre, et aucun geste ne peut être pris en avance :

1. ajouter `experimental` au schéma du magasin, avec une ligne de
   vérificateur qui dise ce que cela signifie et ce que cela ne signifie
   pas ;
2. **ensuite** B-2 : générer la clé de production sous la garde approuvée ;
3. **ensuite** C-5 : l'audit de contenu, à qui le D-2 de cette fiche donne
   enfin quelqu'un pour le valider ;
4. le magasin passe en `store_kind: production`.

Jusqu'au geste 1, toute attestation que ce produit émet reste une
**démonstration**, et doit être décrite comme telle.
