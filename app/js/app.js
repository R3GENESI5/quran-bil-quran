/* ── Quran bil-Quran App ─────────────────────────── */

const App = {
    // State
    surahList: [],
    rootsIndex: {},
    families: {},
    versesText: {},
    mufradat: {},
    furuq: [],
    currentSurah: 1,
    surahCache: {},
    selectedRoot: null,
    showAllVerses: false,
    PREVIEW_LIMIT: 25,

    // Tafsir
    TAFSIR_API: 'https://api.quran.com/api/v4',
    tafsirCache: {},          // { "tafsirId:verseKey": html }
    activeTafsir: 16,         // default: Muyassar (concise)
    TAFSIRS: {
        16: 'التفسير الميسّر',
        14: 'ابن كثير',
        91: 'السعدي',
        94: 'البغوي',
        15: 'الطبري',
        90: 'القرطبي',
        93: 'الوسيط — الطنطاوي',
    },

    // DOM refs
    $: (id) => document.getElementById(id),

    // ── Init ───────────────────────────────────────
    async init() {
        try {
            const [surahList, rootsIndex, families, versesText, mufradat, furuq] = await Promise.all([
                fetch('data/surah_list.json').then(r => r.json()),
                fetch('data/roots_index.json').then(r => r.json()),
                fetch('data/families.json').then(r => r.json()),
                fetch('data/verses_text.json').then(r => r.json()),
                fetch('data/mufradat.json').then(r => r.json()),
                fetch('data/furuq.json').then(r => r.json()),
            ]);

            this.surahList = surahList;
            this.rootsIndex = rootsIndex;
            this.families = families;
            this.versesText = versesText;
            this.mufradat = mufradat;
            this.furuq = furuq;

            this.setupUI();
            this.handleHash();

            this.$('loading-overlay').classList.add('hidden');
        } catch (err) {
            console.error('Init failed:', err);
            document.querySelector('.loader-text').textContent = 'خطأ في التحميل';
        }
    },

    // ── UI Setup ───────────────────────────────────
    setupUI() {
        // Populate surah selector
        const select = this.$('surah-select');
        this.surahList.forEach(s => {
            const opt = document.createElement('option');
            opt.value = s.number;
            opt.textContent = `${s.number}. ${s.name_ar}`;
            select.appendChild(opt);
        });

        select.addEventListener('change', () => {
            this.loadSurah(parseInt(select.value));
        });

        // Nav buttons
        this.$('prev-surah').addEventListener('click', () => {
            if (this.currentSurah > 1) this.loadSurah(this.currentSurah - 1);
        });
        this.$('next-surah').addEventListener('click', () => {
            if (this.currentSurah < 114) this.loadSurah(this.currentSurah + 1);
        });

        // Close panel
        this.$('close-panel').addEventListener('click', () => this.closePanel());

        // Show more button
        this.$('show-more-btn').addEventListener('click', () => {
            this.showAllVerses = true;
            this.renderConnectedVerses(this.selectedRoot);
            this.$('show-more-btn').style.display = 'none';
        });

        // Keyboard nav
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') this.closePanel();
            if (e.key === 'ArrowLeft' && !e.target.closest('select')) {
                e.preventDefault();
                if (this.currentSurah < 114) this.loadSurah(this.currentSurah + 1);
            }
            if (e.key === 'ArrowRight' && !e.target.closest('select')) {
                e.preventDefault();
                if (this.currentSurah > 1) this.loadSurah(this.currentSurah - 1);
            }
        });

        // Hash navigation
        window.addEventListener('hashchange', () => this.handleHash());
    },

    handleHash() {
        const hash = location.hash.slice(1);
        if (!hash) {
            this.loadSurah(1);
            return;
        }
        const parts = hash.split(':');
        const surah = parseInt(parts[0]);
        if (surah >= 1 && surah <= 114) {
            this.loadSurah(surah, true).then(() => {
                if (parts[1]) this.scrollToVerse(`${surah}:${parts[1]}`);
            });
        }
    },

    // ── Data Loading ───────────────────────────────
    async loadSurah(num, skipHash) {
        if (!this.surahCache[num]) {
            const resp = await fetch(`data/surahs/${num}.json`);
            this.surahCache[num] = await resp.json();
        }
        this.currentSurah = num;
        this.renderSurah();
        if (!skipHash) location.hash = `${num}`;

        // Update selector
        this.$('surah-select').value = num;

        // Update nav buttons
        this.$('prev-surah').disabled = num <= 1;
        this.$('next-surah').disabled = num >= 114;

        // Update info
        const info = this.surahList[num - 1];
        this.$('surah-info').textContent =
            `${info.verses_count} verses · ${info.revelation_place === 'makkah' ? 'Makki' : 'Madani'}`;

        // Update themes link with current surah
        const themesLink = document.querySelector('.themes-link');
        if (themesLink) themesLink.href = `themes.html?surah=${num}`;

        window.scrollTo(0, 0);
    },

    // ── Rendering ──────────────────────────────────
    renderSurah() {
        const data = this.surahCache[this.currentSurah];
        const info = this.surahList[this.currentSurah - 1];

        // Surah header
        this.$('surah-name-ar').textContent = `سورة ${info.name_ar}`;
        this.$('surah-name-en').textContent = `${info.name_en} — ${info.name_translation}`;

        // Verses
        const container = this.$('verses');
        container.innerHTML = '';

        data.forEach(verse => {
            const el = document.createElement('div');
            el.className = 'verse';
            el.id = `v-${verse.k}`;

            // Verse text with clickable words + inline verse number
            const textEl = document.createElement('div');
            textEl.className = 'verse-text';

            verse.words.forEach((w, i) => {
                const span = document.createElement('span');
                span.className = 'word';
                span.textContent = w.t;
                span.dataset.index = i;

                if (w.r) {
                    span.classList.add('word-has-root');
                    span.dataset.root = w.r;
                    span.addEventListener('click', () => this.onWordClick(w.r, span));
                }

                textEl.appendChild(span);

                // Space between words
                if (i < verse.words.length - 1) {
                    textEl.appendChild(document.createTextNode(' '));
                }
            });

            // Inline verse number at end (clickable for tafsir)
            const numEl = document.createElement('span');
            numEl.className = 'verse-num';
            numEl.textContent = verse.a;
            numEl.title = 'اضغط لعرض التفسير';
            numEl.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggleTafsir(verse.k, el);
            });
            textEl.appendChild(document.createTextNode(' '));
            textEl.appendChild(numEl);

            el.appendChild(textEl);
            container.appendChild(el);
        });

        // Re-highlight if root is selected
        if (this.selectedRoot) {
            this.highlightRoot(this.selectedRoot);
        }
    },

    // ── Word Click ─────────────────────────────────
    onWordClick(root, wordEl) {
        this.selectedRoot = root;
        this.showAllVerses = false;

        // Clear previous selection
        document.querySelectorAll('.word-selected').forEach(el => {
            el.classList.remove('word-selected');
        });
        wordEl.classList.add('word-selected');

        // Highlight all words with this root
        this.highlightRoot(root);

        // Show panel
        this.openPanel(root);
    },

    highlightRoot(root) {
        // Clear old highlights
        document.querySelectorAll('.word-highlighted').forEach(el => {
            el.classList.remove('word-highlighted');
        });

        // Highlight words with matching root
        document.querySelectorAll(`.word-has-root[data-root="${root}"]`).forEach(el => {
            if (!el.classList.contains('word-selected')) {
                el.classList.add('word-highlighted');
            }
        });
    },

    // ── Panel ──────────────────────────────────────
    openPanel(root) {
        const data = this.rootsIndex[root];
        if (!data) return;

        const panel = this.$('root-panel');

        // Root display
        // Show individual letters separated by dots (traditional Arabic root display)
        const letters = root.split('');
        this.$('root-display').textContent = letters.join(' ');
        this.$('root-buckwalter').textContent = data.b || '';
        this.$('root-meaning').textContent = data.m || 'No meaning available';
        this.$('root-meaning').style.display = data.m ? 'block' : 'none';
        this.$('root-frequency').textContent = `Appears in ${data.f} verses across the Quran`;

        // Mufradat (classical lexicon)
        this.renderMufradat(root);

        // Furuq (linguistic distinctions)
        this.renderFuruq(root);

        // Family info
        this.renderFamilyInfo(root, data.fam || []);

        // Connected verses
        this.renderConnectedVerses(root);

        // Show panel
        panel.classList.add('panel-visible');
        document.body.classList.add('panel-open');
    },

    renderMufradat(root) {
        const section = this.$('mufradat-section');
        const entry = this.mufradat[root];

        if (!entry) {
            section.style.display = 'none';
            return;
        }

        section.style.display = 'block';

        // Original root heading from al-Raghib
        this.$('mufradat-root').textContent = entry.r !== root
            ? `${entry.r} (${root})`
            : entry.r;

        // Definition text
        this.$('mufradat-text').textContent = entry.t;

        // Verse references
        const versesEl = this.$('mufradat-verses');
        versesEl.innerHTML = '';

        if (entry.v && entry.v.length) {
            const label = document.createElement('span');
            label.className = 'mufradat-verses-label';
            label.textContent = `الآيات المذكورة (${entry.vc})`;
            versesEl.appendChild(label);

            const chips = document.createElement('div');
            chips.className = 'mufradat-verse-chips';
            entry.v.forEach(vk => {
                const chip = document.createElement('a');
                chip.className = 'mufradat-verse-chip';
                chip.href = `#${vk}`;
                chip.textContent = vk;
                chip.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.navigateToVerse(vk);
                });
                chips.appendChild(chip);
            });
            if (entry.vc > entry.v.length) {
                const more = document.createElement('span');
                more.className = 'mufradat-verse-more';
                more.textContent = `+${entry.vc - entry.v.length}`;
                chips.appendChild(more);
            }
            versesEl.appendChild(chips);
        }
    },

    renderFuruq(root) {
        const section = this.$('furuq-section');
        const list = this.$('furuq-list');
        list.innerHTML = '';

        // Search for pairs where either word contains or matches the root letters
        const rootLetters = root.split('');
        const matches = this.furuq.filter(pair => {
            return this.rootInWord(rootLetters, pair.a) || this.rootInWord(rootLetters, pair.b);
        });

        if (!matches.length) {
            section.style.display = 'none';
            return;
        }

        section.style.display = 'block';

        matches.slice(0, 5).forEach(pair => {
            const card = document.createElement('div');
            card.className = 'furuq-card';

            const header = document.createElement('div');
            header.className = 'furuq-pair';
            header.textContent = `${pair.a} — ${pair.b}`;

            const text = document.createElement('div');
            text.className = 'furuq-text';
            text.textContent = pair.t.length > 200
                ? pair.t.slice(0, 200) + '…'
                : pair.t;

            card.appendChild(header);
            card.appendChild(text);
            list.appendChild(card);
        });

        if (matches.length > 5) {
            const more = document.createElement('div');
            more.className = 'furuq-more';
            more.textContent = `+${matches.length - 5} more distinctions`;
            list.appendChild(more);
        }
    },

    rootInWord(rootLetters, word) {
        if (!word) return false;
        // Check if root letters appear in order within the word
        let idx = 0;
        for (const ch of word) {
            if (ch === rootLetters[idx]) {
                idx++;
                if (idx === rootLetters.length) return true;
            }
        }
        return false;
    },

    closePanel() {
        this.$('root-panel').classList.remove('panel-visible');
        document.body.classList.remove('panel-open');

        // Clear highlights
        document.querySelectorAll('.word-selected, .word-highlighted').forEach(el => {
            el.classList.remove('word-selected', 'word-highlighted');
        });
        this.selectedRoot = null;
    },

    renderFamilyInfo(root, familyIds) {
        const section = this.$('root-family-section');

        if (!familyIds.length) {
            section.style.display = 'none';
            return;
        }

        section.style.display = 'block';
        const container = this.$('root-family-info');
        container.innerHTML = '';

        familyIds.forEach(fid => {
            const fam = this.families[fid];
            if (!fam) return;

            const div = document.createElement('div');
            div.style.marginBottom = '12px';

            // Badge
            const badge = document.createElement('span');
            badge.className = 'family-badge';
            badge.textContent = fam.name_ar;
            div.appendChild(badge);

            // Meaning
            const meaning = document.createElement('div');
            meaning.className = 'family-meaning';
            meaning.textContent = fam.meaning;
            div.appendChild(meaning);

            // Related roots
            const chips = document.createElement('div');
            chips.className = 'family-roots';

            fam.roots.forEach(r => {
                const chip = document.createElement('span');
                chip.className = 'family-root-chip';
                if (r === root) chip.classList.add('active');
                chip.textContent = r;
                chip.addEventListener('click', () => {
                    this.selectedRoot = r;
                    this.showAllVerses = false;
                    this.openPanel(r);
                    this.highlightRoot(r);
                });
                chips.appendChild(chip);
            });

            div.appendChild(chips);
            container.appendChild(div);
        });
    },

    renderConnectedVerses(root) {
        const data = this.rootsIndex[root];
        if (!data) return;

        const container = this.$('connected-verses');
        container.innerHTML = '';

        const verseKeys = data.v;
        const limit = this.showAllVerses ? verseKeys.length : this.PREVIEW_LIMIT;
        const shown = verseKeys.slice(0, limit);

        // Group by surah
        const groups = {};
        shown.forEach(vk => {
            const surahNum = parseInt(vk.split(':')[0]);
            if (!groups[surahNum]) groups[surahNum] = [];
            groups[surahNum].push(vk);
        });

        Object.keys(groups).sort((a, b) => a - b).forEach(surahNum => {
            const surahInfo = this.surahList[surahNum - 1];
            const group = document.createElement('div');
            group.className = 'connected-group';

            const header = document.createElement('div');
            header.className = 'connected-group-header';
            header.textContent = `${surahInfo.name_en} (${surahInfo.name_ar})`;
            group.appendChild(header);

            groups[surahNum].forEach(vk => {
                const text = this.versesText[vk] || '';
                const verseEl = document.createElement('a');
                verseEl.className = 'connected-verse';
                verseEl.href = `#${vk}`;

                const keyEl = document.createElement('span');
                keyEl.className = 'connected-verse-key';
                keyEl.textContent = vk;

                const textEl = document.createElement('div');
                textEl.className = 'connected-verse-text';
                textEl.textContent = text;

                verseEl.appendChild(keyEl);
                verseEl.appendChild(textEl);

                verseEl.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.navigateToVerse(vk);
                });

                group.appendChild(verseEl);
            });

            container.appendChild(group);
        });

        // Update header count
        this.$('connected-header').textContent =
            `الآيات المتصلة — ${verseKeys.length} Connected Verses`;

        // Show more button
        const btn = this.$('show-more-btn');
        if (verseKeys.length > this.PREVIEW_LIMIT && !this.showAllVerses) {
            btn.style.display = 'block';
            btn.textContent = `عرض الكل (${verseKeys.length} آية)`;
        } else {
            btn.style.display = 'none';
        }
    },

    // ── Tafsir ──────────────────────────────────────
    sanitizeTafsir(html) {
        const tmp = document.createElement('div');
        tmp.innerHTML = html;
        // Strip all tags except safe ones
        const allowed = new Set(['P', 'BR', 'B', 'STRONG', 'I', 'EM', 'SPAN', 'DIV']);
        const walk = (node) => {
            [...node.childNodes].forEach(child => {
                if (child.nodeType === 1) { // Element
                    if (!allowed.has(child.tagName)) {
                        // Replace with its text content
                        child.replaceWith(document.createTextNode(child.textContent));
                    } else {
                        // Remove all attributes (prevent XSS via onclick, style, etc.)
                        [...child.attributes].forEach(a => child.removeAttribute(a.name));
                        walk(child);
                    }
                }
            });
        };
        walk(tmp);
        return tmp.innerHTML;
    },

    async fetchTafsir(tafsirId, verseKey) {
        const cacheKey = `${tafsirId}:${verseKey}`;
        if (this.tafsirCache[cacheKey]) return this.tafsirCache[cacheKey];

        const [surah, ayah] = verseKey.split(':');
        const url = `${this.TAFSIR_API}/tafsirs/${tafsirId}/by_ayah/${surah}:${ayah}`;
        const resp = await fetch(url);
        if (!resp.ok) throw new Error(`API ${resp.status}`);
        const data = await resp.json();

        const raw = data.tafsir?.text || '';
        const clean = this.sanitizeTafsir(raw);
        this.tafsirCache[cacheKey] = clean;
        return clean;
    },

    toggleTafsir(verseKey, verseEl) {
        const existing = verseEl.querySelector('.tafsir-block');
        const numEl = verseEl.querySelector('.verse-num');

        if (existing) {
            // Close
            existing.classList.remove('open');
            numEl.classList.remove('tafsir-open');
            setTimeout(() => existing.remove(), 350);
            return;
        }

        // Open — create block
        const block = document.createElement('div');
        block.className = 'tafsir-block';
        block.innerHTML = `<div class="tafsir-inner"><div class="tafsir-loading">جارٍ تحميل التفسير...</div></div>`;
        verseEl.appendChild(block);
        numEl.classList.add('tafsir-open');

        // Trigger animation
        requestAnimationFrame(() => block.classList.add('open'));

        this.loadTafsirContent(verseKey, block);
    },

    async loadTafsirContent(verseKey, block) {
        try {
            const html = await this.fetchTafsir(this.activeTafsir, verseKey);
            this.renderTafsirBlock(verseKey, block, html);
        } catch (err) {
            const inner = block.querySelector('.tafsir-inner');
            inner.innerHTML = `
                <div class="tafsir-error">
                    تعذر تحميل التفسير
                    <br>
                    <button class="tafsir-retry" data-vk="${verseKey}">إعادة المحاولة</button>
                </div>`;
            inner.querySelector('.tafsir-retry').addEventListener('click', () => {
                inner.innerHTML = `<div class="tafsir-loading">جارٍ تحميل التفسير...</div>`;
                this.loadTafsirContent(verseKey, block);
            });
        }
    },

    renderTafsirBlock(verseKey, block, html) {
        const inner = block.querySelector('.tafsir-inner');

        // Build selector options
        const opts = Object.entries(this.TAFSIRS)
            .map(([id, name]) => `<option value="${id}"${+id === this.activeTafsir ? ' selected' : ''}>${name}</option>`)
            .join('');

        inner.innerHTML = `
            <div class="tafsir-toolbar">
                <span class="tafsir-label">التفسير</span>
                <select class="tafsir-select">${opts}</select>
            </div>
            <div class="tafsir-text">${html || '<em>لا يتوفر تفسير لهذه الآية</em>'}</div>`;

        // Tafsir switch handler
        inner.querySelector('.tafsir-select').addEventListener('change', async (e) => {
            const newId = parseInt(e.target.value);
            this.activeTafsir = newId;
            const textEl = inner.querySelector('.tafsir-text');
            textEl.innerHTML = `<div class="tafsir-loading">جارٍ تحميل التفسير...</div>`;
            try {
                const newHtml = await this.fetchTafsir(newId, verseKey);
                textEl.innerHTML = newHtml || '<em>لا يتوفر تفسير لهذه الآية</em>';
            } catch {
                textEl.innerHTML = `
                    <div class="tafsir-error">
                        تعذر تحميل التفسير
                        <br>
                        <button class="tafsir-retry">إعادة المحاولة</button>
                    </div>`;
                textEl.querySelector('.tafsir-retry').addEventListener('click', async () => {
                    textEl.innerHTML = `<div class="tafsir-loading">جارٍ تحميل التفسير...</div>`;
                    try {
                        const retryHtml = await this.fetchTafsir(newId, verseKey);
                        textEl.innerHTML = retryHtml || '<em>لا يتوفر تفسير لهذه الآية</em>';
                    } catch {
                        textEl.innerHTML = `<div class="tafsir-error">تعذر تحميل التفسير</div>`;
                    }
                });
            }
        });
    },

    // ── Navigation ─────────────────────────────────
    async navigateToVerse(verseKey) {
        const [surah, ayah] = verseKey.split(':').map(Number);
        await this.loadSurah(surah);
        this.scrollToVerse(verseKey);

        // Re-highlight current root in new surah
        if (this.selectedRoot) {
            this.highlightRoot(this.selectedRoot);
        }
    },

    scrollToVerse(verseKey) {
        const el = document.getElementById(`v-${verseKey}`);
        if (el) {
            el.scrollIntoView({ behavior: 'smooth', block: 'center' });
            // Flash effect
            el.style.transition = 'background 0.3s';
            el.style.background = 'var(--gold-light)';
            setTimeout(() => { el.style.background = ''; }, 1500);
        }
    },
};

// ── Start ──────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => App.init());
