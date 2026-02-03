# CSV Keywords Support - ListingBuilderPro

**Data:** 2026-01-20
**Wersja:** 3.1

## Obsługiwane formaty

### Helium 10 (Cerebro, Magnet)
```csv
Keyword,Search Volume,Cerebro IQ Score
wireless earbuds,450000,8
bluetooth earbuds,320000,7
noise cancelling earbuds,180000,9
```

### Jungle Scout (Keyword Scout)
```csv
Keyword,Exact Volume,Broad Volume,Trend
wireless earbuds,450000,890000,stable
bluetooth earbuds,320000,650000,up
```

### Data Dive
```csv
Phrase,Search Volume,Competition
wireless earbuds,450000,high
bluetooth earbuds,320000,medium
```

## Jak używać

1. **Eksportuj CSV** z Helium 10, Jungle Scout lub Data Dive
2. **Skopiuj całą tabelę** (Ctrl+C / Cmd+C)
3. **Wklej do pola "Słowa kluczowe"** w ListingBuilderPro
4. Kliknij **Generate Listings**

## Co robi system automatycznie

- Wykrywa format CSV (przecinki lub tabulatory)
- Rozpoznaje nagłówki (Keyword, Search Volume, Phrase, itp.)
- Pomija wiersz nagłówka
- Wyciąga TYLKO słowa kluczowe (pierwsza kolumna)
- Usuwa duplikaty
- Usuwa cudzysłowy z CSV

## Obsługiwane separatory

| Separator | Przykład |
|-----------|----------|
| Przecinek | `keyword,volume,score` |
| Tabulator | `keyword\tvolume\tscore` |

## Rozpoznawane nagłówki

System automatycznie pomija wiersz jeśli zawiera:
- `keyword`
- `search volume`
- `phrase`
- `cerebro`
- `exact`
- `broad`

## Przykład działania

**Input (CSV z Helium 10):**
```
Keyword,Search Volume,Cerebro IQ Score
wireless earbuds,450000,8
bluetooth earbuds,320000,7
noise cancelling earbuds,180000,9
earbuds with microphone,95000,6
```

**Output (przetworzone keywords):**
```
wireless earbuds
bluetooth earbuds
noise cancelling earbuds
earbuds with microphone
```

## Alternatywny format

Możesz też wpisać ręcznie - jedno słowo kluczowe na linię:
```
wireless earbuds
bluetooth earbuds
noise cancelling earbuds
```

## Limity

- Max 200 znaków na keyword
- Zalecane: 50-100 keywords dla najlepszych rezultatów
- Najważniejsze keywords na górze listy

## Kod parsera

```javascript
function parseKeywords(text) {
    const lines = text.trim().split('\n').map(line => line.trim()).filter(line => line.length > 0);
    if (lines.length === 0) return [];

    const firstLine = lines[0].toLowerCase();
    const isCSV = firstLine.includes(',') || firstLine.includes('\t');
    const hasHeader = firstLine.includes('keyword') || firstLine.includes('search volume') ||
                     firstLine.includes('phrase') || firstLine.includes('cerebro') ||
                     firstLine.includes('exact') || firstLine.includes('broad');

    let keywords = [];
    const startIndex = hasHeader ? 1 : 0;

    for (let i = startIndex; i < lines.length; i++) {
        let keyword = lines[i];

        if (isCSV) {
            const separator = lines[i].includes('\t') ? '\t' : ',';
            const parts = lines[i].split(separator);
            keyword = parts[0].trim().replace(/^["']|["']$/g, '');
        }

        if (keyword.length > 0 && keyword.length < 200) {
            keywords.push(keyword);
        }
    }

    return [...new Set(keywords)]; // Remove duplicates
}
```

## URL

**Produkcja:** https://listing.automatyzacja-ai.pl
