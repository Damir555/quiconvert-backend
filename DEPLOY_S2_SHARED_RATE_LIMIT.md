# S2 — postavljanje zajedničkog rate limitera

Ovo izdanje zamjenjuje zaseban Python brojač svakog procesa atomskim zajedničkim
Redis/Valkey brojačem. Nemoj pokretati novu seriju produkcijskih PDF testova
prije dovršetka postavljanja u nastavku.

## Postojeći Render servis kojim se upravlja ručno

1. U Render Dashboardu odaberi **New > Key Value**.
2. Nazovi ga `quiconvert-rate-limit`.
3. Odaberi istu regiju u kojoj je `quiconvert-backend`.
4. Za provjeru odaberi Free plan, ostavi vanjski pristup isključenim i izradi
   instancu.
5. Otvori novu Key Value instancu i kopiraj njezin **Internal URL**.
6. Otvori `quiconvert-backend > Environment` i dodaj:

   - `REDIS_URL` = the copied internal URL
   - `REQUIRE_SHARED_RATE_LIMIT` = `true`
   - `DAILY_LIMIT_FREE` = `5`
   - `USAGE_TIMEZONE` = `Europe/Zagreb`

7. Spremi postavke okruženja.
8. Pošalji S2 granu i pokreni deploy tek nakon što varijable postoje.

Redis URL nemoj stavljati u Git, snimke zaslona, poruke ili izvorne datoteke.

## Render servis kojim upravlja Blueprint

Priloženi `render.yaml` izrađuje Key Value instancu, povezuje je preko
`REDIS_URL` i automatski zahtijeva zajednički limiter. Prije odobravanja pregledaj
predložene Render Blueprint promjene kako se postojeći web servis ne bi
duplicirao.

## Pravilo provjere

Prvo lokalno pokreni sve testove. Nakon deploya:

1. Potvrdi da su Render deploy i Key Value veza ispravni.
2. Pošalji jedan običan produkcijski PDF zahtjev i provjeri status te rate-limit
   zaglavlja.
3. Zaustavi testiranje. Cijeli slijed provjeri u staging okruženju sa zasebnim
   prefiksom ključeva i nižim limitom.

Free Render Key Value plan dijeli brojače među procesima, ali ih ne čuva nakon
restarta spremišta. Prije aktiviranja plaćenih pretplata ili strogog obračuna
kvota prijeđi na plaćeni plan s trajnim spremanjem.
