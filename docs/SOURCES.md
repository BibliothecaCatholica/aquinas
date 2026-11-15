# Corpus provenance and editorial boundaries

Initial corpus: Thomas Aquinas, Summa Theologiae, I and I-II. Translation: Fathers of the English Dominican Province. Digital transcriptions: Project Gutenberg 17611 and 17897, Benziger Brothers text, credits Sandra K. Perry and David McClamrock. The exact embedded editorial note describes transcription corrections and supplementation. These are the downloaded digital editions, not a claim to have independently collated every line against a print exemplar.

The Gutenberg catalog identifies these editions as public domain in the USA. Full ebook notices remain unchanged in raw source files. Bibliotheca Catholica's Summa I edition page identifies the same Gutenberg source and describes an earlier spot check against pre-1931 printings; that site's check is secondary evidence and is not our own print collation. Source access and provenance are verified; independent scholarly verification of all textual readings and answer-key interpretations remains pending. Publication outside the US or of derived releases requires the relevant rights review. No assumption is made that a modern translation is reusable because Aquinas is medieval.

Sources checked 2026-11-14:

- https://www.gutenberg.org/ebooks/17611
- https://www.gutenberg.org/ebooks/17897
- https://bibliothecacatholica.com/summa/1/
- https://www.gutenberg.org/policy/license.html

The manifest records URL, edition description, retrieval date, SHA-256 of exact downloaded bytes and raw path. Parsed article and section offsets count Unicode characters in the UTF-8 decoded string, preserving CRLF and original spelling; they are not byte offsets. Every section carries original text. Only derived metadata may be reconciled. Conflicting ordinal versus bracket article numbers are recorded in metadata_note, along with the printed number. I q.42 a.4 has the printed bracket Q.4; its title and surrounding question support the recorded index correction. Three articles lack ARTICLE headings: I q.71 a.1 and q.72 a.1 are one-article questions, and I-II q.23 a.1 precedes SECOND ARTICLE. These derived identifiers are disclosed; words are never silently changed. `results/corpus-audit.json` enumerates the discrepancies.

Parts contain 584 and 619 articles respectively. Each article retains part/question/article, objections, sed contra, respondeo and replies. FTS5 indexes sections split at paragraph boundaries (target 2,400 characters; a single long paragraph can exceed that target). Retrieval results label the section kind so that an objection is not presented as Aquinas's conclusion. Parser output is tied to these editions; another source format requires a reviewed parser rather than automatic best guesses. Raw bytes retain any preambles outside indexed article boundaries. No whole external catalogue was imported.

## Expansion queue, not imported corpus

| Work | Candidate edition/access | Status |
|---|---|---|
| Summa contra Gentiles | Joseph Rickaby, Of God and His Creatures, 1905; CCEL | Candidate older abridged/annotated translation. Verify print edition, reuse terms, chapter alignment, and distinguish Rickaby notes before import. Do not label it an unabridged Aquinas corpus. |
| De ente et essentia | Latin critical text or an explicitly licensed translation | Translation and electronic edition rights not established in this build; not imported. |
| De veritate | A specifically cleared translation or Latin edition | Not imported; no inference of permission from online accessibility. |
| Nicomachean Ethics | Gutenberg 8438 | Candidate machine-readable edition; translator/edition metadata and passage structure still to audit. |
| Metaphysics | An identified older translation or licensed edition | Not imported; modern translator rights unresolved. |
| Augustine, selected works | Gutenberg/CCEL older Confessions or City of God translation | Select exact translator/edition and verify rights before ingestion. |

Candidate references: https://www.ccel.org/ccel/aquinas/gentiles (Rickaby), https://www.gutenberg.org/ebooks/8438 (Ethics), https://undpress.nd.edu/9780268016777/summa-contra-gentiles/ (a modern published translation, not imported). Full expansion is deferred deliberately until edition-level provenance, rights, and structure are auditable. This initial version covers two parts of the Summa, not every requested author or work.
