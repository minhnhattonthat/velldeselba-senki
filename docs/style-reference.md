# Style reference

From the pilot (G10_00 #88-#198, the Nades Island opening, `work/tl/pilot.out.tsv`). **Approved by the user
2026-10-23** (screens in work/qa/pilot), names included. Register is mixed by character (D8); sound effects are
translated (D9).

## Voices
| Character | JP cues | English voice |
|---|---|---|
| Player (`<F62>`) | オレ, だぜ, さあな, rough casual | Laid-back, wry, short: "Beats me.", "Say what?", "Oh, boy..." Contractions, mild slang, no swearing beyond "damn" |
| Kafi (Lieutenant Colonel) | わ / よ / のね, feminine, warm but firm | Direct, caring, a little teasing: "You're so carefree." "Oh, fine." Never stiff military-speak with the player |
| Colonel Zexel | たまえ, かね, わが軍 | Polished, paternal, faintly sinister: "Is the airship to your liking?" "Do your best for Noipask." |
| Commander Odenaude | ふん, へたくそめ, だまれ | Gruff, contemptuous, short: "Hmph.", "Clumsy oaf.", "Silence!" |
| Oyu Kikuru (Corporal) | ですよ, 〜しましょうよ, bubbly | Cheerful, eager, exclamation marks, a crush on the player: "Let's do it!", "n-no, it's nothing..." |
| Hauezna (Private) | いたします, formal | Polite, formal, "sir": "From now on, we will be accompanying you, sir." |
| Soldiers, townsfolk | だぜ / な | Plain, blunt: "Hey, what were you dawdling for?" |

## Rules learned
- Speaker label row, then running text; `tools/batches.py` wraps the rows. Keep a page to about 3 rows.
- 少尉 in address -> "Lieutenant"; with the name -> "Lieutenant <F62>".
- ……/…… alone -> "..." ; ………… alone -> "......" (a long silence).
- Game-help pages in colour (`<P13>`/`<P07>`) stay instructional and plain: "Hold the Square button while walking
  to move faster."
- Interjections: へー -> "Huh!", うえっ -> "Bleh!", ゴクッ -> "Gulp." (D9), いてててて -> "Ow ow ow ow..."

## Example pairs
- カフィ中佐：迷ってるのね。無理もないか。 -> "You're torn. Can't say I blame you."
- オデナウデ長官：ふん、あれで慣れたつもりか。へたくそめ。 -> "Hmph. You call that getting used to it? Clumsy oaf."
- <F62>：まいったよ。軍に入れだとさ。 -> "Unbelievable. They want me to join the army."
- Corrected: #116 was first given Odenaude's label; the JP speaker is ゼクセル大佐. Always copy the speaker from the
  JP label, never infer it from who is addressed.
