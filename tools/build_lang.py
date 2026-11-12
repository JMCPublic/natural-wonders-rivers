#!/usr/bin/env python3
"""Builds the translated Rivers pages (es/, pt/, fr/, de/, tr/) from index.html.

   python3 tools/build_lang.py          every language in tools/i18n/
   python3 tools/build_lang.py es       one language

Run it again after any change to the English page. Each English piece below says how many times it must be
found; if the English page changes so that a piece no longer matches, the build stops instead of putting a
half-translated page live.

A language file tools/i18n/<code>.py holds:
  LANG, LOCALE (html lang and og locale), FMT (the JS number format), HOME (where a first-time player starts)
  T      {id: translation} for every id in EN below
  ORD, DEPTH, WHERE      ordinals, the two depth labels, and the "Where" options
  N      river names that differ from English;  SC  region names;  IN  "in <region>" phrases
  WIB    the Where is Bigger? page for this language, whose translated game switcher and feedback form are reused
"""
import importlib, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, 'i18n'))
LANGS = ['es', 'pt', 'fr', 'de', 'tr']
WIBDIR = os.path.join(os.path.dirname(ROOT), 'natural-wonders-where-is-bigger')

# (id, English exactly as in index.html, times it must appear)
EN = [
 ('title', '<title>Natural Wonders · Rivers</title>', 1),
 ('t_aria', "'Time left for this question'", 1),
 ('t_secs', "`${s} second${s===1?'':'s'}`", 1),
 ('t_in', '<b>${right}/${total} in ${this.fmt(secs)}</b>', 1),
 ('t_left', "`left the page ${this.left} time${this.left===1?'':'s'}`", 1),
 ('t_stayed', "'stayed on the page throughout'", 1),
 ('t_label', '<div class="label">Timer</div>', 1),
 ('t_timed', '>⏱ Timed<small>', 1),
 ('t_none', '>No timer<small>Take your time</small>', 1),
 ('map_aria', 'aria-label="Map of ${esc(sc.name)} with rivers"', 1),
 ('layouts', "const LAYOUTS={auto:'Auto',phone:'Phone',tablet:'Tablet',desktop:'Desktop'};", 1),
 ('head', '<b>Natural Wonders</b> · Game 1 of 10 · <a href="https://twominute.games/wonders/">All games</a>', 1),
 ('h1', '<h1>Rivers</h1>', 2),
 ('sub', '<p class="sub">Up to five rivers on the map. The longest is given; put the others in order of length. The real lengths are revealed at the end.</p>', 1),
 ('l_where', '<div class="label">Where</div>', 1),
 ('l_depth', '<div class="label">How many to rank</div>', 1),
 ('t_note', "TM.menuRow('30 seconds a round')", 1),
 ('l_rounds', '<div class="label">Number of rounds</div>', 1),
 ('n_rounds', '>${n} rounds</button>', 1),
 ('start', '>Start — ${S.rounds} rounds</button>', 1),
 ('layout', '<p class="foot">Layout <span', 1),
 ('foot', '${COUNTRY_IDS.length} countries and 5 continents · Natural Wonders: Rivers ${VERSION} · <button class="srclink" onclick="openSources()">Sources</button>', 1),
 ('nogame', "'Could not build a game with those settings. Try again.'", 1),
 ('ord1', '<span class="ord">1st</span>', 1),
 ('given', '<span class="given">Longest · given</span>', 1),
 ('place_aria', 'aria-label="${ORD[i]} place"', 1),
 ('empty', '<span class="empty">tap a river below</span>', 1),
 ('prev', '>← Previous</button>', 1),
 ('quit', 'onclick="quit()">Quit</button>', 1),
 ('q', """<div class="q">${phone?'':'Rank the rivers of '}<em>${esc(where)}</em>${phone?' — longest first':' by length'}<span>Round ${S.cur+1} of ${S.game.length} · the longest is given, you rank the rest</span><span class="note">ⓘ Full river lengths, including any stretch outside ${esc(where)}</span></div>""", 1),
 ('l_order', '<div class="label">Longest to shortest</div>', 1),
 ('l_tray', '<div class="label">Rivers to place</div>', 1),
 ('lock', "${full?'Lock in answer':'Fill every box to lock in'}", 1),
 ('kbd', "<div class=\"kbd\">Keys ${LET.slice(1,n).toUpperCase().split('').join(' ')} place a river · Backspace removes · Enter locks in</div>", 1),
 ('verdict', "function verdict(p){return p===1?'Perfect. A true river expert.':p>=.8?'Excellent. You know your rivers.':p>=.6?'Solid effort. A few surprises in there.':p>=.4?'The rivers have fooled you a bit.':'Rivers can be very deceptive!'}", 1),
 ('abroad', '<div class="abroad">ⓘ Only about ${Math.max(5,Math.round(r.in/r.km*20)*5)}% of it is in ${esc(sc.name)}</div>', 1),
 ('st_given', '<span class="st gv">Given</span>', 1),
 ('st_ok', '<span class="st ok">✓ You had it</span>', 1),
 ('st_put', '`<span class="st no">✗ You put ${esc(mine.n)}</span>`', 1),
 ('st_none', '<span class="st no">⏱ Not placed</span>', 1),
 ('f_close', 'fact=`💡 The ${esc(cp.a.n)} beats the ${esc(cp.b.n)} by just ${fmt(cp.g)} km.`', 1),
 ('f_rest', 'fact=`💡 The ${esc(truth[0].n)} is longer than all the others put together.`', 1),
 ('f_ratio', 'fact=`💡 The ${esc(truth[0].n)} is ${(truth[0].km/truth[truth.length-1].km).toFixed(1)}× the length of the ${esc(truth[truth.length-1].n)}.`', 1),
 ('r_head', 'Round ${ri+1} · ${esc(sc.name)}</div><h3>Longest rivers</h3>', 1),
 ('r_time', "${R.timedOut?'Time ran out':'Answered in '+R.secs.toFixed(1)+' s'}", 1),
 ('srcline', '<div class="srcline">Lengths from ${', 1),
 ('src_and', ".join(' and ')}</div></div></div></div>`);", 1),
 ('surprise', "`<div class=\"surprise\">😲 <b>Biggest surprise:</b> you put the ${esc(surprise.r.n)} ${ORD[surprise.pos]}, but at ${fmt(surprise.r.km)} km it's ${ORD[surprise.i]} in ${esc(surprise.sc.name)}.</div>`", 1),
 ('perfect', '<div class="surprise">🎯 Every river in the right place. Remarkable!</div>', 1),
 ('results', '<h1>Results</h1>', 1),
 ('r_meta', "Natural Wonders · Rivers · ${WHERE[S.where].t.replace('🎲 ','')} · rank ${DEPTH[S.depth].t} · ${S.game.length} rounds", 1),
 ('again', '>Play again</button>', 1),
 ('change', '>Change settings</button>', 1),
 ('share', '>Share score</button>', 1),
 ('sources_btn', 'onclick="openSources()">Sources</button><a', 1),
 ('more', '>More games</a>', 1),
 ('rbr', '<div class="label" style="margin-top:24px">Round by round</div>', 1),
 ('every', 'Every length is shown exactly as published by the source named under each round. <button class="srclink" onclick="openSources()">See all sources</button>', 1),
 ('share_t', "`Natural Wonders: Rivers. I scored ${r}/${n} (${WHERE[S.where].t.replace('🎲 ','')}). Can you beat me?`", 1),
 ('copied', "toast('Score copied. Paste it to a friend.')", 1),
 ('src_dlg', 'aria-label="Sources"><button class="srcx" onclick="closeSources()">Close</button>', 1),
 ('src_group', '<summary>${esc(s.name)} · ${s.rivers.length} rivers</summary>', 1),
 ('src_h2', '<h2>Sources</h2>\n', 1),
 ('src_gf', 'The river lengths in this game were taken in good faith from the published sources below in October 2026, and each figure is shown exactly as that source gives it. River lengths depend on how a river is measured (where it starts, whether it includes estuaries or lakes), so reputable sources often disagree, and a source can occasionally be wrong. If you think a figure is wrong, the source named next to it is where it came from.', 1),
 ('src_fair', '<h3>How the game stays fair</h3>', 1),
 ('src_li1', "<li>Lengths are each river's full length, including any stretch outside the country shown.</li>", 1),
 ('src_li2', '<li>Rivers whose lengths are within about 5% of each other never appear in the same round, so a different source could not change the right answer. The exceptions are two long-established close calls: Severn v Thames, and Adige v Tiber.</li>', 1),
 ('src_li3', '<li>Where a river appears in more than one place (for example the Volga in Russia and in Europe), each uses the figure from the source cited for it, so the number can differ slightly.</li>', 1),
 ('src_len', '<h3>River lengths</h3>', 1),
 ('src_maps', '<h3>Maps</h3>', 1),
 ('src_ne', '<li>Country outlines and river courses: <a href="https://www.naturalearthdata.com/" target="_blank" rel="noopener">Natural Earth</a> (1:10m, public domain). Rivers are drawn simplified, so their length on the map is only a rough guide.</li>', 1),
 ('src_every', '<h3>Every river and its source</h3>', 1),
 ('src_ver', '>Natural Wonders: Rivers ${VERSION}</p>', 1),
]

def js(o): return json.dumps(o, ensure_ascii=False)

def block(s, a, b):
    i = s.index(a); j = s.index(b, i); return i, j

def build(code):
    C = importlib.import_module(code)
    s = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
    def rep(old, new, n=1):
        nonlocal s
        c = s.count(old)
        if c != n: sys.exit(f'{code}: expected {n}x, found {c}x of:\n  {old[:140]}')
        s = s.replace(old, new)
    missing = [i for i, _, _ in EN if i not in C.T]
    if missing: sys.exit(f'{code}: no translation for {missing}')
    # longest English first, so a piece inside a longer one never gets swapped early
    for i, en, n in sorted(EN, key=lambda x: -len(x[1])):
        rep(en, C.T[i], n)
    # lists and labels the game builds from
    rep(re.search(r"const WHERE=\{.*?\};", s).group(0), 'const WHERE=' + C.WHERE + ';')
    rep(re.search(r"const DEPTH=\{.*?\};", s).group(0), 'const DEPTH=' + C.DEPTH + ';')
    rep("const ORD=['1st','2nd','3rd','4th','5th'];", 'const ORD=' + js(C.ORD) + ';')
    rep("const fmt=n=>n.toLocaleString('en-GB');", 'const fmt=n=>' + C.FMT + ';')
    rep('<html lang="en">', f'<html lang="{code}">')
    # river and region names, inside the map data
    i = s.index('const DATA=') + len('const DATA=')
    D, end = json.JSONDecoder().raw_decode(s[i:])
    for sc in D['scopes']:
        sc['name'] = C.SC[sc['id']]
        names = [C.N.get(r['n'], r['n']) for r in sc['rivers']]
        if len(set(names)) != len(names): sys.exit(f'{code}: two rivers share a name in {sc["id"]}: {names}')
        for r, nm in zip(sc['rivers'], names): r['n'] = nm
    s = s[:i] + json.dumps(D, ensure_ascii=False, separators=(',', ':')) + s[i + end:]
    N = lambda x: C.N.get(x, x)
    rep("const OKPAIRS=[['Severn','Thames'],['Adige','Tiber']];", 'const OKPAIRS=' + js([[N('Severn'), N('Thames')], [N('Adige'), N('Tiber')]]) + ';')
    # "in <region>" for the surprise line
    rep('const BYID={};', 'const IN=' + js(C.IN) + ';const BYID={};')
    # settings remembered per language; a first-time player starts on HOME
    rep("localStorage.getItem('nwr_settings')", f"localStorage.getItem('nwr_settings_{code}')")
    rep("localStorage.setItem('nwr_settings',", f"localStorage.setItem('nwr_settings_{code}',")
    rep("let S={screen:'menu',where:'countries',", f"let S={{screen:'menu',where:{js(C.HOME)},")
    rep("if(!WHERE[S.where])S.where='countries';", f"if(!WHERE[S.where])S.where={js(C.HOME)};")
    # the translated game switcher and feedback form, taken from the Where is Bigger? page in this language
    w = open(os.path.join(WIBDIR, code, 'index.html'), encoding='utf-8').read()
    for a, b in (('<!-- nw-nav', '<!-- nw-stats'), ('<!-- tmg-feedback', '<!-- /tmg-feedback -->')):
        wi, wj = block(w, a, b); si, sj = block(s, a, b)
        s = s[:si] + w[wi:wj] + s[sj:]
    # Where is Bigger?'s builder (tools/navlinks.py there) already gives that switcher our translated name and
    # blurb, links to this language, and "in English" only for games that are; check it did
    for must in ("{n:" + js(C.RIVERS_NAME) + ",slug:'rivers',ic:'rivers',t:" + js(C.RIVERS_BLURB) + "}",
                 "'rivers':1", f"(TRL[g.slug]?'{code}/':'')", "${TRL[n.slug]?'':"):
        if must not in s: sys.exit(f'{code}: game switcher from Where is Bigger? lacks {must[:60]}; run its builder first')
    for a, b in getattr(C, 'EXTRA', []): rep(a, b)
    s = s.replace('<!doctype html>', f'<!doctype html>\n<!-- GENERATED by tools/build_lang.py ({code}) from ../index.html. Edit the English page, then run the build again. -->', 1)
    os.makedirs(os.path.join(ROOT, code), exist_ok=True)
    open(os.path.join(ROOT, code, 'index.html'), 'w', encoding='utf-8').write(s)
    print(f'{code}: built')

if __name__ == '__main__':
    for c in (sys.argv[1:] or LANGS):
        if os.path.exists(os.path.join(HERE, 'i18n', c + '.py')): build(c)
