# claude-chat-bar

Une status line pour [Claude Code](https://code.claude.com), avec un chat de compagnie qui réagit à ce qui se passe dans la conversation.

```
(=^･ω･^=)⌨ Mochi tape au clavier · chat niv.2 (47 xp)
Opus 5.5 (high) │ ctx ▓▓▓▓░░░░░░ 42% │ $1.23 │ ⏱ 1h12
agents 2 actifs │ +156/−23 │ 5h ▓░░░░ 24% ↻18h33  7j ▓▓░░░ 41% ↻jeu. 04h53
```

## Ce qui est affiché

| Ligne | Information |
| - | - |
| 1 | Le chat : son humeur, son nom, son stade de croissance et son expérience |
| 2 | Modèle actif (et niveau d'effort), contexte utilisé, coût de la session, durée |
| 3 | Sous-agents en cours, lignes ajoutées/supprimées, limites d'usage 5 h et 7 jours avec l'heure de réinitialisation |

Les barres passent du vert au jaune puis au rouge à mesure qu'elles se remplissent.

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

Il gagne 1 xp par message envoyé et par outil utilisé, et grandit : chaton → chat (30 xp) → matou (120 xp) → chat légendaire (400 xp).

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
