# Dealer List Route Manual QA

1. Direct-load and refresh `/dealers`; expect the public header and dealer cards.
2. Verify desktop/mobile navigation, language switching/RTL, theme persistence, and currency behavior.
3. Verify cards/images/data and Next navigation to `/dealers/[id]`; Back/Forward restores navigation.
4. Verify loading, empty, and failure states; no duplicate request or duplicate header appears.
5. Verify desktop/mobile layout. Search, filter, sort, and pagination are not currently supported by this extracted public list.
