<sub>🇬🇧 <a href="FUTURE_SITE.md">English</a> · 🇫🇷 <b>Français</b> · <a href="../README.fr.md">← README</a></sub>

# Site produit — architecture prévue

Adresse prévue : `evidence.neomundi.org`

**Rien n'est développé, rien n'est déployé, et le nom ne résout pas** —
constaté le 5 novembre 2026. Il n'est délibérément lié nulle part dans ce
dépôt : un produit qui porte sur la vérifiabilité ne livre pas de lien mort.

Ce document fixe l'architecture pour que les choix d'aujourd'hui ne la ferment
pas. Il ne décrit pas un chantier engagé.

---

## Les trois espaces

### Product — ce que c'est, et ce que ce n'est pas

La proposition de valeur et les cas d'usage, avec **les limites au même niveau
que les capacités**. C'est une contrainte de conception, pas une pudeur : une
page qui annonce les fonctions puis cache les limites en bas de page
contredirait le produit qu'elle vend.

Contenu attendu : le problème, les fonctions réellement disponibles, les deux
contrôles que notre vérificateur n'exécute pas, et ce que la vérification ne
détecte pas.

### Demo — découvrir un dossier sur GROUNDED-S1

Une campagne **synthétique** et son dossier de preuve, parcourables sans rien
installer.

Deux règles qui tiennent de la nature du corpus :

- le régime `synthetic` doit être **visible en permanence**, pas dans une note
  de bas de page : ces réponses n'observent aucun opérateur réel ;
- **aucune donnée de pilote, aucun corpus réel** n'y figure jamais. Le corpus
  MED est exclu de tout espace public, et cette exclusion n'est pas
  renégociable par commodité de démonstration.

### Verify — vérifier une archive sans nous

L'espace qui décide de la crédibilité des deux autres.

**Il doit fonctionner dans le navigateur, sans appeler nos services.** Un
vérificateur hébergé qui enverrait l'archive chez nous ne prouverait plus rien :
il demanderait de nous faire confiance pour établir qu'on peut se passer de nous
faire confiance.

Conséquences techniques à respecter le jour où il sera construit :

| | |
|---|---|
| le calcul se fait **côté client** | l'archive ne quitte pas le poste du visiteur |
| aucun téléversement vers nos serveurs | ni pour vérifier, ni pour « améliorer le service » |
| la logique reste celle de `verify.py` | **une seule** implémentation des contrôles, sinon deux versions divergeront et aucune ne fera foi |
| les `NOT TESTED` restent affichés | un contrôle non fait se dit ; il ne disparaît pas de l'interface |

---

## Ce que cette architecture interdit, par construction

- **Aucune collecte.** Un espace de vérification qui journaliserait les
  archives vérifiées deviendrait exactement ce que le produit prétend éviter.
- **Aucun verdict binaire.** Pas de « ✓ Archive authentique » : une archive
  peut être intérieurement parfaite et fausse. L'interface rend les trois états,
  comme le vérificateur.
- **Aucune promesse de certification**, d'exhaustivité ou de valeur juridique.

---

## Ce qui doit exister avant de construire quoi que ce soit

Deux conditions, et aucune n'est technique :

1. **un relecteur qui dit en avoir besoin.** Aujourd'hui, `verify.py` tient en
   un fichier lisible et s'exécute sans rien installer : l'espace *Verify*
   répond à un confort, pas encore à un manque constaté ;
2. **une décision sur la publication du dépôt.** Tant qu'il est privé, le
   vérificateur se transmet avec l'archive. Un espace public suppose de publier
   le code — ce qui est souhaitable pour la crédibilité, et doit être tranché.

> Priorité honnête : l'espace *Verify* est le seul des trois qui apporterait une
> propriété nouvelle. *Product* et *Demo* sont de la présentation, et une
> présentation ne manque à personne tant que le produit n'a pas d'acheteur.
