// Temporary type shim for React when node_modules is not available locally
// This allows TypeScript to understand JSX without requiring @types/react to be installed

// Global JSX namespace - required for react-jsx mode
declare global {
  namespace JSX {
    interface IntrinsicElements {
      [elemName: string]: any;
    }
  }
}

declare module "react" {
  export = React;
  export as namespace React;
  
  namespace React {
    type ReactNode = any;
    type ReactElement = any;
    type ComponentType<P = {}> = any;
    type FC<P = {}> = (props: P) => ReactElement | null;
    
    function useState<T>(initialState: T | (() => T)): [T, (value: T | ((prev: T) => T)) => void];
    function useEffect(effect: () => void | (() => void), deps?: any[]): void;
    
    interface SyntheticEvent<T = Element, E = Event> {
      target: T;
      currentTarget: T;
      stopPropagation(): void;
    }
    
    interface MouseEvent<T = Element, E = globalThis.MouseEvent> extends SyntheticEvent<T, E> {}
    interface ChangeEvent<T = Element> extends SyntheticEvent<T> {
      target: T & { value: string };
    }
  }
  
  const React: {
    useState: typeof React.useState;
    useEffect: typeof React.useEffect;
  };
  
  export default React;
}

// Explicit module declaration for react/jsx-runtime
declare module "react/jsx-runtime" {
  type ReactElement = any;
  export function jsx(type: any, props: any, key?: string | number | null): ReactElement;
  export function jsxs(type: any, props: any, key?: string | number | null): ReactElement;
  export const Fragment: any;
}

// Also declare as react/jsx-dev-runtime for development
declare module "react/jsx-dev-runtime" {
  type ReactElement = any;
  export function jsxDEV(type: any, props: any, key?: string | number | null, isStaticChildren?: boolean, source?: any, self?: any): ReactElement;
  export const Fragment: any;
}

export {};
