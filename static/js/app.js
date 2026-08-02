/**
 * News Pulse Aggregator Client Application Controller
 */
document.addEventListener('DOMContentLoaded', () => {
    // Application State
    const state = {
        page: 1,
        limit: 9,
        source: 'all',
        country: 'all',
        search: '',
        sort: 'newest',
        totalPages: 1,
        totalItems: 0,
        rawArticles: []
    };

    // Default backend Flask server URL
    const FLASK_SERVER_ORIGIN = 'http://127.0.0.1:5000';

    // DOM Elements
    const apiUrlInput = document.getElementById('apiUrlInput');
    const apiKeyInput = document.getElementById('apiKeyInput');
    const fetchApiBtn = document.getElementById('fetchApiBtn');
    const searchInput = document.getElementById('searchInput');
    const clearSearchBtn = document.getElementById('clearSearchBtn');
    const countrySelect = document.getElementById('countrySelect');
    const sourceSelect = document.getElementById('sourceSelect');
    const sortSelect = document.getElementById('sortSelect');
    const resetFiltersBtn = document.getElementById('resetFiltersBtn');
    const newsGrid = document.getElementById('newsGrid');
    const emptyState = document.getElementById('emptyState');
    const paginationNav = document.getElementById('paginationNav');
    const paginationList = document.getElementById('paginationList');
    const newsCounter = document.getElementById('newsCounter');
    const loadingStatus = document.getElementById('loadingStatus');
    const scrapeBtn = document.getElementById('scrapeBtn');
    const scrapeIcon = document.getElementById('scrapeIcon');
    const scrapeSpinner = document.getElementById('scrapeSpinner');
    const emptyStateScrapeBtn = document.getElementById('emptyStateScrapeBtn');
    const liveToast = document.getElementById('liveToast');
    const toastMessage = document.getElementById('toastMessage');

    const defaultFallbackImage = 'https://images.unsplash.com/photo-1504711434969-e33886168f5c?auto=format&fit=crop&w=600&q=80';
    let searchDebounceTimer = null;

    /**
     * Display Bootstrap Toast Notification
     */
    function showToast(msg, isSuccess = true) {
        if (!liveToast) return;
        toastMessage.textContent = msg;
        liveToast.className = `toast align-items-center text-white border-0 shadow-lg ${isSuccess ? 'bg-success' : 'bg-danger'}`;
        const toast = new bootstrap.Toast(liveToast, { delay: 4000 });
        toast.show();
    }

    /**
     * Resolve target URL to absolute Flask server endpoint
     */
    function resolveTargetUrl(pathOrUrl) {
        let base = pathOrUrl ? pathOrUrl.trim() : '/api/news';
        if (base.startsWith('/') || (!base.startsWith('http://') && !base.startsWith('https://'))) {
            if (!base.startsWith('/')) base = '/' + base;
            
            // Only redirect to 127.0.0.1 if running directly off a local file or local dev server (like VS Code Live Server)
            const isLocalDev = window.location.protocol === 'file:' || 
                ((window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') && window.location.port !== '5000');

            if (isLocalDev) {
                return `${FLASK_SERVER_ORIGIN}${base}`;
            }
            return `${window.location.origin}${base}`;
        }
        return base;
    }

    /**
     * Get target API URL string built from user inputs
     */
    function getTargetApiUrl() {
        const rawUrl = (apiUrlInput && apiUrlInput.value.trim()) ? apiUrlInput.value.trim() : '/api/news';
        let fullUrl = resolveTargetUrl(rawUrl);

        const params = new URLSearchParams({
            page: state.page,
            limit: state.limit,
            source: state.source,
            country: state.country,
            search: state.search,
            sort: state.sort
        });

        // Add user optional API Key or query parameter if provided
        if (apiKeyInput && apiKeyInput.value.trim()) {
            const extra = apiKeyInput.value.trim();
            if (extra.includes('=')) {
                extra.split('&').forEach(pair => {
                    const [k, v] = pair.split('=');
                    if (k && v) params.set(k.trim(), v.trim());
                });
            } else {
                params.set('apiKey', extra);
            }
        }

        const separator = fullUrl.includes('?') ? '&' : '?';
        return `${fullUrl}${separator}${params.toString()}`;
    }

    /**
     * Fetch News from Backend or Custom API URL
     */
    async function loadNews() {
        if (loadingStatus) loadingStatus.style.display = 'inline-block';
        const targetUrl = getTargetApiUrl();

        try {
            console.log('Fetching news from API URL:', targetUrl);
            const response = await fetch(targetUrl);
            const responseText = await response.text();

            let data;
            try {
                data = JSON.parse(responseText);
            } catch (jsonErr) {
                if (!response.ok) {
                    throw new Error(`Server returned HTTP ${response.status}. Ensure Flask server is running at ${FLASK_SERVER_ORIGIN}`);
                }
                throw new Error(`Invalid JSON response from API endpoint.`);
            }

            if (!response.ok) {
                throw new Error(data.error || `HTTP ${response.status}: ${response.statusText}`);
            }

            // Flexibly extract articles array from various API structures
            let articles = [];
            let total = 0;
            let totalPages = 1;

            if (Array.isArray(data)) {
                articles = data;
                total = data.length;
            } else if (data.news && Array.isArray(data.news)) {
                articles = data.news;
                total = data.total_items || data.news.length;
                totalPages = data.total_pages || Math.ceil(total / state.limit);
            } else if (data.articles && Array.isArray(data.articles)) {
                articles = data.articles;
                total = data.totalResults || data.articles.length;
                totalPages = Math.ceil(total / state.limit);
            } else if (data.data && Array.isArray(data.data)) {
                articles = data.data;
                total = data.data.length;
            }

            state.totalItems = total;
            state.totalPages = totalPages;
            state.rawArticles = articles;

            // Render UI
            renderNews(articles);
            renderPagination(state.page, state.totalPages);
            updateCounter(total);

        } catch (error) {
            console.error('API Fetch Error:', error);
            newsGrid.innerHTML = `
                <div class="col-12 text-center py-5">
                    <div class="text-danger mb-2"><i class="bi bi-exclamation-triangle display-4"></i></div>
                    <h5 class="text-dark">Unable to load news from API</h5>
                    <p class="text-secondary small max-w-md mx-auto mb-3">${escapeHtml(error.message)}</p>
                    <p class="text-muted fs-7">If testing locally, ensure Flask server is running at <code>http://127.0.0.1:5000</code> by running <code>python app.py</code> in terminal.</p>
                </div>
            `;
            if (emptyState) emptyState.style.display = 'none';
            if (paginationNav) paginationNav.style.display = 'none';
        } finally {
            if (loadingStatus) loadingStatus.style.display = 'none';
        }
    }

    /**
     * Fetch & Populate Source Select Dropdown from API endpoint
     */
    async function loadSourcesList() {
        if (!sourceSelect) return;
        const currentSelected = sourceSelect.value || 'all';
        try {
            const url = resolveTargetUrl('/api/sources');
            const res = await fetch(url);
            const data = await res.json();

            if (data.success && Array.isArray(data.sources) && data.sources.length > 0) {
                let options = `<option value="all" ${currentSelected === 'all' ? 'selected' : ''}>All Sources</option>`;
                data.sources.forEach(srcObj => {
                    const name = srcObj.name;
                    if (name) {
                        options += `<option value="${escapeHtml(name)}" ${currentSelected === name ? 'selected' : ''}>${escapeHtml(name)}</option>`;
                    }
                });
                sourceSelect.innerHTML = options;
            }
        } catch (err) {
            console.error('Error fetching sources list:', err);
        }
    }

    /**
     * Render News Cards Grid
     */
    function renderNews(articles) {
        if (!articles || articles.length === 0) {
            newsGrid.innerHTML = '';
            if (emptyState) emptyState.style.display = 'block';
            if (paginationNav) paginationNav.style.display = 'none';
            return;
        }

        if (emptyState) emptyState.style.display = 'none';
        
        let html = '';
        articles.forEach(art => {
            const title = art.title || art.headline || 'Untitled Article';
            const summary = art.summary || art.description || art.content || 'No summary available.';
            const sourceName = (typeof art.source === 'object' && art.source.name) ? art.source.name : (art.source || 'News Source');
            const uniqueSeed = encodeURIComponent((art.article_url || title).substring(0, 30));
            const imgUrl = art.image_url || `https://picsum.photos/seed/${uniqueSeed}/600/400`;
            const articleUrl = art.article_url || art.url || art.link || '#';
            const rawDate = art.published_date || art.publishedAt || art.pubDate;
            const dateStr = rawDate ? new Date(rawDate).toLocaleDateString('en-US', {
                month: 'short', day: 'numeric', year: 'numeric'
            }) : 'Recent';

            const detailLink = art.id ? `${FLASK_SERVER_ORIGIN}/article/${art.id}` : articleUrl;

            const countryCode = (art.country || 'US').toUpperCase();
            const flagMap = { 'US': '🇺🇸 US', 'UK': '🇬🇧 UK', 'IN': '🇮🇳 IN', 'CA': '🇨🇦 CA', 'AU': '🇦🇺 AU', 'DE': '🇩🇪 DE', 'JP': '🇯🇵 JP' };
            const flagBadge = flagMap[countryCode] || `🌍 ${countryCode}`;

            html += `
                <div class="col-12 col-md-6 col-lg-4">
                    <div class="card h-100 border-0 shadow-sm rounded-4 news-card overflow-hidden">
                        <div class="card-img-wrapper position-relative">
                            <img src="${escapeHtml(imgUrl)}" class="card-img-top news-card-img" alt="${escapeHtml(title)}" 
                                 onerror="this.onerror=null; this.src='https://picsum.photos/seed/${uniqueSeed}/600/400';">
                            <span class="badge bg-primary position-absolute top-0 start-0 m-3 rounded-pill px-3 py-2 fs-7">
                                ${escapeHtml(sourceName)}
                            </span>
                            <span class="badge bg-dark bg-opacity-75 position-absolute top-0 end-0 m-3 rounded-pill px-2 py-1 fs-7">
                                ${flagBadge}
                            </span>
                        </div>
                        <div class="card-body d-flex flex-column p-4">
                            <div class="text-muted small mb-2 d-flex align-items-center gap-1">
                                <i class="bi bi-calendar3"></i> ${dateStr}
                            </div>
                            <h5 class="card-title fw-bold text-dark mb-3 line-clamp-2 title-link">
                                <a href="${escapeHtml(articleUrl)}" target="_blank" rel="noopener noreferrer" class="text-decoration-none text-dark">${escapeHtml(title)}</a>
                            </h5>
                            <p class="card-text text-secondary small line-clamp-3 mb-4 flex-grow-1">
                                ${escapeHtml(summary)}
                            </p>
                            <div class="d-flex align-items-center justify-content-end pt-3 border-top gap-2">
                                <a href="${escapeHtml(articleUrl)}" target="_blank" rel="noopener noreferrer" 
                                   class="btn btn-sm btn-primary rounded-pill px-3">
                                    Read Original <i class="bi bi-box-arrow-up-right ms-1"></i>
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });

        newsGrid.innerHTML = html;
    }

    /**
     * Render Pagination Links
     */
    function renderPagination(currentPage, totalPages) {
        if (!paginationNav || totalPages <= 1) {
            if (paginationNav) paginationNav.style.display = 'none';
            return;
        }

        paginationNav.style.display = 'block';
        let items = '';

        items += `
            <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
                <button class="page-link rounded-pill border-0 px-3" data-page="${currentPage - 1}">
                    <i class="bi bi-chevron-left"></i> Prev
                </button>
            </li>
        `;

        let startPage = Math.max(1, currentPage - 2);
        let endPage = Math.min(totalPages, startPage + 4);
        if (endPage - startPage < 4) {
            startPage = Math.max(1, endPage - 4);
        }

        for (let p = startPage; p <= endPage; p++) {
            items += `
                <li class="page-item ${p === currentPage ? 'active' : ''}">
                    <button class="page-link rounded-pill border-0 px-3" data-page="${p}">${p}</button>
                </li>
            `;
        }

        items += `
            <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
                <button class="page-link rounded-pill border-0 px-3" data-page="${currentPage + 1}">
                    Next <i class="bi bi-chevron-right"></i>
                </button>
            </li>
        `;

        paginationList.innerHTML = items;

        paginationList.querySelectorAll('button.page-link').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const targetPage = parseInt(e.currentTarget.getAttribute('data-page'));
                if (targetPage && targetPage !== state.page && targetPage >= 1 && targetPage <= totalPages) {
                    state.page = targetPage;
                    loadNews();
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                }
            });
        });
    }

    /**
     * Update Counter Badge
     */
    function updateCounter(total) {
        if (newsCounter) {
            newsCounter.textContent = `${total} article${total === 1 ? '' : 's'}`;
        }
    }

    /**
     * Trigger Database Scrape Sync
     */
    async function triggerScrape() {
        if (scrapeBtn) scrapeBtn.disabled = true;
        if (scrapeIcon) scrapeIcon.style.display = 'none';
        if (scrapeSpinner) scrapeSpinner.style.display = 'inline-block';

        showToast('Initiating news scraper cycle...', true);

        try {
            const scrapeUrl = resolveTargetUrl('/api/scrape');
            const res = await fetch(scrapeUrl, { method: 'POST' });
            const responseText = await res.text();

            let data;
            try {
                data = JSON.parse(responseText);
            } catch (e) {
                throw new Error(`Server returned non-JSON response. Ensure Flask server is running at ${FLASK_SERVER_ORIGIN}`);
            }

            if (data.success) {
                const stats = data.stats;
                showToast(`Scrape complete! Added ${stats.new_added} new articles (${stats.duplicates_skipped} duplicates skipped).`, true);
                state.page = 1;
                loadNews();
                loadSourcesList();
            } else {
                throw new Error(data.error || 'Scraping failed');
            }
        } catch (err) {
            console.error('Scrape error:', err);
            showToast(`Scrape Error: ${err.message}`, false);
        } finally {
            if (scrapeBtn) scrapeBtn.disabled = false;
            if (scrapeIcon) scrapeIcon.style.display = 'inline-block';
            if (scrapeSpinner) scrapeSpinner.style.display = 'none';
        }
    }

    /**
     * Helper: Escape HTML strings
     */
    function escapeHtml(str) {
        if (!str) return '';
        return String(str).replace(/[&<>"']/g, function(m) {
            return {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#039;'
            }[m];
        });
    }

    // Attach Event Listeners to UI Buttons & Control Elements

    // 1. Fetch API Data Button
    if (fetchApiBtn) {
        fetchApiBtn.addEventListener('click', () => {
            state.page = 1;
            showToast('Fetching data from specified API URL...', true);
            loadNews();
        });
    }

    // 2. Search Input with debounce & clear button
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const val = e.target.value;
            if (clearSearchBtn) {
                clearSearchBtn.classList.toggle('d-none', val.length === 0);
            }

            clearTimeout(searchDebounceTimer);
            searchDebounceTimer = setTimeout(() => {
                state.search = val;
                state.page = 1;
                loadNews();
            }, 350);
        });
    }

    if (clearSearchBtn) {
        clearSearchBtn.addEventListener('click', () => {
            if (searchInput) searchInput.value = '';
            clearSearchBtn.classList.add('d-none');
            state.search = '';
            state.page = 1;
            loadNews();
        });
    }

    // 3. Country Select Filter
    if (countrySelect) {
        countrySelect.addEventListener('change', (e) => {
            state.country = e.target.value;
            state.page = 1;
            loadNews();
            loadFinancials();
        });
    }

    // 4. Source Select Filter
    if (sourceSelect) {
        sourceSelect.addEventListener('change', (e) => {
            state.source = e.target.value;
            state.page = 1;
            loadNews();
        });
    }

    // 5. Sort Select Filter
    if (sortSelect) {
        sortSelect.addEventListener('change', (e) => {
            state.sort = e.target.value;
            state.page = 1;
            loadNews();
        });
    }

    // 6. Reset Filters Button
    if (resetFiltersBtn) {
        resetFiltersBtn.addEventListener('click', () => {
            if (searchInput) searchInput.value = '';
            if (clearSearchBtn) clearSearchBtn.classList.add('d-none');
            if (countrySelect) countrySelect.value = 'all';
            if (sourceSelect) sourceSelect.value = 'all';
            if (sortSelect) sortSelect.value = 'newest';
            if (apiUrlInput) apiUrlInput.value = '/api/news';
            if (apiKeyInput) apiKeyInput.value = '';

            state.page = 1;
            state.search = '';
            state.country = 'all';
            state.source = 'all';
            state.sort = 'newest';

            showToast('Filters and API configuration reset.', true);
            loadNews();
            loadFinancials();
        });
    }

    // 6. Scrape / Sync Buttons
    if (scrapeBtn) scrapeBtn.addEventListener('click', triggerScrape);
    if (emptyStateScrapeBtn) emptyStateScrapeBtn.addEventListener('click', loadNews);

    // 7. Bank Financial Data Fetcher
    const financialsGrid = document.getElementById('financialsGrid');
    const financialsUpdatedAt = document.getElementById('financialsUpdatedAt');
    const refreshFinancialsBtn = document.getElementById('refreshFinancialsBtn');

    async function loadFinancials() {
        if (!financialsGrid) return;
        try {
            const url = resolveTargetUrl(`/api/financials?country=${encodeURIComponent(state.country)}`);
            const res = await fetch(url);
            const text = await res.text();
            let data;
            try { data = JSON.parse(text); } catch (e) { return; }

            if (data.success && Array.isArray(data.financials)) {
                if (financialsUpdatedAt && data.updated_at) {
                    const countryName = data.country_name || 'Global 🌍';
                    financialsUpdatedAt.innerHTML = `<i class="bi bi-clock me-1"></i> ${countryName} | ${data.updated_at}`;
                }
                
                let html = '';
                data.financials.forEach(bank => {
                    const isPositive = bank.change_pct >= 0;
                    const changeBadge = isPositive 
                        ? `<span class="badge bg-success-subtle text-success border border-success-subtle rounded-pill"><i class="bi bi-caret-up-fill me-1"></i>+${bank.change_pct}%</span>`
                        : `<span class="badge bg-danger-subtle text-danger border border-danger-subtle rounded-pill"><i class="bi bi-caret-down-fill me-1"></i>${bank.change_pct}%</span>`;

                    const statusBadgeClass = bank.status.includes('Buy') || bank.status === 'Bullish' 
                        ? 'bg-primary-subtle text-primary border-primary-subtle' 
                        : 'bg-secondary-subtle text-secondary border-secondary-subtle';

                    html += `
                        <div class="col-12 col-md-6 col-lg-4">
                            <div class="card h-100 border-0 shadow-sm rounded-4 p-3 bg-white">
                                <div class="d-flex align-items-center justify-content-between mb-3">
                                    <div class="d-flex align-items-center gap-3">
                                        <div class="rounded-3 bg-primary-subtle text-primary p-2 d-flex align-items-center justify-content-center" style="width: 44px; height: 44px;">
                                            <i class="bi ${bank.logo_icon || 'bi-bank'} fs-4"></i>
                                        </div>
                                        <div>
                                            <h6 class="fw-bold text-dark mb-0">${escapeHtml(bank.name)}</h6>
                                            <span class="badge bg-light text-secondary border fs-7">${escapeHtml(bank.symbol)}</span>
                                        </div>
                                    </div>
                                    ${changeBadge}
                                </div>

                                <div class="d-flex align-items-baseline gap-2 mb-3">
                                    <h3 class="fw-bold text-dark mb-0">$${bank.price.toFixed(2)}</h3>
                                    <span class="badge border ${statusBadgeClass} rounded-pill fs-7">${escapeHtml(bank.status)}</span>
                                </div>

                                <div class="row g-2 pt-2 border-top text-secondary small">
                                    <div class="col-6">
                                        <div class="text-muted fs-7">Market Cap</div>
                                        <div class="fw-semibold text-dark">${escapeHtml(bank.market_cap)}</div>
                                    </div>
                                    <div class="col-6">
                                        <div class="text-muted fs-7">Total Assets</div>
                                        <div class="fw-semibold text-dark">${escapeHtml(bank.total_assets)}</div>
                                    </div>
                                    <div class="col-6">
                                        <div class="text-muted fs-7">Net Income</div>
                                        <div class="fw-semibold text-dark">${escapeHtml(bank.net_income)}</div>
                                    </div>
                                    <div class="col-6">
                                        <div class="text-muted fs-7">CET1 Capital Ratio</div>
                                        <div class="fw-semibold text-dark">${escapeHtml(bank.cet1_ratio)}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                });
                financialsGrid.innerHTML = html;
            }
        } catch (e) {
            console.error('Financials fetch error:', e);
        }
    }

    if (refreshFinancialsBtn) {
        refreshFinancialsBtn.addEventListener('click', () => {
            showToast('Refreshing bank financial market data...', true);
            loadFinancials();
        });
    }

    // Load initial news, sources & financials on application startup
    loadNews();
    loadSourcesList();
    loadFinancials();
});
