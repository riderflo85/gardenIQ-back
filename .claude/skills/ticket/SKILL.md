---
name: ticket
description: Lit un ticket du kanban Notion GardenIQ (par numéro TK-<id>) ou liste les tickets ouverts, prépare son traitement (résumé de la user story, nom de branche `(TK-<id>)(<type>)-<slug>` d'après ses tags) et tient le statut Notion à jour (En développement, Code review & test, À merge, Fait), avec confirmation. Utiliser quand l'utilisateur demande "traite le ticket TK-74", "prends le ticket 74", "liste les tickets", "quels tickets sont à faire", "où en est le ticket X", "mets le ticket en review", "passe le ticket à Fait" ou équivalent.
---

# ticket

Traite un ticket du kanban Notion de GardenIQ : le lire, en tirer un plan de travail, créer la branche qui porte son numéro, puis suivre son statut pendant que le travail avance (commit, PR, merge). Pour **créer** des tickets à partir de `docs/backlog.md`, voir le skill `ticket-create`.

Les outils Notion (`mcp__notion__*`) sont chargés à la demande : avant le premier appel, les charger avec `ToolSearch` (`select:mcp__notion__notion-fetch,mcp__notion__notion-query-data-sources,mcp__notion__notion-update-page,mcp__notion__notion-search`). Si le serveur `notion` n'est pas connecté, le dire et s'arrêter : ne rien deviner du contenu d'un ticket.

## Le kanban

| Élément | Valeur |
|---|---|
| Base | « Tableau kanban », source de données `collection://28f54287-aae0-81ff-b3d7-000b26a0535c`, sous la page « GardenIQ » |
| `Nom` | Titre du ticket |
| `Id carte` | Numéro automatique `TK-<n>`, **lecture seule**. C'est le `<id>` des branches, commits et titres de PR. |
| `Statut` | `À faire` → `En développement` → `Code review & test` → `À merge` → `Fait` |
| `Priorité` | `Prio - Faible`, `Prio - Normale`, `Prio - Urgent` |
| `Tags` | Type : `feature`, `bug`, `enhancement`. Périmètre : `back`, `front`, `software`. |
| `Équipe` | `Design`, `Ingénierie`, `Documentation`, `Développement`, `Mise en production` |
| `Assigné à` | Multi-sélection `👤 Florent`, `👤 Ryzhy` (des étiquettes, pas des comptes Notion) |
| `Nom de la branche GitHub` | Texte, vide sur les anciens tickets |
| `Pull Requests GitHub` | Relation vers une base de PR synchronisée depuis GitHub |
| `Sous tâches`, `Date d'échéance` | Case à cocher, date |

La connexion MCP utilise le compte Notion « Garden » de l'espace « GardenerIQ » : toute écriture apparaît sous ce compte, pas sous le nom d'une personne.

## Paramètres acceptés

- `ticket list` (ou « liste les tickets ») → tickets dont le statut n'est pas `Fait`. Un statut peut être donné : `ticket list "À faire"`.
- `ticket <id>` (ou « traite TK-<id> ») → lire le ticket et préparer son traitement (étapes 1 à 4).
- `ticket status <id> <statut>` → changer le statut d'un ticket (étape 6).
- `ticket` seul, sur une branche `(TK-<id>)…` → le ticket de la branche courante.

## Procédé

### 1. Retrouver le ticket

Lecture structurée (mode `rows`, pas SQL : le SQL a un quota sur ce plan) :

```json
{"mode": "rows",
 "data_source_url": "collection://28f54287-aae0-81ff-b3d7-000b26a0535c",
 "limit": 5,
 "filter": {"type": "group", "operator": "and", "filters": [
   {"type": "property", "property": "Id carte", "propertyType": "auto_increment_id",
    "operator": "number_equals", "value": {"type": "exact", "value": 74}}]}}
```

Pour lister les tickets ouverts, filtrer sur `Statut` : `{"type": "property", "property": "Statut", "propertyType": "status", "operator": "status_is_not", "value": {"type": "is_option", "value": "Fait"}}`, trié par `Id carte` croissant. Présenter un tableau court (numéro, nom, statut, priorité, tags, assigné) et ignorer les cartes qui ne sont pas du travail (modèles, notes). Aucun résultat : le dire, ne rien créer.

La recherche IA n'est pas disponible sur ce plan : pour chercher par mots-clés, `notion-search` (avec `data_source_url` du kanban pour restreindre).

### 2. Lire et résumer

Lire la page avec `notion-fetch` (son URL est dans le résultat de l'étape 1). Restituer en français, sans recopier :
- la user story et ses critères d'acceptation (cases `- [ ]`) ;
- les contraintes techniques et les dépendances (autres cartes `#TK-<n>` citées : les lire aussi si elles conditionnent le travail) ;
- ce qui manque (pas de critère, pas de périmètre) : le dire plutôt que combler.

Contrôler avant de commencer :
- un statut autre que `À faire`, ou un ticket assigné à une autre personne (par exemple `👤 Ryzhy`) : demander avant de le prendre ;
- une branche existe déjà pour ce numéro : `git branch -a --list '*TK-<id>)*'` ;
- l'état du dépôt : `git status --short` (des modifications non commitées sont à signaler avant de changer de branche).

### 3. Proposer la branche

Format : `(TK-<id>)(<type>)-<slug>`, `<id>` étant le numéro de `Id carte`.

- **Type** d'après les tags : `feature` → `feat`, `bug` → `fix`, `enhancement` → `enh`. Aucun de ces tags, ou plusieurs : demander. Pour `docs`, `refactor`, `test` ou `chore`, qui n'ont pas de tag Notion : demander aussi.
- **Slug** : trois à six mots, **en anglais** (comme l'historique), séparés par des tirets, tirés du titre du ticket. Le proposer, l'utilisateur tranche.

Exemple : ticket `TK-74` « Appliquer le diagramme de relation », tag `enhancement` → `(TK-74)(enh)-Apply-relation-diagram`.

### 4. Confirmer, puis agir

Afficher et attendre une confirmation explicite :

```
Ticket   : TK-<id> · <nom> (<url>)
Branche  : (TK-<id>)(<type>)-<slug>   depuis origin/main
Notion   : Statut <ancien> → En développement ; Nom de la branche GitHub = <branche>
Assigné  : <valeur actuelle> (inchangé)
```

Puis :

```bash
git fetch origin
git switch -c "(TK-<id>)(<type>)-<slug>" origin/main
```

(les guillemets sont nécessaires : le nom contient des parenthèses). Puis mettre à jour Notion avec `notion-update-page` :

```json
{"page_id": "<id de la page>", "command": "update_properties",
 "properties": {"Statut": "En développement", "Nom de la branche GitHub": "(TK-74)(enh)-Apply-relation-diagram"}}
```

`Assigné à` n'est modifié que si l'utilisateur le demande ou si le champ est vide et qu'il a dit qui prend le ticket. Relire la page (`notion-fetch`) pour vérifier le résultat avant de le dire.

### 5. Pendant le travail

Les commits passent par le skill `commit`, la PR par `pr-create`. Les critères d'acceptation du ticket sont la référence de fin : à la fin du travail, les relire et dire lesquels sont couverts. Cocher les cases dans Notion (`update_content`, remplacer `- [ ]` par `- [x]` sur le critère concerné) seulement à la demande de l'utilisateur.

### 6. Transitions de statut

| Événement | Statut Notion |
|---|---|
| Branche créée, travail commencé | `En développement` |
| PR ouverte (`pr-create`) | `Code review & test` |
| PR relue et prête à fusionner | `À merge` |
| PR fusionnée sur `main` (`pr-create merge`) | `Fait` |

**L'intégration GitHub de Notion fait avancer le statut toute seule** une fois la PR ouverte : sur TK-75, quelques minutes après l'ouverture de la PR, le statut est passé à `Code review & test` et la relation `Pull Requests GitHub` s'est remplie, sans aucune écriture du skill. Ne pas écrire un statut avant d'avoir **relu** le ticket après l'événement :

1. Après la création de la branche, `En développement` est écrit par ce skill (étape 4) : l'intégration ne l'a pas fait.
2. Après chaque événement suivant (PR ouverte, PR relue, PR fusionnée), attendre quelques minutes, puis relire le ticket (`notion-fetch`).
3. Statut déjà conforme au tableau : ne rien écrire, le dire.
4. Statut inchangé après un délai raisonnable : le signaler et **proposer** la transition, à confirmer.

Pour `À merge` et `Fait`, le comportement de l'intégration n'a pas encore été observé : c'est à constater à la première fusion, puis à noter ici.

Toute écriture reste **proposée puis confirmée** : le kanban est partagé avec l'équipe. Une demande explicite de l'utilisateur dans le même message vaut confirmation. Ne jamais revenir en arrière sans le demander, ne jamais mettre `Fait` avant d'avoir vérifié que la PR est fusionnée (`gh pr view <n> --json state`).

```json
{"page_id": "<id>", "command": "update_properties", "properties": {"Statut": "Code review & test"}}
```

### 7. Lien avec les pull requests

Les PR sont synchronisées depuis GitHub dans une base liée (relation `Pull Requests GitHub`), que le MCP ne peut pas lire directement (erreur 404 sur sa source de données). Les titres de PR `(TK-<id>)(<type>) …` portent le numéro du ticket. Après la création d'une PR, relire le ticket au bout de quelques minutes : la relation doit lister la PR (observé sur TK-75). Si elle est vide, le dire à l'utilisateur ; ne pas la renseigner à la main. Pour lire une PR liée, utiliser l'URL de la page donnée dans la relation (`notion-fetch`).

### 8. Rendre compte

Une ligne par action faite : ticket lu, branche créée, statut changé (ancien → nouveau), puis ce qui reste à décider.

## Limites

- Le champ `Id carte` ne s'écrit pas ; `Dernière modification` et `Dernière modification par` sont automatiques.
- Les titres sont stockés avec un échappement Markdown (`\[Back\]`) : les normaliser pour comparer.
- Les tags `refactor`, `test`, `chore` et `documentation` n'existent pas dans Notion. Ajouter une option de tag change le schéma de la base : c'est refusé par `settings.json`, à faire par l'utilisateur dans Notion.
- Ni suppression de page ni changement de schéma depuis ce skill.

## À éviter

- Prendre un ticket assigné à quelqu'un d'autre sans demander.
- Changer un statut sans confirmation, ou le faire avancer au-delà de ce que Git montre.
- Remplir la relation `Pull Requests GitHub` ou écrire `Id carte`.
- Créer un ticket ici : c'est le rôle de `ticket-create`.
- Inventer le contenu d'un ticket vide ou illisible.
