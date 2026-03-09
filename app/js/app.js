/* ── Quran bil-Quran App ─────────────────────────── */

const App = {
    // State
    surahList: [],
    rootsIndex: {},
    families: {},
    versesText: {},
    currentSurah: 1,
    surahCache: {},
    selectedRoot: null,
    showAllVerses: false,
    PREVIEW_LIMIT: 25,

    // DOM refs
    $: (id) => document.getElementById(id),

    // ── Init ───────────────────────────────────────
    async init() {
        try {
            const [surahList, rootsIndex, families, versesText] = await Promise.all([
                fetch('data/surah_list.json').then(r => r.json()),
                fetch('data/roots_index.json').then(r => r.json()),
                fetch('data/families.json').then(r => r.json()),
                fetch('data/verses_text.json').then(r => r.json()),
            ]);

            this.surahList = surahList;
            this.rootsIndex = rootsIndex;
            this.families = families;
            this.versesText = versesText;

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
            this.loadSurah(surah).then(() => {
                if (parts[1]) this.scrollToVerse(`${surah}:${parts[1]}`);
            });
        }
    },

    // ── Data Loading ───────────────────────────────
    async loadSurah(num) {
        if (!this.surahCache[num]) {
            const resp = await fetch(`data/surahs/${num}.json`);
            this.surahCache[num] = await resp.json();
        }
        this.currentSurah = num;
        this.renderSurah();
        location.hash = `${num}`;

        // Update selector
        this.$('surah-select').value = num;

        // Update nav buttons
        this.$('prev-surah').disabled = num <= 1;
        this.$('next-surah').disabled = num >= 114;

        // Update info
        const info = this.surahList[num - 1];
        this.$('surah-info').textContent =
            `${info.verses_count} verses · ${info.revelation_place === 'makkah' ? 'Makki' : 'Madani'}`;

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

            // Inline verse number at end
            const numEl = document.createElement('span');
            numEl.className = 'verse-num';
            numEl.textContent = verse.a;
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

        // Family info
        this.renderFamilyInfo(root, data.fam || []);

        // Connected verses
        this.renderConnectedVerses(root);

        // Show panel
        panel.classList.add('panel-visible');
        document.body.classList.add('panel-open');
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
