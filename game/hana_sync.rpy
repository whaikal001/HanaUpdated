define HANA_BACKEND_URL = "https://wanhaikal001.pythonanywhere.com"
define HANA_INGEST_TOKEN = "14daa2406e9a4827b48f7ff2dd5fd446"
define HANA_SYNC_INSECURE = True
define HANA_SYNC_TIMEOUT = 8
# Arm name the backend files sessions under, from HANA_CONDITION in script.rpy.
define HANA_APP_TYPES = {"adaptive": "triadic", "strict_empathy": "strict_empathy", "neutral": "neutral"}

init python:

    import json as _hana_json
    import uuid as _hana_uuid

    # Web (browser) builds run Python under Emscripten, which has no _ssl module
    # and no real sockets or background threads. Detect that platform so we can
    # take a browser-safe path instead of crashing at startup with
    # "ModuleNotFoundError: No module named '_ssl'".
    HANA_IS_WEB = bool(getattr(renpy, "emscripten", False))

    # ssl / urllib / threading only work on desktop & Android. Importing ssl on
    # web throws, so guard the whole block: on web these stay None and the web
    # POST path (renpy.fetch) is used instead.
    _hana_threading = None
    _hana_urlreq = None
    _hana_ssl = None
    _hana_q = None
    if not HANA_IS_WEB:
        try:
            import threading as _hana_threading
            import queue as _hana_queue
            import urllib.request as _hana_urlreq
            import ssl as _hana_ssl
            _hana_q = _hana_queue.Queue()
        except Exception:
            _hana_threading = None
            _hana_urlreq = None
            _hana_ssl = None
            _hana_q = None

    def hana_device_id():
        # Stable per-install id so the dashboard can tell devices/users apart.
        did = getattr(persistent, "hana_device_id", None)
        if not did:
            did = _hana_uuid.uuid4().hex[:12]
            persistent.hana_device_id = did
        return did

    def _hana_enabled():
        return bool(HANA_BACKEND_URL)

    # --- Desktop / Android: urllib + ssl (unchanged, runs on a worker thread) ---
    def _hana_do_post(endpoint, payload, insecure=False):
        url = HANA_BACKEND_URL.rstrip("/") + endpoint
        body = _hana_json.dumps(payload).encode("utf-8")
        req = _hana_urlreq.Request(url, data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("X-Ingest-Token", HANA_INGEST_TOKEN)
        ctx = None
        if insecure:
            ctx = _hana_ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = _hana_ssl.CERT_NONE
        else:
            try:
                import certifi
                ctx = _hana_ssl.create_default_context(cafile=certifi.where())
            except Exception:
                ctx = None
        resp = _hana_urlreq.urlopen(req, timeout=HANA_SYNC_TIMEOUT, context=ctx)
        return 200 <= resp.getcode() < 300

    def _hana_try_post(endpoint, payload):
        try:
            return _hana_do_post(endpoint, payload, insecure=False)
        except Exception:
            # Escape hatch for Android devices that can't verify the TLS chain.
            if HANA_SYNC_INSECURE:
                try:
                    return _hana_do_post(endpoint, payload, insecure=True)
                except Exception:
                    return False
            return False

    # --- Web: fire-and-forget POST via the browser's own fetch() ---
    # We hand the request to the browser and return immediately, so logging never
    # makes gameplay wait for the (slow, free-tier) server to reply. keepalive lets
    # the request finish even if the page is closed right after. The trade-off is
    # we can't tell whether it succeeded, so there's no automatic retry on web.
    def _hana_fire_web(endpoint, payload):
        try:
            import emscripten
        except Exception:
            return
        url = HANA_BACKEND_URL.rstrip("/") + endpoint
        body = _hana_json.dumps(payload)
        # json.dumps emits valid, ASCII-only JS string literals, so url/token/body
        # are safe to embed directly in the snippet.
        js = (
            "(function(){try{fetch(" + _hana_json.dumps(url) + ",{"
            "method:'POST',keepalive:true,"
            "headers:{'Content-Type':'application/json','X-Ingest-Token':"
            + _hana_json.dumps(HANA_INGEST_TOKEN) + "},"
            "body:" + _hana_json.dumps(body) + ""
            "}).catch(function(e){});}catch(e){}})();"
        )
        try:
            emscripten.run_script(js)
        except Exception:
            pass

    def _hana_save_failed(endpoint, payload):
        try:
            pending = list(getattr(persistent, "hana_unsent_logs", None) or [])
            pending.append({"e": endpoint, "p": payload})
            persistent.hana_unsent_logs = pending[-1000:]  # cap so it can't grow forever
        except Exception:
            pass

    def _hana_fire_web_pending():
        # Best-effort: fire off anything an earlier run left behind (e.g. a desktop
        # session that went offline), then clear it. Fire-and-forget, so we don't
        # know if these land either — this is just a recovery attempt.
        try:
            pending = list(getattr(persistent, "hana_unsent_logs", None) or [])
        except Exception:
            pending = []
        if not pending:
            return
        try:
            persistent.hana_unsent_logs = []
        except Exception:
            pass
        for item in pending:
            _hana_fire_web(item.get("e"), item.get("p"))

    def _hana_worker():
        while True:
            try:
                endpoint, payload = _hana_q.get()
            except Exception:
                continue
            ok = False
            try:
                if _hana_enabled():
                    ok = _hana_try_post(endpoint, payload)
            except Exception:
                ok = False
            if not ok and _hana_enabled():
                _hana_save_failed(endpoint, payload)
            try:
                _hana_q.task_done()
            except Exception:
                pass

    def hana_enqueue(endpoint, payload):
        if not _hana_enabled():
            return
        if HANA_IS_WEB:
            # Browser: fire-and-forget so logging never stalls gameplay.
            _hana_fire_web_pending()  # best-effort recovery of leftover logs
            _hana_fire_web(endpoint, payload)
            return
        try:
            _hana_q.put((endpoint, payload))
        except Exception:
            pass

    def hana_flush_unsent():
        # Re-queue anything that failed on a previous run (e.g. offline session).
        if not _hana_enabled():
            return
        if HANA_IS_WEB:
            # Don't hit the network during init on web (the emscripten event loop
            # isn't pumping yet); it'll be drained on the first interaction.
            return
        try:
            pending = list(getattr(persistent, "hana_unsent_logs", None) or [])
            persistent.hana_unsent_logs = []
            for item in pending:
                _hana_q.put((item.get("e"), item.get("p")))
        except Exception:
            pass

    def hana_sync_interaction(session_id, session_file, timestamp, question, answer,
                              score, stress_level, Ea, Ec, Ad, Be, D, Ep,
                              empathy_mode, extra=None):
        payload = {
            "device_id": hana_device_id(),
            "app_type": HANA_APP_TYPES[HANA_CONDITION],
            "user_name": (getattr(renpy.store, "user_name", "") or ""),
            "profile_id": getattr(renpy.store, "hana_active_profile_id", ""),
            "profile_slot": getattr(renpy.store, "hana_selected_profile_slot", ""),
            "session_id": session_id,
            "session_file": session_file,
            "client_ts": timestamp,
            "question": question,
            "answer": answer,
            "score": score,
            "stress_level": stress_level,
            "Ea": Ea, "Ec": Ec, "Ad": Ad, "Be": Be, "D": D, "Ep": Ep,
            "empathy_mode": empathy_mode,
        }
        if extra:
            payload.update(extra)
        hana_enqueue("/api/interaction", payload)

    def hana_sync_summary(session_id, session_file, timestamp, user_name,
                          start_stress_score, end_stress_score, stress_improvement,
                          final_calm_rating, modes_used, techniques_used,
                          total_interactions, session_duration_minutes, end_action,
                          stress_level="", empathy_mode="", intention_level="",
                          empathy_E="", support_need_announced="", extra=None):
        def _join(v):
            if isinstance(v, (list, tuple)):
                return "|".join(str(x) for x in v) if v else "none"
            return v
        payload = {
            "device_id": hana_device_id(),
            "app_type": HANA_APP_TYPES[HANA_CONDITION],
            "user_name": user_name or (getattr(renpy.store, "user_name", "") or ""),
            "profile_id": getattr(renpy.store, "hana_active_profile_id", ""),
            "profile_slot": getattr(renpy.store, "hana_selected_profile_slot", ""),
            "session_id": session_id,
            "session_file": session_file,
            "client_ts": timestamp,
            "start_stress_score": start_stress_score,
            "end_stress_score": end_stress_score,
            "stress_improvement": stress_improvement,
            "final_calm_rating": final_calm_rating,
            "modes_used": _join(modes_used),
            "techniques_used": _join(techniques_used),
            "total_interactions": total_interactions,
            "session_duration_minutes": session_duration_minutes,
            "end_action": end_action,
            "stress_level": stress_level,
            "empathy_mode": empathy_mode,
            "intention_level": intention_level,
            "empathy_E": empathy_E,
            "support_need_announced": support_need_announced,
        }
        # AEM session record (S, Ed, H, Ed_adaptive, Bl, ...) for the backend history.
        if extra:
            payload.update(extra)
        hana_enqueue("/api/summary", payload)

init 999 python:
    # The urllib worker thread only exists / makes sense off the web platform.
    if not HANA_IS_WEB:
        try:
            _hana_thread = _hana_threading.Thread(target=_hana_worker, name="hana-sync", daemon=True)
            _hana_thread.start()
        except Exception:
            _hana_thread = None

    hana_flush_unsent()
