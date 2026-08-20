(function(a,c){"use strict";function p(n){const t=Object.create(null,{[Symbol.toStringTag]:{value:"Module"}});if(n){for(const e in n)if(e!=="default"){const r=Object.getOwnPropertyDescriptor(n,e);Object.defineProperty(t,e,r.get?r:{enumerable:!0,get:()=>n[e]})}}return t.default=n,Object.freeze(t)}const h=p(a);var l={exports:{}},o={};/**
 * @license React
 * react-jsx-runtime.production.js
 *
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */var x=Symbol.for("react.transitional.element"),f=Symbol.for("react.fragment");function d(n,t,e){var r=null;if(e!==void 0&&(r=""+e),t.key!==void 0&&(r=""+t.key),"key"in t){e={};for(var i in t)i!=="key"&&(e[i]=t[i])}else e=t;return t=e.ref,{$$typeof:x,type:n,key:r,ref:t!==void 0?t:null,props:e}}o.Fragment=f,o.jsx=d,o.jsxs=d,l.exports=o;var s=l.exports;const u=window.shinyreact,j=u.useShinyInitialized,y=u.useShinyInput,S=u.useShinyOutputValue;function m(){const n=j(),[t,e]=c.useState(0),[,r]=y("count",0,{debounceMs:0}),i=S("doubled",null);return c.useEffect(()=>{r(t)},[t,r]),s.jsxs("main",{style:{fontFamily:"system-ui, sans-serif",maxWidth:480,margin:"3rem auto"},children:[s.jsx("h1",{children:"Hot reload demo"}),s.jsxs("p",{children:["Shiny initialized: ",String(n)]}),s.jsxs("button",{onClick:()=>e(v=>v+1),children:["Count is ",t]}),s.jsxs("p",{children:["Server doubled it to: ",i??"…"]})]})}h.createRoot(document.body.appendChild(document.createElement("div"))).render(s.jsx(m,{}))})(window.shinyreact.ReactDOM,window.shinyreact.React);
