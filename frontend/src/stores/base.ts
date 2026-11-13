export type Listener = () => void;

export interface Store<T> {
  subscribe: (listener: Listener) => () => void;
  getState: () => T;
  set: (patch: Partial<T> | ((state: T) => T)) => void;
}

export function createStore<T extends object>(initial: T): Store<T> {
  let state = initial;
  const listeners = new Set<Listener>();
  return {
    subscribe(listener) {
      listeners.add(listener);
      return () => {
        listeners.delete(listener);
      };
    },
    getState() {
      return state;
    },
    set(patch) {
      state = typeof patch === 'function' ? (patch as (value: T) => T)(state) : { ...state, ...patch };
      listeners.forEach((listener) => listener());
    },
  };
}
