"""
🎓 Academic Research Tool Super - Version multi-sources optimisée

Sources intégrées: arXiv, PubMed, Crossref, HAL
Réponses compactes et schéma unifié pour préserver le contexte LLM
"""

import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import re
from datetime import datetime, timedelta, timezone
import os

ATOM_NS = {
    'atom': 'http://www.w3.org/2005/Atom',
    'arxiv': 'http://arxiv.org/schemas/atom'
}

@dataclass
class Author:
    name: str
    affiliation: str = ""

@dataclass
class ResearchResult:
    title: str
    authors: List[Author]
    abstract: str
    doi: str
    url: str
    publication_date: str
    journal: str
    source: str
    citations_count: int = 0
    full_text_url: str = ""


class AcademicResearchSuper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Academic-Research-Super/1.0 (Python; Educational Use)'
        }
        self.last_request: Dict[str, Any] = {}

    # ------------------- Utils -------------------
    MONTHS = {
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
        'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
    }

    DATE_FILTER_RE = re.compile(r"(\s+AND\s+)?submittedDate:\[NOW-(\d+)DAYS\s+TO\s+NOW\]", re.IGNORECASE)

    def _extract_date_filter(self, query: str) -> Tuple[str, Optional[datetime]]:
        m = self.DATE_FILTER_RE.search(query)
        if not m:
            return query, None
        days = int(m.group(2))
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        cleaned = self.DATE_FILTER_RE.sub("", query)
        cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
        cleaned = re.sub(r"^(AND|OR)\s+|\s+(AND|OR)$", "", cleaned, flags=re.IGNORECASE).strip()
        return cleaned, cutoff

    def _parse_any_date(self, s: str) -> Optional[datetime]:
        if not s:
            return None
        s = s.strip()
        try:
            if 'T' in s and s.endswith('Z'):
                return datetime.fromisoformat(s.replace('Z', '+00:00'))
            # YYYY-MM-DD
            if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
                return datetime.strptime(s, '%Y-%m-%d').replace(tzinfo=timezone.utc)
            # YYYY-MM
            if re.match(r"^\d{4}-\d{2}$", s):
                return datetime.strptime(s + '-01', '%Y-%m-%d').replace(tzinfo=timezone.utc)
            # YYYY
            if re.match(r"^\d{4}$", s):
                return datetime.strptime(s + '-01-01', '%Y-%m-%d').replace(tzinfo=timezone.utc)
            # PubMed style: '2025 Sep 10' or '2025 Sep'
            m = re.match(r"^(\d{4})\s+([A-Za-z]{3})(?:\s+(\d{1,2}))?$", s)
            if m:
                y = int(m.group(1)); mon = self.MONTHS.get(m.group(2).lower()) or 1; d = int(m.group(3) or 1)
                return datetime(y, mon, d, tzinfo=timezone.utc)
        except Exception:
            return None
        return None

    def _filter_by_cutoff(self, items: List[Dict[str, Any]], cutoff: datetime) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for it in items:
            ts = it.get('publication_date') or ''
            dt = self._parse_any_date(ts)
            if dt is None or dt >= cutoff:
                out.append(it)
        return out

    def _http_get(self, url: str, timeout: int = 20, expect_json: bool = False) -> Any:
        req = urllib.request.Request(url, headers=self.headers)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
            text = data.decode('utf-8', errors='replace')
            if expect_json:
                try:
                    return json.loads(text)
                except Exception:
                    return {}
            return text

    def _norm_str(self, s: str) -> str:
        return (s or '').strip().lower()

    def _make_key(self, it: Dict[str, Any]) -> str:
        doi = self._norm_str(it.get('doi', ''))
        if doi:
            return f"doi::{doi}"
        url = self._norm_str(it.get('url', ''))
        if url:
            return f"url::{url}"
        title = self._norm_str(it.get('title', ''))
        pubdate = self._norm_str(it.get('publication_date', ''))
        if title or pubdate:
            return f"title::{title}|date::{pubdate}"
        return f"idx::{id(it)}"

    def _merge_items(self, a: Dict[str, Any], b: Dict[str, Any], include_abstracts: bool) -> Dict[str, Any]:
        out = dict(a)
        # Prefer non-empty values from either
        for k in ['title','doi','url','publication_date','journal','source','full_text_url']:
            if not out.get(k):
                out[k] = b.get(k) or out.get(k)
        # authors: keep the longer list
        a_auth = a.get('authors') or []
        b_auth = b.get('authors') or []
        out['authors'] = a_auth if len(a_auth) >= len(b_auth) else b_auth
        # abstract: keep longer if allowed, else empty
        if include_abstracts:
            a_abs = a.get('abstract') or ''
            b_abs = b.get('abstract') or ''
            out['abstract'] = a_abs if len(a_abs) >= len(b_abs) else b_abs
        else:
            out['abstract'] = ''
        # citations_count: max
        try:
            out['citations_count'] = max(int(a.get('citations_count') or 0), int(b.get('citations_count') or 0))
        except Exception:
            out['citations_count'] = a.get('citations_count') or b.get('citations_count') or 0
        # full_text_url: prefer non-empty (keep existing if already set)
        if not out.get('full_text_url') and b.get('full_text_url'):
            out['full_text_url'] = b.get('full_text_url')
        return out

    def _deduplicate_and_merge(self, items: List[Dict[str, Any]], include_abstracts: bool) -> List[Dict[str, Any]]:
        by_key: Dict[str, Dict[str, Any]] = {}
        for it in items:
            key = self._make_key(it)
            if key in by_key:
                by_key[key] = self._merge_items(by_key[key], it, include_abstracts)
            else:
                # ensure abstract removed when not included
                cur = dict(it)
                if not include_abstracts:
                    cur['abstract'] = ''
                by_key[key] = cur
        return list(by_key.values())

    # ------------------- arXiv -------------------
    def _arxiv_build_url(self, query: str, start: int, max_results: int) -> str:
        params = {
            'search_query': query,
            'start': str(start),
            'max_results': str(max_results),
            'sortBy': 'submittedDate',
            'sortOrder': 'descending',
        }
        return 'http://export.arxiv.org/api/query?' + urllib.parse.urlencode(params)

    def _arxiv_search(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        url = self._arxiv_build_url(query=query, start=0, max_results=max_results)
        self.last_request = {'provider': 'arxiv', 'url': url}
        xml_text = self._http_get(url, timeout=20, expect_json=False)
        items: List[Dict[str, Any]] = []
        try:
            root = ET.fromstring(xml_text)
            for entry in root.findall('atom:entry', ATOM_NS):
                title = (entry.findtext('atom:title', default='', namespaces=ATOM_NS) or '').strip()
                summary = (entry.findtext('atom:summary', default='', namespaces=ATOM_NS) or '').strip()
                id_url = entry.findtext('atom:id', default='', namespaces=ATOM_NS) or ''
                published = entry.findtext('atom:published', default='', namespaces=ATOM_NS) or ''
                # authors
                authors: List[Dict[str, str]] = []
                for a in entry.findall('atom:author', ATOM_NS):
                    nm = a.findtext('atom:name', default='', namespaces=ATOM_NS) or ''
                    if nm:
                        authors.append({'name': nm})
                doi = entry.findtext('arxiv:doi', default='', namespaces=ATOM_NS) or ''
                journal_ref = entry.findtext('arxiv:journal_ref', default='', namespaces=ATOM_NS) or ''
                # pdf link
                pdf_url = ''
                for link in entry.findall('atom:link', ATOM_NS):
                    if link.get('type') == 'application/pdf':
                        pdf_url = link.get('href') or ''
                        break
                items.append({
                    'title': title,
                    'authors': authors,
                    'abstract': summary,
                    'doi': doi,
                    'url': id_url,
                    'publication_date': published,
                    'journal': journal_ref,
                    'source': 'arxiv',
                    'citations_count': 0,
                    'full_text_url': pdf_url,
                })
        except Exception:
            items = []
        return {'provider': 'arxiv', 'count': len(items), 'items': items, 'request': self.last_request}

    def _arxiv_search_by_author(self, author_name: str, max_results: int = 10) -> Dict[str, Any]:
        # arXiv author query: au:"Lastname, Firstname" or au:"Firstname Lastname"
        q = f'au:"{author_name}"'
        return self._arxiv_search(query=q, max_results=max_results)

    # ------------------- PubMed -------------------
    def _pubmed_esearch(self, query: str, max_results: int) -> List[str]:
        q = urllib.parse.quote(query)
        url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&retmax={max_results}&term={q}"
        data = self._http_get(url, timeout=20, expect_json=True)
        idlist = (((data or {}).get('esearchresult') or {}).get('idlist') or [])
        return idlist[:max_results]

    def _pubmed_esummary(self, pmids: List[str]) -> Dict[str, Any]:
        if not pmids:
            return {}
        ids = ','.join(pmids)
        url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id={ids}"
        return self._http_get(url, timeout=20, expect_json=True)

    def _pubmed_search(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        pmids = self._pubmed_esearch(query, max_results)
        summary = self._pubmed_esummary(pmids)
        result_items: List[Dict[str, Any]] = []
        if not summary:
            return {'provider': 'pubmed', 'count': 0, 'items': [], 'request': {'provider': 'pubmed'}}
        result = (summary.get('result') or {})
        for pmid in pmids:
            item = result.get(pmid)
            if not item:
                continue
            title = item.get('title') or ''
            authors = [{'name': a.get('name')} for a in (item.get('authors') or []) if a.get('name')]
            journal = item.get('fulljournalname') or item.get('source') or ''
            pubdate = item.get('pubdate') or item.get('epubdate') or ''
            doi = item.get('elocationid') or ''
            # Extract DOI if elocationid contains it (e.g., 'doi:10.xxx')
            if doi and doi.lower().startswith('doi:'):
                doi = doi[4:].strip()
            url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
            result_items.append({
                'title': title,
                'authors': authors,
                'abstract': '',  # ESummary ne fournit pas l'abstract; pour l'obtenir: EFetch (non ajouté ici pour limiter les appels)
                'doi': doi,
                'url': url,
                'publication_date': pubdate,
                'journal': journal,
                'source': 'pubmed',
                'citations_count': 0,
                'full_text_url': '',
            })
        return {'provider': 'pubmed', 'count': len(result_items), 'items': result_items, 'request': {'provider': 'pubmed', 'pmids': pmids}}

    def _pubmed_search_by_author(self, author_name: str, max_results: int = 10) -> Dict[str, Any]:
        term = f"{author_name}[Author]"
        return self._pubmed_search(query=term, max_results=max_results)

    # ------------------- Crossref -------------------
    def _crossref_search(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        params = urllib.parse.urlencode({'query': query, 'rows': max_results})
        url = f"https://api.crossref.org/works?{params}"
        data = self._http_get(url, timeout=20, expect_json=True)
        items_in = (((data or {}).get('message') or {}).get('items') or [])
        items: List[Dict[str, Any]] = []
        for it in items_in:
            title = ' '.join((it.get('title') or [])).strip()
            authors = [{'name': f"{a.get('given','')} {a.get('family','')}".strip()} for a in (it.get('author') or []) if a.get('given') or a.get('family')]
            doi = it.get('DOI') or ''
            url = it.get('URL') or ''
            journal = ' '.join((it.get('container-title') or [])).strip()
            # date parts
            issued = (it.get('issued') or {}).get('"date-parts"') or (it.get('issued') or {}).get('date-parts')
            pubdate = ''
            if issued and isinstance(issued, list) and issued:
                parts = issued[0]
                if isinstance(parts, list) and parts:
                    y = parts[0]; m = parts[1] if len(parts) > 1 else 1; d = parts[2] if len(parts) > 2 else 1
                    try:
                        pubdate = f"{int(y):04d}-{int(m):02d}-{int(d):02d}"
                    except Exception:
                        pubdate = str(y)
            cites = it.get('is-referenced-by-count') or 0
            pdf_url = ''
            for lk in (it.get('link') or []):
                if lk.get('content-type') == 'application/pdf' and lk.get('URL'):
                    pdf_url = lk.get('URL'); break
            items.append({
                'title': title,
                'authors': authors,
                'abstract': '',
                'doi': doi,
                'url': url,
                'publication_date': pubdate,
                'journal': journal,
                'source': 'crossref',
                'citations_count': cites,
                'full_text_url': pdf_url,
            })
        return {'provider': 'crossref', 'count': len(items), 'items': items, 'request': {'provider': 'crossref', 'url': url}}

    def _crossref_search_by_author(self, author_name: str, max_results: int = 10) -> Dict[str, Any]:
        params = urllib.parse.urlencode({'query.author': author_name, 'rows': max_results})
        url = f"https://api.crossref.org/works?{params}"
        data = self._http_get(url, timeout=20, expect_json=True)
        # Reuse mapping logic by feeding through _crossref_search on a synthesized 'query' would not apply query.author
        items_in = (((data or {}).get('message') or {}).get('items') or [])
        items: List[Dict[str, Any]] = []
        for it in items_in:
            title = ' '.join((it.get('title') or [])).strip()
            authors = [{'name': f"{a.get('given','')} {a.get('family','')}".strip()} for a in (it.get('author') or []) if a.get('given') or a.get('family')]
            doi = it.get('DOI') or ''
            url = it.get('URL') or ''
            journal = ' '.join((it.get('container-title') or [])).strip()
            issued = (it.get('issued') or {}).get('"date-parts"') or (it.get('issued') or {}).get('date-parts')
            pubdate = ''
            if issued and isinstance(issued, list) and issued:
                parts = issued[0]
                if isinstance(parts, list) and parts:
                    y = parts[0]; m = parts[1] if len(parts) > 1 else 1; d = parts[2] if len(parts) > 2 else 1
                    try:
                        pubdate = f"{int(y):04d}-{int(m):02d}-{int(d):02d}"
                    except Exception:
                        pubdate = str(y)
            cites = it.get('is-referenced-by-count') or 0
            pdf_url = ''
            for lk in (it.get('link') or []):
                if lk.get('content-type') == 'application/pdf' and lk.get('URL'):
                    pdf_url = lk.get('URL'); break
            items.append({
                'title': title,
                'authors': authors,
                'abstract': '',
                'doi': doi,
                'url': url,
                'publication_date': pubdate,
                'journal': journal,
                'source': 'crossref',
                'citations_count': cites,
                'full_text_url': pdf_url,
            })
        return {'provider': 'crossref', 'count': len(items), 'items': items, 'request': {'provider': 'crossref', 'url': url}}

    # ------------------- HAL -------------------
    def _hal_search(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        # HAL Solr API: fields vary; we request a minimal set and map
        fl = ['title_s', 'authFullName_s', 'abstract_s', 'doiId_s', 'uri_s', 'producedDate_s', 'publicationDate_s', 'fileMain_s']
        params = urllib.parse.urlencode({
            'q': query,
            'wt': 'json',
            'rows': max_results,
            'fl': ','.join(fl)
        })
        url = f"https://api.archives-ouvertes.fr/search/?{params}"
        data = self._http_get(url, timeout=20, expect_json=True)
        docs = (((data or {}).get('response') or {}).get('docs') or [])
        items: List[Dict[str, Any]] = []
        for d in docs:
            title = ''
            t = d.get('title_s')
            if isinstance(t, list):
                title = ' '.join(t).strip()
            elif isinstance(t, str):
                title = t
            authors = []
            for nm in (d.get('authFullName_s') or []):
                if isinstance(nm, str) and nm.strip():
                    authors.append({'name': nm.strip()})
            abstract = ''
            a = d.get('abstract_s')
            if isinstance(a, list):
                abstract = ' '.join(a).strip()
            elif isinstance(a, str):
                abstract = a
            doi = d.get('doiId_s') or ''
            url_doc = d.get('uri_s') or ''
            pubdate = d.get('publicationDate_s') or d.get('producedDate_s') or ''
            pdf_url = d.get('fileMain_s') or ''
            items.append({
                'title': title,
                'authors': authors,
                'abstract': abstract,
                'doi': doi,
                'url': url_doc,
                'publication_date': pubdate,
                'journal': '',
                'source': 'hal',
                'citations_count': 0,
                'full_text_url': pdf_url,
            })
        return {'provider': 'hal', 'count': len(items), 'items': items, 'request': {'provider': 'hal', 'url': url}}

    def _hal_search_by_author(self, author_name: str, max_results: int = 10) -> Dict[str, Any]:
        q = f'authFullName_s:"{author_name}"'
        return self._hal_search(query=q, max_results=max_results)

    # ------------------- Limiteurs de taille -------------------
    def _truncate_text(self, s: str, limit: int) -> str:
        if not isinstance(s, str):
            return s
        if limit <= 0:
            return ''
        if len(s) <= limit:
            return s
        return s[: max(0, limit - 1)] + '…'

    def _enforce_size_limits(
        self,
        results: List[Dict[str, Any]],
        notes: List[str],
        max_total_items: int,
        max_abstract_chars: int,
        max_bytes: int,
    ) -> List[Dict[str, Any]]:
        # 1) Troncature champs verbeux
        for it in results:
            if 'abstract' in it and isinstance(it['abstract'], str):
                it['abstract'] = self._truncate_text(it['abstract'], max_abstract_chars)
            # Titre très long (rare): tronque à 512
            if 'title' in it and isinstance(it['title'], str):
                it['title'] = self._truncate_text(it['title'], 512)
            # Limiter le nombre d'auteurs à 20 pour éviter des listes énormes
            if 'authors' in it and isinstance(it['authors'], list) and len(it['authors']) > 20:
                it['authors'] = it['authors'][:20]
        # 2) Limiter le nombre total d'items
        if len(results) > max_total_items:
            notes.append(f"results truncated to max_total_items={max_total_items}")
            results = results[:max_total_items]
        # 3) Limite bytes globale. On coupe des items jusqu'à passer sous la limite.
        def payload_size(cur_results: List[Dict[str, Any]]) -> int:
            payload = {
                'success': True,
                'results': cur_results,
                'notes': notes or None,
            }
            try:
                enc = json.dumps(payload, ensure_ascii=False).encode('utf-8')
                return len(enc)
            except Exception:
                return 10**9
        while results and payload_size(results) > max_bytes:
            results = results[:-1]
        if payload_size(results) > max_bytes:
            # Si même un seul résultat dépasse, tronque davantage les abstracts
            for it in results:
                if 'abstract' in it and isinstance(it['abstract'], str):
                    it['abstract'] = self._truncate_text(it['abstract'], max(200, max_abstract_chars // 2))
        if payload_size(results) > max_bytes:
            notes.append("payload still exceeds max_bytes after truncation; consider lowering max_results or max_abstract_chars")
        else:
            notes.append(f"payload size <= {max_bytes} bytes")
        return results

    # ------------------- façade run -------------------
    def run(self, operation: str, **params) -> Dict[str, Any]:
        operation = (operation or 'search_papers').strip()
        sources = params.get('sources') or ['arxiv']
        if isinstance(sources, str):
            sources = [sources]
        max_results = int(params.get('max_results') or 10)
        query = str(params.get('query') or '').strip()
        year_from = params.get('year_from')
        year_to = params.get('year_to')
        include_abstracts = bool(params.get('include_abstracts', True))

        # Limites par défaut (surchageables par params ou variables d'env)
        max_total_items = int(params.get('max_total_items') or os.getenv('ACADEMIC_RS_MAX_ITEMS', '50'))
        max_abstract_chars = int(params.get('max_abstract_chars') or os.getenv('ACADEMIC_RS_MAX_ABSTRACT_CHARS', '2000'))
        if not include_abstracts:
            max_abstract_chars = 0
        max_bytes = int(params.get('max_bytes') or os.getenv('ACADEMIC_RS_MAX_BYTES', '200000'))  # ~200KB

        if operation == 'search_papers':
            collected: List[Dict[str, Any]] = []
            notes: List[str] = []
            if not query:
                return {"success": False, "error": "query requis"}

            # Extract optional submittedDate filter and clean query for providers
            clean_query, cutoff = self._extract_date_filter(query)
            if clean_query != query:
                notes.append("submittedDate filter detected and applied client-side")

            lower_sources = [s.lower() for s in sources]
            for s in lower_sources:
                try:
                    if s == 'arxiv':
                        data = self._arxiv_search(query=clean_query or query, max_results=max_results)
                    elif s == 'pubmed':
                        data = self._pubmed_search(query=clean_query or query, max_results=max_results)
                    elif s == 'crossref':
                        data = self._crossref_search(query=clean_query or query, max_results=max_results)
                    elif s == 'hal':
                        data = self._hal_search(query=clean_query or query, max_results=max_results)
                    else:
                        notes.append(f"source non supportée: {s}")
                        continue
                    items = data.get('items', [])

                    # Year filter
                    if year_from or year_to:
                        y_from = int(year_from) if year_from else None
                        y_to = int(year_to) if year_to else None
                        kept = []
                        for it in items:
                            dt = self._parse_any_date(it.get('publication_date') or '')
                            if dt is None:
                                kept.append(it)
                                continue
                            if y_from is not None and dt.year < y_from:
                                continue
                            if y_to is not None and dt.year > y_to:
                                continue
                            kept.append(it)
                        items = kept

                    # Cutoff filter (NOW-XDAYS)
                    if cutoff is not None:
                        items = self._filter_by_cutoff(items, cutoff)

                    collected.extend(items)
                except Exception as e:
                    notes.append(f"{s} error: {e}")

            # Déduplication + fusion multi-sources
            unique_results = self._deduplicate_and_merge(collected, include_abstracts=include_abstracts)

            # Tri global par date descendante
            def sort_key(it: Dict[str, Any]):
                dt = self._parse_any_date(it.get('publication_date') or '')
                # None -> plus ancien
                return dt or datetime(1900,1,1, tzinfo=timezone.utc)
            unique_results.sort(key=sort_key, reverse=True)

            # Appliquer les limites de taille avant retour
            bounded = self._enforce_size_limits(
                results=unique_results,
                notes=notes,
                max_total_items=max_total_items,
                max_abstract_chars=max_abstract_chars,
                max_bytes=max_bytes,
            )

            unsupported = [s for s in sources if s.lower() not in ('arxiv','pubmed','crossref','hal')]
            if unsupported:
                notes.append(f"sources non supportées dans cette implémentation: {unsupported}")
            return {
                "success": True,
                "results": bounded,
                "source_count": len(sources),
                "notes": notes or None
            }

        if operation == 'search_authors':
            author_name = str(params.get('author_name') or '').strip()
            if not author_name:
                return {"success": False, "error": "author_name requis"}
            notes: List[str] = []
            collected: List[Dict[str, Any]] = []
            lower_sources = [s.lower() for s in sources]
            for s in lower_sources:
                try:
                    if s == 'arxiv':
                        data = self._arxiv_search_by_author(author_name=author_name, max_results=max_results)
                    elif s == 'pubmed':
                        data = self._pubmed_search_by_author(author_name=author_name, max_results=max_results)
                    elif s == 'crossref':
                        data = self._crossref_search_by_author(author_name=author_name, max_results=max_results)
                    elif s == 'hal':
                        data = self._hal_search_by_author(author_name=author_name, max_results=max_results)
                    else:
                        notes.append(f"source non supportée: {s}")
                        continue
                    items = data.get('items', [])
                    collected.extend(items)
                except Exception as e:
                    notes.append(f"{s} error: {e}")

            # Déduplication + tri
            unique_results = self._deduplicate_and_merge(collected, include_abstracts=include_abstracts)
            def sort_key(it: Dict[str, Any]):
                dt = self._parse_any_date(it.get('publication_date') or '')
                return dt or datetime(1900,1,1, tzinfo=timezone.utc)
            unique_results.sort(key=sort_key, reverse=True)

            # Limites de taille
            bounded = self._enforce_size_limits(
                results=unique_results,
                notes=notes,
                max_total_items=max_total_items,
                max_abstract_chars=max_abstract_chars,
                max_bytes=max_bytes,
            )

            unsupported = [s for s in sources if s.lower() not in ('arxiv','pubmed','crossref','hal')]
            if unsupported:
                notes.append(f"sources non supportées dans cette implémentation: {unsupported}")
            return {
                "success": True,
                "results": bounded,
                "source_count": len(sources),
                "notes": notes or None
            }

        if operation in ("get_paper_details", "get_citations"):
            return {"success": False, "error": f"operation '{operation}' non implémentée dans cette version"}

        return {"success": False, "error": f"operation inconnue: {operation}"}


_tool = AcademicResearchSuper()

_SPEC_DIR = Path(__file__).resolve().parent.parent / "tool_specs"

def _load_spec_override(name: str) -> Dict[str, Any] | None:
    try:
        p = _SPEC_DIR / f"{name}.json"
        if p.is_file():
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return None

def run(**params) -> Dict[str, Any]:
    try:
        operation = params.pop('operation', 'search_papers')
        return _tool.run(operation=operation, **params)
    except Exception as e:
        return {"success": False, "error": str(e)}

def spec() -> Dict[str, Any]:
    base = {
        "type": "function",
        "function": {
            "name": "academic_research_super",
            "displayName": "Research",
            "description": "Recherche académique multi-sources (arXiv, PubMed, Crossref, HAL).",
            "parameters": {
                "type": "object",
                "additionalProperties": True
            }
        }
    }
    override = _load_spec_override("academic_research_super")
    if override and isinstance(override, dict):
        fn = base.get("function", {})
        ofn = override.get("function", {})
        if ofn.get("displayName"):
            fn["displayName"] = ofn["displayName"]
        if ofn.get("description"):
            fn["description"] = ofn["description"]
        if ofn.get("parameters"):
            fn["parameters"] = ofn["parameters"]
    return base
