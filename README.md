# MARS – Simon och Ralfs spel

Du är astronauten Mark Watney, ensam kvar på Mars. Laga raketen, odla potatis,
rädda robotarna från det kraschade skeppet Daidalos och överlev stormar och martianer.

## Starta

    .venv/bin/python main.py

Går det segt? Starta med ett mindre fönster: `.venv/bin/python main.py 960x540`

Första gången på en ny dator:

    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt

## Spela utan Python (Windows, Mac, Linux)

GitHub bygger spelet automatiskt varje gång något pushas till `main`
(se `.github/workflows/bygg.yml`). Gå till fliken **Actions** på GitHub, klicka på
senaste körningen och ladda ner `Mars-Windows`, `Mars-Mac` eller `Mars-Linux` längst ner.

Vill du göra en riktig version att dela ut, skapa en tagg:

    git tag v1.0
    git push origin v1.0

Då hamnar zip-filerna under **Releases** på GitHub.

- **Windows:** packa upp och kör `Mars.exe`. Klicka "Mer information" → "Kör ändå" om Windows varnar.
- **Mac:** packa upp, högerklicka på `Mars` → "Öppna" första gången (appen är inte signerad).
  Bygget är för Mac med Apple-chip (M1 och nyare).
- **Linux:** packa upp och kör `Mars/Mars`.

## Tangenter

| Tangent | Vad den gör |
|---|---|
| W A S D | gå / köra rovern |
| Mus eller piltangenter | titta |
| Shift | spring |
| Mellanslag | hoppa (högt – det är Mars!) |
| E | använd, öppna, gå in och ut |
| F | ät (bara inomhus eller i rovern) |
| Vänster musknapp | skjut med laserborren |
| V | se Mark utifrån |wwwwasdsssssss
| H | hjälp |
| M | släpp / fånga musen |
| F11 | helskärm |
| Esc | paus |

## Filerna

- `main.py` – startar spelet
- `spel.py` – spelets regler: överlevnad, väder, robotar, martianer, instrument
- `modeller.py` – hur alla figurer och byggnader ser ut
- `mesh_bygge.py` – verktyg som bygger 3D-modeller av enkla former
- `grafik.py` – ljus, dimma, himmel och texturer

Vill du ändra något? Högst upp i `spel.py` står till exempel hur lång en dag är (`SOL`)
och var robotarna och raketdelarna ligger.
