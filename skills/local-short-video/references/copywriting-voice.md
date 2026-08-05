# Copywriting and Voice

## Copy rules

- Start with a concrete hook: subject, benefit, occasion, problem, or visible surprise.
- Organize the middle into two or three clear idea groups that match the edit.
- End with one direct next action appropriate to the video.
- Prefer specific nouns and visible details over generic praise.
- Never claim price, quality, durability, location, availability, performance, or safety without user-provided facts or visible support.
- Keep names, addresses, model numbers, and legal wording exactly as provided.
- For a category video, alternate close product views with wider context footage.
- For a location montage, group locations into one compact segment unless the user asks for individual sections.
- Save the final spoken script verbatim. Put translations in separate files; never feed a review translation into TTS by accident.

## Structure patterns

### Product or category showcase

1. Name the category and immediate benefit.
2. Show two to four visible varieties, uses, or details.
3. Add a grounded value statement supplied by the user.
4. Close with where or how to discover, compare, reserve, or buy.

### Store, venue, or service

1. Name the place or service and the reason to visit.
2. Give verified location or access information.
3. Walk through visible areas, offerings, or experience.
4. Close with one invitation.

### Event or campaign

1. Lead with the event and date or urgency.
2. State the verified offer or activity.
3. Show what participants can expect.
4. Close with the required action and deadline.

### Tutorial or explainer

1. State the outcome.
2. Present steps in the same order as the footage.
3. Mention only essential cautions.
4. Recap the result and next action.

## Voice selection

Use `edge-tts` as the default portable provider because it exposes a broad multilingual voice catalog and can produce audio plus WebVTT timing in one run.

Do not hardcode one voice for every project. Filter the live catalog by locale, then audition candidates. Favor natural pronunciation over maximum speed. A lively commercial read usually starts around `+6%` to `+16%` rate and `+0Hz` to `+10Hz` pitch; treat these as audition ranges, not universal defaults.

For calm explanation, reduce rate and pitch. For energetic promotion, increase them moderately. Reject clipped consonants, unnatural proper names, unstable volume, or a voice whose perceived age and tone conflict with the subject.

If the user supplies recorded narration, require matching SRT/VTT or an approved transcription workflow before final rendering. Do not guess timestamps.
