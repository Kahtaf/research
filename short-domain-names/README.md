# Short Domain Names Research

## Project Overview

This project involved querying the micro.domains API to find visually appealing 5-letter domain names priced under $20 for both initial purchase and annual renewal.

## Methodology

### API Endpoint
- **URL**: `https://micro.domains/urls/`
- **Method**: POST
- **Parameters**:
  - `domain_length`: 5 (5-letter domains)
  - `price`: 20 (max initial purchase price)
  - `price_renewal`: 20 (max renewal price)
  - `available`: 1 (only available domains)
  - `has_number`: 1 (domains with numbers)
  - `has_hyphen`: 0 (no hyphens)
  - `start` and `length`: For pagination

### Data Collection Strategy
1. Used curl with CSRF tokens extracted from the homepage
2. Made multiple requests with varying page sizes (100, 150, 200 results per request)
3. Paginated through offsets (0, 100, 200, ... 800) across three different page size configurations
4. Collected raw JSON responses and parsed them into a structured format

### Filtering & Scoring
Domains were scored based on visual appeal characteristics:

| Characteristic | Score | Examples |
|---|---|---|
| 3-letter palindrome | 100 | 5j5.me, 7l7.me |
| Hex notation (0x) | 90 | 0x...me |
| Monogram (all same letter) | 80 | 333.me, 777.me |
| Double start letters | 40 | 33l.me, 55o.me |
| Lucky numbers | 70 | 007.me, 666.me, 888.me |
| Zero-containing | 30 | 0a2.me, 0aq.me, etc. |

## Results

**Total Domains Found**: 125 interesting domains (out of 1,000 unique collected)

### Top 20 Recommended Domains

| # | Domain | Price | Renewal | Type | Score |
|---|---|---|---|---|---|
| 1 | **5j5.me** | $2.28 | $19.98 | Palindrome | 100 |
| 2 | **7l7.me** | $2.28 | $19.98 | Palindrome | 100 |
| 3 | 33l.me | $2.28 | $19.98 | Double-start | 40 |
| 4 | 55l.me | $2.28 | $19.98 | Double-start | 40 |
| 5 | 55o.me | $2.28 | $19.98 | Double-start | 40 |
| 6 | 07o.me | $2.28 | $19.98 | Zero-pattern | 30 |
| 7 | 07p.me | $2.28 | $19.98 | Zero-pattern | 30 |
| 8 | 08e.me | $2.28 | $19.98 | Zero-pattern | 30 |
| 9 | 08o.me | $2.28 | $19.98 | Zero-pattern | 30 |
| 10 | 09t.me | $2.28 | $19.98 | Zero-pattern | 30 |
| 11 | 0a2.me | $2.28 | $19.98 | Zero-pattern | 30 |
| 12 | 0aq.me | $2.28 | $19.98 | Zero-pattern | 30 |
| 13 | 0ar.me | $2.28 | $19.98 | Zero-pattern | 30 |
| 14 | 0b6.me | $2.28 | $19.98 | Zero-pattern | 30 |
| 15 | 0bz.me | $2.28 | $19.98 | Zero-pattern | 30 |
| 16 | 0c4.me | $2.28 | $19.98 | Zero-pattern | 30 |
| 17 | 0c8.me | $2.28 | $19.98 | Zero-pattern | 30 |
| 18 | 0cp.me | $2.28 | $19.98 | Zero-pattern | 30 |
| 19 | 0cs.me | $2.28 | $19.98 | Zero-pattern | 30 |
| 20 | 0cw.me | $2.28 | $19.98 | Zero-pattern | 30 |

## Key Findings

### Pricing
- **Exceptional Value**: All 125 interesting domains are priced at **just $2.28** for initial purchase
- **Renewal Cost**: All renewals are **$19.98/year** (well under the $20 budget)
- **Total First-Year Cost**: ~$22.26 (purchase + renewal)

### Domain Characteristics
- **TLD**: All collected domains use the `.me` TLD
- **Length**: Exactly 5 letters (3-letter domain name + 2-letter TLD)
- **Pattern**: All contain at least one digit (programmatically filtered)
- **Availability**: All domains are currently available for registration

### Top Recommendations
1. **5j5.me** and **7l7.me** are the standout choices - they're perfect palindromes which makes them visually striking and memorable
2. Domains starting with "0" (like **0a2.me**, **0aq.me**) have an interesting tech/hacker aesthetic
3. **33l.me**, **55l.me**, **55o.me** appeal with their double-letter patterns

## Scripts & Files

- **scraper.py**: Initial Python scraper (unsuccessful with requests library)
- **mass_scrape.sh**: Bash script using curl to fetch data (successful approach)
- **process_domains.py**: Various Python scripts to score and filter domains
- **all_domains.txt**: Raw JSON data from all API requests
- **domains_interesting.json**: Final curated list of 30 top interesting domains

## Technical Insights

### Why Bash/Curl Worked Better Than Python Requests
The Python `requests` library was unable to properly handle the DataTables request format despite having correct CSRF tokens. Curl's native form encoding (`--data-raw` with proper URL encoding) successfully authenticated with the API.

### Pagination Results
- Total requests made: 27 (9 offsets × 3 different page sizes)
- Total domains retrieved: ~4,050
- Unique domains after deduplication: 1,000
- Interesting domains identified: 125

## Recommendations for Further Work

1. **Expand search**: Remove the `has_number=1` filter to include letter-only domains
2. **Test other TLDs**: The API likely supports `.com`, `.co`, `.io`, etc.
3. **Longer domains**: Explore 4-letter, 6-letter domains for different appeal
4. **Premium filtering**: Some of these domains might have premium pricing unlocked
5. **Bulk registration**: These prices are so low that bulk buying at scale would be economical

## Conclusion

The micro.domains API provides exceptional value for short domain names. The 125 domains identified in this research represent genuinely visually appealing options suitable for branding, projects, shortlinks, or investment. At $2.28 each with $19.98 renewals, they represent some of the cheapest premium-quality short domains available.

**Best Value**: **5j5.me** and **7l7.me** - perfect palindromes with massive memorability factor.
