/* eslint-disable @typescript-eslint/no-explicit-any */
// PROD path. The hooks come from the shinyreact bridge global, sharing the one
// React instance that owns them. This file is aliased in by vite.config only for
// `vite build`.
const sr = (window as any).shinyreact;

export const useShinyInitialized = sr.useShinyInitialized;
export const useShinyInput = sr.useShinyInput;
export const useShinyOutputValue = sr.useShinyOutputValue;
