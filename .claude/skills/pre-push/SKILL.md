---
name: pre-push
description: Déroule la checklist avant de pousser une branche GardenIQ (rebase sur la cible, migrations, traductions, documentation, logs, lint et typage, tests, hygiène des commits) et rend un bilan point par point, sans pousser. Utiliser quand l'utilisateur demande "pre-push", "je peux pousser ?", "checklist avant push", "prépare le push", "vérifie avant de pousser" ou avant `pr-create`.
---

# pre-push

Automatise la checklist « Avant de pousser » de `docs/git_version.md` et en fait un bilan honnête. C'est une **porte de contrôle** : elle diagnostique, propose des corrections, mais **ne pousse jamais** (le push et la PR se font à la demande, via `pr-create`).

Règle générale : tout ce qui réécrit l'historique (rebase) ou modifie du code (fusion de migrations, logs, traductions) est **proposé puis confirmé**, jamais fait en silence. Un point non vérifié est marqué « non vérifié », jamais « OK ».

## Procédé

### 0. Contexte

```bash
git branch --show-current
git fetch origin
git status --short
```

- Arrêter sur `main` ou sur une branche qui ne suit pas `(TK-<id>)(<type>)-<slug>`.
- Arbre de travail non propre : le signaler (les vérifications portent sur les commits, mais tests et lint s'exécutent sur l'arbre).
- **Branche cible** : celle de la PR si elle existe (`gh pr view --json baseRefName -q .baseRefName`), sinon `main`. Pour une PR **empilée** (cible différente de `main`), toutes les comparaisons ci-dessous se font contre cette branche. Dans la suite : `<cible>`.
- Commits concernés : `git log origin/<cible>..HEAD --oneline`. Aucun commit : rien à pousser, le dire.

### 1. Rebase sur la cible

```bash
git rev-list --count HEAD..origin/<cible>
```

0 : à jour. Sinon `<cible>` a avancé : proposer `git rebase origin/<cible>`.
- **Branche jamais poussée** : le rebase est sans conséquence, le faire après confirmation.
- **Branche déjà poussée** : un rebase obligerait à forcer le push (`git push --force` est refusé par `settings.json`). Ne pas rebaser seul : expliquer et laisser l'utilisateur décider.
- Conflit sur une migration : ne jamais modifier une migration déjà présente sur `main` ; demander à l'utilisateur (voir `.claude/rules/migrations.md`).

Faire cette étape **en premier** : elle change ce que les suivantes vérifient.

### 2. Migrations

```bash
git diff --name-status origin/<cible>...HEAD -- 'gardeniq/*/migrations/*.py'
./manage.py makemigrations --check --dry-run
```

- **Modifiées (`M`) ou supprimées (`D`)** : **bloquant**, demander à l'utilisateur. Une migration déjà sur `main` peut être déployée. Seules les ajoutées (`A`) sont normales.
- **Modèle changé sans migration** (`makemigrations --check` échoue) : bloquant, proposer `./manage.py makemigrations <app>`. Une migration se génère, ne s'écrit jamais à la main. La CI ne détecte pas ce cas : ce point est le seul filet.
- **Plusieurs migrations ajoutées dans une même app** : proposer de les fusionner en une seule (uniquement celles de la branche) et expliquer la marche à suivre ; ne pas le faire sans confirmation, ni supprimer de fichier de migration sans l'accord explicite de l'utilisateur.
- Retenir si des migrations ont été ajoutées : l'étape 7 doit alors recréer la base de test.
- La base est du SQLite local : aucune infrastructure à démarrer.

### 3. Traductions

L'internationalisation est activée (`USE_I18N`, `LOCALE_PATHS = gardeniq/locale`, langues `en` et `fr`), mais le dépôt ne contient **aucun fichier `.po` ni `.mo`**, et le code applicatif n'a aucune chaîne traduisible (les messages d'erreur portent un `TODO` sur la traduction).

- Le diff n'ajoute aucune chaîne traduisible (`_()`, `gettext`, `gettext_lazy`, `verbose_name` traduit) : marquer « non concerné ».
- Le diff en ajoute : le signaler et demander à l'utilisateur comment procéder, car il n'y a pas de procédure établie (génération des `.po`, versionnement des `.mo`). Ne pas générer de fichiers de traduction de sa propre initiative.

### 4. Documentation

Si le **comportement** change (nouvelle feature, règle métier, procédure d'exploitation), la fiche de référence `docs/features/` ou `docs/runbooks/` doit être créée ou mise à jour : proposer le skill `write-doc`. Les pages Sphinx d'`docs/` ne sont plus maintenues : ne pas y toucher. Si la branche change une règle ou une commande décrite dans `CLAUDE.md` ou `.claude/rules/`, vérifier que ces fichiers restent justes. Pur refactor ou changement sans effet visible : « non concerné ».

### 5. Logs

Lire le code **ajouté** : un chemin qui a des effets de bord ou peut échouer (protocole USB, seeder, commande de management, appel externe, gestion d'une erreur attendue) sans aucune trace est à signaler, avec une proposition de `logger.info/warning/error` au bon endroit. Le projet suit `logger = logging.getLogger(__name__)` (voir `hardware/protocols/usb/handler.py`) ; le lint tolère les f-strings dans les logs (`G004` ignoré), comme le code existant. Aucun `LOGGING` n'est configuré : sans configuration, seuls les messages `WARNING` et plus sortent. Ne rien ajouter sans accord, et pas de log dans du code trivial.

### 6. Lint et typage

```bash
black --check gardeniq
isort --check-only --diff .
flake8 .
```

(les mêmes contrôles que la CI). Corriger ce qui relève de la branche, avec `black gardeniq` ou `isort .` si besoin, sans reformater de fichier sans rapport. `pre-commit run --all-files` rejoue en plus les contrôles de fin de fichier et d'espaces.

**Typage** : aucun outil ne le vérifie (voir « Typage » dans `CLAUDE.md`). Lire le code ajouté ou modifié : une fonction ou méthode sans paramètres ou retour typés, un nouveau `typing.Dict/List/Optional`, un `# pyright: ignore` sans règle précise sont à signaler (⚠️, non bloquant). Les tests et migrations sont exclus.

### 7. Tests

Faire cette étape **en dernier** pour tester l'état final (après rebase et migrations).

```bash
pytest -n auto --reuse-db
```

Suite complète en local (environ 35 s, 2 minutes sans `-n auto`). Si l'étape 2 a trouvé ou ajouté des migrations, ou si le rebase en a apporté, utiliser `--create-db` à la place de `--reuse-db` pour ne pas tester un schéma périmé. Pour un périmètre réduit : `pytest -- gardeniq/<app>/tests` ; l'écrire dans le bilan. Échec : donner le test et l'erreur, ne pas conclure sans les avoir lus (un test instable se relance, un échec reproductible est à traiter).

### 8. Hygiène des commits

```bash
git log origin/<cible>..HEAD --format='%h %s'
git diff --name-only origin/<cible>...HEAD
```

- Chaque titre suit `(TK-<id>)(<type>) - <module>: <Description>`, en anglais, avec le ticket de la branche ajouté par le hook local. Le type est celui de la branche, ou un type explicite valide (par exemple `docs` pour de la documentation). Un préfixe absent, doublé ou avec un autre ticket indique un hook inactif ou ancien : le signaler.
- Pas de commit `fixup`, `WIP`, ni de fichier personnel ou sensible dans le diff : `.env`, `db.sqlite3`, `CLAUDE.local.md`, `.claude/settings.local.json`, secret.
- Un fichier de migration généré fait partie du même commit que le changement de modèle.
- Les commits sont conservés sur la branche et **squashés au merge de la PR** : le titre de la PR devient le message sur `main`. Ne pas les squasher avant.

### 9. Bilan

Un tableau, dans le chat, en français :

| Point | Statut | Détail |
|---|---|---|
| Rebase sur `<cible>` | ✅ / ⚠️ / ❌ / ➖ non concerné / ⏭️ non vérifié | … |
| Migrations | | |
| Traductions | | |
| Documentation | | |
| Logs | | |
| Lint | | |
| Typage | | |
| Tests | | commande, nombre de tests, périmètre |
| Commits | | |

Terminer par un verdict : **prêt à pousser**, **à corriger avant** (liste des ❌) ou **non vérifié** pour ce qui n'a pas pu être contrôlé. Les fichiers produits par les étapes (migrations, doc) se commitent avec le skill `commit`, un commit par changement logique. Les problèmes repérés hors du périmètre de la branche se notent dans `docs/backlog.md` plutôt que d'être corrigés ici. Puis, à la demande de l'utilisateur seulement : push et `pr-create`.

## À éviter

- Pousser, ou forcer un push, depuis ce skill.
- Rebaser une branche déjà poussée sans l'accord explicite de l'utilisateur.
- Modifier, supprimer ou renuméroter une migration déjà sur `main`, ou en écrire une à la main.
- Fusionner des migrations ou supprimer des fichiers sans confirmation.
- Générer des fichiers de traduction sans accord.
- Annoncer « tests OK » sans les avoir lancés, ou sur un périmètre réduit sans le dire.
- Annoncer « typage vérifié » : il n'y a pas de vérificateur automatique.
- Embarquer dans la branche des changements sans rapport avec elle.
- Contourner les hooks (`--no-verify`).
