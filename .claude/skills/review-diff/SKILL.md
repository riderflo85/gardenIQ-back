---
name: review-diff
description: Relit une branche, une pull request GitHub ou un diff comme le ferait un développeur généraliste senior (bugs de correction appuyés sur un scénario d'échec concret, puis réutilisation/simplification/efficacité, plus le respect des règles d'architecture et de typage de GardenIQ) et produit un rapport narratif en français, avec une piste de correction par constat (jamais appliquée) et un verdict de merge. Utiliser quand l'utilisateur demande "review cette PR", "review cette MR", "fais une code review", "relis ce diff", "review cette branche", "donne-moi ton avis sur ce diff", "review-diff" ou équivalent.
---

# review-diff

Un développeur senior qui relit une PR ne produit pas une liste sèche de constats : il raconte ce que le changement cherche à faire, ce qui ne va pas (avec un scénario concret, pas une impression), ce qu'il proposerait à la place, et s'il approuverait. Ce skill produit ce récit, en français.

**Langue de sortie : français.** Titres, prose et pied de page en français ; code, chemins et identifiants restent tels quels.

**Périmètre.** Deux axes : la **correction** (bugs, cas limites, comportement erroné) et la **réutilisation / simplification / efficacité** (logique dupliquée, utilitaire existant non réutilisé, chemin inutilement complexe, N+1), plus le **respect des règles** de `CLAUDE.md` : architecture et typage (voir étape 2). Pas de chasse au style : black, isort et flake8 s'en chargent (`black --check gardeniq`, `isort --check-only --diff .`, `flake8 .`).

**Ce que ce skill n'est pas.**
- Pas un walkthrough pédagogique (ni contexte, ni glossaire).
- Pas un correcteur : chaque constat reçoit une piste de correction en prose ou en extrait de code, **jamais appliquée** au working tree. Appliquer est une demande distincte, après la review.
- Pas un poseur de commentaires : jamais de `gh pr comment`, `gh pr review` ni de commentaire inline, sauf demande explicite de l'utilisateur après coup.
- Pas exhaustif : si rien ne ressort sur un axe, le dire simplement plutôt que d'inventer.

## Cible

Dans l'ordre :

1. **Numéro de PR** dans la demande (`review-diff 14`) :
   ```bash
   gh pr view <N> --json number,title,url,headRefName,headRefOid,baseRefName,body
   git fetch origin pull/<N>/head
   gh pr diff <N>
   ```
   Le champ `headRefOid` est le commit de tête : adresser les fichiers par ce SHA (`git show <sha>:<chemin>`), pas par `FETCH_HEAD`. Ne jamais utiliser `gh pr checkout` (modifie le working tree). Lire le JSON réel plutôt que supposer les champs.
2. **Branche ou ref explicite** : la résoudre avec `git rev-parse`. La base est `origin/main`, sauf indication contraire.
3. **Sinon, branche courante contre `main`** :
   ```bash
   git fetch origin
   git diff $(git merge-base origin/main HEAD)...HEAD
   ```
   Ajouter `git diff HEAD` s'il y a des changements non commités, et écrire « changements non commités inclus » dans la ligne d'ouverture.

Si `gh` est absent ou non authentifié (`gh auth status`), le dire (installation : `docs/runbooks/installer-gh.md`) et basculer en mode local (cas 3) plutôt que de bloquer. Si le dépôt courant n'est pas un dépôt git, s'arrêter.

Pour une PR empilée (base différente de `main`), relire seulement la diff de la PR contre sa base et l'indiquer (« empilé sur `<branche>` »).

## Étapes

### 1. Lire tout le diff, puis enquêter

Lire le diff en entier. Pour chaque fichier modifié, lire aussi assez de code autour pour juger honnêtement : appelants des fonctions modifiées, tests existants, code frère qui fait la même chose (pour repérer « il existe déjà un helper »), classe de base ou mixin hérité. Un constat bâti sur un hunk isolé, sans vérifier que le code voisin ne gère pas déjà le cas, est la recette du faux positif.

Les règles par chemin de `.claude/rules/` (`api.md`, `migrations.md`, `tests.md`) donnent les conventions des fichiers touchés : les lire quand le diff les concerne.

Si la branche ou la PR porte un ticket `TK-<id>` et que le MCP Notion est connecté, lire le ticket (skill `ticket`, étapes 1 et 2, en lecture seule) : ses critères d'acceptation disent ce que le diff doit couvrir. Un critère non couvert est un constat 🟡 (🔴 s'il s'agit du comportement principal), à relier à ce que le diff change réellement. Ticket introuvable ou MCP absent : le dire en une ligne, sans bloquer la review. Ne jamais écrire dans Notion depuis ce skill.

### 2. Identifier les constats

- **Correction.** Un bug n'existe que si l'on peut énoncer l'entrée ou l'état qui le déclenche et le résultat erroné (crash, valeur fausse, no-op silencieux, race, fuite). « Cela pourrait théoriquement poser problème » n'est pas un constat : tracer un scénario réel ou abandonner.
- **Réutilisation / simplification / efficacité.** Logique déjà présente ailleurs dans le code (mixins de `base`, `BaseSerializer`, `ReadOnlySerializer`, seeders), complexité inutile, motif manifestement coûteux (N+1 sur un queryset, `.all()` itéré sans `select_related`/`prefetch_related`, réimplémentation d'une primitive Django/DRF).
- **Règles d'architecture** (celles de `CLAUDE.md`, à vérifier sur le diff) :
  - sens des imports : `base` n'importe aucune autre app, `hardware` et `users` n'importent que `base`, `orderlg` importe `base` et `hardware`, pas de cycle (exception : les tests) ;
  - un module n'importe pas son module parent, seulement ses frères ; un import par ligne ;
  - un module `utils` n'importe ni modèle, ni serializer, ni vue de `gardeniq` en tête de fichier ;
  - les routes d'une app sont dans son `api_urls.py`, inclus dans `gardeniq/urls.py` ;
  - les vues héritent de `BaseAPIModelViewSet` (`serializer_class`, `detail_serializer_class`, `list_serializer_class`), les serializers de `BaseSerializer` (pas de `ModelSerializer`), ceux de lecture de `ReadOnlySerializer` ;
  - les modèles réutilisent les mixins de `base/models/mixins.py` ;
  - les erreurs attendues sont gérées explicitement dans la vue, `APIException` en dernier recours ;
  - une `Meta` qui combine des parents hérite de leurs `Meta` quand ils y définissent des attributs.
- **Typage** (section « Typage » de `CLAUDE.md`) : une fonction ou méthode écrite ou modifiée sans paramètres ni retour typés, un nouveau `typing.Dict/List/Optional`, un `# pyright: ignore` sans règle précise. Aucun outil ne le vérifie : c'est à la relecture de le voir. Tests et migrations exclus.
- **Points propres au dépôt** à garder en tête :
  - une migration déjà présente sur `main` ne doit être ni modifiée ni supprimée, et un modèle modifié sans migration est un constat (la CI ne le détecte pas) ; les migrations de `users` touchent aussi `knox` ;
  - les données de référence passent par les seeders, pas par des migrations de données ;
  - sécurité de l'API : par défaut authentification Knox et `IsAuthenticated`, avec throttling. Un nouvel endpoint en `AllowAny`, un `permission_classes` plus large que nécessaire, un secret ou une valeur de `.env` dans le diff sont à signaler ;
  - matériel : aucun accès réel à un port série ou au réseau dans les tests ;
  - les défauts déjà connus de `docs/backlog.md` (routes `enable/` et `disable/`, protection des relations non implémentée…) ne sont pas de nouveaux constats, sauf si le diff les aggrave ou y touche ;
  - le titre de la PR suit `(TK-<id>)(<type>) <description>` (il devient le message sur `main`) et les commits `(TK-<id>)(<type>) - <module>: <Description>` : un écart est une suggestion 🟢 au plus.

Sévérité de chaque constat :
- 🔴 **Bloquant** : vrai bug ou risque de correction qui doit bloquer le merge (ou règle d'architecture enfreinte, faille d'accès).
- 🟡 **À surveiller** : vrai problème, mais non bloquant seul (cas limite peu probable, robustesse, coût de complexité modéré).
- 🟢 **Suggestion** : amélioration réelle, optionnelle (dont le typage manquant).

### 3. Points positifs (optionnel, bref)

Une ligne sur un choix notablement bon (cas limite bien géré, simplification propre, bon test sur un vrai risque). Omettre la section si rien ne ressort ; ne pas fabriquer de compliments pour équilibrer.

### 4. Rédiger le rapport

Structure, avec ces titres exacts :

- **`## Vue d'ensemble`** : 1 à 3 phrases. Ce que fait le diff (d'après la description de la PR et les commits, pas deviné), son périmètre, un avis global en une ligne. S'il n'y a aucun constat sur un axe, le dire ici (« Aucun bug identifié sur ce diff. »).
- **`## Constats`** : une sous-section par constat, 🔴 d'abord, puis 🟡, puis 🟢. Chacune :
  - `#### <emoji> <résumé en une ligne> — <fichier>:<ligne>`
  - 1 à 3 phrases : le problème, appuyé sur le scénario d'échec concret ou l'opportunité concrète de l'étape 2.
  - **`Piste de correction :`** extrait de code court ou description précise du changement. Jamais appliquée.
- **`## Points positifs`** : seulement si l'étape 3 a produit quelque chose, sinon pas de titre.
- **`## Synthèse`** : un verdict parmi **Prêt à merger**, **À corriger avant merge** (liste les 🔴 par titre) ou **Bloquant** (problème de fond, rare). Terminer par une liste priorisée de 1 à 3 points s'il y a plus d'un constat.

Prose serrée partout : c'est une review, pas un essai.

### 5. Livrer

Le livrable est un **message dans le chat**, en français, imprimé en entier. Il s'ouvre par une ligne de cadrage :

- **Mode PR** : `[**PR #<N> · <titre>**](<url>)` puis `— relu à <sha court>`, plus `empilé sur <branche de base>` si elle n'est pas `main`.
- **Mode local** : nom de la branche + SHA court (sans lien), plus « changements non commités inclus » le cas échéant.

Puis les sections de l'étape 4, puis un pied de page :

```
---
*review-diff · <cible> · gardeniq-back · <sha court>*
```

Rien après le pied de page.

**Fichier optionnel.** Ne pas écrire de fichier par défaut. Si l'utilisateur demande de conserver la review, l'enregistrer dans `.claude/out/reviews/<slug>-<sha court>.md` (à créer avec `mkdir -p`). **Avant d'écrire, vérifier que le dossier est ignoré par git** (`git check-ignore -q .claude/out/reviews/x.md`) : `.claude/out/` figure dans le `.gitignore`. Si ce n'est plus le cas, le dire et proposer de l'y remettre ; n'écrire qu'après accord, pour qu'aucune review ne parte dans un commit. `<slug>` = numéro de PR + titre en kebab-case, ou nom de la branche en mode local ; suffixe `+uncommitted` sur le SHA si des changements non commités sont inclus. Le corps du fichier est identique à celui du chat ; en cas d'échec d'écriture, imprimer quand même la review et signaler l'échec en une ligne.

Une nouvelle exécution sur la même cible crée un nouveau fichier : le SHA dans le nom les distingue.

## Cas limites

- **Gros diff** (plus d'environ 40 fichiers) : concentrer `Constats` sur les fichiers qui portent du risque ou de la duplication ; citer le reste dans `Vue d'ensemble` comme « relu, rien à signaler ».
- **Diff de documentation, de dépendances ou de configuration seulement** : le dire en une ligne, `Constats` = « Rien à signaler », puis `Synthèse : Prêt à merger`.
- **Rien d'anormal** : issue légitime et fréquente. Le dire avec assurance dans `Vue d'ensemble` et `Synthèse`, sans fabriquer de suggestions 🟢.
- **Fichiers de règles et de skills** (`.claude/`, `CLAUDE.md`, `docs/`) : relire leur exactitude par rapport au code (commandes, chemins, noms de classes) comme on relit du code.

## À éviter

- **Inventer des constats.** Chaque 🔴/🟡 doit se tracer à un scénario concret trouvé en lisant le code. En cas de doute : lire davantage, ou abandonner.
- **Enseigner au lieu de relire.** Si l'utilisateur veut comprendre un diff plutôt que le faire juger, le dire.
- **Appliquer des corrections**, même d'une ligne.
- **Poster sur la PR** (`gh pr comment`, `gh pr review`, commentaires inline) sans demande explicite.
- **Sauter le verdict `Synthèse`** : le lecteur veut un « je merge ou pas » clair.
- **Reproduire des secrets ou des identifiants réels** (jetons, clés, valeurs de `.env`, identifiants d'appareils) vus dans le diff : utiliser des valeurs manifestement fictives dans les exemples.
- **Relire uniquement les hunks**, sans appelants, tests ni helpers existants.
- **`gh pr checkout`** : utiliser `git fetch origin pull/<N>/head` et adresser les fichiers par SHA.
