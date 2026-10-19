---
name: commit
description: Crée un commit au format GardenIQ (`(TK-<id>)(<type>) - <module>: <Description>`, en anglais, un commit par changement logique) après avoir vérifié la branche, lancé le lint et obtenu la confirmation de l'utilisateur. Écrit seulement `<module>: <Description>` : le hook local prepare-commit-msg ajoute le préfixe depuis le nom de la branche. Utiliser quand l'utilisateur demande "commite", "fais le commit", "crée un commit", "commit ça", "commit" ou termine un changement à enregistrer.
---

# commit

Crée des commits au format GardenIQ, un par changement logique. Le format est décrit dans `CLAUDE.md` (section « Git et GitHub ») et `docs/git_version.md` : `(TK-<id>)(<type>) - <module>: <Description>`, en anglais (décision d'équipe).

**Une approbation de l'utilisateur = un seul commit.** Ne jamais commiter sans confirmation explicite, même si `settings.json` demande déjà une validation de la commande.

## Procédé

### 0. Vérifier le contexte

```bash
git branch --show-current
git status --short
ls -l .git/hooks/prepare-commit-msg .git/hooks/pre-commit
```

- La branche doit être de la forme `(TK-<id>)(<type>)-<slug>` (ex. `(TK-61)(feat)-Optimise-remove-and-add-models`). Sur `main` : arrêter et prévenir, ne pas commiter (une branche par ticket, depuis `main`). Si la branche a un `(TK-<id>)` mais pas de `(<type>)`, le préfixe ajouté n'aura pas de type : le signaler et demander avant de continuer.
- Le hook local `prepare-commit-msg` doit exister et être exécutable : c'est lui qui ajoute le préfixe. Il n'est pas versionné (une copie fraîche du dépôt ne l'a pas). S'il manque, prévenir l'utilisateur : ne pas écrire le préfixe soi-même sans son accord.
- Les hooks pre-commit (black, flake8, isort…) utilisent les outils de l'environnement pipenv : lancer le commit dans `pipenv shell`, ou avec `pipenv run git commit …`. Un message « `pre-commit` not found » ou « Executable `black` not found » veut dire que l'environnement n'est pas actif. Si le hook pointe vers un environnement virtuel disparu, `pre-commit install` le régénère : le proposer, ne pas le lancer sans demande.

### 1. Lire le changement

```bash
git diff            # non indexé
git diff --staged   # indexé
```

Lire le diff réel, pas seulement les noms de fichiers. Si l'utilisateur a déjà indexé des fichiers, respecter son index : le commit porte sur ce qui est indexé. Sinon, déterminer les fichiers du changement.

**Un commit = un changement logique.** Si le diff mélange plusieurs changements (une correction et un refactor, du code et une doc sans lien…), proposer un découpage en plusieurs commits et les enchaîner un par un, chacun avec sa propre confirmation (étape 5).

**Migrations** : un fichier de migration généré fait partie du même commit que le changement de modèle qui l'a provoqué. Un modèle modifié sans migration, ou l'inverse, est à signaler avant de commiter (`./manage.py makemigrations --check --dry-run`).

### 2. Indexer précisément

Indexer **par nom de fichier**, jamais `git add -A` ni `git add .` :

```bash
git add <fichier> [<fichier>…]
```

Ne jamais indexer : `.env`, `db.sqlite3`, fichiers personnels (`CLAUDE.local.md`, `.claude/settings.local.json`), ni fichier contenant un secret. Si l'un d'eux apparaît dans le diff, le signaler à l'utilisateur.

### 3. Lancer le lint

Les hooks pre-commit rejouent black, flake8, isort, check-json, end-of-file-fixer et trailing-whitespace sur les fichiers indexés. Les lancer avant évite un commit refusé puis à refaire :

```bash
pre-commit run
```

(sans `--all-files` : uniquement les fichiers indexés.) Si un contrôle échoue, corriger les fichiers concernés **avant** de commiter, sans changement hors du périmètre. Les hooks qui réécrivent des fichiers (black, isort, fin de fichier) les modifient : réindexer ensuite.

Ne pas lancer toute la suite de tests à chaque commit (~2 min, ~35 s avec `-n auto --reuse-db`). Si le changement touche du code testé, lancer au moins les tests concernés (`pytest -- gardeniq/<app>/tests/<dossier>/<fichier>.py`) et le dire dans la proposition.

### 4. Rédiger le message

```
<module>: <Description>
```

- **En anglais**, à l'impératif, première lettre en majuscule, sans point final : `Add frame protocol unit tests`, `Fix firmware version comparison`.
- **`<module>`** : l'application concernée (`base`, `hardware`, `orderlg`, `telemetry`, `users`), d'après le chemin des fichiers (`gardeniq/<app>/…`), ou `settings`, `ci`, `docker`, `deps`, `hooks`, `claude` pour ce qui est hors des apps. Si aucun ne convient, demander. Un nouveau module dans `gardeniq/` s'ajoute à la liste de `CLAUDE.md`.
- **Type** : par défaut celui de la branche, ajouté par le hook (`feat`, `fix`, `enh`, `refactor`, `test`, `docs`, `chore`). **Ne pas écrire le ticket `(TK-<id>)`** : le hook le met. Pour un autre type, écrire `(<type>) - <module>: <Description>` ; le hook garde ce type et met le ticket de la branche. Cas voulu : **`docs`** pour un commit qui ne touche que de la documentation (`docs/`, `README.md`, `CLAUDE.md`, règles et skills de `.claude/`) dans une branche qui n'est pas de type `docs` ; le proposer à l'utilisateur dans la confirmation. Les autres types (`test`, `refactor`…) ne se choisissent que si la nature du commit diffère clairement de la branche, et en le disant. Un type hors de la liste n'est pas reconnu par le hook et serait traité comme du texte.
- Une ligne de titre courte (environ 72 caractères). Un corps, séparé par une ligne vide, seulement quand le pourquoi n'est pas évident.

### 5. Confirmer, puis commiter

Afficher et attendre une confirmation explicite **pour ce commit** :

```
Branche  : <branche>
Message  : (TK-<id>)(<type>) - <module>: <Description>   (préfixe ajouté par le hook ; type <branche|explicite>)
Fichiers : <liste indexée, avec +/- lignes>
Lint     : <ok / non applicable>
```

Puis, dans l'environnement pipenv :

```bash
git commit -m "<module>: <Description>"
```

Pour un corps, passer un second `-m "<corps>"`. **Jamais `--no-verify`** (ni `-n`) : les hooks pre-commit sont obligatoires, et `settings.json` refuse ces options sur `git commit` (la règle ne couvre pas `pipenv run git commit`, c'est donc à respecter ici).

Si le pre-commit modifie des fichiers ou échoue, le commit n'a pas eu lieu : réindexer les fichiers corrigés, redemander confirmation si le contenu a changé, puis refaire le commit. Ne pas utiliser `--amend` dans ce cas, il n'y a pas de commit à amender.

### 6. Vérifier le résultat

```bash
git log -1 --format=%B
git show --stat --format= HEAD
```

- Le titre doit être `(TK-<id>)(<type>) - <module>: <Description>`, avec le ticket de la branche et le type voulu (celui de la branche, ou `docs` etc. s'il était explicite). Sinon (préfixe absent, doublé ou autre type), le hook n'a pas fonctionné comme prévu (version ancienne du hook ?) : le dire, et proposer de corriger le message avec `git commit --amend`, après confirmation, tant que le commit n'est pas poussé. Un amend est un commit de plus : il demande aussi une confirmation.
- Le résultat n'est jamais poussé par ce skill : le push se fait à la demande.

Si plusieurs commits sont prévus, revenir à l'étape 2 pour le suivant.

## Cas limites

- **Rien d'indexé ni de modifié** : le dire, ne rien créer.
- **Changement trop gros pour un seul commit** : proposer le découpage plutôt que d'en faire un fourre-tout.
- **Correction d'un commit déjà poussé** : ne pas réécrire l'historique partagé ; créer un nouveau commit, ou demander à l'utilisateur.
- **Branche à rebaser** : rebaser sur `main` se fait avant de pousser, à la demande de l'utilisateur, jamais en cours de commit.
- **Fichier `.git/COMMIT_EDITMSG-e`** : sur macOS le hook (`sed -i -e`) en laisse un. Il est dans `.git/`, sans effet sur le dépôt : ne pas s'en inquiéter.

## À éviter

- Commiter sans confirmation, ou plusieurs commits sur une seule confirmation.
- `git add -A` / `git add .`, et indexer des fichiers sensibles ou personnels.
- `--no-verify`, `-n`.
- Un message en français, ou sans module.
- Écrire soi-même le ticket `(TK-<id>)` : le hook le fait. Seul un type différent de la branche s'écrit, sous la forme `(<type>) - `.
- Commiter sur `main`.
- Pousser sans demande explicite.
