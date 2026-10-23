---
name: pr-create
description: Génère une synthèse de pull request en français à partir des commits de la branche courante non encore présents dans `main` (regroupés par module), puis crée la pull request sur GitHub avec label de type et assignation à l'auteur. Gère aussi la fusion d'une PR ouverte (squash, suppression de la branche). Utiliser quand l'utilisateur demande "fais une synthèse de MR", "pr-create", "crée la MR", "crée la PR", "ouvre la pull request", une préparation de PR, ou "merge la PR", "fusionne la PR", "pr-create merge".
---

# pr-create

Génère la synthèse d'une pull request (PR) à partir des commits de la branche courante, puis crée la PR sur GitHub (via `gh`) avec label de type et assignation à l'auteur. Peut aussi la fusionner.

## Paramètres acceptés

- `pr-create` → tous les commits de la branche courante absents de `main`.
- `pr-create 10` → limite aux 10 derniers de ces commits.
- `pr-create --draft` → PR en brouillon (`--draft` de `gh`).
- `pr-create --target <branche>` → PR vers une autre branche que `main` (cas d'une PR empilée sur une PR non encore fusionnée : seule la diff du lot courant est relue).
- `pr-create merge` → fusionne la PR déjà ouverte pour la branche courante (voir « Fusion d'une PR existante »).

Les options se combinent.

## Prérequis

- `gh` installé et authentifié (`gh auth status`). S'il manque, arrêter et le dire, en renvoyant vers `docs/runbooks/installer-gh.md` (macOS, Linux, Windows) ; l'authentification `gh auth login` est à lancer par l'utilisateur, par exemple avec `! gh auth login`. Ne pas contourner par l'API ou `curl`.
- Ne pas être sur la branche cible (pas de PR d'une branche vers elle-même) : sinon arrêter et prévenir l'utilisateur.
- Les commits sont déjà faits (skill `commit`). Si la checklist avant push n'a pas été passée (skill `pre-push`), le proposer sans l'imposer.

## Procédé exact

### 0. Vérifications préalables

```bash
git branch --show-current
git status --short
gh repo view --json defaultBranchRef -q .defaultBranchRef.name
git fetch origin
```

La branche cible est `--target` si fourni, sinon la branche par défaut retournée (`main`). Si la branche courante lui est égale, arrêter. Des modifications non commitées : le signaler, elles ne feront pas partie de la PR.

### 1. Récupérer les commits de la branche

Tous les commits présents sur la branche courante mais absents de la cible (`origin/<cible>..<branche>`), pas un nombre fixe :

```bash
git log origin/<cible>..<branche> --oneline
git log origin/<cible>..<branche> --stat
```

Si un `<N>` est passé, l'ajouter (`-n <N>`). Aucun commit : arrêter et le dire. Si la branche est en retard sur la cible, le signaler (rebase sur `main` avant de pousser, à la demande de l'utilisateur).

### 2. Comprendre le changement pour donner du contexte au relecteur

Lire le diff réel, pas seulement les messages de commit :

```bash
git log origin/<cible>..<branche> -p
```

Rédiger un court paragraphe de contexte (2 à 4 phrases, en français, sans remplissage) : le problème ou besoin, l'approche technique, la zone concernée. Section **obligatoire**, même pour un seul commit : elle oriente la revue, elle ne répète pas les messages de commit.

### 3. Regrouper les commits par module

Format de commit : `(TK-<id>)(<type>) - <module>: <Description>` (voir `CLAUDE.md`). Les commits ont en général le type de la branche, sauf ceux qui portent un type explicite (par exemple `docs`) : le regroupement se fait par **module**, en indiquant le type entre parenthèses quand il diffère de celui de la branche (`base`, `hardware`, `orderlg`, `telemetry`, `users`, `settings`, `ci`, `docker`, `deps`, `hooks`, `claude`), lu après le ` - `. Un commit sans module reconnu (ancien format, revert, merge) va dans « Autres ». Aucun commit ne reste non classé.

### 4. Extraire le ticket et le type de la branche

Branche `(TK-<id>)(<type>)-<slug>` (ex. `(TK-61)(feat)-Optimise-remove-and-add-models`) → ticket `TK-61`, type `feat`. Sans `(TK-<id>)`, ne pas écrire de ligne « Réf. ticket » et utiliser le nom de branche dans le titre. Sans `(<type>)`, ne pas poser de label de type et le dire.

`TK-<id>` est l'`Id carte` du ticket dans le kanban Notion. Si le MCP Notion est connecté, lire le ticket (skill `ticket`, étape 1) pour reprendre son titre et ses critères d'acceptation dans le « Contexte » et les « Vérifications » de la synthèse, et récupérer son URL. Ticket introuvable ou MCP absent : le dire et continuer avec la branche seule, sans inventer de contenu.

Label de type d'après le type de la branche (insensible à la casse) :

| Type de branche | Label GitHub | Couleur |
|---|---|---|
| `feat`, `feature` | `feature` | `428BCA` |
| `fix`, `bugfix` | `bug` | `D9534F` |
| `enh`, `update` | `enhancement` | `5BC0DE` |
| `refactor` | `refactor` | `8E44AD` |
| `docs` | `documentation` | `17A2B8` |
| `test` | `test` | `FFC107` |
| `chore` | `chore` | `AAAAAA` |

**Label de statut** (labels existants du dépôt, vérifiés avec `gh label list`) : `ready to review` par défaut, `work in progress` avec `--draft`. À la fusion, la PR relue passe à `ready to merge` (voir « Fusion d'une PR existante »). Ne jamais créer ces labels : ils existent.

Type absent de ce tableau : ne pas inventer de label. Proposer à l'utilisateur, au cas par cas, un nom et une couleur, et attendre son accord ; s'il valide, l'ajouter au tableau ci-dessus pour les prochaines fois.

### 5. Générer le markdown de la description (en français)

```markdown
# 🚀 Synthèse : <branche>

**Réf. ticket :** TK-<id> ([Notion](<url du ticket>))

### 🧭 Contexte
<paragraphe de l'étape 2>

### 📦 <module> (<n> commits)
- <description du commit> (+<ajouts>/-<suppressions> lignes)

### ✅ Vérifications
<ce qui a réellement été exécuté ou contrôlé, et ce qui ne l'a PAS été>

### 📁 Top fichiers modifiés
1. <fichier> (+<ajouts>/-<suppressions>)
```

Une section par module présent, sans section vide. « Contexte » et « Vérifications » restent toujours présentes. **Ne pas affirmer qu'une vérification a eu lieu si elle n'a pas été faite** : dire explicitement ce qui n'a pas été testé. La CI (black, isort, flake8, pytest) tourne à chaque push : citer son résultat seulement s'il a été lu (`gh pr checks`).

Aucun fichier n'est écrit dans le repo : la description part directement dans la commande de l'étape 8 (`--body-file -`). Si l'utilisateur veut en garder une copie, la proposer dans le chat.

### 6. Titre et assigné

- **Titre :** `(TK-<id>)(<type>) <description>` : la description est le slug de branche après le préfixe, tirets/underscores → espaces. Exemple : `(TK-61)(feat) Optimise remove and add models`. C'est ce titre qui deviendra le message sur `main` (GitHub ajoute ` (#<n>)` au squash) : le relire. Sans ticket, utiliser le nom de branche.
- **Assigné :** l'auteur de la PR, `--assignee @me`, jamais un nom en dur.
- **Reviewer :** toujours demander à l'utilisateur qui doit relire (un ou plusieurs logins GitHub, ou personne). Ne jamais en choisir un, ni en déduire un de l'historique. Sans réponse, ne pas poser de reviewer.

### 7. Récapituler avant de pousser

Cette étape pousse la branche sur `origin` et crée un objet visible par l'équipe. Afficher dans le chat :

```
Titre       : <titre>
<branche> → <cible>
Labels      : <label de type>, <label de statut>
Assigné à   : @me
Reviewer    : <login(s) donné(s) par l'utilisateur, ou aucun>
Brouillon   : <oui/non>
Commits     : <n>
```

Puis attendre la confirmation explicite de l'utilisateur, sauf s'il a déjà demandé explicitement de pousser et de créer la PR dans le même message. Ne jamais utiliser `git push --force` ni `-f`.

### 8. Pousser et créer la pull request

Labels : `gh label list`. Un label du tableau de l'étape 4 absent du dépôt est créé avec la couleur du tableau (un label hors tableau demande l'accord de l'utilisateur, voir l'étape 4) :

```bash
gh label create "<label>" --color "<couleur>" --description "<type>"
```

Puis :

```bash
git push --set-upstream origin <branche>
gh pr create \
  --base <cible> \
  --head <branche> \
  --title "<titre>" \
  --body-file - \
  --label "<label de type>,<label de statut>" \
  --assignee @me \
  [--reviewer "<login>[,<login>]"] \
  [--draft] <<'PR_BODY'
<markdown de l'étape 5>
PR_BODY
```

Si une PR existe déjà pour la branche (`gh pr view` la trouve), ne pas en créer une seconde : proposer de mettre à jour son titre et sa description (`gh pr edit`).

### 9. Livrer

Afficher la synthèse dans le chat, puis l'URL retournée :

```
🚀 PR créée : <URL>
```

La CI démarre au push : `gh pr checks` donne son état. Ne pas dire qu'elle est verte sans l'avoir lu.

**Notion.** Ne pas écrire le statut du ticket : l'intégration GitHub de Notion relie la PR (relation `Pull Requests GitHub`, le titre `(TK-<id>)(<type>) …` porte le numéro) et passe le ticket à `Code review & test` toute seule, quelques minutes après l'ouverture. Relire le ticket (skill `ticket`, étape 6) : s'il est conforme, le dire ; s'il ne l'est pas après un délai raisonnable, le signaler et proposer la transition, à confirmer. Ne jamais renseigner la relation à la main.

## Fusion d'une PR existante (`pr-create merge`)

Action séparée, demandée plus tard une fois la PR relue. Ne s'exécute jamais automatiquement après la création.

### a. Retrouver la PR de la branche courante

```bash
git branch --show-current
gh pr view --json number,title,state,isDraft,mergeable,baseRefName,headRefName
gh pr checks
```

Aucune PR ouverte : arrêter et prévenir. PR en brouillon, non fusionnable (`CONFLICTING`) ou CI en échec : le dire et ne pas fusionner sans demande explicite.

### b. Confirmer avant de fusionner

Action visible par toute l'équipe et difficile à annuler : afficher le récapitulatif et attendre une confirmation explicite (garde-fou de `CLAUDE.md`).

```
PR          : <titre> (#<n>)
<branche> → <cible>
CI          : <état lu>
Label       : ready to review → ready to merge
Message sur <cible> : <titre> (#<n>)
Suppression de la branche source : oui
```

### c. Fusionner

Avant la fusion, passer le label de statut à `ready to merge` :

```bash
gh pr edit <n> --remove-label "ready to review" --add-label "ready to merge"
```

Puis :

```bash
gh pr merge <n> --squash --delete-branch
```

Le squash est systématique (politique d'équipe) : le titre de la PR devient le message du commit sur `main`, avec le suffixe ` (#<n>)` ajouté par GitHub. Ne pas ajouter `--admin` ni `--rebase` sans demande explicite. `--delete-branch` supprime la branche distante et la branche locale.

### d. Vérifier et livrer

```bash
gh pr view <n> --json state,mergeCommit
git fetch origin
git log origin/<cible> -1 --format=%s
```

Le titre du dernier commit de `<cible>` doit être `<titre> (#<n>)`. Sinon, le dire.

```
✅ PR #<n> fusionnée dans <cible>
```

Proposer `git switch <cible> && git pull` ; ne pas le faire sans demande.

**Notion.** Après la fusion, relire le ticket au bout de quelques minutes (skill `ticket`, étape 6) : si l'intégration l'a passé à `Fait`, le dire ; sinon proposer la transition une fois la fusion vérifiée, à confirmer. Noter dans le skill `ticket` ce qui a été observé (statut intermédiaire `À merge`, délai). Si les entrées du backlog liées à ce ticket sont corrigées par la PR, le dire pour qu'elles passent à `Traité`.

## À éviter

- Créer ou fusionner sans confirmation.
- `git push --force`, `-f`.
- Inventer un numéro de ticket, un label ou un résultat de CI.
- Créer une seconde PR pour une branche qui en a déjà une.
- Fusionner une PR en brouillon, en conflit ou dont la CI échoue, sans demande explicite.
