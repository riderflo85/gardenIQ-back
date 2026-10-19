---
name: write-doc
description: Produit une documentation technique durable en Markdown avec diagrammes Mermaid, après qu'une feature est construite ou qu'une procédure est en place, selon deux gabarits fixes. Doc de feature (Résumé, Contexte, Architecture, Flux, Configuration & Utilisation, Points d'attention, Tests & Vérification, Fichiers clés, Références) dans `docs/features/`, ou procédure / runbook (Résumé, Prérequis, Vue d'ensemble, Étapes, Vérification, Rollback, Points d'attention, Références) dans `docs/runbooks/`. Utiliser quand l'utilisateur demande "documente cette feature", "écris la doc de X", "génère un runbook pour Y", "documente cette procédure", "fais la doc technique de ce qu'on vient de faire" ou équivalent.
---

# write-doc

Une doc de référence est faite pour être rouverte six mois plus tard par quelqu'un qui veut savoir « comment ça marche » ou « quelles sont les étapes exactes », sans l'auteur sous la main. Elle est dense, structurée, facile à parcourir. Ce skill la produit, en français, dans le dépôt.

**Langue : français.** Titres et prose en français ; code, chemins, identifiants, clés de configuration et blocs de code restent tels quels.

**Où vit la doc.** Dans `docs/features/` (features) et `docs/runbooks/` (procédures), en Markdown avec diagrammes Mermaid (rendus nativement par GitHub). Il n'y a pas de Sphinx ni de fichier `.rst` : ne pas en créer. Créer les dossiers au premier usage. Le dossier `docs/` contient aussi des documents qui ne suivent pas ces gabarits et que ce skill ne régénère pas : `docs/git_version.md` (règles Git) et `docs/backlog.md` (tickets à créer).

**Ce que ce skill n'est pas.**
- Pas un walkthrough pédagogique (ni contexte pas à pas, ni glossaire).
- Pas une review : ni bugs, ni sévérités, ni verdict de merge. Un défaut trouvé en écrivant la doc se note dans `docs/backlog.md`, il ne s'écrit pas dans la doc comme un constat.
- Pas un document de conception écrit *avant* le travail : il décrit ce qui existe, pas ce qui est prévu.

## Deux gabarits, pas un de plus

Le mode est choisi à l'étape 0. Ne pas les mélanger.

| | **Feature** | **Procédure** |
|---|---|---|
| Documente | Du code, une capacité | Un processus qu'un humain exécutera plus tard |
| Colonne vertébrale | Résumé → Contexte → Architecture → Flux / Comportement → Configuration & Utilisation → Points d'attention → Tests & Vérification → Fichiers clés → Références | Résumé → Prérequis → Vue d'ensemble → Étapes → Vérification → Rollback / Annulation → Points d'attention → Références |
| Dossier | `docs/features/` | `docs/runbooks/` |
| Le lecteur | Lit pour comprendre et maintenir | Lit pour *exécuter*, pas à pas |

## Entrées

- **Signal de mode** dans la demande : « documente cette feature », « doc technique de X » → feature ; « écris un runbook », « documente comment faire Z », « note la procédure d'installation » → procédure. Si c'est vraiment ambigu (« documente le protocole USB »), poser la question à l'utilisateur avant tout travail : les deux gabarits divergent trop pour deviner.
- **Contexte de session.** Si la feature ou la procédure a été construite dans cette conversation, c'est une source primaire. Mais la mémoire de la conversation n'est pas la vérité : **vérifier chaque affirmation concrète (clés de config, chemins, options de commande, comportement) dans les fichiers actuels avant de l'écrire.** Une doc qui répète un plan périmé vaut moins que pas de doc.
- **Contexte git**, s'il existe : diff de la branche courante contre `main` (`git diff $(git merge-base origin/main HEAD)...HEAD`), ou une PR nommée par l'utilisateur (`gh pr view <N> --json number,title,url,headRefOid,body`, `gh pr diff <N>`, fichiers adressés par SHA, jamais `gh pr checkout`). Une procédure purement opérationnelle n'a pas de diff : s'en passer.
- **Contexte du dépôt** : `CLAUDE.md`, `.claude/rules/` et les docs déjà présentes dans `docs/`. Les référencer plutôt que les répéter ou les contredire.
- **Modèles à suivre** : `docs/runbooks/installer-gh.md` pour une procédure. `docs/features/authentication.md` est la seule doc de feature : elle date d'avant ces gabarits (sans diagramme Mermaid, sections différentes), ne pas la prendre comme modèle (voir `docs/backlog.md`).

## Étapes

### 0. Choisir le mode et résoudre la cible

Décider feature ou procédure. Puis résoudre *ce qui* est documenté :
- un diff, une branche ou une PR est en jeu : le résoudre comme ci-dessus ;
- le travail a eu lieu dans cette conversation, sans diff à récupérer : la conversation est la résolution, identifier les fichiers touchés ou les étapes exécutées ;
- sinon (on documente de l'existant) : partir de la description de l'utilisateur et explorer le code (point d'entrée, fichiers porteurs, configuration, et pour une procédure les scripts qui implémentent chaque étape : `Pipfile` (scripts), `update_dependencies.py`, `docker-compose.yml` et `docker/`, `.github/workflows/ci.yml`, `.pre-commit-config.yaml`, `start_usb_docker.py`).

### 1. Lire pour de vrai avant d'écrire

Lire les fichiers actuels, pas seulement les hunks du diff ni ce que la conversation annonçait. **Feature** : points d'entrée, logique centrale, modèles, surface de configuration (settings, variables d'environnement du `.env`), tests existants. **Procédure** : chaque script, commande et fichier de configuration que chaque étape touche, et déterminer ce qui se passe si une étape est sautée ou jouée deux fois, car c'est exactement ce que « Points d'attention » et « Rollback » doivent dire juste.

Pour GardenIQ, penser aux apps (`base`, `hardware`, `orderlg`, `users`, `telemetry`), au matériel relié en USB (protocole de trames, `Device`), à l'authentification Knox, aux seeders (`./manage.py seed`), aux réglages par `.env` et à l'environnement pipenv.

### 2. Rassembler le contenu propre au mode

**Feature**, depuis le code :
- le problème résolu et pourquoi la feature existe (cadrage produit) ;
- l'app ou le module qui la porte ;
- chaque surface de configuration pertinente (settings, variables d'environnement, options de commande) avec sa **valeur par défaut actuelle**, jamais « à définir » ;
- le plus petit exemple réel d'utilisation (requête d'API, appel de fonction, commande) ;
- limites connues, cas limites gérés (et non gérés), invariants non évidents ;
- comment vérifier : fichiers et commandes de tests (`pytest -- gardeniq/<app>/tests/<dossier>/<fichier>.py`), ou une recette manuelle faute de test automatisé.

**Procédure**, depuis le code et la conversation :
- ce qui déclenche la procédure (quand le lecteur ouvrira-t-il cette doc ?) ;
- les prérequis : accès, outils, état à garantir avant de commencer ;
- les étapes ordonnées, chacune = une **action** + un **résultat attendu** (+ une commande si c'en est une) ; ne pas fusionner deux actions, ne pas en couper une en deux ;
- la vérification de bout en bout (pas seulement la dernière étape) ;
- comment annuler, ou que faire si ça échoue en cours de route, même si la réponse honnête est « non réversible, prévenir X avant de réessayer ».

Une commande qui n'a pas été exécutée se documente comme telle (« non rejouée ici, d'après la documentation officielle »), jamais comme vérifiée.

### 3. Diagrammes : systématiques

Chaque doc a **au moins deux** diagrammes Mermaid. Seuil dur, même pour une petite feature ou une procédure courte.

**Feature :**
- **Architecture** (`flowchart TD`, un `subgraph` par app ou composant) : composants et flux de données, 6 à 10 nœuds ;
- **Flux / Comportement** (`sequenceDiagram`, ou `stateDiagram-v2` si la feature est pilotée par un cycle de vie) : un chemin concret, de la requête à la réponse ou du déclencheur à l'effet de bord.

**Procédure :**
- **Vue d'ensemble** (`flowchart TD`) : systèmes, outils, environnements touchés et leurs relations ;
- **Étapes en flux** (`flowchart TD`, ou `sequenceDiagram` si plusieurs acteurs interviennent tour à tour) : étapes en nœuds, décisions en losanges (« tests OK ? »). S'ajoute à la liste numérotée, ne la remplace pas : le diagramme donne la forme, la liste donne les commandes exactes.

D'autres figures (diagramme d'états, tableau clé de config → effet, tableau code d'erreur → correctif) sont bienvenues quand elles apportent ce que la prose ne dit pas. Chaque figure a une légende d'une ligne. Pas de méga-diagramme : deux figures ciblées valent mieux qu'un graphe de 25 nœuds.

Vérifier la syntaxe Mermaid avant de livrer : pas de parenthèses ni de guillemets non échappés dans les libellés de nœuds, identifiants de nœuds uniques, noms de branches simples dans un `gitGraph`. On ne peut pas rendre le diagramme ici : le dire si un doute subsiste.

### 4. Rédiger

**Discipline de prose.** Blocs de 2 à 4 phrases, sauf quand un tableau ou une liste sert mieux. Pas de phrases de transition (« Voyons maintenant… »). Un diagramme ou un tableau énonce un fait une fois ; la prose ne le répète pas, elle dit ce qu'il ne peut pas dire (le pourquoi, un cas limite, une mise en garde).

**Feature**, titres exacts, dans cet ordre :

- **`## Résumé`** : 2 à 4 phrases (ce que fait la feature, statut actuel, périmètre en une ligne).
- **`## Contexte`** : le problème résolu, pourquoi elle existe, ce qui était vrai avant.
- **`## Architecture`** : prose + diagramme d'architecture.
- **`## Flux / Comportement`** : prose + diagramme de séquence ou d'états, avec un exemple concret déroulé.
- **`## Configuration & Utilisation`** : tableau clé → valeur par défaut → effet, et le plus petit exemple fonctionnel dans un bloc de code.
- **`## Points d'attention`** : limites, cas limites, invariants non évidents. S'il n'y en a vraiment pas, le dire en une ligne plutôt que d'omettre la section.
- **`## Tests & Vérification`** : commandes de test à lancer, ou recette de QA manuelle.
- **`## Fichiers clés`** : tableau compact `chemin → rôle`, une ligne chacun. Un index, pas une visite guidée du code (pas de code cité, pas de paragraphe par fichier).
- **`## Références`** : PR (`#<n>`), branche ou ticket d'origine (`TK-<id>`, carte du kanban Notion, avec son lien : le retrouver avec le skill `ticket` plutôt que de le deviner), plus une sous-liste **« Voir aussi »** vers les docs voisines de `docs/` qui existent réellement (les vérifier avec `ls`, ne jamais inventer un lien). Omettre la sous-liste si rien ne correspond.

**Procédure**, titres exacts, dans cet ordre :

- **`## Résumé`** : ce que la procédure accomplit et quand l'ouvrir.
- **`## Prérequis`** : accès, outils, état requis. Une checklist (`- [ ]`), pas de la prose.
- **`## Vue d'ensemble`** : prose + diagramme des systèmes touchés.
- **`## Étapes`** : le diagramme en flux en tête de section, puis une liste numérotée. Chaque étape : **action**, **commande** (bloc de code, si applicable), **résultat attendu**.
- **`## Vérification`** : le contrôle d'état final qui confirme que *toute* la procédure a réussi, distinct du résultat attendu de chaque étape.
- **`## Rollback / Annulation`** : comment défaire, par étape ou globalement ; si une étape n'est pas réversible, le dire explicitement et nommer qui ou quoi contacter.
- **`## Points d'attention`** : pièges, sensibilités de timing, choses qui ont l'air d'avoir réussi sans l'avoir fait.
- **`## Références`** : mêmes conventions que pour une feature.

Une étape qui relève du jugement humain (« regarder la sortie et décider si on continue ») s'écrit comme un point de décision avec ses critères, pas comme une fausse commande.

### 5. Livrer

**Écrire le fichier dans le dépôt** :
- feature : `docs/features/<slug>.md` ;
- procédure : `docs/runbooks/<slug>.md`.

`<slug>` est en kebab-case, sans date ni SHA, par exemple `protocole-usb` ou `installer-gh`. Si un fichier existe déjà pour la cible, le **lire puis le mettre à jour** (la doc vit avec le code, l'historique git sert de versions) au lieu d'en créer un second.

Le fichier s'ouvre par un titre `# <Feature|Procédure> : <nom>` et une ligne `Dernière vérification : <date> · <sha court de HEAD>`, puis les sections de l'étape 4. Pas de pied de page.

**Dans le chat** : ne pas réimprimer toute la doc. Donner le chemin du fichier, la liste de ses sections, et signaler tout point que l'utilisateur doit trancher ou vérifier (valeur de configuration incertaine, commande non rejouée, diagramme non rendu).

**Ne pas commiter.** La doc d'une feature fait partie du même changement que le code, ou d'un commit distinct sur la même branche, avec le skill `commit` et sa confirmation habituelle. Le module du commit est l'app documentée (ou `claude` pour un fichier de `.claude/`) ; le type est celui de la branche, sauf pour un commit qui ne contient que de la documentation dans une branche `feat`, `fix` ou `enh` : il prend le type `docs` (`(docs) - <module>: <Description>`).

**Jamais de secrets ni de données réelles** (jetons, clés, valeurs du `.env`, identifiants d'appareils, adresses) dans la doc : valeurs manifestement fictives dans les exemples.

## Cas limites

- **Mode ambigu** : poser la question avant de travailler.
- **Procédure sans artefact git** (processus manuel, configuration de compte) : pas de résolution git ; le diagramme d'architecture devient « systèmes touchés », la source est la conversation plus la vérification directe des outils, URL ou tableaux de bord nommés.
- **Feature sans diff** (existant documenté à froid) : explorer depuis le sujet décrit ; la ligne « Dernière vérification » porte le SHA courant de `HEAD`.
- **Rien à dire dans « Points d'attention »** : le dire en une ligne.
- **Défaut découvert pendant la rédaction** : le décrire dans « Points d'attention » comme comportement actuel s'il touche l'utilisateur de la doc, et l'ajouter à `docs/backlog.md` (après recherche d'un doublon) ; ne pas le corriger dans ce skill.

## À éviter

- **Mélanger les gabarits** : une doc de feature n'a pas d'« Étapes », une procédure n'a pas d'« Architecture » au sens propriété du code.
- **Sauter le seuil de deux diagrammes.**
- **Enseigner au lieu de documenter** : pas de Background ni de glossaire, c'est le rôle d'une explication, pas d'une référence.
- **Relire/juger** : pas de sévérités, pas de verdict.
- **Se fier à la mémoire de la conversation** plutôt qu'aux fichiers actuels.
- **Présenter comme vérifiée une commande qu'on n'a pas exécutée.**
- **Une visite guidée du code dans « Fichiers clés »** : c'est un index à parcourir.
- **Inventer un lien « Voir aussi »** : vérifier que le fichier existe.
- **Créer des fichiers `.rst` ou un Sphinx** : le projet n'en a pas.
- **Créer un doublon** quand un fichier existe déjà pour la cible : le mettre à jour.
