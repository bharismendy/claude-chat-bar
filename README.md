# claude-chat-bar

Une status line pour [Claude Code](https://code.claude.com), avec un chat de compagnie qui réagit à ce qui se passe dans la conversation.

```
(=^･ω･^=)⌨ Mochi niv.2 tape au clavier │ Opus 5.5 (high) │ ctx ▓▓▓▓░░░░░░ 42% │ $1.23 │ ⏱ 1h12 │ agents 2 actifs │ +156/−23 │ 5h ▓░░░░ 24% ↻18h33  7j ▓▓░░░ 41% ↻jeu. 04h53
```

## Ce qui est affiché

Tout tient sur une ligne, de gauche à droite :

1. Le chat : son humeur, son nom et son niveau
2. Le modèle actif et son niveau d'effort
3. Le contexte utilisé
4. Le coût de la session
5. La durée de la session
6. Les sous-agents en cours
7. Les lignes ajoutées et supprimées
8. Les limites d'usage 5 h et 7 jours, avec l'heure de réinitialisation

Les barres passent du vert au jaune puis au rouge à mesure qu'elles se remplissent.

### Terminal étroit

Quand la ligne ne tient pas dans la largeur du terminal, les infos les moins utiles disparaissent dans cet ordre : durée, `agents 0`, lignes modifiées, limite 7 jours, coût, agents actifs, limite 5 h. Ensuite le chat perd sa légende, puis son nom ; le modèle et le contexte sont masqués en dernier. Une info masquée revient si elle tient dans la place libérée.

## Le chat

Son humeur suit la conversation, de la plus prioritaire à la moins prioritaire :

| Humeur | Quand |
| - | - |
| `(=ↀ﹏ↀ=)` a trop mangé de contexte | contexte ≥ 85 % |
| `(=～ω～=)` épuisé | quota 5 h ≥ 90 % |
| `(=ＴωＴ=)` oups | le dernier outil a renvoyé une erreur |
| `(=^･ω･^=)ﾉ` mène la meute | des sous-agents tournent |
| `(=-ω-=) zZ` dort | aucune activité depuis 5 min |
| `⌨` `📖` `✎` `⌕` | Claude lance une commande, lit, écrit ou cherche sur le web |
| `(=ºωº=)?` t'écoute | tu viens d'envoyer un message |
| `(=^▽^=)✧` fier | plus de 300 lignes ajoutées |
| `(=^･ω･^=)` ronronne | le reste du temps |

Il gagne 1 xp par message envoyé et par outil utilisé, et monte de niveau : niv.1 à 0 xp, niv.2 à 30 xp, niv.3 à 120 xp, niv.4 à 400 xp.

## Installation

Python 3 est requis, sans aucune dépendance.

```sh
git clone https://github.com/bharismendy/claude-chat-bar.git
cd claude-chat-bar
./install.sh
```

Le script est copié dans `~/.claude/claude-chat-bar/` et l'entrée suivante est ajoutée à `~/.claude/settings.json` (une sauvegarde `settings.json.bak` est faite avant) :

```json
{
  "statusLine": {
    "type": "command",
    "command": "python3 ~/.claude/claude-chat-bar/statusline.py",
    "refreshInterval": 2
  }
}
```

`refreshInterval` fait bouger le chat et met à jour le nombre d'agents même quand la session est inactive.

## Personnalisation

| Variable d'environnement | Effet |
| - | - |
| `CLAUDE_PET_NAME` | Nom du chat (`Mochi` par défaut) |
| `NO_COLOR` | Désactive les couleurs |

## Tester sans Claude Code

```sh
echo '{"model":{"display_name":"Opus"},"context_window":{"used_percentage":42},"cost":{"total_cost_usd":1.2}}' | ./statusline.py
```

## Désinstallation

Supprime l'entrée `statusLine` de `~/.claude/settings.json` et le dossier `~/.claude/claude-chat-bar/`.

## Licence

MIT
