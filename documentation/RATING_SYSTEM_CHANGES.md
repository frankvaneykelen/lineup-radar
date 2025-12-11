# Rating System Changes: Discovery-Focused Weighting

## Problem Statement

The original AI rating system was biased towards established artists with long careers, awards, and festival track records. This created a systematic disadvantage for emerging and new artists, which contradicts the primary purpose of this app: **discovering new artists**.

### Original Bias

The old rating scale guidance was:

```
- 8-9: Critically acclaimed, award-winning artists with strong festival track record
- 6-7: Solid, established acts with good reviews but not breakthrough/groundbreaking
- 4-5: Developing artists, niche appeal, or mixed critical reception
```

This meant:
- New artists were automatically rated 4-5 just for being "developing"
- High ratings required long career history and awards
- Innovation and freshness were not valued as rating factors
- Discovery potential was treated as a limitation, not an asset

## Solution

We've modified the AI enrichment prompt in `scripts/enrich_artists.py` to introduce discovery-focused weighting that values:

1. **Innovation and freshness** as positive attributes
2. **Emerging talent with buzz** as worthy of high ratings (7-9)
3. **Current relevance** over past achievements for established artists
4. **Breakout potential** as a rating factor

### New Rating Scale

```
RATING SCALE (USE THE FULL RANGE - weighted for discoverability):
- 10: Reserved ONLY for universally acclaimed legends (e.g., Radiohead, Beyoncé, Kendrick Lamar level)
- 8-9: Exceptional artists - includes both established acts with strong track record AND exciting emerging artists with innovative sound, strong buzz, or unique artistic vision
- 6-7: Quality artists - solid established acts OR promising new artists with good reviews and interesting musical approach
- 4-5: Developing artists with potential OR established acts with mixed/declining reception
- 1-3: Very limited appeal, poor reviews, or completely unknown
- IMPORTANT: For discovery purposes, FAVOR innovation, freshness, and emerging talent alongside critical acclaim
- NEW/EMERGING artists with buzz, unique sound, or critical excitement should rate 7-9 (not 4-5)
- ESTABLISHED artists should be rated based on their current relevance and live reputation, not just past achievements
- Don't penalize artists for being new - youth, innovation, and freshness are POSITIVE factors
- Artists who are "ones to watch" or have "breakout potential" deserve higher ratings (7-8 range)
```

### Key Changes

1. **8-9 range expanded** to include emerging artists with:
   - Innovative sound
   - Strong buzz/excitement
   - Unique artistic vision
   - Critical excitement

2. **Discovery focus added** with explicit guidance:
   - VALUE innovation, freshness, and emerging talent
   - Treat "new" or "emerging" as POSITIVE attributes
   - Don't penalize artists for being new

3. **Balanced criteria**:
   - Established artists judged on current relevance, not past glory
   - Developing artists with potential can reach 7-8 range
   - "Ones to watch" explicitly deserve 7-8 ratings

## Impact

This change should result in:

- **More balanced ratings** across career stages
- **Higher ratings for emerging artists** with innovative sounds
- **Discovery value reflected** in the rating system
- **Fairer representation** of new talent alongside established acts

## Compatibility

- ✅ Works with existing `rating_boost` parameter for discovery festivals (e.g., Footprints: +1.5)
- ✅ Maintains rating scale boundaries (1-10)
- ✅ Preserves all existing functionality
- ✅ No database schema changes required
- ✅ Existing ratings are preserved (only affects new enrichments)

## Testing

- ✅ All existing unit tests pass (38/40, 2 pre-existing failures unrelated to changes)
- ✅ Python syntax validation passes
- ✅ No breaking changes to API or data structures

## Usage

When running enrichment, the AI will now automatically apply discovery-focused weighting:

```bash
python scripts/enrich_artists.py --festival down-the-rabbit-hole --year 2026 --ai
```

No additional flags or configuration needed. The change is embedded in the AI prompt.

## Future Considerations

- Monitor ratings over time to ensure balance is achieved
- Consider adding a `--strict-mode` flag for traditional rating criteria if needed
- Could add explicit recency weighting based on release dates
- May want to track and report rating distribution statistics

## Related Files

- `scripts/enrich_artists.py` - Main enrichment script with updated prompt
- `festival_helpers/config.py` - Festival configuration with `rating_boost` parameter
- This documentation file

## Credits

Issue reported by: @frankvaneykelen
Implementation: GitHub Copilot Agent
Date: 2025-12-11
