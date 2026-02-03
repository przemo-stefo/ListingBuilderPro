// Groq Translate EU v3.14 - Bullet quality verification + retry
// Fixes: product_name mode, Jogi→Yoga, BULLET N: strip, PL name in descriptions
// Updated: 2026-02-03

const data = $input.first().json;
const listings = { ...data.listings };
const debugLog = [];

// 3 Groq API keys for rotation on rate limit
const GROQ_API_KEYS = [
  'gsk_REDACTED',  // Primary
  'gsk_REDACTED',  // Backup #1
  'gsk_REDACTED'   // Backup #2
];
let currentKeyIndex = 0;

const httpRequest = this.helpers.httpRequest.bind(this.helpers);
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

const DELAYS = { 
  between_translations: 2000,
  retry_base: 3000,
  between_marketplaces: 1500
};

const TITLE_LIMITS = {
  amazon: { min: 80, max: 200 },
  ebay: { min: 60, max: 80 },
  etsy: { min: 80, max: 140 },
  allegro: { min: 30, max: 50 }
};

const TITLE_PADDING = {
  DE: ['Premium-Qualität', 'Professionell', 'Hochwertig', 'Langlebig', 'Erstklassig'],
  FR: ['Haute Qualité', 'Premium', 'Professionnel', 'Durable', 'Excellence'],
  IT: ['Alta Qualità', 'Premium', 'Professionale', 'Durevole', 'Eccellente'],
  ES: ['Alta Calidad', 'Premium', 'Profesional', 'Duradero', 'Excelente'],
  NL: ['Hoogwaardige', 'Premium Kwaliteit', 'Professioneel', 'Duurzaam'],
  SV: ['Högkvalitativ', 'Premium', 'Professionell', 'Hållbar'],
  PL: ['Wysoka Jakość', 'Premium', 'Profesjonalny', 'Trwały', 'Doskonały'],
  EN: ['Premium Quality', 'Professional Grade', 'Heavy Duty', 'Durable', 'Multi-Purpose']
};

debugLog.push('=== Groq Translate EU v3.13 (title lang verify + retry) ===');
debugLog.push(`Available API keys: ${GROQ_API_KEYS.length}`);

function switchToNextKey() {
  if (currentKeyIndex < GROQ_API_KEYS.length - 1) {
    currentKeyIndex++;
    debugLog.push(`Switched to key #${currentKeyIndex + 1}`);
    return true;
  }
  debugLog.push('All keys exhausted!');
  return false;
}

async function translateWithGroq(text, targetLang, mode) {
  const langNames = { DE: 'German', PL: 'Polish', FR: 'French', IT: 'Italian', ES: 'Spanish', NL: 'Dutch', SV: 'Swedish', EN: 'English' };
  const langName = langNames[targetLang] || 'German';
  
  // Mode-aware system prompt: specialized for bullets and product names
  let systemMsg;
  if (mode === 'product_name') {
    systemMsg = `You are a professional e-commerce translator. Translate this product name from its original language to ${langName}. IMPORTANT RULES:
- This is a PRODUCT NAME for an online listing, not a person's name
- Translate ALL words including sport/activity terms (e.g., "Jogi"/"Yoga" → use the ${langName} word for Yoga)
- "Mata do Jogi" = "Yoga Mat" in English, "Yogamatte" in German
- "Antypoślizgowa" = "Anti-Slip"/"Non-Slip" in English, "Antirutsch"/"Rutschfest" in German
- Return ONLY the translated product name, nothing else`;
  } else if (mode === 'bullets') {
    systemMsg = `You are a translator. Translate each line below to ${langName}. RULES:
- Translate EACH line word-by-word to ${langName}
- Keep the SAME number of lines (one translated line per input line)
- Keep CAPS HEADER format (translate the header words too)
- Keep bullet markers (-, •, numbers)
- Do NOT add category labels, section headers, or framework structure
- Do NOT reorganize or regenerate content
- Return ONLY the translated lines`;
  } else {
    systemMsg = `You are a professional translator. Translate the user's text to ${langName}. Return ONLY the translated text. No explanations, no commentary, no instructions.`;
  }
  const userMsg = text;
  
  for (let attempt = 0; attempt < 6; attempt++) {
    try {
      const response = await httpRequest({
        method: 'POST',
        url: 'https://api.groq.com/openai/v1/chat/completions',
        headers: {
          'Authorization': `Bearer ${GROQ_API_KEYS[currentKeyIndex]}`,
          'Content-Type': 'application/json'
        },
        body: {
          model: 'llama-3.3-70b-versatile',
          messages: [
            { role: 'system', content: systemMsg },
            { role: 'user', content: userMsg }
          ],
          temperature: 0.3,
          max_tokens: 1500
        },
        json: true
      });
      
      if (response?.choices?.[0]) {
        let result = response.choices[0].message.content.trim();
        // Safety net: strip instruction echo if LLM repeated the prompt
        if (result.includes('\n\n')) {
          const parts = result.split('\n\n');
          const first = parts[0].toLowerCase();
          const echoWords = ['must', 'critical', 'translate', 'muss', 'kritisch', 'traduire', 'tradurre', 'traducir', 'przetłumacz', 'tylko'];
          if (echoWords.some(w => first.includes(w))) {
            result = parts.slice(1).join('\n\n').trim();
          }
        }
        // Strip "Translation:" prefixes in any language
        result = result.replace(/^(Translation|Übersetzung|Traduction|Traducción|Traduzione|Tłumaczenie)\s*:\s*/i, '');
        return result;
      }
      throw new Error('Invalid response');
    } catch (error) {
      const is429 = error.message.includes('429');
      
      if (is429) {
        debugLog.push(`Rate limited (key #${currentKeyIndex + 1})`);
        if (switchToNextKey()) {
          await sleep(1000);
          continue;
        }
      }
      
      if (attempt < 5) {
        await sleep(DELAYS.retry_base * (attempt + 1));
      } else {
        throw error;
      }
    }
  }
}

function fixPolishGrammar(text) {
  if (!text) return text;
  return text
    .replace(/\bz stali/gi, 'ze stali')
    .replace(/\bz szkła/gi, 'ze szkła')
    .replace(/\bz srebra/gi, 'ze srebra');
}

// Strip newlines and LLM explanation artifacts from titles
// Groq sometimes returns "X becomes Y" or "Since the text is already..." instead of clean translation
function cleanTitleArtifacts(title) {
  if (!title) return title;
  // Strip parenthetical LLM meta-comments: "(No translation needed)", "(Already in English)", etc.
  let clean = title.replace(/\s*\((No translation|Already|Note|Translation|Original)[^)]*\)/gi, '').trim();
  // Strip newlines — titles must be single-line
  if (clean.includes('\n')) {
    const lines = clean.split('\n')
      .map(l => l.trim())
      .filter(l => l.length > 5)
      .filter(l => !/^(becomes|since|here is|note:|translation:)/i.test(l));
    clean = (lines[0] || clean.split('\n')[0]).trim();
  }
  return clean;
}

function mergeBulletPairs(lines) {
  // Merge header+content split: short header line followed by long content paragraph
  // e.g. "**HEADER** - Subtitle" (58ch) + "Content paragraph..." (272ch) → merged
  const merged = [];
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    const nextLine = i + 1 < lines.length ? lines[i + 1].trim() : '';
    const isShort = line.length < 80;
    const nextIsLong = nextLine.length > 100;
    const lengthRatio = nextLine.length > 3 * line.length;
    const hasBoldMarkers = line.includes('**');
    if (isShort && nextIsLong && (lengthRatio || hasBoldMarkers)) {
      merged.push(line + ' ' + nextLine);
      i++;
    } else {
      merged.push(line);
    }
  }
  return merged;
}

function cleanBulletArtifacts(bullet) {
  if (!bullet) return bullet;
  // Remove "BULLET N:" or "**BULLET N:**" prefixes
  let clean = bullet.replace(/^\*?\*?\s*BULLET\s*\d+\s*:?\*?\*?\s*/i, '').trim();
  // Remove leading "N." or "N)" numbering if followed by content
  clean = clean.replace(/^\d+[.):]\s*/, '').trim();
  return clean || bullet;
}

function extendTitle(title, lang, minLen, maxLen) {
  let ext = title.trim();
  if (ext.length >= minLen) {
    return ext.length > maxLen ? ext.slice(0, maxLen - 3).trim() + '...' : ext;
  }
  const padding = TITLE_PADDING[lang] || TITLE_PADDING.DE;
  for (const word of padding) {
    if (ext.length >= minLen) break;
    if (!ext.toLowerCase().includes(word.toLowerCase())) ext += ' ' + word;
  }
  return ext.length > maxLen ? ext.slice(0, maxLen - 3).trim() + '...' : ext.trim();
}

async function translateListing(listing, targetLang, marketplace, originalData) {
  const baseMp = marketplace.startsWith('amazon') ? 'amazon' : marketplace;
  const limits = TITLE_LIMITS[baseMp] || TITLE_LIMITS.amazon;
  
  let translatedTitle, translatedBullets, translatedDesc;
  let usedFallback = false;
  
  try {
    debugLog.push(`[${marketplace}] Translating to ${targetLang}`);
    
    // Translate RAW product name (not padded title) to avoid LLM treating PL as proper noun
    // listing.title = "Brand ProductNamePL keyword1 padding..." (mixed languages, confuses LLM)
    // originalData.title = "ProductNamePL" (clean, single language — translates properly)
    const brandPrefix = (originalData.brand || '').trim();
    const rawProductName = originalData.title || listing.title;
    let productToTranslate = rawProductName;
    // Strip brand if present in raw name too
    if (brandPrefix && productToTranslate.startsWith(brandPrefix)) {
      productToTranslate = productToTranslate.slice(brandPrefix.length).trim();
    }
    translatedTitle = await translateWithGroq(productToTranslate, targetLang, 'product_name');
    translatedTitle = translatedTitle.replace(/^["']|["']$/g, '').trim();
    translatedTitle = cleanTitleArtifacts(translatedTitle);
    // Verify title is in target language — retry if source language (PL/EN) detected
    const titleChk = ' ' + translatedTitle.toLowerCase() + ' ';
    let titleRetry = false;
    // Polish chars in non-PL title = untranslated
    if (targetLang !== 'PL' && /[ąćęłśźż]/i.test(translatedTitle)) {
      titleRetry = true;
      debugLog.push(`[${marketplace}] Title has Polish chars, retrying`);
    }
    if (!titleRetry) {
      // PL-specific function words (won't appear in DE/FR/IT/ES product names)
      const plOnly = [' ze ', ' dla ', ' się '];
      // EN function words (shouldn't be in non-EN product names)
      const enOnly = [' with ', ' the '];
      if (targetLang !== 'PL' && plOnly.some(w => titleChk.includes(w))) {
        titleRetry = true;
        debugLog.push(`[${marketplace}] Title has PL words, retrying`);
      } else if (enOnly.some(w => titleChk.includes(w))) {
        titleRetry = true;
        debugLog.push(`[${marketplace}] Title has EN words, retrying`);
      }
    }
    if (titleRetry) {
      await sleep(DELAYS.between_translations);
      const langFull = {DE:'German',PL:'Polish',FR:'French',IT:'Italian',ES:'Spanish',NL:'Dutch',SV:'Swedish'}[targetLang] || targetLang;
      const retryT = await translateWithGroq(
        'TRANSLATE THIS PRODUCT NAME TO ' + langFull + ': ' + productToTranslate,
        targetLang, 'product_name'
      );
      if (retryT && retryT.length > 5) {
        translatedTitle = retryT.replace(/^["']|["']$/g, '').trim();
        translatedTitle = cleanTitleArtifacts(translatedTitle);
        debugLog.push(`[${marketplace}] Title retry applied`);
      }
    }
    if (targetLang === 'PL') translatedTitle = fixPolishGrammar(translatedTitle);
    // Rebuild: brand + translated product name, then pad to meet min length
    translatedTitle = brandPrefix ? (brandPrefix + ' ' + translatedTitle).trim() : translatedTitle;
    translatedTitle = extendTitle(translatedTitle, targetLang, limits.min, limits.max);
    debugLog.push(`[${marketplace}] Title OK (from raw product name)`);
    
    // Pre-replace Polish product name in description with translated version
    // Prevents "Mata do Jogi Antypoślizgowa" appearing in German/French/etc descriptions
    const escapeRx = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    let cleanTranslatedName = translatedTitle;
    if (brandPrefix) cleanTranslatedName = cleanTranslatedName.replace(brandPrefix, '').trim();
    const padWords = TITLE_PADDING[targetLang] || [];
    for (const pw of padWords) {
      cleanTranslatedName = cleanTranslatedName.replace(new RegExp('\\s*' + escapeRx(pw) + '$', 'i'), '').trim();
    }
    if (productToTranslate && productToTranslate.length > 5 && cleanTranslatedName.length > 3) {
      const fullPolishName = brandPrefix ? (brandPrefix + ' ' + productToTranslate) : productToTranslate;
      listing.description = listing.description
        .replace(new RegExp(escapeRx(fullPolishName), 'gi'), brandPrefix ? (brandPrefix + ' ' + cleanTranslatedName) : cleanTranslatedName)
        .replace(new RegExp(escapeRx(productToTranslate), 'gi'), cleanTranslatedName);
      debugLog.push(`[${marketplace}] Replaced PL product name in desc`);
    }
    
    await sleep(DELAYS.between_translations);
    
    const bulletsText = listing.bullets.join('\n');
    try {
      const bulletsResponse = await translateWithGroq(bulletsText, targetLang, 'bullets');
      let parsed = bulletsResponse.split('\n').filter(l => l.trim().length > 10);
      
      // Merge header+content split (IT/ES/NL pattern)
      parsed = mergeBulletPairs(parsed);
      
      // Filter meta-comment bullets (framework headers LLM generates instead of translating)
      parsed = parsed.filter(b => {
        const stripped = b.replace(/\*\*/g, '').trim();
        // Skip lines that are JUST uppercase category headers (no product content)
        if (/^[A-Z\u00C0-\u024F\s\/\-\>→:&]+$/.test(stripped) && stripped.length < 80) return false;
        // Skip lines that are framework labels (MAIN USP, DIFFERENTIATOR, etc.)
        if (/^(BULLET\s*\d|MAIN\s+USP|DIFFERENTIATOR|KEY\s+(SELLING|FEATURE)|QUALITY|TRUST|PRIMARY\s+FEATURE|VERSATIL)/i.test(stripped)) return false;
        // Skip lines too short to be real bullets
        if (stripped.length < 30) return false;
        return true;
      }).slice(0, 5);
      parsed = parsed.map(b => cleanBulletArtifacts(b));
      if (targetLang === 'PL') parsed = parsed.map(b => fixPolishGrammar(b));
      
      // Bullet quality retry: if < 5 good bullets, retry with simpler prompt
      if (parsed.length < 5) {
        debugLog.push(`[${marketplace}] Only ${parsed.length} bullets, retrying translation...`);
        await sleep(DELAYS.between_translations);
        const langFull = {DE:'German',PL:'Polish',FR:'French',IT:'Italian',ES:'Spanish',NL:'Dutch',SV:'Swedish'}[targetLang] || targetLang;
        const retryBulletsText = listing.bullets.map((b, i) => (i+1) + '. ' + b.replace(/\*\*/g, '').replace(/^[-•]\s*/, '').trim()).join('\n');
        try {
          const retryResp = await translateWithGroq(
            'Translate these 5 product bullet points to ' + langFull + '. CRITICAL RULES:\n1. Return EXACTLY 5 lines\n2. Each line = **BOLD HEADER** - full description paragraph (100+ chars)\n3. Do NOT split header and description into separate lines\n4. Each bullet must be self-contained on ONE line\n\n' + retryBulletsText,
            targetLang, 'bullets'
          );
          let retryParsed = retryResp.split('\n')
            .map(l => l.trim())
            .filter(l => l.length > 10);
          retryParsed = mergeBulletPairs(retryParsed);
          retryParsed = retryParsed
            .filter(l => l.replace(/\*\*/g, '').trim().length > 30)
            .map(b => cleanBulletArtifacts(b))
            .slice(0, 5);
          if (targetLang === 'PL') retryParsed = retryParsed.map(b => fixPolishGrammar(b));
          if (retryParsed.length > parsed.length) {
            parsed = retryParsed;
            debugLog.push(`[${marketplace}] Bullet retry OK: ${retryParsed.length} bullets`);
          }
        } catch (retryErr) {
          debugLog.push(`[${marketplace}] Bullet retry failed: ${retryErr.message}`);
        }
      }
      
      translatedBullets = parsed.length >= 3 ? parsed : listing.bullets;
      debugLog.push(`[${marketplace}] Bullets: ${translatedBullets.length}`);
    } catch (e) {
      debugLog.push(`[${marketplace}] Bullets fallback`);
      translatedBullets = listing.bullets;
    }
    
    await sleep(DELAYS.between_translations);
    
    translatedDesc = await translateWithGroq(listing.description, targetLang);
    // Verify translation actually changed language — LLM sometimes returns source text
    const descHasTarget = (() => {
      const d = ' ' + translatedDesc.toLowerCase() + ' ';
      const markers = {
        DE: [' und ', ' mit ', ' aus ', ' der ', ' die ', ' das '],
        PL: [' do ', ' ze ', ' dla ', ' na ', ' jest ', ' się '],
        FR: [' et ', ' avec ', ' dans ', ' pour ', ' les '],
        IT: [' e ', ' con ', ' della ', ' per ', ' una '],
        ES: [' y ', ' con ', ' para ', ' una ', ' del ']
      };
      const check = markers[targetLang] || [];
      return check.filter(w => d.includes(w)).length >= 2;
    })();
    if (!descHasTarget && translatedDesc.length > 100) {
      debugLog.push(`[${marketplace}] Description may not be in ${targetLang}, retrying...`);
      await sleep(DELAYS.between_translations);
      const retry = await translateWithGroq(
        'TRANSLATE TO ' + targetLang + ': ' + listing.description.slice(0, 1500),
        targetLang
      );
      if (retry && retry.length > 50) translatedDesc = retry;
    }
    if (targetLang === 'PL') translatedDesc = fixPolishGrammar(translatedDesc);
    debugLog.push(`[${marketplace}] Description OK`);
    
  } catch (error) {
    debugLog.push(`[${marketplace}] FALLBACK: ${error.message}`);
    usedFallback = true;
    
    const brand = originalData.brand || 'Brand';
    const origTitle = originalData.title || 'Product';
    let fallbackTitle = `${brand} ${origTitle}`;
    const padding = TITLE_PADDING[targetLang] || TITLE_PADDING.DE;
    for (const word of padding) {
      if (fallbackTitle.length >= limits.min) break;
      fallbackTitle += ' ' + word;
    }
    translatedTitle = extendTitle(fallbackTitle, targetLang, limits.min, limits.max);
    translatedBullets = listing.bullets;
    translatedDesc = listing.description;
  }
  
  return {
    ...listing,
    title: translatedTitle,
    title_length: translatedTitle.length,
    bullets: translatedBullets,
    description: translatedDesc,
    language: targetLang,
    translated: !usedFallback,
    fallback_used: usedFallback
  };
}

const LANG_MAP = {
  allegro: 'PL',
  amazon_pl: 'PL',
  amazon_de: 'DE',
  amazon_fr: 'FR',
  amazon_it: 'IT',
  amazon_es: 'ES',
  amazon_nl: 'NL',
  amazon_se: 'SV'
};

try {
  for (const [mp, lang] of Object.entries(LANG_MAP)) {
    if (listings[mp]) {
      listings[mp] = await translateListing(listings[mp], lang, mp, data);
      await sleep(DELAYS.between_marketplaces);
    }
  }
  // Translate titles to English for EN markets if product name is non-English
  const EN_MARKETS = ['amazon_us', 'amazon_uk', 'ebay', 'etsy'];
  // Detect non-English text: diacritics OR common non-English word patterns
  const looksNonEnglish = (text) => {
    if (/[^\x00-\x7F]/.test(text)) return true;
    const lower = ' ' + text.toLowerCase() + ' ';
    const patterns = [' do ', ' ze ', ' z ', ' dla ', ' na ', ' nie ', ' od ', ' lub ', ' jak ', ' jest ', ' czosnku ', ' stali ', ' aus ', ' und ', ' fuer ', ' mit ', ' von ', ' der ', ' die ', ' das ', ' pour ', ' avec ', ' dans ', ' para ', ' con ', ' della '];
    if (patterns.some(p => lower.includes(p))) return true;
    // Polish word suffixes (instrumental/genitive case: filtrem, jonizatorem, powietrza)
    if (/\b\w+(iem|rem|torem|ówk|ości|acja|aniu|eniu|owiec)\b/i.test(text)) return true;
    return false;
  };
  
  // Translate raw product name to EN once, then replace in each EN market title
  const origProductTitle = data.title || '';
  let enProductNameCache = null;
  if (origProductTitle && looksNonEnglish(origProductTitle)) {
    try {
      enProductNameCache = await translateWithGroq(origProductTitle, 'EN', 'product_name');
      enProductNameCache = enProductNameCache.replace(/^["']|["']$/g, '').trim();
      debugLog.push(`EN product name: "${enProductNameCache}"`);
    } catch(e) {
      debugLog.push(`EN product name translation failed: ${e.message}`);
    }
    await sleep(DELAYS.between_translations);
  }
  
  const escRegex = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  for (const mp of EN_MARKETS) {
    if (listings[mp] && looksNonEnglish(listings[mp].title)) {
      debugLog.push(`[${mp}] Title has non-English chars, translating to EN`);
      try {
        let enTitle = listings[mp].title;
        // Replace Polish product name with cached EN translation (gives LLM a head start)
        if (enProductNameCache && origProductTitle) {
          enTitle = enTitle.replace(new RegExp(escRegex(origProductTitle), 'gi'), enProductNameCache);
        }
        // ALWAYS translate full title to catch remaining PL keywords used as title padding
        enTitle = await translateWithGroq(enTitle, 'EN');
        enTitle = enTitle.replace(/^["']|["']$/g, '').trim();
        enTitle = cleanTitleArtifacts(enTitle);
        // Verify EN title doesn't contain non-English text (e.g. Spanish from LLM glitch)
        const enChk = ' ' + enTitle.toLowerCase() + ' ';
        const nonEnMk = [' und ', ' mit ', ' für ', ' der ', ' die ', ' con ', ' para ', ' del ', ' avec ', ' pour ', ' dans ', ' ze ', ' dla ', ' och ', ' med '];
        const brandClean = enTitle.replace(data.brand || '', '');
        if (nonEnMk.some(w => enChk.includes(w)) || /[ąćęłńóśźżäöüßàâéèêëïôùûüÿçáéíóúñåö]/i.test(brandClean)) {
          debugLog.push(`[${mp}] EN title has non-English content, retrying...`);
          await sleep(DELAYS.between_translations);
          const retryEn = await translateWithGroq('TRANSLATE TO ENGLISH: ' + enTitle, 'EN');
          if (retryEn && retryEn.length > 10) {
            enTitle = retryEn.replace(/^["']|["']$/g, '').trim();
            enTitle = cleanTitleArtifacts(enTitle);
            debugLog.push(`[${mp}] EN title retry applied`);
          }
        }
        const baseMp = mp.startsWith('amazon') ? 'amazon' : mp;
        const limits = TITLE_LIMITS[baseMp] || TITLE_LIMITS.amazon;
        enTitle = extendTitle(enTitle, 'EN', limits.min, limits.max);
        listings[mp].title = enTitle;
        listings[mp].title_length = enTitle.length;
        listings[mp].title_translated_to_en = true;
        debugLog.push(`[${mp}] EN title: ${enTitle.length} chars`);
      } catch (e) {
        debugLog.push(`[${mp}] EN title translation failed: ${e.message}`);
      }
      await sleep(DELAYS.between_translations);
    }
  }
  
  // Fix Polish product name in EN market descriptions (from fallback templates)
  const origProductName = data.title || '';
  if (origProductName && looksNonEnglish(origProductName)) {
    const escRx = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    for (const mp of EN_MARKETS) {
      if (listings[mp] && listings[mp].description) {
        const desc = listings[mp].description;
        if (desc.includes(origProductName) || desc.includes((data.brand || '') + ' ' + origProductName)) {
          // Extract clean EN product name from translated title
          let enName = listings[mp].title || '';
          const brand = (data.brand || '').trim();
          if (brand) enName = enName.replace(brand, '').trim();
          for (const pw of (TITLE_PADDING.EN || [])) {
            enName = enName.replace(new RegExp('\\s*' + escRx(pw) + '$', 'i'), '').trim();
          }
          if (enName.length > 3) {
            const fullPL = brand ? (brand + ' ' + origProductName) : origProductName;
            listings[mp].description = desc
              .replace(new RegExp(escRx(fullPL), 'gi'), brand ? (brand + ' ' + enName) : enName)
              .replace(new RegExp(escRx(origProductName), 'gi'), enName);
            debugLog.push(`[${mp}] Replaced PL product name in EN description`);
          }
        }
      }
    }
  }
  
  // Universal bullet cleanup for ALL marketplaces (catches meta-comments from both generation and translation)
  for (const mp of Object.keys(listings)) {
    if (listings[mp] && listings[mp].bullets) {
      listings[mp].bullets = listings[mp].bullets
        .map(b => cleanBulletArtifacts(b))
        .filter(b => {
          const stripped = b.replace(/\*\*/g, '').trim();
          // Remove framework headers that slipped through
          if (/^(BULLET\s*\d|MAIN\s+USP|DIFFERENTIATOR|KEY\s+(SELLING|FEATURE)|QUALITY|TRUST)/i.test(stripped)) return false;
          if (/^[A-Z\s\/\-\>→:]+$/.test(stripped) && stripped.length < 60) return false;
          return stripped.length > 15;
        });
      // Ensure at least 3 bullets (keep originals if filter removed too many)
      if (listings[mp].bullets.length < 3) {
        listings[mp].bullets = ($input.first().json.listings?.[mp]?.bullets || listings[mp].bullets);
      }
    }
  }
  
  // Pre-replace Polish product name in non-EN bullets that still contain it
  const origPN = data.title || '';
  if (origPN) {
    const escPN = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    for (const [mp, listing] of Object.entries(listings)) {
      if (listing.translated && listing.language !== 'EN') {
        const translatedName = listing.title.replace(data.brand || '', '').trim()
          .replace(/\s*(Premium|Professionell|Hochwertig|Langlebig|Erstklassig|Haute|Wysoka|Doskonały).*$/i, '').trim();
        if (translatedName.length > 3) {
          listing.bullets = listing.bullets.map(b =>
            b.replace(new RegExp(escPN(origPN), 'gi'), translatedName)
          );
          listing.description = listing.description.replace(new RegExp(escPN(origPN), 'gi'), translatedName);
        }
      }
    }
  }
  
  debugLog.push(`Complete (used key #${currentKeyIndex + 1})`);
  return [{ json: { ...data, listings, translationsApplied: true, debug: debugLog } }];
} catch (error) {
  debugLog.push(`ERROR: ${error.message}`);
  return [{ json: { ...data, listings, translationsApplied: false, translateError: error.message, debug: debugLog } }];
}