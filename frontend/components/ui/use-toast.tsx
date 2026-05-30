"use client";

import * as React from "react";

type ToastVariant = "default" | "destructive";

type ToastProps = {
  id: string;
  title?: string;
  description?: string;
  action?: React.ReactNode;
  variant?: ToastVariant;
  duration?: number;
};

type ToastState = {
  toasts: ToastProps[];
};

type ToastActionType =
  | { type: "ADD_TOAST"; toast: ToastProps }
  | { type: "DISMISS_TOAST"; toastId?: string }
  | { type: "REMOVE_TOAST"; toastId?: string };

const TOAST_LIMIT = 3;
const TOAST_REMOVE_DELAY = 5000;

function toastReducer(state: ToastState, action: ToastActionType): ToastState {
  switch (action.type) {
    case "ADD_TOAST":
      return {
        ...state,
        toasts: [action.toast, ...state.toasts].slice(0, TOAST_LIMIT)
      };
    case "DISMISS_TOAST":
      return {
        ...state,
        toasts: state.toasts.map((toast) =>
          toast.id === action.toastId || action.toastId === undefined
            ? { ...toast }
            : toast
        )
      };
    case "REMOVE_TOAST":
      return {
        ...state,
        toasts: state.toasts.filter((toast) => toast.id !== action.toastId)
      };
    default:
      return state;
  }
}

let toastCount = 0;

function generateId() {
  toastCount = (toastCount + 1) % Number.MAX_SAFE_INTEGER;
  return toastCount.toString();
}

const ToastStateContext = React.createContext<{
  state: ToastState;
  dispatch: React.Dispatch<ToastActionType>;
} | null>(null);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [state, dispatch] = React.useReducer(toastReducer, { toasts: [] });

  React.useEffect(() => {
    if (state.toasts.length === 0) {
      return undefined;
    }

    const timer = setTimeout(() => {
      dispatch({ type: "REMOVE_TOAST", toastId: state.toasts[0]?.id });
    }, TOAST_REMOVE_DELAY);

    return () => clearTimeout(timer);
  }, [state.toasts]);

  return (
    <ToastStateContext.Provider value={{ state, dispatch }}>
      {children}
    </ToastStateContext.Provider>
  );
}

export function useToast() {
  const context = React.useContext(ToastStateContext);
  if (!context) {
    throw new Error("useToast must be used within ToastProvider");
  }

  const toast = React.useCallback(
    ({
      title,
      description,
      action,
      variant = "default",
      duration
    }: Omit<ToastProps, "id">) => {
      const id = generateId();
      context.dispatch({
        type: "ADD_TOAST",
        toast: { id, title, description, action, variant, duration }
      });
      if (duration) {
        setTimeout(() => {
          context.dispatch({ type: "REMOVE_TOAST", toastId: id });
        }, duration);
      }
      return id;
    },
    [context]
  );

  const dismiss = React.useCallback(
    (toastId?: string) => {
      context.dispatch({ type: "DISMISS_TOAST", toastId });
      setTimeout(() => {
        context.dispatch({ type: "REMOVE_TOAST", toastId });
      }, 250);
    },
    [context]
  );

  return {
    toasts: context.state.toasts,
    toast,
    dismiss
  };
}
