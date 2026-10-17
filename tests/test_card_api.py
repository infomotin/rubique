"""FastAPI mobile card API tests.

Covers the ``/api/v1/cards`` router: catalogue, wallet + hash-chained ledger,
stakeless practice tables (create / resume / move / illegal rejection /
finish) and the real-money classic tables the mobile client drives through
`models.classic_arena`.
"""

import unittest

from fastapi.testclient import TestClient

from fastapi_app.main import app
from fastapi_app.session_manager import encode_flask_cookie
from models.db import init_database, query_one
from models.user_model import UserModel
from models import classic_arena as arena
from models.card_club import economy, practice
from models.card_club.engines import CATALOG as CLUB_CATALOG


class CardApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_database()
        cls.client = TestClient(app)

    # ------------------------------------------------------------------ tools
    def make_user(self, prefix):
        import uuid
        name = f"{prefix}_{uuid.uuid4().hex[:8]}"
        uid = UserModel.create_user(name, f"{name}@mobile.test",
                                    "password123", "1995-04-12")
        return int(uid), name

    def cookie_for(self, uid, name, role="user"):
        return {"session": encode_flask_cookie(
            {"user_id": int(uid), "username": name, "role": role})}

    def api(self, method, url, cookie=None, body=None):
        fn = getattr(self.client, method)
        kwargs = {}
        if cookie:
            kwargs["cookies"] = cookie
        if body is not None:
            kwargs["json"] = body
        res = fn(url, **kwargs)
        try:
            return res.status_code, res.json()
        except Exception:
            return res.status_code, {}

    # --------------------------------------------------------------- catalogue
    def test_catalog_lists_classic_and_club(self):
        code, data = self.api("get", "/api/v1/cards/catalog")
        self.assertEqual(code, 200)
        slugs = [g["slug"] for g in data["classic"]]
        self.assertEqual(slugs, [g["slug"] for g in practice.CATALOG])
        for expected in ("29", "spades", "hearts", "bridge"):
            self.assertIn(expected, slugs)
        self.assertIn("rummy", [c["slug"] for c in data["club"]])
        self.assertEqual(data["bet_limit"], economy.MAX_BET_LIMIT)

    # ----------------------------------------------------------------- wallet
    def test_wallet_requires_a_session(self):
        code, data = self.api("get", "/api/v1/cards/wallet")
        self.assertEqual(code, 401)
        code, data = self.api("get", "/api/v1/cards/practice")
        self.assertEqual(code, 401)

    def test_wallet_and_ledger_match(self):
        uid, name = self.make_user("wallet")
        economy.replenish_wallet(uid, 250)
        ck = self.cookie_for(uid, name)

        code, data = self.api("get", "/api/v1/cards/wallet", cookie=ck)
        self.assertEqual(code, 200, data)
        self.assertTrue(data["success"])
        self.assertGreaterEqual(data["personal"], 250)

        code, entries = self.api("get", "/api/v1/cards/ledger?limit=10", cookie=ck)
        self.assertEqual(code, 200)
        self.assertTrue(entries["success"])
        self.assertTrue(entries["entries"], "the grant must be on the ledger")
        top = entries["entries"][0]
        for key in ("seq", "amount", "balance_after", "entry_type", "entry_hash"):
            self.assertIn(key, top)
        # the newest entry's running balance is the wallet balance
        self.assertEqual(top["balance_after"], data["personal"])

    # --------------------------------------------------------------- practice
    def test_practice_deal_runs_to_the_end(self):
        uid, name = self.make_user("practice")
        ck = self.cookie_for(uid, name)

        code, data = self.api("post", "/api/v1/cards/practice", cookie=ck,
                              body={"slug": "spades"})
        self.assertEqual(code, 200, data)
        state = data["state"]
        self.assertEqual(state["status"], "active")
        self.assertEqual(state["kind"], "practice")
        self.assertEqual(len(state["hand"]), state["counts"]["0"])
        self.assertNotIn("hands", state)
        game_id = state["game_id"]

        # an out-of-turn card is refused by the engine gate
        code, bad = self.api("post", f"/api/v1/cards/practice/{game_id}/action",
                             cookie=ck, body={"action": "play", "card": "ZZ"})
        self.assertEqual(code, 400, bad)
        self.assertIn("detail", bad)

        moves, settlement = 0, None
        while moves < 400:
            code, data = self.api("get", f"/api/v1/cards/practice/{game_id}",
                                  cookie=ck)
            self.assertEqual(code, 200, data)
            state = data["state"]
            if state.get("over"):
                break
            if not state.get("legal_actions"):
                break
            code, data = self.api(
                "post", f"/api/v1/cards/practice/{game_id}/action",
                cookie=ck, body=state["legal_actions"][0])
            self.assertEqual(code, 200, data)
            moves += 1
        self.assertTrue(state["over"], "practice deal must finish")
        self.assertEqual(state["status"], "finished")
        self.assertGreater(moves, 0)

    def test_practice_resume_and_privacy(self):
        uid, name = self.make_user("resume")
        ck = self.cookie_for(uid, name)
        code, data = self.api("post", "/api/v1/cards/practice", cookie=ck,
                              body={"slug": "hearts"})
        self.assertEqual(code, 200, data)
        game_id = data["state"]["game_id"]

        # the same player resumes the open deal by id and by /active
        code, again = self.api("get", f"/api/v1/cards/practice/{game_id}",
                               cookie=ck)
        self.assertEqual(again["state"]["game_id"], game_id)
        code, active = self.api("get", "/api/v1/cards/practice/active", cookie=ck)
        self.assertEqual(active["state"]["game_id"], game_id)

        # a stranger cannot read or move it
        uid2, name2 = self.make_user("nosy")
        ck2 = self.cookie_for(uid2, name2)
        code, denied = self.api("get", f"/api/v1/cards/practice/{game_id}",
                                cookie=ck2)
        self.assertEqual(code, 403, denied)
        code, denied = self.api("post",
                                f"/api/v1/cards/practice/{game_id}/action",
                                cookie=ck2, body={"action": "pass"})
        self.assertEqual(code, 403, denied)

        code, done = self.api("delete", f"/api/v1/cards/practice/{game_id}",
                              cookie=ck)
        self.assertEqual(code, 200, done)
        self.assertIsNone(practice.active_game(uid))

    def test_practice_rejects_unknown_slug(self):
        uid, name = self.make_user("badslug")
        ck = self.cookie_for(uid, name)
        code, data = self.api("post", "/api/v1/cards/practice", cookie=ck,
                              body={"slug": "chess"})
        self.assertEqual(code, 400)
        self.assertIn("detail", data)

    # ---------------------------------------------------------- classic tables
    def test_classic_money_table_settles_the_pot(self):
        uid, name = self.make_user("money")
        economy.replenish_wallet(uid, 300)
        ck = self.cookie_for(uid, name)

        code, data = self.api("post", "/api/v1/cards/classic", cookie=ck,
                              body={"slug": "hearts", "mode": "ai", "stake": 25})
        self.assertEqual(code, 200, data)
        game_id = data["game_id"]
        self.assertEqual(data["state"]["status"], "active")
        self.assertEqual(economy.balances_view(uid)["personal"], 275)

        state, settlement, moves = data["state"], None, 0
        while moves < 400 and not state.get("over"):
            if not state.get("legal_actions"):
                break
            code, data = self.api("post",
                                  f"/api/v1/cards/classic/{game_id}/action",
                                  cookie=ck, body=state["legal_actions"][0])
            self.assertEqual(code, 200, data)
            state, settlement = data["state"], data.get("settlement")
            moves += 1

        self.assertTrue(state["over"], "money table must finish")
        self.assertIsNotNone(settlement)
        self.assertEqual(settlement["pot"], 100)
        self.assertIn(settlement["kind"], ("settlement", "refund"))
        self.assertTrue(economy.verify_ledger()["ok"])

        # once finished it is no longer the player's active table
        code, data = self.api("get", "/api/v1/cards/classic/active", cookie=ck)
        self.assertEqual(code, 200)
        self.assertIsNone(data["state"])

    def test_classic_action_is_rejected_for_a_stranger(self):
        uid, name = self.make_user("owner")
        ck = self.cookie_for(uid, name)
        code, data = self.api("post", "/api/v1/cards/classic", cookie=ck,
                              body={"slug": "29", "mode": "ai", "stake": 0})
        game_id = data["game_id"]

        uid2, name2 = self.make_user("intruder")
        ck2 = self.cookie_for(uid2, name2)
        code, denied = self.api("post",
                                f"/api/v1/cards/classic/{game_id}/action",
                                cookie=ck2, body={"action": "bid", "value": 20})
        self.assertIn(code, (403, 404), denied)
        code, denied = self.api("get", f"/api/v1/cards/classic/{game_id}",
                                cookie=ck2)
        self.assertEqual(code, 404, denied)

    def test_classic_group_table_starts_with_bots(self):
        uid, name = self.make_user("host")
        ck = self.cookie_for(uid, name)
        code, data = self.api("post", "/api/v1/cards/classic", cookie=ck,
                              body={"slug": "spades", "mode": "group",
                                    "group_id": 0, "stake": 0})
        self.assertEqual(code, 200, data)
        game_id = data["game_id"]
        self.assertEqual(data["state"]["status"], "waiting")

        code, data = self.api("post", f"/api/v1/cards/classic/{game_id}/start",
                              cookie=ck)
        self.assertEqual(code, 200, data)
        state = data["state"]
        self.assertEqual(state["status"], "active")
        self.assertEqual(state["human_seats"], [0])
        self.assertEqual(sum(1 for p in state["players"] if p["is_bot"]), 3)

        code, tables = self.api("get", "/api/v1/cards/classic/tables?group_id=0",
                                cookie=ck)
        self.assertEqual(code, 200)
        self.assertIn(game_id, [t["id"] for t in tables["tables"]])

    def test_classic_stake_is_refunded_when_the_table_is_cancelled(self):
        uid, name = self.make_user("canceller")
        economy.replenish_wallet(uid, 150)
        ck = self.cookie_for(uid, name)
        before = economy.balances_view(uid)["personal"]

        code, data = self.api("post", "/api/v1/cards/classic", cookie=ck,
                              body={"slug": "whist", "mode": "group",
                                    "group_id": 0, "stake": 50})
        game_id = data["game_id"]
        self.assertEqual(economy.balances_view(uid)["personal"], before - 50)

        code, data = self.api("post", f"/api/v1/cards/classic/{game_id}/cancel",
                              cookie=ck)
        self.assertEqual(code, 200, data)
        self.assertEqual(economy.balances_view(uid)["personal"], before)
        self.assertTrue(economy.verify_ledger()["ok"])
        row = query_one("SELECT status FROM classic_games WHERE id = %s",
                        "SELECT status FROM classic_games WHERE id = ?",
                        (game_id,))
        status = row["status"] if isinstance(row, dict) else row[0]
        self.assertEqual(status, "cancelled")


if __name__ == "__main__":
    unittest.main()
