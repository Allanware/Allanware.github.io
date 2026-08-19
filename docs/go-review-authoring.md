# Authoring a Go review

How to get from a finished game to a published review with live boards. Read
once, then use the checklists.

Shortcut names below are the Sabaki **menu item** first, accelerator second.
On macOS most accelerators are ⌘, not Ctrl — trust the menu, not this file.
Verified against Sabaki **v0.60.2**; use that version, because it is the one
that opens legacy-encoded SGFs (GB18030/Big5/Shift-JIS with no `CA[]`), which
is exactly what Fox exports.

---

## 0. The shape of a review

One record, two or three boards, each at a moment where the game could have
gone another way.

```markdown
## 引言              — date, result, and the questions this piece answers
## 谜团1：左上的攻防   {{< go-board … move="35"  … >}}   + prose
## 谜团2：右上的突破   {{< go-board … move="117" … >}}   + prose
## 最后              — numbered mechanical summary, then the human outro
```

Do not start at move 1. Open where the trouble starts.

**The prose split is the thing to get right:**

| Surface | Carries |
|---|---|
| **Markdown**, above the board | The decision. What the position asks, what A and B *are*, what you feared. |
| **SGF `C[]`**, on nodes inside a branch | The sequence. One short line per move: what it does, why it works. |
| SGF `C[]` on mainline nodes | **Nothing.** The Markdown above already said it. |

So the reader reads your argument, presses `A`, and steps through the
refutation with your voice arriving move by move. Roughly 10–30 short
comments per review, not 165.

---

## Part A — Sabaki

### Get a clean record

1. **Export the SGF from the Fox desktop client.** The mobile app has no direct
   export. Write down the exact button and output folder the first time; it is
   documented nowhere.
2. **Open it in Sabaki** (File → Open, `Ctrl+O`). Never open an SGF in a text
   editor — see [Escaping](#escaping).
3. **File → Game Info (`Ctrl+I`) — fix Komi first.** Fox writes integer komi
   (`KM[375]` for 7.5), which makes KataGo reject the position. The viewer does
   not care, but a wrong komi poisons any engine numbers you generate next.
4. **File → Save As (`Ctrl+Shift+S`)** straight into
   `content/blog/<slug>/`, named per [Naming the record](#naming-the-record).
   This one save normalises the file to UTF-8 with `CA[UTF-8]` and no BOM.

### If you run an engine, clean up after it

5. Attach KataGo and toggle analysis (`F4`). Walk the game. **Turn it off when
   done** — every node visited while it runs gets `SBKV`/`SBKS` stamped on it.
6. **Tools → Clean Markup…** → tick **Analysis data**, **Arrow/Line markers**,
   and **Annotations** → **From Entire Game**.
   🚨 **Do not tick "Comments"** — that deletes your `C` notes.

### Write the commentary

7. **View → Show Comments (`Ctrl+Shift+T`)** for the sidebar;
   **Edit → Edit Mode (`Ctrl+E`)** to type. Step with `↓`/`↑`.
   `Ctrl+Shift+↑/↓` jumps between commented nodes.
8. **Comment the branch nodes, not the mainline.** Walk into each variation and
   give every node one line. Leave mainline nodes bare.
   - Type into the **Comment** (注释) textarea.
   - 🚨 **Never the Title field.** Title writes `N[]`, which the viewer has no
     case for. Anything you put there is **invisible on the blog.**
   - **Plain text only.** Sabaki previews Markdown; the site publishes
     `textContent`. `**重要**` ships as literal asterisks. Newlines do survive
     and render.
   - `Ctrl+click` a board point to append its coordinate into the comment.
9. **Marks** — `Ctrl+3` triangle, `Ctrl+5` circle, `Ctrl+4` square, `Ctrl+2`
   cross, `Ctrl+8` letter label, `Ctrl+9` number label. Click the same mark
   again to remove it.
   - **One mark per intersection.** `CR[dd]` plus `LB[dd:10]` renders only the
     label.
   - Skip `Ctrl+6` Line and `Ctrl+7` Arrow — the viewer drops both.
   - `SL` (selection) has no tool; it needs Tools → Edit SGF Properties → Add.
10. **Branches** — leave edit mode (`Ctrl+E`), navigate to the fork, play the
    alternative. It appends as the **last** child.
    ⚠️ Left-clicking the current move's own stone **deletes that node.**
11. 🚨 **Fix child order — this is what publishes as A/B.** Open the game tree
    (`Ctrl+T`), stand in the branch you want first, and use
    **Make Main Variation** (`Ctrl+Alt+Shift+←`) or nudge with
    `Ctrl+Shift+←/→`. There is no other input: **A = child 1, B = child 2.**
    Note the collision — plain `Shift+←/→` *navigates*, but
    `Ctrl+Shift+←/→` *mutates order*. One stray keystroke silently swaps A and
    B, and your prose then points at the wrong branch. Nothing catches this.
12. **Click out of the textarea before saving.** Keystrokes debounce into the
    tree after 500 ms and flush on blur. Then `Ctrl+S`.

### Pick the board start positions

13. With the tree in front of you, for each section:
    - a **mainline** position → `move="<n>"`
    - a position **inside a sibling branch** → `path="N<k>B<i>"`

    Verify every number with **Go to Move Number** (`Ctrl+G`). Two gotchas:
    - **`move=` silently follows child 1 past every fork**, so it can only ever
      land on the mainline. To point into a sibling branch you *must* use `path=`.
    - For a clean record **`N<k>` == move `k`**, which is why `path="N64B2"`
      reads as "the second continuation after move 64". That equality **breaks**
      as soon as a non-move node enters the mainline — notably a Stone-tool edit
      on a node that already has a move, which appends a `PL[]`+`AB`/`AW` node
      carrying no `B`/`W`.

### Escaping

Type Chinese, brackets, backslashes and newlines freely **in Sabaki** — it
escapes them correctly and this site's parser un-escapes them correctly,
including strings like `此时 [A] 位是关键点。`

**Never hand-edit `C[…]` in a text editor.** One unescaped `]` throws
`Missing property ID` and kills the **entire board** with a "无法读取棋谱。"
error, not just that one comment.

### What the viewer silently drops

`N` (Title), `AR`, `LN`, `SBKV`, `SBKS`, `HO`, `MN`, `VW`, `DD`, `TB`/`TW`,
`PL`, and every judgement property — `TE`/`BM`/`IT`/`DO`/`GB`/`GW`/`DM`/`UC`.

So Sabaki's **Good Move** / **Bad Move** buttons have *no visible effect.* Put
the verdict in the prose: 妙手 / 问题手 / 败着. Root game info (`PB`, `PW`,
`KM`, `RE`) is parsed and then never printed, so it is invisible too — if you
want the result on the page, write it in the 引言.

Supported: moves `B`/`W`, setup `AB`/`AW`/`AE`, marks `CR`/`TR`/`SQ`/`MA`/
`LB`/`SL`, and `C` comments.

---

## Part B — Writing the post

### Naming the record

The language suffix is part of the filename, same convention as images.

| Post | File on disk | `src=` in the shortcode |
|---|---|---|
| **Chinese-only** (the default) | `game.zh.sgf` | `"game.zh.sgf"` |
| English-only | `game.sgf` | `"game.sgf"` |
| Paired, one shared commentary | `game.sgf` | `"game.sgf"` on both pages |

🚨 **A Chinese-only post whose record is named plainly `game.sgf` is a hard
build failure** — the default language is English, so the unsuffixed resource
is assigned to an English page that does not exist. Name it `.zh.sgf`.

🚨 **Never use an `.en.` suffix.** A bundle holding both `game.sgf` and
`game.en.sgf` silently shadows the plain file and never publishes it, with no
diagnostic at all.

Paired posts with *two different* commentaries (`game.sgf` + `game.zh.sgf`,
both pages writing `src="game.sgf"`) work in Hugo but have **no safety net**:
if the zh record is missing, the build succeeds silently and the English page
serves the Chinese commentary. Don't do this until the guard test exists.

### The shortcode

```markdown
{{< go-board src="game.zh.sgf" move="35" caption="白36挂角时的局面。" >}}
```

`src` and `caption` are required and the caption may not be empty. `move` and
`path` are mutually exclusive; with neither, the board opens at move 0.

### What the reader gets

One control row under the board, then the commentary:

```
  ◀    第 35 手    ▶     A  B     试走变化
  ────────────────────────────────────────
  黑棋此手守角偏缓。若改走 A 位尖顶…
```

- `◀ ▶` step one node. `A`/`B` appear only at a fork.
- **试走变化** opens a coordinate box: type `D4`, press Enter. Clicking the
  board works too. Press it again (撤销试走) to throw the tried moves away and
  drop the reader back on the position they started trying from — *not* the
  caption's position, so they keep their place in a long variation.
- With focus on the board, `←`/`→` step, `Home` jumps back to the caption's
  position, `End` runs to the end of the current line.
- Tried moves are local and ephemeral. Nothing is saved, nothing is shared.

---

## Style — 胡耀宇, adapted to a live board

Measured across 16 of his reviews (~110k characters, 286 diagrams).

**Rhythm.** ~200 Chinese characters per position, 3–6 sentences — which is
about one `C[]` comment. Between positions he uses a cliffhanger:
`事情可没那么简单：` / `我们先来看实战：` / `好戏开始上演：`. These land
*harder* here than in print, because the reader must actually press `▶`.

**Openings.** A narrative lede carrying date, event and result in one sentence,
then the hook, then a numbered list of the questions the article answers. Each
set-piece opens with his signed formula:
**`我们从{棋手}{黑/白}{手数}{动词}开始聊起`**.

**Markup is not decoration — it is what makes the prose legible:**

| Device | His frequency | Write it as |
|---|---|---|
| `A位` / `B位` on empty points | ~470 | `LB`, letters A–G |
| `黑三角大龙` / `白圆圈四子` — naming a group | 757 | `TR`/`CR`/`SQ` on arbitrary stone sets, reassigned per node |
| `圆圈标识处4目` — counting territory | 23 | same glyphs on empty points |
| `左上` / `右下角` / `中央` | 583 | prose only — no cropping, no coordinates |

**Label rules, measured:**

1. **1–2 ASCII characters. Never CJK.** The renderer sizes 1 char at 72 units
   and 2 at 56, and **silently corrupts anything ≥4 chars** to `"12…"`. `黑1`
   passes the length check but two 56-unit CJK glyphs overflow the 88-unit cell
   into its neighbours. Use `A`, `B`, `1`, `2`.
2. **Never label the immediate child point of a fork.** An authored label there
   *suppresses that child's automatic A/B letter* and recolors itself dark red.
   The label and the variation affordance fight over the same point.

**Three of his devices do not port — drop them:**

- **`见图N` / `接图5` / `图14中的白8`** (37 in the corpus). There are no
  figures. Replace with a temporal reference (`就是刚才挖那一路变化`) or,
  better, an actual steppable branch. His closing summary is *built* out of
  `（见图11）（见图14）`, so write the coda as pure conditionals over letters.
- **`白4=A` / `A位有颗黑子`** (24 sub-captions). These exist only because a
  static picture cannot replay a ko or show a lifted stone. The board just
  plays it. Pure deletion.
- **`黑1` / `黑3` local renumbering inside a variation.** Entering a variation
  does **not** reset the counter, so `黑1` in your prose and `192` in the
  counter contradict each other on screen. Write `此时黑若挖` / `黑先靠一下`
  and let the board show it.

**The move counter is your referent.** With no numbers on the stones, `黑189虎`
resolves only because the counter reads 189 and the last stone is marked.
Prefer `此手` / `这步棋` for the move just played — he alternates freely, so
this is in-style, not a compromise.

**What he cannot do and you can.** Try mode lets you write
`先别看下面，你猜黑棋下一手在哪？试着摆一下再往下走。` Use it where he writes
`在这里我敲个黑板`.

**Scope warning.** His hypothetical-to-actual diagram ratio is **2–3 : 1**. If
you write in his proportions, the A/B chips are the hot path, not `◀ ▶`.

---

## Before publishing

```sh
# in the post bundle
grep -c 'SBKV\[\|SBKS\[\|AR\[\|LN\['  content/blog/<slug>/*.sgf   # expect 0
grep -o  'B\[\]\|W\[\]'               content/blog/<slug>/*.sgf   # stray passes
grep -c  'C\['                        content/blog/<slug>/*.sgf   # comments saved?
grep -o  'N\['                        content/blog/<slug>/*.sgf   # prose stranded in Title

# the suite
python3 scripts/validate_interaction_ids.py content
python3 -m unittest discover -s tests -p 'test_*.py'
node --test tests/*.test.mjs
hugo --gc --minify --panicOnWarning --noBuildLock --cleanDestinationDir \
  --printI18nWarnings --printPathWarnings --baseURL https://example.org/
python3 scripts/check_site.py public --base-url https://example.org/
```

Note that **`.sgf` bodies are never linted** — `check_site.py` reads only HTML
and XML. Nothing validates comment content, mark placement, or branch order.
Step 11 and the eyeball pass below are the only checks on those.

Then `hugo server -D` and read the post in the browser:

- [ ] Every board loads and opens at the position the caption claims.
- [ ] **A and B point at what the prose says they point at.**
- [ ] Commentary appears on every branch node and updates as you step.
- [ ] Marks are legible; no label overflows into a neighbouring point.
- [ ] Try: step a few moves in, play a point, then return — you land back where
      you started trying, with the tried stones gone.
- [ ] Set `draft = false` and confirm `interactionId` is unchanged.

---

## Review #1

The record is `2026-7-26_pro.sgf` (`PB[Wenxuan] PW[Bill Lin]`), 165 moves.

**Prep, in this order:**

1. **Delete the stray pass.** The record opens `;B[pd];W[];B[dp]` — a White
   pass as move 2. It counts, so every number below already accounts for its
   removal. Re-derive every selector with `Ctrl+G` afterwards.
2. **Resolve the four stub branches** at forks 41, 94 and 117 — the `+0`/`+1`
   children. They would render as A/B chips with nothing behind them. Flesh
   them out or delete them.
3. **Strip the 160 `SBKV`/`SBKS` pairs** (~3.5 KB) via step 6.
4. The record has **zero comments and zero marks** today. All greenfield.

**Two set-pieces:**

| Section | Entry | Why |
|---|---|---|
| 谜团1：左上的攻防 | `move="35"` | Forks at 35 and 41, captures at 37, 43, 55 — a whole fight in a 20-move window |
| 谜团2：右上的突破 | `move="117"` | The fork at 121 has a **25-move branch**, the richest variation in the record and a ready-made 参考图 chain |

The endgame (fork 158, captures 161/163) goes unremarked — as he routinely does.

🚨 **Leave `2026-7-26.sgf` on disk, unmodified.** The README's `path="N64B2"`
example is pinned against *that* file, and two test suites resolve it from
disk. It need not be referenced by any shortcode.
