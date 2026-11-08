"""Disabled-by-default Discord inbox; Python standard library only.

No import starts polling, reads an environment variable or opens a connection.
``Bridge(config, db_path).handle(message, now=aware_datetime)`` is offline: it
validates an incoming message and atomically records processed ID, optional
request and safe reply in SQLite. It never invokes a shell or an LLM.

``list_requests(Path, limit=20)`` returns reviewable inbox rows for the MCP
coordinator. It returns an empty list if the database does not exist and opens
an existing database read-only. All request statuses start as
``awaiting_review``. There is intentionally no automatic execute endpoint.

Live polling exists only while ``--run`` remains alive (Ctrl+C stops it).
It additionally requires enabled=true, ids_confirmed=true,
credential_rotation_confirmed=true and a nonempty authorized_user_ids list.
The previously exposed token must be revoked/replaced by its owner; this
module cannot confirm rotation and must not be given that old token. The new
bot credential is read only by main(), from LCA_DISCORD_BOT_TOKEN. No secret is
printed. --once still needs --run and all gates. No service/scheduler is made.

Official references read before implementation:
https://docs.discord.com/developers/resources/message#get-channel-messages
https://docs.discord.com/developers/events/gateway#message-content-intent
https://docs.discord.com/developers/topics/rate-limits
GET channel messages needs VIEW_CHANNEL/READ_MESSAGE_HISTORY. Message content
may be empty without MESSAGE_CONTENT privileged intent; this code cannot turn
it on. Requests obey retry_after/Retry-After on 429, at most two total attempts.
401/403 stop. POST transport failure is uncertain and is never auto-retried.

The guild/channel example IDs from planning are not confirmations. Validate
the actual channel's guild before reading messages. REST message objects may
omit guild_id: poll_once enriches it only from that verified channel route.
First polling contact saves the latest ID, without replaying channel history.
Every network request is blocked Monday 08:45 <= time < 09:15 at UTC-03:00.
Secret detection is deliberately conservative, not a complete DLP system;
never submit patient information or credentials through this proof of concept.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import time
from typing import Any, Callable, Mapping
import urllib.error
import urllib.parse
import urllib.request

UTC = timezone.utc
LOCAL = timezone(timedelta(hours=-3))
API_BASE = "https://discord.com/api/v10"
USER_AGENT = "DiscordBot (https://github.com/gmaltad-boop/lca-mvp, 0.1.0)"
MAX_CONTENT = 500
SECRET_PATTERNS = (
    re.compile(r"\b(?:sk-(?:proj-)?|dk-|dt-)[A-Za-z0-9_-]{12,}"),
    re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})"),
    re.compile(r"\b(?:mfa\.[A-Za-z0-9_-]{20,}|[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{6,}\.[A-Za-z0-9_-]{20,})"),
    re.compile(r"\bDRL-(?:[A-Z0-9]{4}-){3}[A-Z0-9]{4}\b", re.I),
    re.compile(r"https://(?:(?:canary|ptb)\.)?discord(?:app)?\.com/api(?:/v[0-9]+)?/webhooks/[0-9]+/[^\s]+", re.I),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\b(?:api[_ -]?key|token|password|senha|secret|authorization)\s*[:=]\s*\S+", re.I),
)


class ConfigError(ValueError):
    pass


class BridgeStop(RuntimeError):
    """Safe classified reason only; never contains response bodies or tokens."""


class ProtectedWindow(BridgeStop):
    pass


class RateLimited(BridgeStop):
    pass


class TransportFailure(BridgeStop):
    pass


def _snowflake(value: Any) -> str:
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ConfigError("snowflake_must_be_numeric")
    result = str(value)
    if not re.fullmatch(r"[1-9][0-9]{0,19}", result) or int(result) >= 2**64:
        raise ConfigError("snowflake_must_be_numeric")
    return result


def _aware(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError("timezone_aware_datetime_required")
    return value.astimezone(UTC)


def protected_window(now: datetime) -> bool:
    local = _aware(now).astimezone(LOCAL)
    minute = local.hour * 60 + local.minute
    return local.weekday() == 0 and 8 * 60 + 45 <= minute < 9 * 60 + 15


def contains_secret(text: str) -> bool:
    return any(pattern.search(text) for pattern in SECRET_PATTERNS)


def _config(config: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(config, Mapping):
        raise ConfigError("config_must_be_object")
    users = config.get("authorized_user_ids")
    if not isinstance(users, list) or not users:
        raise ConfigError("authorized_user_ids_required")
    result = dict(config)
    result["guild_id"] = _snowflake(config.get("guild_id"))
    result["channel_id"] = _snowflake(config.get("channel_id"))
    result["authorized_user_ids"] = frozenset(_snowflake(user) for user in users)
    for flag in ("enabled", "ids_confirmed", "credential_rotation_confirmed"):
        value = config.get(flag, False)
        if not isinstance(value, bool):
            raise ConfigError("boolean_flag_required")
        result[flag] = value
    poll = config.get("poll_seconds", 10)
    if isinstance(poll, bool) or not isinstance(poll, (int, float)) or not 5 <= poll <= 60:
        raise ConfigError("poll_seconds_must_be_5_to_60")
    result["poll_seconds"] = float(poll)
    return result


SCHEMA = """
CREATE TABLE IF NOT EXISTS discord_meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS discord_processed(
 message_id TEXT PRIMARY KEY, guild_id TEXT NOT NULL, channel_id TEXT NOT NULL,
 author_id TEXT NOT NULL, received_at TEXT NOT NULL, decision TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS discord_requests(
 request_id INTEGER PRIMARY KEY AUTOINCREMENT,
 message_id TEXT NOT NULL UNIQUE REFERENCES discord_processed(message_id),
 task_id TEXT NOT NULL CHECK(task_id='T-003'), request_text TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'awaiting_review' CHECK(status='awaiting_review'),
 created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS discord_outbox(
 outbox_id INTEGER PRIMARY KEY AUTOINCREMENT,
 message_id TEXT NOT NULL UNIQUE REFERENCES discord_processed(message_id),
 channel_id TEXT NOT NULL, content TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('pending','sending','sent','send_uncertain','failed')),
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
 discord_message_id TEXT, last_error_code TEXT);
"""


@contextmanager
def _connect(path: Path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=5)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    try:
        db.executescript(SCHEMA)
        yield db
        db.commit()
    except BaseException:
        db.rollback()
        raise
    finally:
        db.close()


def list_requests(db_path: Path, limit: int = 20) -> list[dict[str, Any]]:
    """Read inbox for MCP; never processes, approves or sends a request.

    Returns request_id, message_id, task_id, request_text, status and created_at.
    This function never creates a directory or schema. A 1..100 integer limit is required.
    The caller must constrain db_path to its own private runtime directory.
    """
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
        raise ValueError("limit_must_be_1_to_100")
    path = Path(db_path)
    if not path.is_file():
        return []
    db = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    try:
        return [dict(row) for row in db.execute(
            "SELECT request_id,message_id,task_id,request_text,status,created_at "
            "FROM discord_requests ORDER BY request_id DESC LIMIT ?", (limit,))]
    finally:
        db.close()


class Bridge:
    """Offline inbox plus explicitly invoked poll/dispatch methods.

    Construct with a config dict and private SQLite Path. `enabled` is not an
    offline simulator switch: handle() stays offline regardless. Live methods
    additionally require three explicit booleans and verified numeric IDs.
    No provider callback, subprocess, eval or shell is accepted by handle().
    """

    def __init__(self, config: Mapping[str, Any], db_path: Path):
        self.config = _config(config)
        self.db_path = Path(db_path)
        with _connect(self.db_path):
            pass

    def list_requests(self, limit: int = 20) -> list[dict[str, Any]]:
        return list_requests(self.db_path, limit)

    def _live_gate(self) -> None:
        if not self.config["enabled"]:
            raise BridgeStop("disabled")
        if not self.config["ids_confirmed"]:
            raise BridgeStop("ids_not_confirmed")
        if not self.config["credential_rotation_confirmed"]:
            raise BridgeStop("credential_rotation_required")

    def _message(self, message: Mapping[str, Any], now: datetime) -> tuple[dict[str, str] | None, str]:
        if not isinstance(message, Mapping):
            return None, "invalid_message"
        author = message.get("author")
        if not isinstance(author, Mapping):
            return None, "invalid_author"
        if author.get("bot", False) is not False or message.get("webhook_id") is not None:
            return None, "bot_or_webhook"
        try:
            identity = {key: _snowflake(message.get(key)) for key in ("id", "guild_id", "channel_id")}
            author_id = _snowflake(author.get("id"))
        except ConfigError:
            return None, "invalid_identity"
        if identity["guild_id"] != self.config["guild_id"] or identity["channel_id"] != self.config["channel_id"]:
            return None, "outside_channel_allowlist"
        if author_id not in self.config["authorized_user_ids"]:
            return None, "outside_author_allowlist"
        try:
            stamp = datetime.fromisoformat(str(message.get("timestamp", "")).replace("Z", "+00:00"))
            age = (_aware(now) - _aware(stamp)).total_seconds()
        except (ValueError, TypeError):
            return None, "invalid_timestamp"
        if age > 300 or age < -30:
            return None, "stale_or_future"
        content = message.get("content")
        if not isinstance(content, str) or not content.lower().startswith("!lca"):
            return None, "not_a_command"
        if len(content) > MAX_CONTENT:
            return None, "content_too_long"
        if not re.match(r"^!lca(?:\s|$)", content, re.I):
            return None, "not_a_command"
        identity.update(author_id=author_id, content=content.strip())
        return identity, "eligible"

    def handle(self, message: Mapping[str, Any], now: datetime | None = None) -> dict[str, Any]:
        """Offline, deterministic with explicit now. Never sends or executes.

        Rejected outside-allowlist messages are not stored. Eligible command IDs
        are deduplicated in one IMMEDIATE transaction with inbox and outbox.
        Detectable secrets are never stored, even in an error/log field.
        """
        now = _aware(now or datetime.now(UTC))
        if protected_window(now):
            return {"decision": "ignored", "reason": "protected_window"}
        item, reason = self._message(message, now)
        if item is None:
            return {"decision": "ignored", "reason": reason}
        stamp = now.isoformat()
        with _connect(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            if db.execute("SELECT 1 FROM discord_processed WHERE message_id=?", (item["id"],)).fetchone():
                return {"decision": "duplicate", "message_id": item["id"]}
            command = item["content"][4:].strip()
            request_text = None
            if contains_secret(item["content"]):
                decision = "secret_rejected"
                reply = "Não registrei o pedido: há um possível segredo no texto. Remova-o e envie outro pedido."
            elif command.lower() in ("ajuda", "help", ""):
                decision = "help"
                reply = "Comandos: !lca status; !lca pendencias; !lca pedir T-003 <texto>. Pedidos ficam aguardando revisão; não executam tarefas."
            elif command.lower() == "status":
                decision = "status"
                count = db.execute("SELECT COUNT(*) FROM discord_requests").fetchone()[0]
                reply = f"Caixa local: {count} pedido(s) aguardando revisão. Este comando não inicia agente ou tarefa."
            elif command.lower() == "pendencias":
                decision = "pending"
                rows = db.execute("SELECT request_id,task_id FROM discord_requests ORDER BY request_id DESC LIMIT 10").fetchall()
                reply = "Pedidos aguardando revisão: " + (", ".join(f"#{r[0]} {r[1]}" for r in rows) if rows else "nenhum nesta caixa local") + "."
            else:
                match = re.fullmatch(r"pedir\s+T-003\s+(.+)", command, re.I | re.S)
                if match:
                    decision = "request_queued"
                    request_text = " ".join(match.group(1).split())
                    reply = "Pedido T-003 registrado como aguardando revisão. Nenhuma execução foi iniciada."
                else:
                    decision = "unknown_command"
                    reply = "Comando não reconhecido. Use !lca ajuda. Somente pedidos T-003 podem entrar nesta caixa."
            db.execute("INSERT INTO discord_processed VALUES(?,?,?,?,?,?)", (item["id"], item["guild_id"], item["channel_id"], item["author_id"], stamp, decision))
            request_id = None
            if request_text is not None:
                request_id = db.execute("INSERT INTO discord_requests(message_id,task_id,request_text,created_at) VALUES(?,'T-003',?,?)", (item["id"], request_text, stamp)).lastrowid
            outbox_id = db.execute("INSERT INTO discord_outbox(message_id,channel_id,content,status,created_at,updated_at) VALUES(?,?,?,'pending',?,?)", (item["id"], item["channel_id"], reply, stamp, stamp)).lastrowid
            return {"decision": decision, "message_id": item["id"], "request_id": request_id, "outbox_id": outbox_id, "reply": reply, "network_used": False}

    def cursor(self) -> str | None:
        with _connect(self.db_path) as db:
            row = db.execute("SELECT value FROM discord_meta WHERE key='cursor'").fetchone()
            return row[0] if row else None

    def _cursor(self, value: str) -> None:
        with _connect(self.db_path) as db:
            db.execute("INSERT INTO discord_meta VALUES('cursor',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value "
                       "WHERE length(excluded.value)>length(discord_meta.value) OR "
                       "(length(excluded.value)=length(discord_meta.value) AND excluded.value>discord_meta.value)", (value,))

    def dispatch_pending(self, client: Any, now: datetime | None = None) -> list[dict[str, Any]]:
        """Claim outbox before POST. Never resend sent/sending/uncertain rows.

        A crash after claim leaves 'sending': treat it as uncertain and inspect
        manually. There is intentionally no reset-to-pending/retry command.
        """
        self._live_gate()
        now = _aware(now or datetime.now(UTC))
        if protected_window(now):
            return []
        with _connect(self.db_path) as db:
            ids = [r[0] for r in db.execute("SELECT outbox_id FROM discord_outbox WHERE status='pending' ORDER BY outbox_id LIMIT 100")]
        results = []
        for outbox_id in ids:
            if protected_window(now):
                break
            with _connect(self.db_path) as db:
                db.execute("BEGIN IMMEDIATE")
                row = db.execute("SELECT * FROM discord_outbox WHERE outbox_id=? AND status='pending'", (outbox_id,)).fetchone()
                if row is None:
                    continue
                if (now - datetime.fromisoformat(row["created_at"])).total_seconds() > 300:
                    db.execute("UPDATE discord_outbox SET status='failed',last_error_code='expired_reply',updated_at=? WHERE outbox_id=?", (now.isoformat(), outbox_id))
                    continue
                db.execute("UPDATE discord_outbox SET status='sending',updated_at=? WHERE outbox_id=?", (now.isoformat(), outbox_id))
            try:
                result = client.post_message(row["channel_id"], {"content": row["content"], "allowed_mentions": {"parse": [], "replied_user": False}})
                sent_id = _snowflake(result.get("id"))
                status, code = "sent", None
            except (TransportFailure, TimeoutError):
                status, code, sent_id = "send_uncertain", "transport_uncertain", None
            except BridgeStop:
                with _connect(self.db_path) as db:
                    db.execute("UPDATE discord_outbox SET status='failed',last_error_code='http_stop',updated_at=? WHERE outbox_id=?", (now.isoformat(), outbox_id))
                raise
            except Exception:
                status, code, sent_id = "send_uncertain", "unexpected_send_result", None
            with _connect(self.db_path) as db:
                db.execute("UPDATE discord_outbox SET status=?,last_error_code=?,discord_message_id=?,updated_at=? WHERE outbox_id=?", (status, code, sent_id, now.isoformat(), outbox_id))
            results.append({"outbox_id": outbox_id, "status": status})
        return results

    def poll_once(self, client: Any, now: datetime | None = None) -> dict[str, Any]:
        self._live_gate()
        now = _aware(now or datetime.now(UTC))
        if protected_window(now):
            return {"state": "protected_window", "processed": 0}
        channel = client.get_channel(self.config["channel_id"])
        if str(channel.get("id")) != self.config["channel_id"] or str(channel.get("guild_id")) != self.config["guild_id"]:
            raise BridgeStop("verified_channel_mismatch")
        cursor = self.cursor()
        if cursor is None:
            latest = client.get_messages(self.config["channel_id"], after=None, limit=1)
            valid_ids = [_snowflake(row.get("id")) for row in latest]
            self._cursor(max(valid_ids, key=int) if valid_ids else "0")
            # Offline previews may have queued replies before activation. A
            # first live contact must not publish those previews to a channel.
            with _connect(self.db_path) as db:
                db.execute("UPDATE discord_outbox SET status='failed',last_error_code='bootstrap_no_replay',updated_at=? WHERE status='pending'", (now.isoformat(),))
            return {"state": "bootstrapped_without_replay", "processed": 0}
        messages = client.get_messages(self.config["channel_id"], after=cursor, limit=100)
        if len(messages) >= 100:
            raise BridgeStop("backlog_requires_review")
        rows = sorted(messages, key=lambda m: int(_snowflake(m.get("id"))))
        decisions = []
        for original in rows:
            message = dict(original)
            if "guild_id" not in message:
                message["guild_id"] = channel["guild_id"]
            decisions.append(self.handle(message, now=now)["decision"])
            self._cursor(_snowflake(message["id"]))
        sent = self.dispatch_pending(client, now=now)
        return {"state": "polled", "processed": len(rows), "decisions": decisions, "outbox": sent}


class RESTClient:
    """Bounded Discord REST transport. Tests inject opener/sleep/clock.

    Only a bot token supplied by main is supported; no user tokens, self-bots,
    browser sessions or credentials from other services. Retry is only for a
    known HTTP 429 rejection. Other transport failures are not auto-retried.
    """

    def __init__(self, token: str, *, opener: Callable = urllib.request.urlopen,
                 sleeper: Callable = time.sleep, clock: Callable = lambda: datetime.now(UTC)):
        if not isinstance(token, str) or not token.strip():
            raise ConfigError("bot_token_required")
        self._token, self._opener, self._sleep, self._clock = token, opener, sleeper, clock

    def request(self, method: str, route: str, body: Any = None) -> Any:
        for attempt in range(2):
            if protected_window(self._clock()):
                raise ProtectedWindow("protected_window")
            request = urllib.request.Request(API_BASE + route, method=method,
                data=json.dumps(body).encode() if body is not None else None,
                headers={"Authorization": "Bot " + self._token, "User-Agent": USER_AGENT, "Content-Type": "application/json"})
            try:
                with self._opener(request, timeout=10) as response:
                    payload = response.read(1024 * 1024 + 1)
                    if len(payload) > 1024 * 1024:
                        raise BridgeStop("response_too_large")
                    return json.loads(payload or b"null")
            except urllib.error.HTTPError as error:
                if error.code in (401, 403):
                    error.close()
                    raise BridgeStop("discord_unauthorized" if error.code == 401 else "discord_forbidden") from None
                if error.code != 429:
                    error.close()
                    if method == "POST" and error.code >= 500:
                        raise TransportFailure("discord_post_result_uncertain") from None
                    raise BridgeStop("discord_http_error") from None
                try:
                    payload = json.loads(error.read(4096))
                    retry = float(payload.get("retry_after", error.headers.get("Retry-After", "nan")))
                except (ValueError, TypeError, AttributeError):
                    raise RateLimited("rate_limit_without_safe_delay") from None
                finally:
                    error.close()
                if attempt >= 1 or not math.isfinite(retry) or not 0 <= retry <= 30:
                    raise RateLimited("rate_limit_stop") from None
                self._sleep(retry)
            except (urllib.error.URLError, TimeoutError, OSError):
                raise TransportFailure("discord_transport_failure") from None
            except (json.JSONDecodeError, UnicodeDecodeError):
                raise TransportFailure("discord_response_unknown") from None
        raise RateLimited("rate_limit_stop")

    def get_channel(self, channel_id: str) -> dict[str, Any]:
        result = self.request("GET", "/channels/" + _snowflake(channel_id))
        if not isinstance(result, dict):
            raise BridgeStop("invalid_channel_response")
        return result

    def get_messages(self, channel_id: str, *, after: str | None, limit: int) -> list[dict[str, Any]]:
        params = {"limit": limit}
        if after is not None:
            params["after"] = after
        result = self.request("GET", "/channels/" + _snowflake(channel_id) + "/messages?" + urllib.parse.urlencode(params))
        if not isinstance(result, list) or any(not isinstance(row, dict) for row in result):
            raise BridgeStop("invalid_messages_response")
        return result

    def post_message(self, channel_id: str, body: Mapping[str, Any]) -> dict[str, Any]:
        return self.request("POST", "/channels/" + _snowflake(channel_id) + "/messages", body)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args(argv)
    if not args.run:
        print(json.dumps({"state": "disabled", "network_used": False, "reason": "explicit_run_required"}))
        return 0
    try:
        raw_config = json.loads(args.config.read_text(encoding="utf-8"))
        config = _config(raw_config)
        if not all(config[flag] for flag in ("enabled", "ids_confirmed", "credential_rotation_confirmed")):
            raise BridgeStop("activation_gates_not_confirmed")
        token = os.environ.get("LCA_DISCORD_BOT_TOKEN", "")
        if not token:
            raise BridgeStop("bot_token_not_configured")
        bridge = Bridge(raw_config, args.db)
        client = RESTClient(token)
        while True:
            print(json.dumps(bridge.poll_once(client), ensure_ascii=False))
            if args.once:
                return 0
            time.sleep(config["poll_seconds"])
    except KeyboardInterrupt:
        print(json.dumps({"state": "stopped", "reason": "operator_interrupt"}))
        return 0
    except (BridgeStop, ConfigError, ValueError, sqlite3.Error, OSError):
        print(json.dumps({"state": "stopped", "reason": "configuration_access_or_transport_failure"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
