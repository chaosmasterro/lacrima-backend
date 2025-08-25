import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Bet
import requests
from django.conf import settings

def ping(request):
    return JsonResponse({"status": "ok"})

DEFAULT_SPORTS = ["basketball_nba", "baseball_mlb", "soccer_epl"]  # e.g., add "soccer_usa_mls"

@require_http_methods(["GET"])
def bets_list(request):
    bets = Bet.objects.all()
    data = [{
        "id": str(b.id),
        "eventId": b.event_id,
        "teamA": b.team_a,
        "teamB": b.team_b,
        "sport": b.sport,
        "odds": b.odds,
        "stake": b.stake,
        "status": b.status,
        "created_at": b.created_at.isoformat(),
    } for b in bets]
    return JsonResponse(data, safe=False)

@csrf_exempt
@require_http_methods(["POST"])
def place_bet(request):
    try:
        body = json.loads(request.body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("Invalid JSON")

    # required
    event_id = body.get("eventId")
    stake = body.get("stake")
    team_a = body.get("teamA")
    team_b = body.get("teamB")
    sport = body.get("sport")
    odds = body.get("odds")   # may be null

    if not event_id or not team_a or not team_b or not sport:
        return HttpResponseBadRequest("Missing required fields")
    try:
        stake = float(stake)
        if stake <= 0:
            return HttpResponseBadRequest("Stake must be > 0")
    except Exception:
        return HttpResponseBadRequest("Invalid stake")

    bet = Bet.objects.create(
        event_id=event_id,
        team_a=team_a,
        team_b=team_b,
        sport=sport,
        odds=odds,
        stake=stake,
        status="pending",
    )
    return JsonResponse({"success": True, "id": str(bet.id)}, status=201)

def events(request):
    """
    GET /api/events/?sports=basketball_nba,baseball_mlb,soccer_epl
    Returns normalized events for selected sports.
    """
    api_key = settings.ODDS_API_KEY

    # Allow query param override, else use defaults
    raw = request.GET.get("sports")
    sports = [s.strip() for s in raw.split(",")] if raw else DEFAULT_SPORTS

    all_events = []
    for sport in sports:
        url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds"
        params = {
            "regions": "us",         # US books
            "markets": "h2h",        # moneyline
            "oddsFormat": "decimal", # your frontend assumes decimal like 1.85, 2.10, etc.
            "apiKey": api_key,
        }

        r = requests.get(url, params=params, timeout=15)
        if r.status_code != 200:
            # Keep going for other sports but note the failure
            continue

        try:
            data = r.json()
        except Exception:
            continue

        for ev in data:
            home = ev.get("home_team")
            away = ev.get("away_team")
            commence = ev.get("commence_time")
            event_id = ev.get("id")  # Odds API event id

            # Defensive odds extraction: bookmakers -> markets[h2h] -> outcomes (home/away)
            avg_price = None
            try:
                bmk = ev["bookmakers"][0]
                market = bmk["markets"][0]  # "h2h"
                outcomes = market.get("outcomes", [])
                if outcomes:
                    # If we want a single number for UI, use the average of the two prices
                    prices = [o.get("price") for o in outcomes if isinstance(o.get("price"), (int, float))]
                    if prices:
                        avg_price = round(sum(prices) / len(prices), 2)
            except Exception:
                pass

            all_events.append({
                "id": event_id,
                "teamA": away,         # you can flip these if you prefer home first
                "teamB": home,
                "sport": sport,
                "odds": avg_price,     # single number for your current UI
                "start_time": commence,
            })

    return JsonResponse(all_events, safe=False)
