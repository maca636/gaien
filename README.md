# 外苑エリア イベント・天気情報

神宮外苑エリア4施設のイベントと天気をまとめた静的ダッシュボード。

公開URL: https://maca636.github.io/gaien/

## 仕組み

- **天気** … ブラウザから [Open-Meteo](https://open-meteo.com/) を直接取得。開いた時＋1時間ごとに自動更新。
- **イベント** … `events.json` を読み込んで表示するだけ。ページ自体は完全に静的。
- `events.json` は毎朝、スケジュール実行の Claude Code エージェント（クラウド）が
  Web検索で4施設の当日イベントを確認して更新・commit する。
  ルーティン: https://claude.ai/code/routines

## events.json の形式

```json
{
  "jingu":     { "name": "イベント名（無ければ空文字）", "time": "18:00 試合開始（開場16:00）" },
  "kokuritsu": { "name": "", "time": "" },
  "rugby":     { "name": "", "time": "" },
  "hall":      { "name": "", "time": "" },
  "alert":     "混雑注意などの一言（無ければ空文字）",
  "updated":   "2026-09-10T05:30:00+09:00"
}
```

- `name` が空文字 / `なし` / `イベントなし` の場合は「本日のイベントはありません」と表示。
- `time` は `HH:MM` を含めると大きく表示。`開場HH:MM` を含めると開場時刻も表示。

## 対象施設

| キー | 施設 | 公式イベントページ |
|---|---|---|
| `jingu` | 明治神宮野球場 | https://www.jingu-stadium.com/event/ |
| `kokuritsu` | 国立競技場（MUFGスタジアム） | https://jns-e.com/event/ |
| `rugby` | 秩父宮ラグビー場 | https://www.jpnsport.go.jp/chichibunomiya/event/tabid/59/Default.aspx |
| `hall` | 日本青年館ホール | https://seinenkan-hall.com/category/performance |

神宮球場の大学野球（東京六大学・東都）は球場サイトに載らないため、各リーグの公式サイトも確認すること。
