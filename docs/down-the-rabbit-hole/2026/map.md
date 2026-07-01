# Down The Rabbit Hole 2026 Map

Numbered locations from the map:

- `4` = Bossa Nova, in "Eden"
- `14` = Radiate VI, in "Het Bos"

```svg
<svg viewBox="0 0 1900 520" width="100%" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Down The Rabbit Hole stage flow map">
    <defs>
        <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#333"/>
        </marker>
        <style>
            .line { stroke: #333; stroke-width: 2; fill: none; marker-end: url(#arrow); }
            .stage { fill: #f6d365; stroke: #7c4d00; stroke-width: 2; }
            .main-stage { fill: #f39c12; stroke: #7c2d12; stroke-width: 4; }
            .access { fill: #d0e0ff; stroke: #1d4ed8; stroke-width: 2; }
            .dot { fill: #fff; stroke: #333; stroke-width: 2; }
            .node-text { font: 600 15px "Segoe UI", Arial, sans-serif; fill: #111; text-anchor: middle; dominant-baseline: middle; }
        </style>
    </defs>

    <!-- Top row branches (both on the same row) -->
    <rect class="stage" x="430" y="80" width="100" height="40" rx="0"/>
    <text class="node-text" x="480" y="100">Bossa Nova</text>

    <rect class="stage" x="550" y="80" width="70" height="40" rx="0"/>
    <text class="node-text" x="585" y="100">Rex</text>

    <rect class="stage" x="640" y="80" width="110" height="40" rx="0"/>
    <text class="node-text" x="695" y="100">Holding</text>

    <path class="line" d="M530,100 L550,100"/>
    <path class="line" d="M620,100 L640,100"/>

    <rect class="stage" x="940" y="80" width="100" height="40" rx="0"/>
    <text class="node-text" x="990" y="100">Radiate VI</text>

    <rect class="stage" x="1060" y="80" width="130" height="40" rx="0"/>
    <text class="node-text" x="1125" y="100">Idyllische Veldje</text>

    <rect class="stage" x="1210" y="80" width="150" height="40" rx="0"/>
    <text class="node-text" x="1285" y="100">CROQUE Madame</text>

    <path class="line" d="M1040,100 L1060,100"/>
    <path class="line" d="M1190,100 L1210,100"/>

    <!-- Main line nodes (straight horizontal line) -->
    <rect class="access" x="60" y="300" width="170" height="62" rx="0"/>
    <text class="node-text" x="145" y="331">Entrance</text>

    <rect class="main-stage" x="260" y="309" width="140" height="44" rx="0"/>
    <text class="node-text" x="330" y="331">Teddy Widder</text>

    <rect class="main-stage" x="790" y="309" width="130" height="44" rx="0"/>
    <text class="node-text" x="855" y="331">Fuzzy Lop</text>

    <rect class="stage" x="1360" y="309" width="140" height="44" rx="0"/>
    <text class="node-text" x="1430" y="331">Bizarre</text>

    <rect class="main-stage" x="1660" y="309" width="100" height="44" rx="0"/>
    <text class="node-text" x="1710" y="331">Hotot</text>

    <!-- Main line connectors (straight) -->
    <path class="line" d="M230,331 L260,331"/>
    <path class="line" d="M400,331 L790,331"/>
    <path class="line" d="M920,331 L1360,331"/>
    <path class="line" d="M1500,331 L1660,331"/>

    <!-- Main-line split/rejoin dots -->
    <circle class="dot" cx="430" cy="331" r="6"/>
    <circle class="dot" cx="760" cy="331" r="6"/>
    <circle class="dot" cx="940" cy="331" r="6"/>
    <circle class="dot" cx="1580" cy="331" r="6"/>

    <!-- Split/rejoin connectors -->
    <!-- Teddy -> branch 1 -> Fuzzy -->
    <path class="line" d="M430,331 L430,100"/>
    <path class="line" d="M750,100 L760,100 L760,331"/>

    <!-- Fuzzy -> branch 2 -> The Bizarre -->
    <path class="line" d="M940,331 L940,100"/>
    <path class="line" d="M1360,100 L1360,250 L1580,250 L1580,331"/>
</svg>
```

## Notes

- The main path runs from Entrance to Hotot through Teddy Widder, Fuzzy Lop, and The Bizarre.
- A side branch leaves Teddy Widder and runs through Bossa Nova, Rex, and Holding before rejoining at Fuzzy Lop.
- A second side branch leaves Fuzzy Lop and runs through Radiate VI, Idyllische Veldje, and the CROQUE Madame before rejoining at The Bizarre.
