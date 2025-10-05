import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from .models import Bet
import requests

def ping(request):
    return JsonResponse({"status": "ok"})

DEFAULT_SPORTS = ["basketball_nba", "baseball_mlb", "soccer_epl"]

def _as_float(value, default=None):
    try:
        return float(value)
    except Exception:
        return default

def _fee_rates():
    placement = getattr(settings, "PLACEMENT_FEE_RATE", 0.02)
    win = getattr(settings, "WIN_FEE_RATE", 0.05)
    return placement, win

@require_http_methods(["GET"])
def bets_list(request):
    bets = Bet.objects.order_by("-created_at")
    data = [{
        "id": str(b.id),
        "eventId": b.event_id,
        "teamA": b.team_a,
        "teamB": b.team_b,
        "sport": b.sport,
        "odds": b.odds,
        "stake": b.stake,
        "placementFee": getattr(b, "placement_fee", 0.0),
        "totalCharged": getattr(b, "total_charged", b.stake),
        "winFeeRate": getattr(b, "win_fee_rate", getattr(settings, "WIN_FEE_RATE", 0.05)),
        "vipXp": getattr(b, "vip_xp", 1),
        "vipMultiplier": getattr(b, "vip_multiplier", 1.0),
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

    event_id = body.get("eventId")
    team_a   = body.get("teamA")
    team_b   = body.get("teamB")
    sport    = body.get("sport")
    odds     = body.get("odds")            # may be null
    stake    = _as_float(body.get("stake"))

    if not all([event_id, team_a, team_b, sport]) or stake is None:
        return HttpResponseBadRequest("Missing required fields")
    if stake <= 0:
        return HttpResponseBadRequest("Stake must be > 0")

    placement_rate, win_rate = _fee_rates()
    placement_fee = round(stake * placement_rate, 2)
    total_charged = round(stake + placement_fee, 2)

    vip_xp = int(body.get("vipXp", 1))
    vip_multiplier = _as_float(body.get("vipMultiplier"), 1.0) or 1.0

    bet = Bet.objects.create(
        event_id=event_id,
        team_a=team_a,
        team_b=team_b,
        sport=sport,
        odds=odds,
        stake=stake,
        placement_fee=placement_fee,
        total_charged=total_charged,
        vip_xp=vip_xp,
        vip_multiplier=vip_multiplier,
        win_fee_rate=win_rate,
        status="pending",
    )

    return JsonResponse({
        "success": True,
        "id": str(bet.id),
        "stake": bet.stake,
        "placementFee": bet.placement_fee,
        "totalCharged": bet.total_charged,
        "winFeeRate": bet.win_fee_rate,
        "vipXp": bet.vip_xp,
        "vipMultiplier": bet.vip_multiplier,
        "createdAt": bet.created_at.isoformat(),
    }, status=201)

@require_http_methods(["GET"])
def events(request):
    """
    GET /api/events/?sports=basketball_nba,baseball_mlb,soccer_epl
    Returns normalized events for selected sports.
    """
    api_key = settings.ODDS_API_KEY
    raw = request.GET.get("sports")
    sports = [s.strip() for s in raw.split(",")] if raw else DEFAULT_SPORTS

    all_events = []
    for sport in sports:
        url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds"
        params = {
            "regions": "us",
            "markets": "h2h",
            "oddsFormat": "decimal",
            "apiKey": api_key,
        }
        r = requests.get(url, params=params, timeout=15)
        if r.status_code != 200:
            continue

        try:
            data = r.json()
        except Exception:
            continue

        for ev in data:
            home = ev.get("home_team")
            away = ev.get("away_team")
            commence = ev.get("commence_time")
            event_id = ev.get("id")

            avg_price = None
            try:
                bmk = ev["bookmakers"][0]
                market = bmk["markets"][0]
                outcomes = market.get("outcomes", [])
                if outcomes:
                    prices = [o.get("price") for o in outcomes if isinstance(o.get("price"), (int, float))]
                    if prices:
                        avg_price = round(sum(prices) / len(prices), 2)
            except Exception:
                pass

            all_events.append({
                "id": event_id,
                "teamA": away,   # flip if you prefer home first
                "teamB": home,
                "sport": sport,
                "odds": avg_price,
                "start_time": commence,
            })

    return JsonResponse(all_events, safe=False)
