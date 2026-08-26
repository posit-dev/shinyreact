var lt = Object.defineProperty;
var dt = (r, t, e) => t in r ? lt(r, t, { enumerable: !0, configurable: !0, writable: !0, value: e }) : r[t] = e;
var u = (r, t, e) => dt(r, typeof t != "symbol" ? t + "" : t, e);
import { jsx as V } from "react/jsx-runtime";
import ht, { createContext as ft, useContext as pt, useRef as w, useEffect as g, useCallback as J, useSyncExternalStore as it, useState as D } from "react";
import { createRoot as St } from "react-dom/client";
const Y = "1.0";
function yt() {
  if (typeof document > "u") return null;
  const r = document.getElementById("shinyreact-config"), t = r == null ? void 0 : r.textContent;
  if (!t) return null;
  try {
    return JSON.parse(t);
  } catch (e) {
    return console.error("shinyreact: could not parse #shinyreact-config JSON", e), null;
  }
}
function gt(r) {
  const t = (e) => e.split(".")[0];
  if (t(r) !== t(Y))
    throw new Error(
      `shinyreact protocol mismatch: the server speaks protocol ${r} but this JS client supports ${Y}. Upgrade the older side (the shinyreact R/Python package, or the client bundle) so the major protocol versions match.`
    );
}
let rt = !1;
function mt() {
  rt = !0;
}
function bt() {
  return rt;
}
const A = Symbol("MISSING");
function vt(r) {
  const t = typeof window < "u" ? window : globalThis, e = t.shinyreact = t.shinyreact || {}, n = e._restore;
  if (n && typeof n == "object" && n["-applied"])
    return;
  const i = yt();
  if (i == null && bt())
    throw new Error(
      "shinyreact: no #shinyreact-config tag found in this page. The @posit/shinyreact client requires a shinyreact server recent enough to emit it — upgrade the shinyreact Python/R package."
    );
  i != null && i.protocolVersion && gt(i.protocolVersion);
  const s = i == null ? void 0 : i.restore, a = /* @__PURE__ */ Object.create(null);
  if (s && typeof s == "object")
    for (const [o, c] of Object.entries(s))
      r.add(o, c), a[o] = c;
  e._restore = { "-applied": !0, "-values": a };
}
function b() {
  return window.Shiny;
}
let x = !1, N = !1;
const B = /* @__PURE__ */ new Set();
let G = !1, K, Q, X;
function at() {
  for (const r of B)
    r();
}
function Z() {
  x || (x = !0, at());
}
function tt(r) {
  N !== r && (N = r, at());
}
function Et() {
  if (G || typeof document > "u")
    return;
  G = !0, document.documentElement.classList.contains("shiny-busy") && (N = !0), K = () => tt(!0), Q = () => tt(!1), document.addEventListener("shiny:busy", K), document.addEventListener("shiny:idle", Q);
  const r = b();
  if (r) {
    r.initializedPromise.then(Z);
    return;
  }
  X = () => {
    const t = b();
    t && t.initializedPromise.then(Z);
  }, document.addEventListener("shiny:connected", X, {
    once: !0
  });
}
function ot(r) {
  return Et(), B.add(r), () => {
    B.delete(r);
  };
}
function et() {
  return x;
}
function nt() {
  return N;
}
class Rt {
  constructor() {
    u(this, "messageHandlers", /* @__PURE__ */ new Map());
    u(this, "initialized", !1);
  }
  /**
   * Initialize the message registry by registering the single dispatcher
   * with Shiny's custom message handler system.
   */
  init() {
    if (this.initialized)
      return;
    const t = b();
    t && (t.addCustomMessageHandler(
      "shinyReactMessage",
      (e) => {
        this.dispatchMessage(e.type, e.data);
      }
    ), this.initialized = !0);
  }
  /**
   * Add a message handler for the specified message type.
   *
   * @param messageType The type/name of the message to listen for
   * @param handler The function to call when a message of this type is received
   */
  addHandler(t, e) {
    this.init(), this.messageHandlers.has(t) || this.messageHandlers.set(t, /* @__PURE__ */ new Set()), this.messageHandlers.get(t).add(e);
  }
  /**
   * Remove a message handler for the specified message type.
   *
   * @param messageType The type/name of the message
   * @param handler The handler function to remove
   */
  removeHandler(t, e) {
    const n = this.messageHandlers.get(t);
    n && (n.delete(e), n.size === 0 && this.messageHandlers.delete(t));
  }
  /**
   * Dispatch a message to all registered handlers for the given type.
   *
   * @param messageType The type of message to dispatch
   * @param data The message data to pass to handlers
   */
  dispatchMessage(t, e) {
    const n = this.messageHandlers.get(t);
    n && n.forEach((i) => i(e));
  }
  /**
   * Get the number of handlers registered for a specific message type.
   * Useful for debugging and testing.
   *
   * @param messageType The message type to check
   * @returns The number of handlers registered for this type
   */
  getHandlerCount(t) {
    const e = this.messageHandlers.get(t);
    return e ? e.size : 0;
  }
  /**
   * Get all message types that currently have registered handlers.
   * Useful for debugging and testing.
   *
   * @returns Array of message types with active handlers
   */
  getActiveMessageTypes() {
    return Array.from(this.messageHandlers.keys());
  }
}
const Vt = new Rt();
function wt() {
  const r = b();
  r && (r.messageRegistry = Vt);
}
class Ft {
  constructor(t) {
    u(this, "id");
    u(this, "status", "pending");
    u(this, "hasValue", !1);
    // Cached most-recent value and error so a late-mounting subscriber can be
    // synced to the entry's current state without waiting for the next server
    // update. Without these, `OutputRegistry.add` would push status (e.g.
    // "ready" / "error") into the new subscriber while leaving its value/error
    // useState slots at their initial defaults — divergent state.
    u(this, "lastValue");
    u(this, "lastError", null);
    u(this, "useStateSetValueFns");
    u(this, "useStateSetStatusFns");
    u(this, "useStateSetErrorFns");
    this.id = t, this.useStateSetValueFns = /* @__PURE__ */ new Set(), this.useStateSetStatusFns = /* @__PURE__ */ new Set(), this.useStateSetErrorFns = /* @__PURE__ */ new Set();
  }
  hasReceivedValue() {
    return this.hasValue;
  }
  getLastValue() {
    return this.lastValue;
  }
  getLastError() {
    return this.lastError;
  }
  addUseStateSetValueFn(t) {
    this.useStateSetValueFns.add(t);
  }
  removeUseStateSetValueFn(t) {
    this.useStateSetValueFns.delete(t);
  }
  addUseStateSetStatusFn(t) {
    this.useStateSetStatusFns.add(t);
  }
  removeUseStateSetStatusFn(t) {
    this.useStateSetStatusFns.delete(t);
  }
  addUseStateSetErrorFn(t) {
    this.useStateSetErrorFns.add(t);
  }
  removeUseStateSetErrorFn(t) {
    this.useStateSetErrorFns.delete(t);
  }
  getStatus() {
    return this.status;
  }
  setStatus(t) {
    this.status !== t && (this.status = t, this.useStateSetStatusFns.forEach((e) => e(t)));
  }
  setValue(t) {
    this.hasValue = !0, this.lastValue = t, this.useStateSetValueFns.forEach((e) => e(t)), this.status === "error" && (this.lastError = null, this.useStateSetErrorFns.forEach((e) => e(null))), this.setStatus("ready");
  }
  setRecalculating(t) {
    t ? this.hasValue && (this.status === "error" && (this.lastError = null, this.useStateSetErrorFns.forEach((e) => e(null))), this.setStatus("recalculating")) : this.hasValue && this.status === "recalculating" && this.setStatus("ready");
  }
  setError(t) {
    this.lastError = t, this.useStateSetErrorFns.forEach((e) => e(t)), this.setStatus("error");
  }
  isEmpty() {
    return this.useStateSetValueFns.size === 0 && this.useStateSetStatusFns.size === 0 && this.useStateSetErrorFns.size === 0;
  }
}
class Ot {
  constructor() {
    u(this, "outputs", /* @__PURE__ */ new Map());
    u(this, "bindAllScheduled", !1);
    u(this, "container");
    const t = document.createElement("div");
    t.className = "shiny-react-output-container", t.style.visibility = "hidden", this.container = t, document.body.appendChild(this.container);
  }
  add(t, e, n, i) {
    let s = this.get(t);
    if (!s) {
      const a = document.createElement("div");
      a.className = "shiny-react-output", a.id = t, a.textContent = `This is the output div for ${t}`, this.container.appendChild(a), s = new Ft(t), this.outputs.set(t, s), this.scheduleBindAll();
    }
    return s.addUseStateSetValueFn(e), s.addUseStateSetStatusFn(n), s.addUseStateSetErrorFn(i), s.hasReceivedValue() && e(s.getLastValue()), n(s.getStatus()), s.getStatus() === "error" && i(s.getLastError()), () => {
      s.removeUseStateSetValueFn(e), s.removeUseStateSetStatusFn(n), s.removeUseStateSetErrorFn(i), this.scheduleCleanup(t);
    };
  }
  has(t) {
    return this.outputs.has(t);
  }
  get(t) {
    return this.outputs.get(t);
  }
  scheduleCleanup(t) {
    requestAnimationFrame(() => {
      const e = this.outputs.get(t);
      if (!e || !e.isEmpty())
        return;
      this.outputs.delete(t);
      const n = document.getElementById(t);
      n && n.remove(), this.scheduleBindAll();
    });
  }
  /**
   * Schedules a Shiny binding operation to run after DOM updates are complete.
   *
   * Note: I'm not sure if this is 100% reliable. I believe we need to avoid
   * overlapping calls to bindAll(), and am not sure if requestAnimationFrame()
   * will provide perfect reliability for this.
   */
  scheduleBindAll() {
    const t = b();
    t && (this.bindAllScheduled || (this.bindAllScheduled = !0, requestAnimationFrame(() => {
      var e, n;
      (e = t.unbindAll) == null || e.call(t, this.container), (n = t.bindAll) == null || n.call(t, this.container), this.bindAllScheduled = !1;
    })));
  }
}
function zt() {
  const r = b();
  if (!r)
    return;
  class t extends r.OutputBinding {
    find(n) {
      return $(n).find(".shiny-react-output");
    }
    renderValue(n, i) {
      var a;
      const s = (a = r.reactRegistry) == null ? void 0 : a.outputs.get(n.id);
      if (!s) {
        console.error(`Output ${n.id} not found`);
        return;
      }
      s.setValue(i);
    }
    renderError(n, i) {
      var a;
      console.error(`Error for ${n.id}:`, i);
      const s = (a = r.reactRegistry) == null ? void 0 : a.outputs.get(n.id);
      s && s.setError(i);
    }
    showProgress(n, i) {
      var a;
      const s = (a = r.reactRegistry) == null ? void 0 : a.outputs.get(n.id);
      if (!s) {
        console.error(`Output ${n.id} not found`);
        return;
      }
      s.setRecalculating(i);
    }
  }
  r.outputBindings.register(new t(), "shiny.reactOutput");
}
function j(r, t) {
  let e = null;
  const n = function(...i) {
    const s = () => {
      e = null, r(...i);
    };
    e !== null && clearTimeout(e), e = setTimeout(s, t);
  };
  return n.setDelay = (i) => {
    t = i;
  }, n.getDelay = () => t, n.cancel = () => {
    e !== null && (clearTimeout(e), e = null);
  }, n;
}
const I = class I {
  constructor(t, e) {
    u(this, "id");
    // Shiny input ID
    u(this, "value");
    u(this, "useStateSetValueFns");
    u(this, "shinySetInputValueDebounced");
    u(this, "opts", {
      debounceMs: 100
    });
    // Input-handler type suffix. Set once via updateType(); subsequent
    // mismatches throw. `undefined` is a valid finalized state ("no suffix").
    u(this, "type");
    u(this, "typeFinalized", !1);
    this.id = t, this.value = e, this.useStateSetValueFns = /* @__PURE__ */ new Set(), this.shinySetInputValueDebounced = j(
      this.setShinyInputValue.bind(this),
      this.opts.debounceMs
    );
  }
  isEmpty() {
    return this.useStateSetValueFns.size === 0;
  }
  setShinyInputValue(t) {
    var n, i;
    const e = `${this.id}:${this.type ?? I.DEFAULT_TYPE}`;
    (i = (n = b()) == null ? void 0 : n.setInputValue) == null || i.call(n, e, t, this.opts);
  }
  updateDebounceDelay(t) {
    this.shinySetInputValueDebounced.setDelay(t);
  }
  updatePriority(t) {
    this.opts.priority = t;
  }
  updateType(t) {
    if (!this.typeFinalized) {
      this.type = t, this.typeFinalized = !0;
      return;
    }
    if (t !== void 0 && this.type !== t)
      throw new Error(
        `Input "${this.id}" is already registered with type=${this.type === void 0 ? `undefined (wire id "${this.id}:${I.DEFAULT_TYPE}")` : JSON.stringify(this.type)}. A second mount requested type=${JSON.stringify(t)}. An input's handler type changes server-side semantics and must be consistent across every useShinyInput / useSetShinyInput call for the same id.`
      );
  }
  addUseStateSetValueFn(t) {
    this.useStateSetValueFns.add(t);
  }
  removeUseStateSetValueFn(t) {
    this.useStateSetValueFns.delete(t);
  }
  setValue(t) {
    const e = typeof t == "function" ? t(this.value) : t;
    this.value = e, this.useStateSetValueFns.forEach((n) => n(e)), e !== A && this.shinySetInputValueDebounced(e);
  }
  getValue() {
    return this.value;
  }
};
/** Wire-id suffix applied when no explicit `type` is set, so untyped inputs
 * route through shinyreact's server-side handler (clean records on R). */
u(I, "DEFAULT_TYPE", "shinyreact.default");
let q = I;
class Ct {
  constructor() {
    u(this, "inputs", /* @__PURE__ */ new Map());
    u(this, "pendingSubscribers", /* @__PURE__ */ new Map());
  }
  /**
   * Get an input registry entry by ID
   */
  get(t) {
    return this.inputs.get(t);
  }
  /**
   * Check if an input registry entry exists
   */
  has(t) {
    return this.inputs.has(t);
  }
  /**
   * Add a new input registry entry
   */
  add(t, e) {
    if (this.inputs.has(t))
      throw new Error(`Input ${t} already exists`);
    const n = new q(t, e);
    this.inputs.set(t, n);
    const i = this.pendingSubscribers.get(t);
    return i && (i.forEach((s) => {
      n.addUseStateSetValueFn(s), s(n.getValue());
    }), this.pendingSubscribers.delete(t)), n;
  }
  /**
   * Get or create an input registry entry
   *
   * Note that value is used only if the entry is created; if it already exists,
   * then the existing entry is returned and the value is unused.
   */
  getOrCreate(t, e) {
    let n = this.get(t);
    return n || (n = this.add(t, e)), n;
  }
  /**
   * Read-only subscription to an input value.
   *
   * If the entry already exists, attaches the subscriber and immediately
   * calls it with the current value (parity with `useState` initial mount
   * semantics). If the entry does not yet exist (consumer mounted before
   * producer), the subscriber is queued and attached when `add()` later
   * creates the entry.
   *
   * @returns A dispose function that detaches the subscriber, whether or
   * not the entry currently exists.
   */
  subscribe(t, e) {
    const n = this.get(t);
    if (n)
      return n.addUseStateSetValueFn(e), e(n.getValue()), () => {
        const s = this.get(t);
        s && s.removeUseStateSetValueFn(e);
      };
    let i = this.pendingSubscribers.get(t);
    return i || (i = /* @__PURE__ */ new Set(), this.pendingSubscribers.set(t, i)), i.add(e), () => {
      const s = this.get(t);
      if (s) {
        s.removeUseStateSetValueFn(e);
        return;
      }
      const a = this.pendingSubscribers.get(t);
      a && (a.delete(e), a.size === 0 && this.pendingSubscribers.delete(t));
    };
  }
  /**
   * Remove an input registry entry
   */
  remove(t) {
    const e = this.inputs.get(t);
    return e && e.shinySetInputValueDebounced.cancel(), this.inputs.delete(t);
  }
  /**
   * Get all input IDs
   */
  keys() {
    return this.inputs.keys();
  }
  /**
   * Get the number of registered inputs
   */
  size() {
    return this.inputs.size;
  }
}
let P;
function It() {
  P = {
    inputs: new Ct(),
    outputs: new Ot()
  };
  const r = b();
  r && (r.reactRegistry = P);
}
function m() {
  const r = b();
  if (!r) {
    if (!P)
      throw new Error("React registry not initialized");
    return P;
  }
  return r.reactRegistry;
}
const ut = ft(null);
function $t({
  namespace: r,
  children: t
}) {
  return /* @__PURE__ */ V(ut.Provider, { value: r, children: t });
}
function At() {
  return pt(ut);
}
function Dt(r, t) {
  return t ? `${t}-${r}` : r;
}
function R(r, t) {
  const e = At();
  return Dt(r, t !== void 0 ? t : e);
}
function k(r, t, {
  debounceMs: e = 100,
  priority: n,
  namespace: i,
  type: s
} = {}) {
  if (O(), s !== void 0 && !/^[^\s:]+$/.test(s))
    throw new Error(
      `useShinyInput("${r}"): invalid type=${JSON.stringify(s)}. Must be non-empty and contain no whitespace or ':' characters.`
    );
  const a = R(r, i), c = w(t).current;
  let p = c;
  const d = m().inputs.get(
    a
  );
  d && (p = d.getValue());
  const [f, H] = D(p), S = F();
  g(() => {
    if (!S)
      return;
    const y = m().inputs.getOrCreate(
      a,
      c
    );
    return e !== void 0 && y.updateDebounceDelay(e), n && y.updatePriority(n), y.updateType(s), y.addUseStateSetValueFn(H), y.setValue(y.getValue()), () => {
      y.removeUseStateSetValueFn(H);
    };
  }, [a, S, e, n, c, s]);
  const U = J(
    (v) => {
      if (!S)
        return;
      const T = m().inputs.get(a);
      if (!T) {
        console.error(`Input ${a} not found`);
        return;
      }
      T.setValue(v);
    },
    [a, S]
  );
  return [f, U];
}
const _ = () => {
};
function Ht(r, t = void 0, {
  namespace: e
} = {}) {
  const [n, i] = D(t), s = F();
  O();
  const a = R(r, e);
  return g(() => s ? m().outputs.add(
    a,
    i,
    _,
    _
  ) : void 0, [a, s]), n;
}
function Ut(r, {
  namespace: t
} = {}) {
  const [e, n] = D("pending"), i = F();
  O();
  const s = R(r, t);
  return g(() => i ? m().outputs.add(
    s,
    _,
    n,
    _
  ) : void 0, [s, i]), e;
}
function _t(r, {
  namespace: t
} = {}) {
  O();
  const e = R(r, t), [n, i] = D(() => {
    const a = m().inputs.get(e);
    if (!a) return;
    const o = a.getValue();
    return o === A ? void 0 : o;
  }), s = F();
  return g(() => s ? m().inputs.subscribe(e, (c) => {
    i(c === A ? void 0 : c);
  }) : void 0, [e, s]), n;
}
function kt(r, t, {
  debounceMs: e = 100,
  priority: n,
  namespace: i,
  type: s
} = {}) {
  if (O(), s !== void 0 && !/^[^\s:]+$/.test(s))
    throw new Error(
      `useSetShinyInput("${r}"): invalid type=${JSON.stringify(s)}. Must be non-empty and contain no whitespace or ':' characters.`
    );
  const a = R(r, i), c = w(t).current, p = F();
  return g(() => {
    if (!p)
      return;
    const d = m().inputs.getOrCreate(
      a,
      c
    );
    e !== void 0 && d.updateDebounceDelay(e), n && d.updatePriority(n), d.updateType(s), d.setValue(d.getValue());
  }, [a, p, e, n, c, s]), J(
    (l) => {
      if (!p)
        return;
      const f = m().inputs.get(a);
      if (!f) {
        console.error(`Input ${a} not found`);
        return;
      }
      f.setValue(l);
    },
    [a, p]
  );
}
function xt(r, t, {
  namespace: e
} = {}) {
  const n = F();
  O();
  const i = R(r, e), s = w(t);
  s.current = t, g(() => {
    if (!n || !i)
      return;
    const a = b();
    if (!a)
      return;
    const o = (c) => s.current(c);
    return a.messageRegistry.addHandler(i, o), () => {
      a.messageRegistry.removeHandler(i, o);
    };
  }, [n, i]);
}
function F() {
  return it(
    ot,
    et,
    et
  );
}
function Bt() {
  return it(
    ot,
    nt,
    nt
  );
}
let st = !1;
function O() {
  st || (It(), vt(m().inputs), zt(), wt(), st = !0);
}
function jt({
  id: r,
  className: t,
  width: e,
  height: n,
  debounceMs: i = 400,
  onRecalculating: s,
  namespace: a
}) {
  const o = R(r, a), c = { namespace: null }, [p, l] = k(
    `.clientdata_output_${o}_width`,
    A,
    c
  ), [d, f] = k(
    `.clientdata_output_${o}_height`,
    A,
    c
  ), [H] = k(
    `.clientdata_output_${o}_hidden`,
    !1,
    c
  ), S = Ht(o, void 0, c), U = Ut(o, c), v = w(null), y = w(null), [T, ct] = D(0);
  g(() => {
    S && ct((h) => h + 1);
  }, [S]), g(() => {
    s && s(U === "recalculating");
  }, [U, s]);
  const z = J(() => {
    if (v.current) {
      const h = v.current.clientWidth, E = v.current.clientHeight;
      h > 0 && E > 0 && (l(h), f(E));
    }
  }, [l, f]);
  return g(() => {
    const h = v.current;
    if (!h) return;
    h.addEventListener("load", z);
    const E = j(() => {
      h && h.complete && z();
    }, i), C = new ResizeObserver((L) => {
      for (const M of L)
        M.target === h && E();
    });
    return C.observe(h), () => {
      h.removeEventListener("load", z), C.disconnect(), E.cancel();
    };
  }, [
    v,
    T,
    l,
    f,
    i,
    z
  ]), g(() => {
    if (S) return;
    const h = y.current;
    if (!h) return;
    const E = () => {
      const M = h.clientWidth, W = h.clientHeight;
      M > 0 && W > 0 && (l(M), f(W));
    };
    E();
    const C = j(E, i), L = new ResizeObserver(() => C());
    return L.observe(h), () => {
      L.disconnect(), C.cancel();
    };
  }, [S, l, f, i]), H ? null : S ? /* @__PURE__ */ V(
    "img",
    {
      ref: v,
      src: S.src,
      alt: "",
      className: t,
      style: {
        width: e,
        height: n
      },
      onLoad: z
    }
  ) : /* @__PURE__ */ V(
    "div",
    {
      ref: y,
      className: t,
      style: {
        width: e,
        height: n,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        color: "#9ca3af"
      },
      children: /* @__PURE__ */ V(
        "svg",
        {
          width: "24",
          height: "24",
          viewBox: "0 0 24 24",
          fill: "none",
          style: {
            animation: "spin 1s linear infinite"
          },
          children: /* @__PURE__ */ V(
            "circle",
            {
              cx: "12",
              cy: "12",
              r: "10",
              stroke: "currentColor",
              strokeWidth: "2.5",
              strokeDasharray: "31.4 31.4",
              strokeLinecap: "round"
            }
          )
        }
      )
    }
  );
}
class Tt extends HTMLElement {
  constructor() {
    super(...arguments);
    u(this, "root", null);
    u(this, "slotContents", /* @__PURE__ */ new Map());
  }
  /**
   * Captures children with [data-slot] attribute, storing their contents
   * keyed by slot name. Called automatically in connectedCallback.
   *
   * Named slots are captured by their `data-slot` attribute value.
   * All remaining direct children (without a `data-slot` attribute) are
   * captured under the reserved slot name "__children__".
   *
   * @param selector CSS selector for slot containers (default: '[data-slot]')
   * @returns Map of slot names to their child nodes
   */
  captureSlots(e = "[data-slot]") {
    const n = this.querySelectorAll(`:scope > ${e}`), i = new Set(n);
    n.forEach((a) => {
      const o = a.getAttribute("data-slot");
      o && this.slotContents.set(o, Array.from(a.childNodes));
    });
    const s = Array.from(this.childNodes).filter(
      (a) => !i.has(a)
    );
    return s.length > 0 && this.slotContents.set("__children__", s), this.slotContents;
  }
  /**
   * Moves captured slot content into a container element and initializes
   * Shiny bindings. Call this from your React component via onSlotMount callback.
   *
   * @param slotName The slot identifier (from data-slot attribute)
   * @param container The DOM element to move content into
   */
  async mountSlot(e, n) {
    var s, a;
    const i = this.slotContents.get(e);
    i && n && (i.forEach((o) => n.appendChild(o)), await ((a = (s = window.Shiny) == null ? void 0 : s.bindAll) == null ? void 0 : a.call(s, n)));
  }
  /**
   * Bound callback for mounting slots. Pass this to your React component
   * to handle slot content mounting.
   *
   * @example
   * ```typescript
   * protected render() {
   *   return <MyLayout onSlotMount={this.onSlotMount} />;
   * }
   * ```
   */
  get onSlotMount() {
    return this.mountSlot.bind(this);
  }
  /**
   * Converts data-* attributes to a props object.
   * Automatically attempts JSON parsing for rich values (numbers, booleans,
   * arrays, objects). Falls back to string if parsing fails.
   *
   * @returns Config object with parsed data attributes
   *
   * @example
   * ```html
   * <my-element data-count="5" data-enabled="true" data-items="[1,2,3]" data-title="Hello">
   * ```
   * Results in: { count: 5, enabled: true, items: [1,2,3], title: "Hello" }
   */
  getConfig() {
    const e = {};
    for (const [n, i] of Object.entries(this.dataset))
      if (i !== void 0)
        try {
          e[n] = JSON.parse(i);
        } catch {
          e[n] = i;
        }
    return e;
  }
  /**
   * The namespace for Shiny module support, derived from the element's id.
   * Returns undefined if no id is set.
   */
  get namespace() {
    return this.id || void 0;
  }
  /**
   * Renders the React component. Override this to customize rendering,
   * pass additional props, or wrap in providers.
   *
   * @returns React node to render
   */
  render() {
    const e = this.constructor.component;
    return e ? /* @__PURE__ */ V(e, { ...this.getConfig() }) : (console.error(`${this.constructor.name}: No static component defined`), null);
  }
  /**
   * Wraps content in ShinyModuleProvider if namespace exists.
   */
  wrapWithProvider(e) {
    return this.namespace ? /* @__PURE__ */ V($t, { namespace: this.namespace, children: e }) : e;
  }
  /**
   * Clears the element's innerHTML before React renders.
   * Override with a no-op if you need to preserve existing content.
   */
  clearContent() {
    this.innerHTML = "";
  }
  /**
   * Called when the element is added to the DOM.
   * Captures slots, clears content, and renders the React component.
   */
  connectedCallback() {
    this.captureSlots(), this.clearContent(), this.root = St(this), this.root.render(this.wrapWithProvider(this.render()));
  }
  /**
   * Called when the element is removed from the DOM.
   * Unbinds Shiny and unmounts the React root.
   */
  disconnectedCallback() {
    var e, n, i;
    (n = (e = window.Shiny) == null ? void 0 : e.unbindAll) == null || n.call(e, this), (i = this.root) == null || i.unmount(), this.root = null;
  }
}
/**
 * The React component to render. Set this on your subclass.
 * @example
 * ```typescript
 * class MyElement extends ShinyReactComponentElement {
 *   static component = MyReactComponent;
 * }
 * ```
 */
u(Tt, "component", null);
function qt({
  id: r,
  tagName: t = "div",
  namespace: e,
  ...n
}) {
  const i = R(r, e), s = w(null);
  return g(() => {
    var p;
    const a = s.current, o = a == null ? void 0 : a.parentElement;
    if (!a || !o || !((p = window.Shiny) != null && p.bindAll)) return;
    const c = (l, d) => {
      console.error(
        `[shinyreact] ShinyOutput "${i}" ${d} failed:`,
        { id: i, phase: d, error: l }
      );
    };
    try {
      const l = window.Shiny.bindAll(o);
      l && typeof l.catch == "function" && l.catch((d) => c(d, "bindAll"));
    } catch (l) {
      c(l, "bindAll");
    }
    return () => {
      var l, d;
      try {
        (d = (l = window.Shiny) == null ? void 0 : l.unbindAll) == null || d.call(l, a, !0);
      } catch (f) {
        c(f, "unbindAll");
      }
    };
  }, [i, t]), ht.createElement(t, { id: i, ref: s, ...n });
}
mt();
export {
  jt as ImageOutput,
  A as MISSING,
  Y as PROTOCOL_VERSION,
  $t as ShinyModuleProvider,
  qt as ShinyOutput,
  Tt as ShinyReactComponentElement,
  kt as useSetShinyInput,
  Bt as useShinyBusy,
  F as useShinyInitialized,
  k as useShinyInput,
  _t as useShinyInputValue,
  xt as useShinyMessageHandler,
  Ut as useShinyOutputStatus,
  Ht as useShinyOutputValue
};
//# sourceMappingURL=index.js.map
