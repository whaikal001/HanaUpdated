image logos_row = HBox(
    Transform("logo_uum.png", fit="contain", ysize=160),
    Transform("logo_kpt.png", fit="contain", ysize=160),
    Transform("logo_ums.png", fit="contain", ysize=160),
    spacing=80,
)

#kucing tukar position
image room_cat_wake = Transform("room_catWakeup.png", xysize=(1920, 1080), fit="cover")
image room_cat_walk = Transform("room_catwalkaway.png", xysize=(1920, 1080), fit="cover")
image room_cat_shelf = Transform("room_catonshelf.png", xysize=(1920, 1080), fit="cover")
image bg room_cat:
    "room_cat_wake"
    pause 2.5
    "room_cat_walk"
    pause 1.6
    "room_cat_shelf"
image hana neutral = "Sprites/Neutral.png"
image hana smiling = "Sprites/Smiling.png"
image hana listening:
    "Sprites/Listening.png"
    pause renpy.random.uniform(0.6, 1.4)
    block:
        "Sprites/Listening_eyeclose.png"
        pause 0.18
        "Sprites/Listening.png"
        pause renpy.random.uniform(2.4, 5.0)
        repeat

image breathing_guide = Movie(play="video/478breathing.webm", loop=True)

# --- Hana Location transforms ---
transform hana_center_listen:
    zoom 1.82
    xalign renpy.random.choice([0.10, 0.22, 0.34])
    yanchor 0.912
    ypos 0.993

    on show:
        alpha 0.0
        linear 0.3 alpha 1.0
    on replace:
        linear 0.15 alpha 1.0
    on hide:
        alpha 1.0
        linear 0.3 alpha 0.0

# --- Random scene position transforms ---
transform hana_left:
    zoom 0.7
    xalign 0.1
    yanchor 0.925
    ypos 0.993
    on show:
        alpha 0.0
        linear 0.3 alpha 1.0
    on replace:
        linear 0.15 alpha 1.0
    on hide:
        alpha 1.0
        linear 0.3 alpha 0.0

transform hana_mid:
    zoom 0.7
    xalign 0.5
    yanchor 0.925
    ypos 0.993
    on show:
        alpha 0.0
        linear 0.3 alpha 1.0
    on replace:
        linear 0.15 alpha 1.0
    on hide:
        alpha 1.0
        linear 0.3 alpha 0.0

transform hana_right:
    zoom 0.7
    xalign 0.9
    yanchor 0.925
    ypos 0.993
    on show:
        alpha 0.0
        linear 0.3 alpha 1.0
    on replace:
        linear 0.15 alpha 1.0
    on hide:
        alpha 1.0
        linear 0.3 alpha 0.0

transform breathing_guide_pos:
    zoom 0.5
    xalign 0.9
    yalign 0.42
    on show:
        alpha 0.0
        linear 0.4 alpha 1.0
    on hide:
        linear 0.4 alpha 0.0

init python:
    import math
    import datetime, csv, uuid, os

    def _hana_writable_log_dir():
        candidates = []
        for base in (getattr(config, "basedir", None), getattr(config, "savedir", None)):
            if base:
                candidates.append(os.path.join(base, "logs"))
        for d in candidates:
            try:
                os.makedirs(d, exist_ok=True)
                test = os.path.join(d, ".write_test")
                with open(test, "w") as _wf:
                    _wf.write("ok")
                os.remove(test)
                return d
            except Exception:
                continue
        try:
            import tempfile
            d = os.path.join(tempfile.gettempdir(), "hana_logs")
            os.makedirs(d, exist_ok=True)
            return d
        except Exception:
            return getattr(config, "savedir", ".") or "."

    DROPBOX_LOG_DIR = _hana_writable_log_dir()

    def generate_session_id():
        return str(uuid.uuid4())[:8]

    CONDITION_CODES = {
        "adaptive": "Adaptive",
        "strict_empathy": "Triadic",
        "neutral": "Neutral",
    }

    def make_session_filename(participant_id):
        condition_code = CONDITION_CODES.get(HANA_CONDITION, HANA_CONDITION)
        participant_id = str(participant_id or "unknown")
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        return "HANA_%s_%s_%s.csv" % (
            participant_id, condition_code, timestamp,
        )

    def _log_filename(session_filename, stage):
        stem, extension = os.path.splitext(session_filename)
        return "%s_%s%s" % (stem, stage, extension or ".csv")

    SESSION_LOG_HEADER = [
        "Participant_ID", "Session_ID", "Condition", "Timestamp", "Cycle",
        "Stage", "Duration", "HANA_Question", "User_Response", "HANA_Response",
        "Ea", "Ec", "Be", "D", "Ep", "E", "I", "Ed", "H", "Ed_Adaptive",
        "Behaviour_Profile",
    ]

    def _write_session_rows(session_filename, rows, stage):
        log_path = os.path.join(
            DROPBOX_LOG_DIR, _log_filename(session_filename, stage),
        )
        try:
            write_header = not os.path.exists(log_path)
            with open(log_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if write_header:
                    writer.writerow(SESSION_LOG_HEADER)
                writer.writerows(rows)
        except Exception:
            pass

    def log_interaction(session_filename, session_id, question, answer,
                        score=None, stress_level=None,
                        Ea=None, Ec=None, Ad=None, Be=None, D=None, Ep=None,
                        empathy_mode=None, extra=None):

        st = renpy.store
        x = extra or {}
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        row = [
            getattr(st, "hana_active_profile_id", ""), session_id,
            CONDITION_CODES.get(HANA_CONDITION, HANA_CONDITION), timestamp,
            x.get("cycle"), x.get("stage", "Interaction"), x.get("duration"),
            question, answer, x.get("hana_response"), Ea, Ec, Be, D, Ep,
            x.get("E"), x.get("I"), x.get("Ed"), x.get("H"),
            x.get("Ed_adaptive"), x.get("Bl", empathy_mode),
        ]
        _write_session_rows(session_filename, [row], "interaction")

        try:
            hana_sync_interaction(
                session_id, session_filename, timestamp, question, answer,
                score, stress_level, Ea, Ec, Ad, Be, D, Ep, empathy_mode,
                extra=extra,
            )
        except Exception:
            pass

    SESSION_SUMMARY_FIELDS = [
        "Session start", "Session end", "User", "Profile ID", "Session ID", "Session #",
        "Condition", "Language", "Check-in", "DASS stress raw (0-21)",
        "DASS stress score (0-42)", "Stress level", "S", "Ed", "H", "Ed_adaptive",
        "Bl", "Intention (I)", "Pathway", "Cycle 2 choice", "Activities",
        "Checkpoint 1", "Checkpoint 2", "Final check", "Bl per cycle",
        "Counselling offered", "Turns", "Duration (min)", "Ended by",
    ]

    def log_session_summary(session_filename, session_id, user_name,
                           start_stress_score, end_stress_score,
                           modes_used, techniques_used, total_interactions,
                           final_calm_rating, session_duration_minutes, end_action,
                           stress_improvement="",
                           stress_level="", empathy_mode="", intention_level="",
                           empathy_E="", support_need_announced="", extra=None,
                           cycles=None):

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        x = extra or {}

        values = [
            x.get("session_start", ""), timestamp, user_name,
            x.get("participant_id", ""), session_id, x.get("session_index", ""),
            x.get("condition", HANA_CONDITION), x.get("language", ""),
            x.get("checkin", ""), x.get("dass_raw", ""), start_stress_score,
            stress_level, x.get("S", ""), x.get("Ed", ""), x.get("H", ""),
            x.get("Ed_adaptive", ""), x.get("Bl", ""), intention_level,
            x.get("pathway", ""), x.get("cycle2_choice", ""),
            x.get("activity", ""), x.get("checkpoint_1", ""),
            x.get("checkpoint_2", ""), x.get("final_check", ""),
            empathy_mode, support_need_announced, total_interactions,
            session_duration_minutes, end_action,
        ]

        rows = [
            [
                x.get("participant_id", ""), session_id,
                CONDITION_CODES.get(x.get("condition", HANA_CONDITION),
                                    x.get("condition", HANA_CONDITION)),
                timestamp, "", "Summary", "", field, value, "",
            ] + [""] * (len(SESSION_LOG_HEADER) - 10)
            for field, value in zip(SESSION_SUMMARY_FIELDS, values)
        ]
        _write_session_rows(session_filename, rows, "summary")

        try:
            sync_extra = dict(extra or {})
            if cycles:
                sync_extra["cycles"] = cycles
            hana_sync_summary(
                session_id, session_filename, timestamp, user_name,
                start_stress_score, end_stress_score, stress_improvement,
                final_calm_rating, modes_used, techniques_used,
                total_interactions, session_duration_minutes, end_action,
                stress_level, empathy_mode, intention_level,
                empathy_E, support_need_announced, extra=sync_extra,
            )
        except Exception:
            pass


    def profile_key_for(name):
        return name.strip().lower()

    def default_user_profile(name):
        return {
            "name": name,
            "visit_count": 0,
            "last_session_id": "",
            "last_stress_score": None,
            "last_stress_level": "unknown",
            "last_technique": None,
            "last_end_action": "",
            "music_enabled": None,  
            "last_Bl": None,
            "aem_history": [],   
        }

    def load_user_profile(name):
        profile_store = getattr(persistent, "hana_user_memory", None) or {}
        key = profile_key_for(name)
        profile = default_user_profile(name)

        if key in profile_store:
            profile.update(profile_store[key])

        return key, profile_store, profile

    def save_user_profile(name, updates):
        profile_store = getattr(persistent, "hana_user_memory", None) or {}
        key = profile_key_for(name)
        profile = default_user_profile(name)

        if key in profile_store:
            profile.update(profile_store[key])

        profile.update(updates)
        profile_store[key] = profile
        persistent.hana_user_memory = profile_store
        return profile

#profile menu bole pilih
    PROFILE_SLOT_COUNT = 6

    def profile_slot_key(slot_index):
        return "slot_%d" % int(slot_index)

    def default_profile_slot(slot_index):
        return {
            "slot_index": int(slot_index),
            "profile_id": "",
            "name": "",
            "visit_count": 0,
            "last_session_id": "",
            "last_stress_level": "unknown",
            "last_Bl": None,
        }

    def load_profile_slot(slot_index):
        slot_store = getattr(persistent, "hana_profile_slots", None) or {}
        key = profile_slot_key(slot_index)
        slot = default_profile_slot(slot_index)

        if key in slot_store:
            slot.update(slot_store[key])

        return key, slot_store, slot

    def save_profile_slot(slot_index, updates):
        slot_store = getattr(persistent, "hana_profile_slots", None) or {}
        key = profile_slot_key(slot_index)
        slot = default_profile_slot(slot_index)

        if key in slot_store:
            slot.update(slot_store[key])

        slot.update(updates)
        slot_store[key] = slot
        persistent.hana_profile_slots = slot_store
        return slot

    def get_or_create_profile_id(slot_index):
        pid = "P%02d" % int(slot_index)
        key, slot_store, slot = load_profile_slot(slot_index)
        if slot.get("profile_id") != pid:
            save_profile_slot(slot_index, {"profile_id": pid})
        return pid

    def delete_profile_slot(slot_index):
        slot_store = getattr(persistent, "hana_profile_slots", None) or {}
        key = profile_slot_key(slot_index)

        slot = slot_store.get(key)
        if slot:
            name = (slot.get("name", "") or "").strip()
            if name:
                profile_store = getattr(persistent, "hana_user_memory", None) or {}
                pkey = profile_key_for(name)
                if pkey in profile_store:
                    del profile_store[pkey]
                    persistent.hana_user_memory = profile_store
            del slot_store[key]
            persistent.hana_profile_slots = slot_store

        renpy.restart_interaction()

    def cleanup_unfinished_profile_slots():
        slot_store = getattr(persistent, "hana_profile_slots", None) or {}
        profile_store = getattr(persistent, "hana_user_memory", None) or {}
        changed = False

        for i in range(1, PROFILE_SLOT_COUNT + 1):
            key = profile_slot_key(i)
            slot = slot_store.get(key)
            if not slot:
                continue
            name = (slot.get("name", "") or "").strip()
            if name and slot.get("visit_count", 0) <= 0:
                pkey = profile_key_for(name)
                # only drop the user memory if it also never completed a session
                if pkey in profile_store and profile_store[pkey].get("visit_count", 0) <= 0:
                    del profile_store[pkey]
                del slot_store[key]
                changed = True

        if changed:
            persistent.hana_profile_slots = slot_store
            persistent.hana_user_memory = profile_store

    def profile_slot_title(slot_index):
        dummy1, dummy2, slot = load_profile_slot(slot_index)
        name = slot.get("name", "").strip()

        if name:
            return name

        return "Profile %d" % int(slot_index)

    def profile_slot_summary(slot_index):
        dummy1, dummy2, slot = load_profile_slot(slot_index)
        visit_count = slot.get("visit_count", 0)
        last_stress_level = slot.get("last_stress_level", "unknown")
        last_bl = slot.get("last_Bl", None)

        if visit_count <= 0 and last_stress_level == "unknown":
            return "New slot"

        bl_text = "-" if last_bl is None else "B%d" % int(last_bl)
        return "Visits: %d | Stress: %s | Profile: %s" % (visit_count, last_stress_level, bl_text)

    def profile_save_page(slot_index):
        return "profile_%d" % int(slot_index)


    def clamp_range(x, lo, hi):
        return max(lo, min(hi, x))

    def pick_random_scene_pos():
        return renpy.random.choice([hana_left, hana_mid, hana_right])

    dt = 0.1
    T = 50.0

    # --- Baseline ---
    Ea0 = 0.1
    Ec0 = 0.1
    Be0 = 0.1
    sigma_d = 1.0

    # --- Parameters for Affective Empathy Unit ---
    alpha_Ea = 0.5
    gamma_Ea = 0.1
    delta_Ea = 0.05

    # --- Parameters for Cognitive Empathy Unit ---
    alpha_Ec = 0.3
    gamma_Ec = 0.1
    delta_Ec = 0.05
    tau = 2.0

    # --- Parameters for Belief Unit and Desire ---
    alpha_Be = 0.4
    gamma_Be = 0.1
    beta_Be = 0.2
    delta_Be = 0.05
    theta_be = 0.5

    # --- Parameters for Compassionate Empathy Unit ---
    alpha_Ep = 0.2
    delta_Ep = 0.01

    # --- Empathy Integrator ---
    w_ea = 0.3
    w_ec = 0.3
    w_ep = 0.4

    # --- Intention ---
    K = 5
    theta_1 = 0.93
    theta_2 = 1.85
    theta_3 = 2.78
    theta_4 = 3.70

    # --- Empathic Display ---
    eta_Ed = 1.0
    theta_Ed = 2.3

    # --- Habituation and Adaptive Empathic Display ---
    lambda_h = 0.1
    delta_adaptive = 0.1

    # --- Behaviour Generation ---
    phi_1 = 0.189
    phi_2 = 0.297
    phi_3 = 0.476
    phi_4 = 0.754

    # --- Update functions ---
    def update_affective(Ea, S):
        dEa = alpha_Ea * S - gamma_Ea * Ea + delta_Ea * (Ea0 - Ea)
        return max(0.0, Ea + dt * dEa)

    def update_cognitive(Ec, Ea_history):
        window = int(round(tau / dt))
        recent = Ea_history[-window:]
        Ea_prime = sum(recent) / len(recent)
        dEc = alpha_Ec * Ea_prime - gamma_Ec * Ec + delta_Ec * (Ec0 - Ec)
        return max(0.0, Ec + dt * dEc)

    def update_belief(Be, S, Ec):
        dBe = alpha_Be * S - gamma_Be * Be + beta_Be * Ec + delta_Be * (Be0 - Be)
        return max(0.0, Be + dt * dBe)

    def desire(Be):
        return sigma_d if Be > theta_be else 0.0

    def update_compassionate(Ea, Ec, D, t):
        return (alpha_Ep * Ea + (1.0 - alpha_Ep) * Ec) * D * math.exp(-delta_Ep * t)

    def integrate(Ea, Ec, Ep):
        return w_ea * Ea + w_ec * Ec + w_ep * Ep

    def intention_score(E):
        if E < theta_1:
            return 1
        elif E < theta_2:
            return 2
        elif E < theta_3:
            return 3
        elif E < theta_4:
            return 4
        return 5

    def empathic_display(E):
        I = intention_score(E)
        return (float(I) / K) * (1.0 / (1.0 + math.exp(-eta_Ed * (E - theta_Ed))))

    def habituation(prev_eds):
        j = len(prev_eds) + 1
        H = 0.0
        for k, ed in enumerate(prev_eds, 1):
            H += float(ed) * math.exp(-lambda_h * (j - k))
        return H

    def adaptive_empathic_display(Ed, H):
        return Ed * (1.0 - delta_adaptive * H)

    def behaviour_generation(Ed_adaptive):
        if Ed_adaptive < phi_1:
            return 1
        elif Ed_adaptive < phi_2:
            return 2
        elif Ed_adaptive < phi_3:
            return 3
        elif Ed_adaptive < phi_4:
            return 4
        return 5

    def load_prior_h(profile):
        prior_h = 0.0
        for rec in profile.get("aem_history", []) or []:
            if rec.get("condition") != HANA_CONDITION:
                continue
            try:
                cycles = rec.get("cycles", []) or []
                if cycles:
                    prior_h = float(cycles[-1].get("H", 0.0))
                else:
                    prior_h = float(rec.get("H", 0.0))
            except (TypeError, ValueError):
                continue
        return prior_h

    def run_aem(S_raw):
        S = S_raw / 21.0
        N = int(round(T / dt)) + 1

        Ea = Ea0
        Ec = Ec0
        Be = Be0
        Ea_history = [Ea]
        D = desire(Be)
        Ep = 0.0
        E = integrate(Ea, Ec, Ep)

        for i in range(1, N):
            t = i * dt
            Ea_new = update_affective(Ea, S)
            Ec_new = update_cognitive(Ec, Ea_history)
            Be = update_belief(Be, S, Ec)          
            Ea, Ec = Ea_new, Ec_new
            Ea_history.append(Ea)
            D = desire(Be)
            Ep = update_compassionate(Ea, Ec, D, t)
            E = integrate(Ea, Ec, Ep)

        return {
            "S": S, "Ea": Ea, "Ec": Ec, "Be": Be, "D": D, "Ep": Ep, "E": E,
            "I": intention_score(E), "Ed": empathic_display(E),
        }
    def previous_cycle_eds():
        eds = []
        for rec in renpy.store.cycle_records or []:
            try:
                eds.append(float(rec["Ed"]))
            except Exception:
                continue
        return eds

    def start_cycle(r):
        st = renpy.store
        Ed = st.aem["Ed"]
        if HANA_CONDITION == "adaptive":
            current_cycle_eds = previous_cycle_eds()
            H = st.prior_h + habituation(current_cycle_eds)
        else:
            H = 0.0
        Ed_adaptive = adaptive_empathic_display(Ed, H)
        Bl = behaviour_generation(Ed_adaptive)
        if HANA_CONDITION == "neutral":
            Bl = 1

        st.cycle = r
        st.H = H
        st.Ed_adaptive = Ed_adaptive
        st.Bl = Bl
        st.cycle_records.append({
            "cycle": r,
            "started_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Ed": round(Ed, 6),
            "H": round(H, 6),
            "Ed_adaptive": round(Ed_adaptive, 6),
            "Bl": "B%d" % Bl,
            "check_type": "",
            "check": "",
        })
        log_turn("Cycle %d start" % r, "B%d" % Bl)

    def record_check(check_type, answer):
        st = renpy.store
        if check_type == "final":
            st.final_check = answer
        else:
            st.checkpoint_history.append(answer)
        if st.cycle_records:
            st.cycle_records[-1]["check_type"] = check_type
            st.cycle_records[-1]["check"] = answer
        log_turn("How do you feel compared with earlier?", answer)
    def log_turn(question, answer, response=None):
        st = renpy.store
        a = st.aem or {}
        st.interaction_count += 1
        log_interaction(
            st.session_filename, st.session_id, question, answer,
            None, st.stress_level, a.get("Ea"), a.get("Ec"), None,
            a.get("Be"), a.get("D"), a.get("Ep"), "B%d" % st.Bl,
            extra={
                "language": st.session_lang,
                "condition": HANA_CONDITION,
                "cycle": st.cycle,
                "S": a.get("S"), "E": a.get("E"), "I": a.get("I"),
                "Ed": a.get("Ed"), "H": st.H, "Ed_adaptive": st.Ed_adaptive,
                "Bl": "B%d" % st.Bl, "hana_response": response or "",
            },
        )

    def hana_store_session(end_action):
        st = renpy.store
        a = st.aem or {}
        profile = st.user_profile or {}
        cycles = [dict(c) for c in st.cycle_records]
        bl_path = ">".join(c["Bl"] for c in cycles)

        record = {
            "session_id": st.session_id,
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "condition": HANA_CONDITION,
            "dass_raw": st.raw_score,
            "stress_level": st.stress_level,
            "S": round(a.get("S", 0.0), 6),
            "Ed": round(a.get("Ed", 0.0), 6),
            "H": round(st.H, 6),
            "Ed_adaptive": round(st.Ed_adaptive, 6),
            "Bl": "B%d" % st.Bl,
            "cycles": cycles,
            "final_check": st.final_check,
        }
        aem_history = list(profile.get("aem_history", []) or []) + [record]
        visit_count = profile.get("visit_count", 0) + 1

        st.user_profile = save_user_profile(st.user_name, {
            "name": st.user_name,
            "visit_count": visit_count,
            "last_session_id": st.session_id,
            "last_stress_score": st.stress_score,
            "last_stress_level": st.stress_level,
            "last_Bl": st.Bl,
            "last_technique": st.activity_done or None,
            "last_end_action": end_action,
            "aem_history": aem_history,
        })
        save_profile_slot(st.hana_selected_profile_slot, {
            "name": st.user_name,
            "visit_count": visit_count,
            "last_session_id": st.session_id,
            "last_stress_level": st.stress_level,
            "last_Bl": st.Bl,
        })
        try:
            renpy.save_persistent()
        except Exception:
            pass

        duration = 0.0
        session_start = ""
        if st.session_start_time is not None:
            duration = (datetime.datetime.now() - st.session_start_time).total_seconds() / 60.0
            session_start = st.session_start_time.strftime("%Y-%m-%d %H:%M:%S")

        extra = {
            "session_start": session_start,
            "participant_id": st.hana_active_profile_id,
            "language": st.session_lang,
            "condition": HANA_CONDITION,
            "session_index": visit_count,
            "checkin": st.checkin_ans,
            "dass_raw": st.raw_score,
            "S": record["S"],
            "Ed": record["Ed"],
            "H": record["H"],
            "Ed_adaptive": record["Ed_adaptive"],
            "Bl": record["Bl"],
            "pathway": st.pathway,
            "cycle2_choice": st.c2_choice,
            "activity": "|".join(st.activity_log) or "none",
            "checkpoint_1": st.checkpoint_history[0] if len(st.checkpoint_history) > 0 else "",
            "checkpoint_2": st.checkpoint_history[1] if len(st.checkpoint_history) > 1 else "",
            "final_check": st.final_check,
        }
        for n in (1, 2, 3):
            extra["H_%d" % n] = ""
            extra["Ed_adaptive_%d" % n] = ""
            extra["Bl_%d" % n] = ""
        for c in cycles:
            n = c["cycle"]
            extra["H_%d" % n] = c["H"]
            extra["Ed_adaptive_%d" % n] = c["Ed_adaptive"]
            extra["Bl_%d" % n] = c["Bl"]

        log_session_summary(
            st.session_filename, st.session_id, st.user_name,
            st.stress_score, "",
            [c["Bl"] for c in cycles], st.techniques_used_list,
            st.interaction_count, st.final_check,
            round(duration, 2), end_action,
            "",
            st.stress_level, bl_path, a.get("I", ""),
            st.Ed_adaptive, st.counselling_offered,
            extra=extra, cycles=cycles,
        )

# method nak clean menu function sebab nak bg main menu clear and bukan ingame
init 999 python:
    cleanup_unfinished_profile_slots()

default quick_menu = True

# --- Characters ---
define e = Character("Hana", color="#b56ab3")
define HANA_CONDITION = "adaptive"

# =========================
# STATE VARIABLES
# =========================
default Ea = 0.2
default Ec = 0.2
default Be = 0.1
default stress_level = "Normal"

default techniques_used_list = []
default interaction_count = 0
default session_start_time = None

default session_id = ""
default session_filename = ""

default stress_score = 0
default session_lang = "english"
default checkin_ans = ""
default aem = {}
default Bl = 1
default cycle = 1
default H = 0.0
default Ed_adaptive = 0.0
default checkpoint_history = []
default cycle_records = []
default final_check = ""
default c2_choice = ""
default c2_detail = ""
default activity_log = []
default cmp_ans = ""
default raw_score = 0
default pathway = ""
default activity_done = ""
default counselling_offered = False
default closed_at = ""
default resp = ""
default ns_q1 = ""
default ns_q2 = ""
default ns_topic = ""
default ns_feel = ""
default st_q1 = ""
default st_q2 = ""
default st_q3 = ""
default st_q4 = ""
default st_q5 = ""
default hana_selected_profile_slot = 1
default hana_active_profile_id = ""
default hana_pos = hana_mid
default prior_h = 0.0
# --- Flow Starts ---

label start:

    scene black
    with fade

    $ session_lang = "english"
    if _preferences.language is not None:
        $ renpy.change_language(None)

    show logos_row:
        xalign 0.5 yalign 0.9
    centered "Disclaimer\n\nThis session includes questions about stress adapted from the DASS-21.\n\nThese questions are for research purposes only. They are not a medical test and cannot be used to diagnose or treat any health condition.\n\n{size=-10}This research is supported by the Ministry of Higher Education (MoHE) Malaysia through the Fundamental Research Grant Scheme (FRGS/1/2024/ICT02/UUM/02/1).{/size}"
    hide logos_row

    scene bg room_cat
    show black:
        alpha 0.6
    with fade
#ni critical part if error sume tak jalan
    # nak clear slot yang session tak settle abis
    $ cleanup_unfinished_profile_slots()
    $ session_id = generate_session_id()
    $ Ea = Ea0
    $ Ec = Ec0
    $ Be = Be0
    $ aem = {}
    $ Bl = 1
    $ cycle = 1
    $ H = 0.0
    $ Ed_adaptive = 0.0
    $ checkpoint_history = []
    $ cycle_records = []
    $ final_check = ""
    $ c2_choice = ""
    $ c2_detail = ""
    $ activity_log = []
    $ raw_score = 0
    $ pathway = ""
    $ activity_done = ""
    $ counselling_offered = False
    $ closed_at = ""
    $ stress_score = 0
    $ stress_level = "Normal"
    $ checkin_ans = ""
    $ techniques_used_list = []
    $ interaction_count = 0
    $ session_start_time = datetime.datetime.now()
    $ selected_slot = clamp_range(hana_selected_profile_slot, 1, PROFILE_SLOT_COUNT)
    $ dummy1, dummy2, selected_slot_data = load_profile_slot(selected_slot)
    $ user_name = selected_slot_data.get("name", "").strip()
    $ hana_selected_profile_slot = selected_slot
    $ hana_active_profile_id = get_or_create_profile_id(selected_slot)
    $ session_filename = make_session_filename(hana_active_profile_id)
    $ hana_pos = hana_mid

    if user_name:
        $ user_profile_key, user_profile_store, user_profile = load_user_profile(user_name)
    else:
        $ user_profile_key, user_profile_store, user_profile = None, None, {}

    $ is_returning_user = user_profile.get("visit_count", 0) > 0
    #2 flow: user baru or lama
    if is_returning_user:
        show hana neutral at hana_pos
        e "Hi, [user_name]. Welcome back."
        show hana smiling at hana_pos
        with Fade(0.3, 0.0, 0.3)
        e "Nice to talk to you again."
    else:
        show hana smiling at hana_pos
        e "Hi, I'm HANA."
        if not user_name:
            show hana neutral at hana_pos
            with Fade(0.3, 0.0, 0.3)
            e "What's your name?"
            show hana listening at hana_center_listen
            $ user_name = renpy.input("")
            $ user_name = user_name.strip().title() if user_name.strip() else __("friend")
            $ save_profile_slot(selected_slot, {"name": user_name})
            $ user_profile_key, user_profile_store, user_profile = load_user_profile(user_name)

        show hana smiling at hana_pos
        with Fade(0.3, 0.0, 0.3)
        e "Nice to meet you, [user_name]."

    $ music_pref = None
    show hana neutral at hana_pos
    with Fade(0.3, 0.0, 0.3)
    e "Would you like some music?"
    show hana listening at hana_center_listen

    menu:
        "Yes, please.":
            $ music_pref = True
            show hana neutral at hana_pos
            e "Okay, I'll play some music."
            play music "audio/BGM/Hana_lofi.mp3" volume 0.3 fadein 3.0 loop

        "No, thanks.":
            $ music_pref = False
            stop music fadeout 1.0
            show hana neutral at hana_pos
            e "Okay, we'll continue without music."

    $ user_profile = save_user_profile(user_name, {"music_enabled": music_pref})
    $ prior_h = load_prior_h(user_profile) if HANA_CONDITION == "adaptive" else 0.0
    $ log_interaction(session_filename, session_id,
                      "Music preference", "music_on" if music_pref else "music_off",
                      None, None, Ea, Ec, None, Be, None, None, "preference")

    hide black
    with Dissolve(0.5)

    show hana neutral at hana_pos
    e "How are you feeling today?"
    show hana listening at hana_center_listen
    menu:
        "I feel good.":
            $ checkin_ans = "I feel good"
            show hana smiling at hana_pos
            e "Good to hear that."

        "I'm okay.":
            $ checkin_ans = "I'm okay"
            show hana neutral at hana_pos
            e "Thanks for sharing with me."

        "I'm not feeling good.":
            $ checkin_ans = "I'm not feeling good"
            show hana neutral at hana_pos
            e "Thanks for telling me."

        "I feel stressed.":
            $ checkin_ans = "I feel stressed"
            show hana neutral at hana_pos
            e "Thanks for telling me."

    $ log_interaction(session_filename, session_id,
                      "How are you feeling today?", checkin_ans,
                      None, None, Ea, Ec, None, Be, None, None, "checkin")

    show hana listening at hana_center_listen
    jump stress_input


label stress_input:
    $ hana_pos = pick_random_scene_pos()

    show hana neutral at hana_pos
    e "Let's check your stress level."
    e "Think about the past seven days."

    $ stress_questions = [
        _("Was it hard to wind down?"),
        _("Did you overreact to things?"),
        _("Did you feel restless?"),
        _("Was it hard to relax?"),
        _("Did delays make you upset?"),
        _("Did you feel easily annoyed?"),
        _("Was it hard to calm down?"),
    ]

    $ stress_responses = []
    $ i = 0

    while i < len(stress_questions):
        $ q = stress_questions[i]
        show hana neutral at hana_pos
        e "[q!t]"
        show hana listening at hana_center_listen

        menu:
            "Not at all":
                $ stress_responses.append(0)
                $ ans = "Not at all"

            "Sometimes":
                $ stress_responses.append(1)
                $ ans = "Sometimes"

            "Often":
                $ stress_responses.append(2)
                $ ans = "Often"

            "Most of the time":
                $ stress_responses.append(3)
                $ ans = "Most of the time"

        $ log_interaction(session_filename, session_id, q, ans, stress_responses[-1], None, None, None, None, None, None, None, "dass_q" + str(i+1))
        $ i += 1

    show hana listening at hana_center_listen

    $ raw_score = sum(stress_responses)
    $ max_raw = float(len(stress_questions) * 3)
    $ stress_scale = (raw_score / max_raw) if max_raw > 0 else 0.0
    $ stress_score = int(round(stress_scale * 42.0))

    if stress_score <= 14:
        $ stress_level = "Normal"
    elif stress_score <= 18:
        $ stress_level = "Mild"
    elif stress_score <= 25:
        $ stress_level = "Moderate"
    elif stress_score <= 33:
        $ stress_level = "Severe"
    else:
        $ stress_level = "Extremely severe"

    $ log_interaction(session_filename, session_id, "Stress score summary", str(raw_score),
                stress_score, stress_level, None, None, None, None, None, None, "stress_summary")
    $ aem = run_aem(raw_score)
    $ start_cycle(1)
    if stress_level in ["Normal", "Mild"]:
        jump non_stress_pathway
    else:
        jump stress_pathway

label non_stress_pathway:
    $ pathway = "non_stress"
    show hana neutral at hana_pos
    e "What has been going well lately?"
    show hana listening at hana_center_listen
    menu:
        "Family":
            $ ns_q1 = "family"
            if Bl <= 1:
                $ resp = _("Okay")
            elif Bl == 2:
                $ resp = _("That's good to hear.")
            elif Bl == 3:
                $ resp = _("It's good things are going well.")
            elif Bl == 4:
                $ resp = _("That sounds positive for you.")
            else:
                $ resp = _("It's good to have that support.")
        "Caring for someone":
            $ ns_q1 = "caring"
            if Bl <= 1:
                $ resp = _("Okay")
            elif Bl == 2:
                $ resp = _("That's good to hear.")
            elif Bl == 3:
                $ resp = _("It's good that things are going well.")
            elif Bl == 4:
                $ resp = _("That sounds meaningful to you.")
            else:
                $ resp = _("It's good to have positive moments.")
        "Work or daily activities":
            $ ns_q1 = "work"
            if Bl <= 1:
                $ resp = _("Okay")
            elif Bl == 2:
                $ resp = _("That's good to hear.")
            elif Bl == 3:
                $ resp = _("It's good things are going well.")
            elif Bl == 4:
                $ resp = _("That sounds positive for you.")
            else:
                $ resp = _("It's good to have things going well.")
        "My health":
            $ ns_q1 = "health"
            if Bl <= 1:
                $ resp = _("Okay")
            elif Bl == 2:
                $ resp = _("That's good to hear.")
            elif Bl == 3:
                $ resp = _("It's good you're feeling well.")
            elif Bl == 4:
                $ resp = _("That sounds positive for you.")
            else:
                $ resp = _("It's good that you're doing well.")
        "Things are just okay":
            $ ns_q1 = "okay"
            if Bl <= 1:
                $ resp = _("Okay")
            elif Bl == 2:
                $ resp = _("I understand.")
            elif Bl == 3:
                $ resp = _("It's okay for things to feel steady.")
            elif Bl == 4:
                $ resp = _("It sounds like things are steady.")
            else:
                $ resp = _("Having some stability can be helpful.")
    if ns_q1 == "okay":
        show hana neutral at hana_pos
    else:
        show hana smiling at hana_pos
    e "[resp!t]"
    $ log_turn("What has been going well lately?", ns_q1, resp)

    show hana neutral at hana_pos
    e "What helps you feel okay?"
    show hana listening at hana_center_listen
    menu:
        "Resting":
            $ ns_q2 = "resting"
            if Bl <= 1:
                $ resp = _("Okay.")
            elif Bl == 2:
                $ resp = _("Rest can be helpful.")
            elif Bl == 3:
                $ resp = _("It's good that rest helps.")
            elif Bl == 4:
                $ resp = _("Rest seems important for you.")
            else:
                $ resp = _("It's good you know what helps you.")
        "Talking to someone":
            $ ns_q2 = "talking"
            if Bl <= 1:
                $ resp = _("Okay.")
            elif Bl == 2:
                $ resp = _("Talking can help.")
            elif Bl == 3:
                $ resp = _("It's good to have someone.")
            elif Bl == 4:
                $ resp = _("Having someone to talk to matters.")
            else:
                $ resp = _("That support seems important to you.")
        "Doing something I enjoy":
            $ ns_q2 = "enjoy"
            if Bl <= 1:
                $ resp = _("Okay.")
            elif Bl == 2:
                $ resp = _("That sounds good.")
            elif Bl == 3:
                $ resp = _("It's good to enjoy things.")
            elif Bl == 4:
                $ resp = _("That sounds meaningful for you.")
            else:
                $ resp = _("It's good to have something you enjoy.")
        "Having time alone":
            $ ns_q2 = "alone"
            if Bl <= 1:
                $ resp = _("Okay.")
            elif Bl == 2:
                $ resp = _("That can be helpful.")
            elif Bl == 3:
                $ resp = _("Quiet time can feel good.")
            elif Bl == 4:
                $ resp = _("Having your own space seems helpful.")
            else:
                $ resp = _("It's good you know what works for you.")
        "My daily routine":
            $ ns_q2 = "routine"
            if Bl <= 1:
                $ resp = _("I'm listening.")
            elif Bl == 2:
                $ resp = _("Routine can be helpful.")
            elif Bl == 3:
                $ resp = _("It's good to have a routine.")
            elif Bl == 4:
                $ resp = _("Your routine seems to work for you.")
            else:
                $ resp = _("Keeping that routine may support you.")
    show hana neutral at hana_pos
    e "[resp!t]"
    $ log_turn("What helps you feel okay?", ns_q2, resp)

    show hana neutral at hana_pos
    e "Is there anything you want to talk about?"
    show hana listening at hana_center_listen
    menu:
        "Yes":
            $ log_turn("Is there anything you want to talk about?", "yes")
        "No":
            $ log_turn("Is there anything you want to talk about?", "no")
            show hana neutral at hana_pos
            e "Okay, thanks for sharing with me."
            jump checkpoint_1

    show hana neutral at hana_pos
    e "What would you like to talk about?"
    show hana listening at hana_center_listen
    menu:
        "Caring for someone":
            $ ns_topic = "caring"
        "Family":
            $ ns_topic = "family"
        "Work or money":
            $ ns_topic = "work"
        "Health":
            $ ns_topic = "health"
        "Something else":
            $ ns_topic = "other"
    $ log_turn("What would you like to talk about?", ns_topic)

    show hana neutral at hana_pos
    e "How do you feel about it?"
    show hana listening at hana_center_listen
    menu:
        "I feel good about it.":
            $ ns_feel = "good"
            if Bl <= 1:
                $ resp = _("Okay")
            elif Bl == 2:
                $ resp = _("That's good to hear.")
            elif Bl == 3:
                $ resp = _("It's good you feel that way.")
            elif Bl == 4:
                $ resp = _("That sounds positive for you.")
            else:
                $ resp = _("It's good to feel good about it.")
        "I feel okay about it.":
            $ ns_feel = "okay"
            if Bl <= 1:
                $ resp = _("Okay")
            elif Bl == 2:
                $ resp = _("I understand.")
            elif Bl == 3:
                $ resp = _("It's okay for things to feel steady.")
            elif Bl == 4:
                $ resp = _("It sounds like things are steady.")
            else:
                $ resp = _("Having some stability can be helpful.")
        "I'm a little concerned.":
            $ ns_feel = "concerned"
        "I'm worried about it.":
            $ ns_feel = "worried"

    if ns_feel in ["good", "okay"]:
        if ns_feel == "good":
            show hana smiling at hana_pos
        else:
            show hana neutral at hana_pos
        e "[resp!t]"
        $ log_turn("How do you feel about it?", ns_feel, resp)
        jump checkpoint_1
    $ log_turn("How do you feel about it?", ns_feel)

    jump stress_q2

label stress_pathway:
    $ pathway = "stress"

    show hana neutral at hana_pos
    e "What has been stressful lately?"
    show hana listening at hana_center_listen
    menu:
        "Caring for someone":
            $ st_q1 = "caring"
            if Bl <= 1:
                $ resp = _("I'm listening.")
            elif Bl == 2:
                $ resp = _("Take your time.")
            elif Bl == 3:
                $ resp = _("Caring can be difficult.")
            elif Bl == 4:
                $ resp = _("That sounds really difficult.")
            else:
                $ resp = _("You don't have to face it alone.")
        "Family":
            $ st_q1 = "family"
            if Bl <= 1:
                $ resp = _("I'm listening.")
            elif Bl == 2:
                $ resp = _("Take your time.")
            elif Bl == 3:
                $ resp = _("Family stress can be difficult.")
            elif Bl == 4:
                $ resp = _("That sounds really difficult.")
            else:
                $ resp = _("You don't have to face it alone.")
        "Work or money":
            $ st_q1 = "work"
            if Bl <= 1:
                $ resp = _("I'm listening.")
            elif Bl == 2:
                $ resp = _("Take your time.")
            elif Bl == 3:
                $ resp = _("That can feel stressful.")
            elif Bl == 4:
                $ resp = _("That sounds really stressful.")
            else:
                $ resp = _("You don't have to handle it alone.")
        "Health":
            $ st_q1 = "health"
            if Bl <= 1:
                $ resp = _("I'm listening.")
            elif Bl == 2:
                $ resp = _("Take your time.")
            elif Bl == 3:
                $ resp = _("That can be difficult.")
            elif Bl == 4:
                $ resp = _("That sounds really difficult.")
            else:
                $ resp = _("You don't have to face it alone.")
        "Something else":
            $ st_q1 = "other"
            if Bl <= 1:
                $ resp = _("I'm listening.")
            elif Bl == 2:
                $ resp = _("Take your time.")
            elif Bl == 3:
                $ resp = _("That sounds difficult.")
            elif Bl == 4:
                $ resp = _("That sounds really difficult.")
            else:
                $ resp = _("It sounds like a lot to deal with.")
    show hana neutral at hana_pos
    e "[resp!t]"
    $ log_turn("What has been stressful lately?", st_q1, resp)

label stress_q2:
    show hana neutral at hana_pos
    e "What worries you most about it?"
    show hana listening at hana_center_listen
    menu:
        "It may get worse":
            $ st_q2 = "worse"
            if Bl <= 1:
                $ resp = _("I'm listening.")
            elif Bl == 2:
                $ resp = _("I understand your concern.")
            elif Bl == 3:
                $ resp = _("That uncertainty can be worrying.")
            elif Bl == 4:
                $ resp = _("It makes sense to feel concerned.")
            else:
                $ resp = _("It can be hard not knowing what will happen.")
        "I can't manage it":
            $ st_q2 = "cant_manage"
            if Bl <= 1:
                $ resp = _("I'm listening.")
            elif Bl == 2:
                $ resp = _("I hear you.")
            elif Bl == 3:
                $ resp = _("It sounds like a lot.")
            elif Bl == 4:
                $ resp = _("It sounds overwhelming right now.")
            else:
                $ resp = _("You don't have to manage everything alone.")
        "It affects other people":
            $ st_q2 = "others"
            if Bl <= 1:
                $ resp = _("I'm listening.")
            elif Bl == 2:
                $ resp = _("I understand.")
            elif Bl == 3:
                $ resp = _("You're thinking about others too.")
            elif Bl == 4:
                $ resp = _("That sounds like a lot to carry.")
            else:
                $ resp = _("It sounds difficult carrying that concern for others.")
        "I don't know what to do":
            $ st_q2 = "unsure"
            if Bl <= 1:
                $ resp = _("I'm listening.")
            elif Bl == 2:
                $ resp = _("That's okay.")
            elif Bl == 3:
                $ resp = _("Feeling unsure can be difficult.")
            elif Bl == 4:
                $ resp = _("It's understandable to feel stuck.")
            else:
                $ resp = _("It can be hard when you're unsure what to do.")
        "Something else":
            $ st_q2 = "other"
            if Bl <= 1:
                $ resp = _("I'm listening.")
            elif Bl == 2:
                $ resp = _("Take your time.")
            elif Bl == 3:
                $ resp = _("I understand this is difficult.")
            elif Bl == 4:
                $ resp = _("It sounds important to you.")
            else:
                $ resp = _("It sounds like this is weighing on you.")
    show hana neutral at hana_pos
    e "[resp!t]"
    $ log_turn("What worries you most about it?", st_q2, resp)

    show hana neutral at hana_pos
    e "How has this been affecting you?"
    show hana listening at hana_center_listen
    menu:
        "I feel tired":
            $ st_q3 = "tired"
            if Bl <= 1:
                $ resp = _("I'm listening.")
            elif Bl == 2:
                $ resp = _("I hear you.")
            elif Bl == 3:
                $ resp = _("You sound quite tired.")
            elif Bl == 4:
                $ resp = _("That sounds exhausting.")
            else:
                $ resp = _("It sounds like this has taken a lot out of you.")
        "I feel overwhelmed":
            $ st_q3 = "overwhelmed"
            if Bl <= 1:
                $ resp = _("I'm listening.")
            elif Bl == 2:
                $ resp = _("Take your time.")
            elif Bl == 3:
                $ resp = _("That sounds like a lot.")
            elif Bl == 4:
                $ resp = _("That sounds overwhelming.")
            else:
                $ resp = _("You don't have to carry everything alone.")
        "I can't focus":
            $ st_q3 = "focus"
            if Bl <= 1:
                $ resp = _("I'm listening.")
            elif Bl == 2:
                $ resp = _("I understand.")
            elif Bl == 3:
                $ resp = _("Focusing can be difficult.")
            elif Bl == 4:
                $ resp = _("That sounds frustrating.")
            else:
                $ resp = _("It sounds hard when this affects your focus.")
        "I can't relax":
            $ st_q3 = "relax"
            if Bl <= 1:
                $ resp = _("I'm listening.")
            elif Bl == 2:
                $ resp = _("I understand.")
            elif Bl == 3:
                $ resp = _("It sounds hard to unwind.")
            elif Bl == 4:
                $ resp = _("That sounds really draining.")
            else:
                $ resp = _("It sounds exhausting not being able to relax.")
        "Something else":
            $ st_q3 = "other"
            if Bl <= 1:
                $ resp = _("I'm listening.")
            elif Bl == 2:
                $ resp = _("Take your time.")
            elif Bl == 3:
                $ resp = _("That sounds difficult.")
            elif Bl == 4:
                $ resp = _("It sounds like this affects you.")
            else:
                $ resp = _("It sounds like this is affecting you quite a lot.")
    show hana neutral at hana_pos
    e "[resp!t]"
    $ log_turn("How has this been affecting you?", st_q3, resp)

    show hana neutral at hana_pos
    e "What usually helps you feel better?"
    show hana listening at hana_center_listen
    menu:
        "Resting":
            $ st_q4 = "resting"
            if Bl <= 1:
                $ resp = _("I'm listening.")
            elif Bl == 2:
                $ resp = _("Rest can be helpful.")
            elif Bl == 3:
                $ resp = _("It's good that rest helps.")
            elif Bl == 4:
                $ resp = _("Making time to rest sounds important.")
            else:
                $ resp = _("It sounds like rest really helps you.")
        "Talking to someone":
            $ st_q4 = "talking"
            if Bl <= 1:
                $ resp = _("I'm listening.")
            elif Bl == 2:
                $ resp = _("Talking can help.")
            elif Bl == 3:
                $ resp = _("It's good to have someone.")
            elif Bl == 4:
                $ resp = _("Having someone to talk to can help.")
            else:
                $ resp = _("That support seems important to you.")
        "Doing something I enjoy":
            $ st_q4 = "enjoy"
            if Bl <= 1:
                $ resp = _("I'm listening.")
            elif Bl == 2:
                $ resp = _("That sounds helpful.")
            elif Bl == 3:
                $ resp = _("It's good that this helps.")
            elif Bl == 4:
                $ resp = _("Making time for yourself can help.")
            else:
                $ resp = _("It's good you have something that helps you.")
        "Having time alone":
            $ st_q4 = "alone"
            if Bl <= 1:
                $ resp = _("I'm listening.")
            elif Bl == 2:
                $ resp = _("That can help.")
            elif Bl == 3:
                $ resp = _("Some quiet time can help.")
            elif Bl == 4:
                $ resp = _("Giving yourself space sounds helpful.")
            else:
                $ resp = _("It sounds like having some space helps you.")
        "Nothing really helps":
            $ st_q4 = "nothing"
            if Bl <= 1:
                $ resp = _("I'm listening.")
            elif Bl == 2:
                $ resp = _("I hear you.")
            elif Bl == 3:
                $ resp = _("That can feel difficult.")
            elif Bl == 4:
                $ resp = _("It sounds hard when nothing helps.")
            else:
                $ resp = _("It sounds like you may need more support.")
    show hana neutral at hana_pos
    e "[resp!t]"
    $ log_turn("What usually helps you feel better?", st_q4, resp)

    show hana neutral at hana_pos
    e "Who can you talk to when things are difficult?"
    show hana listening at hana_center_listen
    menu:
        "Family":
            $ st_q5 = "family"
            if Bl <= 1:
                $ resp = _("I'm listening.")
            elif Bl == 2:
                $ resp = _("That's good to know.")
            elif Bl == 3:
                $ resp = _("Family can be helpful.")
            elif Bl == 4:
                $ resp = _("It's good you have someone in your family to talk to.")
            else:
                $ resp = _("Having family to turn to can be meaningful.")
        "A friend":
            $ st_q5 = "friend"
            if Bl <= 1:
                $ resp = _("I'm listening.")
            elif Bl == 2:
                $ resp = _("That's good to know.")
            elif Bl == 3:
                $ resp = _("Having a friend can help.")
            elif Bl == 4:
                $ resp = _("It's good you have a friend to talk to.")
            else:
                $ resp = _("Having a friend to turn to can be meaningful.")
        "Someone I trust":
            $ st_q5 = "trust"
            if Bl <= 1:
                $ resp = _("I'm listening.")
            elif Bl == 2:
                $ resp = _("That's good to know.")
            elif Bl == 3:
                $ resp = _("Having someone you trust can help.")
            elif Bl == 4:
                $ resp = _("That support can be important.")
            else:
                $ resp = _("Having someone you trust can make a difference.")
        "A professional":
            $ st_q5 = "professional"
            if Bl <= 1:
                $ resp = _("I'm listening.")
            elif Bl == 2:
                $ resp = _("That's good to know.")
            elif Bl == 3:
                $ resp = _("Professional support can be helpful.")
            elif Bl == 4:
                $ resp = _("Having professional support can be helpful.")
            else:
                $ resp = _("It's good that professional support is available to you.")
        "No one":
            $ st_q5 = "none"
            if Bl <= 1:
                $ resp = _("I'm listening.")
            elif Bl == 2:
                $ resp = _("I hear you.")
            elif Bl == 3:
                $ resp = _("That can feel difficult.")
            elif Bl == 4:
                $ resp = _("It can be hard without support.")
            else:
                $ resp = None
    if resp:
        show hana neutral at hana_pos
        e "[resp!t]"
    $ log_turn("Who can you talk to when things are difficult?", st_q5, resp)

    if st_q5 == "none":
        $ counselling_offered = True
        show hana neutral at hana_pos
        e "Would you like information about counselling support?"
        show hana listening at hana_center_listen
        menu:
            "Yes":
                $ log_turn("Would you like information about counselling support?", "yes")
                show hana neutral at hana_pos
                call support_contacts from _st_q5_contacts
            "No":
                $ log_turn("Would you like information about counselling support?", "no")
                show hana neutral at hana_pos
                e "Okay, that's fine."

label checkpoint_1:
    call compare_check("checkpoint_1") from _checkpoint_1_check
    $ start_cycle(2)
    jump cycle_2

label cycle_2:
    if stress_level in ["Normal", "Mild"]:
        show hana neutral at hana_pos
        e "What would be helpful now?"
        show hana listening at hana_center_listen
        menu:
            "Talk a little more":
                $ c2_choice = "talk"
            "Think about what helps me":
                $ c2_choice = "think"
            "Try a short activity":
                $ c2_choice = "activity"
            "Nothing right now":
                $ c2_choice = "nothing"
        $ log_turn("What would be helpful now?", c2_choice)

        if c2_choice == "talk":
            show hana neutral at hana_pos
            e "What would you like to talk about?"
            show hana listening at hana_center_listen
            menu:
                "Caring for someone":
                    $ c2_detail = "caring"
                    if Bl <= 1:
                        $ resp = _("Okay.")
                    elif Bl == 2:
                        $ resp = _("Thanks for sharing that.")
                    elif Bl == 3:
                        $ resp = _("Caring for someone matters.")
                    elif Bl == 4:
                        $ resp = _("Caring for someone sounds meaningful to you.")
                    else:
                        $ resp = _("It's good to make space to talk about caring.")
                "Family":
                    $ c2_detail = "family"
                    if Bl <= 1:
                        $ resp = _("Okay.")
                    elif Bl == 2:
                        $ resp = _("Thanks for sharing that.")
                    elif Bl == 3:
                        $ resp = _("Family can mean a lot.")
                    elif Bl == 4:
                        $ resp = _("Family sounds important to you.")
                    else:
                        $ resp = _("It's good to make space to talk about family.")
                "Work or money":
                    $ c2_detail = "work"
                    if Bl <= 1:
                        $ resp = _("Okay.")
                    elif Bl == 2:
                        $ resp = _("Thanks for sharing that.")
                    elif Bl == 3:
                        $ resp = _("Work and money matter.")
                    elif Bl == 4:
                        $ resp = _("That sounds important to you.")
                    else:
                        $ resp = _("It's good to make space to talk about this.")
                "Health":
                    $ c2_detail = "health"
                    if Bl <= 1:
                        $ resp = _("Okay.")
                    elif Bl == 2:
                        $ resp = _("Thanks for sharing that.")
                    elif Bl == 3:
                        $ resp = _("Health is important.")
                    elif Bl == 4:
                        $ resp = _("Your health sounds important to you.")
                    else:
                        $ resp = _("It's good to make space for your health.")
                "Something else":
                    $ c2_detail = "other"
                    if Bl <= 1:
                        $ resp = _("Okay.")
                    elif Bl == 2:
                        $ resp = _("Thanks for sharing that.")
                    elif Bl == 3:
                        $ resp = _("I'm glad you shared that.")
                    elif Bl == 4:
                        $ resp = _("That sounds important to you.")
                    else:
                        $ resp = _("It's good to make space for what matters to you.")
            show hana neutral at hana_pos
            e "[resp!t]"
            $ log_turn("What would you like to talk about?", c2_detail, resp)
        elif c2_choice == "think":
            call c2_help(_("What might help today?")) from _c2_ns_help
        elif c2_choice == "activity":
            call run_activity from _c2_ns_activity
        else:
            if Bl <= 1:
                $ resp = _("Okay.")
            elif Bl == 2:
                $ resp = _("That's okay.")
            elif Bl == 3:
                $ resp = _("That's okay. We can take it easy.")
            elif Bl == 4:
                $ resp = _("That's completely okay.")
            else:
                $ resp = _("That's okay. You know what you need right now.")
            show hana neutral at hana_pos
            e "[resp!t]"
            $ log_turn("What would be helpful now?", "nothing", resp)

    else:
        show hana neutral at hana_pos
        e "What would help you most now?"
        show hana listening at hana_center_listen
        menu:
            "Talk a little more":
                $ c2_choice = "talk"
            "Think about what may help":
                $ c2_choice = "think"
            "Try a short activity":
                $ c2_choice = "activity"
            "Get support information":
                $ c2_choice = "support"
        $ log_turn("What would help you most now?", c2_choice)

        if c2_choice == "talk":
            show hana neutral at hana_pos
            e "What would you like to focus on?"
            show hana listening at hana_center_listen
            menu:
                "What is worrying me":
                    $ c2_detail = "worry"
                    if Bl <= 1:
                        $ resp = _("I'm listening.")
                    elif Bl == 2:
                        $ resp = _("I understand.")
                    elif Bl == 3:
                        $ resp = _("Worries can feel heavy.")
                    elif Bl == 4:
                        $ resp = _("It makes sense to focus on that.")
                    else:
                        $ resp = _("It sounds like this worry is weighing on you.")
                "How it is affecting me":
                    $ c2_detail = "impact"
                    if Bl <= 1:
                        $ resp = _("I'm listening.")
                    elif Bl == 2:
                        $ resp = _("I understand.")
                    elif Bl == 3:
                        $ resp = _("It sounds like it affects you a lot.")
                    elif Bl == 4:
                        $ resp = _("It makes sense to look at how it affects you.")
                    else:
                        $ resp = _("It sounds like this has been hard on you.")
                "What I can do":
                    $ c2_detail = "can_do"
                    if Bl <= 1:
                        $ resp = _("I'm listening.")
                    elif Bl == 2:
                        $ resp = _("That's a good focus.")
                    elif Bl == 3:
                        $ resp = _("Small steps can help.")
                    elif Bl == 4:
                        $ resp = _("Thinking about what you can do sounds helpful.")
                    else:
                        $ resp = _("It's good to focus on what is within your control.")
                "Something else":
                    $ c2_detail = "other"
                    if Bl <= 1:
                        $ resp = _("I'm listening.")
                    elif Bl == 2:
                        $ resp = _("Take your time.")
                    elif Bl == 3:
                        $ resp = _("That sounds important.")
                    elif Bl == 4:
                        $ resp = _("It sounds like that matters to you.")
                    else:
                        $ resp = _("It's okay to focus on what matters to you.")
            show hana neutral at hana_pos
            e "[resp!t]"
            $ log_turn("What would you like to focus on?", c2_detail, resp)
        elif c2_choice == "think":
            call c2_help(_("What might help right now?")) from _c2_st_help
        elif c2_choice == "activity":
            call run_activity from _c2_st_activity
        else:
            $ counselling_offered = True
            if Bl <= 1:
                $ resp = _("Okay.")
            elif Bl == 2:
                $ resp = _("Okay, here it is.")
            elif Bl == 3:
                $ resp = _("Support can be helpful.")
            elif Bl == 4:
                $ resp = _("It's good to know where to find support.")
            else:
                $ resp = _("It's good to reach out. You don't have to face this alone.")
            show hana neutral at hana_pos
            e "[resp!t]"
            $ log_turn("What would help you most now?", "support", resp)
            call support_contacts from _c2_support_contacts

label checkpoint_2:
    call compare_check("checkpoint_2") from _checkpoint_2_check
    if cmp_ans == "better":
        show hana neutral at hana_pos
        e "Would you like to continue?"
        show hana listening at hana_center_listen
        menu:
            "Yes, please.":
                $ log_turn("Would you like to continue?", "yes")
            "No, thanks.":
                $ log_turn("Would you like to continue?", "no")
                $ closed_at = "checkpoint_2"
                show hana neutral at hana_pos
                e "Okay, that's fine."
                jump session_closure
    $ start_cycle(3)

label cycle_3:
    show hana neutral at hana_pos
    e "Would you like to try a short activity?"
    show hana listening at hana_center_listen
    menu:
        "Yes, please.":
            $ log_turn("Would you like to try a short activity?", "yes")
            call run_activity from _c3_activity
        "No, thanks.":
            if Bl <= 1:
                $ resp = _("Okay, that's fine.")
            elif Bl == 2:
                $ resp = _("Okay, that's fine.")
            elif Bl == 3:
                $ resp = _("That's okay. We can stop here.")
            elif Bl == 4:
                $ resp = _("That's completely okay.")
            else:
                $ resp = _("That's okay. You know what feels right for you.")
            show hana neutral at hana_pos
            e "[resp!t]"
            $ log_turn("Would you like to try a short activity?", "no", resp)

    call compare_check("final") from _final_check
    jump session_closure

label compare_check(check_type):
    show hana neutral at hana_pos
    e "How do you feel compared with earlier?"
    show hana listening at hana_center_listen
    menu:
        "Better":
            $ cmp_ans = "better"
            show hana smiling at hana_pos
            e "Good to hear."
        "About the same":
            $ cmp_ans = "same"
            show hana neutral at hana_pos
            e "Okay, thanks for telling me."
        "Worse":
            $ cmp_ans = "worse"
            show hana neutral at hana_pos
            e "Okay, thanks for telling me."
    $ record_check(check_type, cmp_ans)
    return

label c2_help(question):
    show hana neutral at hana_pos
    e "[question!t]"
    show hana listening at hana_center_listen
    menu:
        "Taking a short break":
            $ c2_detail = "break"
            if Bl <= 1:
                $ resp = _("Okay.")
            elif Bl == 2:
                $ resp = _("A short break can help.")
            elif Bl == 3:
                $ resp = _("It's good to give yourself a break.")
            elif Bl == 4:
                $ resp = _("A short break sounds helpful for you.")
            else:
                $ resp = _("You deserve some time to rest and reset.")
        "Talking to someone":
            $ c2_detail = "talking"
            if Bl <= 1:
                $ resp = _("Okay.")
            elif Bl == 2:
                $ resp = _("Talking can help.")
            elif Bl == 3:
                $ resp = _("It's good to have someone to talk to.")
            elif Bl == 4:
                $ resp = _("Talking to someone sounds helpful for you.")
            else:
                $ resp = _("Reaching out to someone can make a difference.")
        "Doing something calming":
            $ c2_detail = "calming"
            if Bl <= 1:
                $ resp = _("Okay.")
            elif Bl == 2:
                $ resp = _("That can help.")
            elif Bl == 3:
                $ resp = _("Something calming can be helpful.")
            elif Bl == 4:
                $ resp = _("Doing something calming sounds helpful.")
            else:
                $ resp = _("It's good to give yourself something calming.")
        "Thinking about my next step":
            $ c2_detail = "next_step"
            if Bl <= 1:
                $ resp = _("Okay.")
            elif Bl == 2:
                $ resp = _("That can help.")
            elif Bl == 3:
                $ resp = _("Thinking ahead can be helpful.")
            elif Bl == 4:
                $ resp = _("Planning your next step sounds helpful.")
            else:
                $ resp = _("Taking one small step at a time can help.")
    show hana neutral at hana_pos
    e "[resp!t]"
    $ log_turn(question, c2_detail, resp)
    return

label run_activity:
    show hana neutral at hana_pos
    e "Which activity would you like to try?"
    show hana listening at hana_center_listen
    menu:
        "Breathing":
            $ activity_done = "breathing"
        "Grounding":
            $ activity_done = "grounding"
        "Body scan":
            $ activity_done = "body_scan"
    $ activity_log.append("c%d:%s" % (cycle, activity_done))
    if Bl <= 1:
        $ resp = _("Okay.")
    elif Bl == 2:
        $ resp = _("Okay, let's try it.")
    elif Bl == 3:
        $ resp = _("That sounds like a good choice.")
    elif Bl == 4:
        $ resp = _("Let's take a few minutes for this together.")
    else:
        $ resp = _("Let's take this time for yourself together.")
    show hana neutral at hana_pos
    e "[resp!t]"
    $ log_turn("Which activity would you like to try?", activity_done, resp)
    call deliver_technique(activity_done) from _run_activity_technique
    $ hana_pos = hana_mid
    return

label support_contacts:
    show hana neutral at hana_pos
    e "UUM Counselling Centre: 04-928 4059 / 4060 / 4071"
    e "MENTARI Kota Setar: 013-434 2359"
    e "Talian HEAL: 15555"
    return

# guided activities offered by run_activity
label deliver_technique(tech):
    $ hana_pos = pick_random_scene_pos()
    python:
        if tech not in techniques_used_list:
            techniques_used_list.append(tech)

    if tech == "breathing":
        show hana neutral at hana_pos
        e "Let us start with a simple breathing exercise."
        e "When we feel stressed, we may breathe faster without noticing."
        e "Slow breathing can help the body feel calmer."
        $ hana_pos = hana_left
        show hana neutral at hana_pos
        e "Let's do it together at a comfortable pace."
        show breathing_guide at breathing_guide_pos
        python:
            renpy.show("hana neutral", at_list=[hana_left])
            e(_("Breathe in slowly through your nose for four seconds."), interact=False)
            renpy.pause(4.0)
            e(_("Hold your breath for seven seconds."), interact=False)
            renpy.pause(7.0)
            e(_("Now breathe out slowly through your mouth for eight seconds."), interact=False)
            renpy.pause(8.0)
            for _round in range(2):
                renpy.show("hana neutral", at_list=[hana_left])
                e(_("Breathe in. One, two, three, four."), interact=False)
                renpy.pause(4.0)
                renpy.show("hana neutral", at_list=[hana_left])
                e(_("Hold your breath. One, two, three, four, five, six, seven."), interact=False)
                renpy.pause(7.0)
                renpy.show("hana smiling", at_list=[hana_left])
                e(_("Breathe out. One, two, three, four, five, six, seven, eight."), interact=False)
                renpy.pause(8.0)
                if _round == 0:
                    renpy.show("hana smiling", at_list=[hana_left])
                    e(_("There you go."), interact=False)
                    renpy.pause(2.0)
                    e(_("Let us do one more round."), interact=False)
                    renpy.pause(2.0)
        hide breathing_guide
        show hana smiling at hana_pos
        e "Well done. Even a few slow breaths can help you feel calmer."

    elif tech == "grounding":
        show hana neutral at hana_pos
        e "This exercise is called the 5-4-3-2-1 grounding technique."
        e "When we feel stressed or overwhelmed, our minds can become very busy."
        e  "This exercise helps us focus on the present by noticing what we can see, hear, feel, smell, and taste."
        show hana neutral at hana_pos
        e "Take a moment to look around you. There's no need to rush."
        show hana neutral at hana_pos
        e "First, notice 5 things you can see."
        e "Next, notice 4 things you can touch or feel, like your chair, your clothes, or your hands."
        e "Now, listen for 3 sounds around you. Even quiet sounds count."
        e "Then, notice 2 things you can smell, or remember smelling recently."
        e "Finally, notice 1 thing you can taste."
        show hana smiling at hana_pos
        e "Good job. Right now, you're here. Just focus on this moment."

    elif tech == "body_scan":
        show hana neutral at hana_pos
        e "Let us try a short body scan exercise."
        e "Stress can sometimes affect the body without us noticing."
        e "You may feel tightness in your shoulders, jaw, neck, or hands."
        show hana neutral at hana_pos
        e "Take a moment to notice how your body feels."
        show hana neutral at hana_pos
        e "Start with your shoulders. Let them relax."
        e "Now notice your jaw. Let it relax, and let your tongue rest."
        e "Next, notice your hands. Let them relax and rest."
        e "Now pay attention to the rest of your body."
        e "Notice your neck, chest, stomach, or any part that feels tight."
        show hana neutral at hana_pos
        e "If you notice a tight area, that's okay."
        e "You do not need to change anything right now."
        e "Just take a slow breath and notice how your body feels."
        show hana smiling at hana_pos
        e "Well done. Noticing tension can be the first step to letting it go."

    return

label session_closure:
    if closed_at:
        $ hana_store_session("closed_after_" + closed_at)
    else:
        $ hana_store_session("activity" if activity_done else "no_activity")

    # terus save after every flow nak avoid user tak save progress
    $ renpy.save("auto-1")

    $ hana_pos = hana_mid
    show hana neutral at hana_pos
    e "That's all for today."
    e "Thank you for sharing with me."
    show hana smiling at hana_pos
    e "Take care. See you next time."
    stop music fadeout 5.0

    return